from decoder_forge.pattern import Pattern
from functools import reduce
from dataclasses import dataclass
from typing import cast
from typing import Optional


@dataclass(eq=True, frozen=True)
class DecodeNode:
    """Base class for nodes in a decode tree.

    This class acts as an abstract base class for different node types used in
    representing a hierarchical decode tree built from Pattern objects.
    """

    pass


@dataclass(eq=True, frozen=True)
class DecodeLeaf(DecodeNode):
    """Leaf node in a decode tree holding a Pattern and its original form.

    Attributes:
        pat (Pattern): The pattern after processing (e.g. after applying a mask).
        origin (Pattern): The original Pattern from which this leaf was derived.
    """

    pat: Pattern
    origin: Pattern


@dataclass(eq=True, frozen=True)
class DecodeTree(DecodeNode):
    """Internal tree node representing a group of Patterns sharing fixed bits.

    Attributes:
        pat (Pattern): A Pattern representing the common fixed bits for this group.
            Can be None for the root node.
        children (list[DecodeNode]): A list of child nodes (either DecodeLeaf or
            DecodeTree) representing further subdivisions of patterns.
    """

    pat: Optional[Pattern]
    children: list[DecodeNode]


def compute_common_fixedmask(pats: list[Pattern]) -> int:
    """
    Compute the common fixed mask for a list of Pattern objects.

    This function calculates the bitwise AND (intersection) of the fixedmask
    attributes from all Pattern objects in the provided list. The result is an integer
    that represents the bits that are fixed (common) across every pattern.

    Args:
        pats (list[Pattern]): A list of Pattern objects whose fixedmask values will be
            combined.

    Returns:
        int: The bitwise AND of all fixedmask attributes of the Pattern objects.

    Examples:
        >>> p1 = Pattern(0b111, 0b101, 3)
        >>> p2 = Pattern(0b101, 0b001, 3)
        >>> compute_common_fixedmask([p1, p2])
        5
    """

    def logic_and(fma: int, fmb: int) -> int:
        return fma & fmb

    out = reduce(logic_and, (i.fixedmask for i in pats))
    return out


def build_groups_by_fixed_bits(
    pats: list[Pattern],
) -> dict[Pattern, list[tuple[Pattern, Pattern]]]:
    """
    Group Patterns based on their fixed bits after splitting by a common mask.

    This function computes a common fixed mask for the provided Pattern objects and
    then splits each pattern using the 'split_by_mask' method. The patterns are grouped
    by the part of the pattern that corresponds to the fixed bits of the computed mask.

    Args:
        pats (list[Pattern]): A list of Pattern objects to be grouped.

    Returns:
        dict: A dictionary where each key is the fixed portion (result of splitting by
        the mask) and each value is a list of tuples. Each tuple contains:

        - The remainder of the pattern after splitting
        - The original Pattern object before the split

    Raises:
        ValueError: If 'split_by_mask' is invoked with a mask not contained within the
            pattern's fixedmask.
    """

    # find fixed parts
    mask = compute_common_fixedmask(pats)

    groups: dict[Pattern, list[tuple[Pattern, Pattern]]] = {}
    for pn in pats:
        pa, pb = pn.split_by_mask(mask)
        group = groups.get(pa, list())
        group.append((pb, pn))
        groups[pa] = group

    return groups


def build_decode_tree_by_fixed_bits(
    pats: list[Pattern],
) -> DecodeTree:
    """
    Construct a hierarchical decode tree of Pattern objects grouped by shared fixed
    bits.

    This function organizes the provided list of Pattern objects into a tree structure.
    Each Pattern is first wrapped as a DecodeLeaf node and set as a child of the root
    DecodeTree node. The tree is built iteratively by:

    1. Clearing the children of the current tree node.
    2. Grouping its Patterns by computing the common fixed mask and splitting them.
    3. For each group:

       - If the group has a single member, combine the fixed bits with the inner pattern
         (using the combine method) and create a DecodeLeaf.
       - If the group's fixed portion (outer pattern) has a non-zero fixedmask, create a
         new DecodeTree with DecodeLeaf children, and schedule that subtree for further
         processing.
       - Otherwise, simply append the corresponding DecodeLeaf nodes.

    Args:
        pats (list[Pattern]): A list of Pattern objects to be organized into a decode
          tree.

    Returns:
        DecodeTree: The root node of the constructed decode tree representing
        hierarchical grouping.

    Raises:
        ValueError: If 'split_by_mask' is invoked with an invalid mask for any Pattern.

    Example:
        >>> tree = build_decode_tree_by_fixed_bits([pattern1, pattern2, pattern3])
        >>> print(tree)
    """

    pats_unfolded: list[DecodeNode] = [DecodeLeaf(pat=i, origin=i) for i in pats]
    root = DecodeTree(pat=None, children=pats_unfolded)

    stack: list[DecodeTree] = []
    stack.append(root)

    while len(stack) != 0:
        current_tree = stack.pop()
        leafs = cast(list[DecodeLeaf], [i for i in current_tree.children])

        if len(pats) == 0:
            continue

        current_tree.children.clear()

        # remember which patterns were orginated by which origin
        pats_to_origins = {i.pat: i.origin for i in leafs}

        # split pats into groups with fixed bits
        fgrps = build_groups_by_fixed_bits([i.pat for i in leafs])

        for outer_pat, inner_pats in fgrps.items():
            if len(inner_pats) == 1:
                combined_pat = outer_pat.combine(inner_pats[0][0])
                src_pat = inner_pats[0][1]
                dleaf = DecodeLeaf(pat=combined_pat, origin=pats_to_origins[src_pat])
                current_tree.children.append(dleaf)
            else:
                if outer_pat.fixedmask != 0x0:  # catch all
                    children: list[DecodeNode] = [
                        DecodeLeaf(pat=i, origin=pats_to_origins[src_pat])
                        for (i, src_pat) in inner_pats
                    ]

                    dtree = DecodeTree(pat=outer_pat, children=children)
                    current_tree.children.append(dtree)
                    stack.append(dtree)  # process during next cycles
                else:
                    children = [
                        DecodeLeaf(pat=i, origin=pats_to_origins[src_pat])
                        for (i, src_pat) in inner_pats
                    ]
                    current_tree.children.extend(children)

    return root


def flatten_decode_tree(tree: DecodeTree):
    """
    Flatten a hierarchical DecodeTree into a list of tuples.

    This function converts a DecodeTree hierarchy into a flat list for easier
    traversal or debugging. Each element in the list is a tuple containing:

    - The Pattern object at that node.
    - The original Pattern object (None for internal tree nodes).
    - The depth level of the node within the tree.
    - A boolean indicating if the node is the first child
    - A boolean indicating if the node is the last child (used for backtracking
      information during visual representation).

    Args:
        tree (DecodeTree): The root node of the DecodeTree to be flattened.

    Returns:
        list: A list of tuples, each containing:
            (Pattern, origin Pattern or None, depth integer, last_child flag boolean).

    Example:
        >>> flat_list = build_flat_tree(tree)
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
    flattend_tree: list[tuple[Pattern, Optional[Pattern], int, bool, bool]] = []
    while len(stack) != 0:
        item, depth, first_child, last_child = stack.pop()
        if isinstance(item, DecodeLeaf):
            flattend_tree.append(
                (item.pat, item.origin, depth, first_child, last_child)
            )
        elif isinstance(item, DecodeTree):
            dtree = cast(DecodeTree, item)
            assert dtree.pat is not None
            flattend_tree.append((dtree.pat, None, depth, first_child, last_child))
            stack.extend(
                (
                    (i, depth + 1, idx == len(item.children) - 1, idx == 0)
                    for idx, i in enumerate(reversed(item.children))
                )
            )
    return flattend_tree
