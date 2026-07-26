import operator
from decoder_forge.bit_pattern import BitPattern
from functools import reduce
from dataclasses import dataclass
from typing import cast
from typing import Optional
from uuid import uuid1


@dataclass(eq=True, frozen=True)
class DecodeNode:
    """
    Base class for nodes in a decode tree.

    This abstract class is used as a parent for different node types in a hierarchical
    decode tree built from BitPattern objects.

    Attributes:
        uid (str): A unique identifier for the node.
    """

    uid: str


@dataclass(eq=True, frozen=True)
class DecodeLeaf(DecodeNode):
    """Leaf node in a decode tree holding a BitPattern and its original form.

    Attributes:
        pat (BitPattern): The pattern after processing (e.g. after applying a mask).
    """

    pat: BitPattern


@dataclass(eq=True, frozen=True)
class DecodeTree(DecodeNode):
    """Internal tree node representing a group of BitPatterns sharing fixed bits.

    Attributes:
        pat (BitPattern): A BitPattern representing the common fixed bits for this
            group.  Can be None for the root node.
        children (list[DecodeNode]): A list of child nodes (either DecodeLeaf or
            DecodeTree) representing further subdivisions of patterns.
    """

    pat: Optional[BitPattern]
    children: list[DecodeNode]


def compute_common_fixedmask(pats: list[BitPattern]) -> int:
    """Compute the common fixed mask for a list of BitPattern objects.

    This function calculates the bitwise AND (intersection) of the fixedmask attributes
    from all BitPattern objects in the provided list. The result is an integer that
    represents the bits that are fixed (common) across every pattern.

    Args:
        pats (list[BitPattern]): A list of BitPattern objects whose fixedmask values
            will be combined.

    Returns:
        int: The bitwise AND of all fixedmask attributes of the BitPattern objects.

    Examples:
        >>> p1 = BitPattern(0b111, 0b101, 3)
        >>> p2 = BitPattern(0b101, 0b001, 3)
        >>> compute_common_fixedmask([p1, p2])
        5

    """

    return reduce(operator.and_, (i.fixedmask for i in pats))


def build_groups_by_fixed_bits(
    pats: list[BitPattern],
) -> dict[BitPattern, list[tuple[BitPattern, BitPattern]]]:
    """
    Group BitPatterns based on their fixed bits after splitting by a common mask.

    This function computes a common fixed mask for the provided BitPattern objects and
    then splits each pattern using the 'split_by_mask' method. The patterns are grouped
    by the part of the pattern that corresponds to the fixed bits of the computed mask.

    Args:
        pats (list[BitPattern]): A list of BitPattern objects to be grouped.

    Returns:
        dict: A dictionary where each key is the fixed portion (result of splitting by
        the mask) and each value is a list of tuples. Each tuple contains:

        - The remainder of the pattern after splitting
        - The original BitPattern object before the split

    Raises:
        ValueError: If 'split_by_mask' is invoked with a mask not contained within the
            pattern's fixedmask.
    """

    # find fixed parts
    mask = compute_common_fixedmask(pats)

    groups: dict[BitPattern, list[tuple[BitPattern, BitPattern]]] = {}
    for pn in pats:
        pa, pb = pn.split_by_mask(mask)
        group = groups.get(pa, list())
        group.append((pb, pn))
        groups[pa] = group

    return groups


UID = str
BitPatternWithUID = tuple[BitPattern, UID]


def assign_uids(
    pats: list[BitPattern],
) -> tuple[dict[UID, BitPattern], dict[BitPattern, UID], list[BitPatternWithUID]]:
    """Assign a fresh UID to each BitPattern and build the lookup structures.

    Both the code generator and the decode-tree viewer need to correlate a pattern
    with a stable identifier while the tree is built and flattened. This mints one
    ``uuid1()`` per pattern and returns the mappings both directions plus the
    ``(pattern, uid)`` pairs the tree builder consumes.

    Args:
        pats (list[BitPattern]): The patterns to identify.

    Returns:
        tuple: ``(uid_to_pat, pat_to_uid, pats_with_uid)``.
    """

    uid_to_pat = {uuid1(): pat for pat in pats}
    pat_to_uid = {pat: uid for uid, pat in uid_to_pat.items()}
    pats_with_uid = [(pat, pat_to_uid[pat]) for pat in pats]
    return uid_to_pat, pat_to_uid, pats_with_uid


def build_decode_tree_by_fixed_bits(
    pats: list[BitPatternWithUID], decoder_width: int
) -> DecodeTree:
    """Build a hierarchical decode tree by grouping BitPattern objects with shared
    fixed bits.

    Each BitPattern is first extended to the target decoder_width using
    extend_and_shift_to_msb() and wrapped into a DecodeLeaf. The leaves are grouped into
    a tree by computing a common fixed mask and splitting the patterns with
    split_by_mask. Groups with a single pattern are merged, while groups with multiple
    patterns form subtrees.

    Args:
        pats (list[BitPatternWithUID]): A list of tuples, each containing a BitPattern
           and its UID.
        decoder_width (int): The target bit width for extending each BitPattern.

    Returns:
        DecodeTree: The root node of the constructed decode tree.

    Raises:
        ValueError: If a BitPattern cannot be split with the computed common fixed mask.

     Example:
        >>> tree = build_decode_tree_by_fixed_bits([(pattern1, 'id1'), (pattern2, 'id2')], 8)
        >>> print(tree)
    """
    pats_unfolded: list[DecodeNode] = [
        DecodeLeaf(pat=i.extend_and_shift_to_msb(decoder_width), uid=uid)
        for i, uid in pats
    ]

    root = DecodeTree(pat=None, children=pats_unfolded, uid="")

    stack: list[DecodeTree] = []
    stack.append(root)

    def longest_match(i):
        pat_str = str(i.pat)
        no_zeros = pat_str.count("0")
        no_ones = pat_str.count("1")
        return no_zeros + no_ones

    while len(stack) != 0:
        current_tree = stack.pop()
        leafs = cast(list[DecodeLeaf], list(current_tree.children))
        current_tree.children.clear()

        # remember which patterns were orginated by which origin
        pats_to_uids = {i.pat: i.uid for i in leafs}

        # split pats into groups with fixed bits
        fgrps = build_groups_by_fixed_bits([i.pat for i in leafs])

        for outer_pat, inner_pats in fgrps.items():
            if len(inner_pats) == 1:
                # A lone pattern folds its fixed bits back into the group's and
                # becomes a leaf directly.
                combined_pat = outer_pat.combine(inner_pats[0][0])
                src_pat = inner_pats[0][1]
                current_tree.children.append(
                    DecodeLeaf(pat=combined_pat, uid=pats_to_uids[src_pat])
                )
                continue

            children: list[DecodeNode] = [
                DecodeLeaf(pat=i, uid=pats_to_uids[src_pat])
                for (i, src_pat) in inner_pats
            ]
            if outer_pat.fixedmask != 0x0:
                # Shared fixed bits form a subtree to refine on the next cycle.
                dtree = DecodeTree(pat=outer_pat, children=children, uid="")
                current_tree.children.append(dtree)
                stack.append(dtree)
            else:
                # Nothing left in common (catch-all): splice the leaves in place.
                current_tree.children.extend(children)

        # keep children list sorted (most fixed bits first)
        current_tree.children.sort(key=longest_match, reverse=True)
    return root


def flatten_decode_tree(
    tree: DecodeTree,
) -> list[tuple[BitPattern, UID, int, bool, bool]]:
    """Flatten a hierarchical DecodeTree into a flat list of tuples.

    The function traverses the decode tree and converts it into a flat list. Each tuple
    in the list contains the BitPattern, its associated UID, the depth level in the
    tree, a flag indicating if it is the first child, and a flag indicating if it is the
    last child.

    Args:
        tree (DecodeTree): The root node of the decode tree to flatten.

    Returns:
        list[tuple[BitPattern, UID, int, bool, bool]]:
            A list of tuples, where each tuple contains:
              - BitPattern: The pattern at the node.
              - UID: The unique identifier associated with the pattern.
              - int: The depth level in the tree.
              - bool: True if the node is the first child.
              - bool: True if the node is the last child.

    Example:
        >>> flat_list = flatten_decode_tree(tree)
        >>> for node in flat_list:
        ...     print(node)

    """

    stack: list[tuple[DecodeNode, int, bool, bool]] = []
    stack.extend(
        (
            (i, 0, idx == len(tree.children) - 1, idx == 0)
            for idx, i in enumerate(reversed(tree.children))
        )
    )

    flattend_tree: list[tuple[BitPattern, UID, int, bool, bool]] = []
    while len(stack) != 0:
        item, depth, first_child, last_child = stack.pop()
        if isinstance(item, DecodeLeaf):
            flattend_tree.append((item.pat, item.uid, depth, first_child, last_child))
        elif isinstance(item, DecodeTree):
            dtree = cast(DecodeTree, item)
            assert dtree.pat is not None
            flattend_tree.append((dtree.pat, dtree.uid, depth, first_child, last_child))

            stack.extend(
                (
                    (i, depth + 1, idx == len(item.children) - 1, idx == 0)
                    for idx, i in enumerate(reversed(item.children))
                )
            )
    return flattend_tree
