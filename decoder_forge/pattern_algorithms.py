from decoder_forge.pattern import Pattern
from functools import reduce
from dataclasses import dataclass


class DecodeNode:
    pass


@dataclass(eq=True, frozen=True)
class DecodeLeaf(DecodeNode):
    pat: Pattern
    origin: Pattern


@dataclass(eq=True, frozen=True)
class DecodeTree(DecodeNode):
    pat: Pattern
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


def build_groups_by_fixed_bits(pats: list[Pattern]):
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

    groups = {}
    for pn in pats:
        pa, pb = pn.split_by_mask(mask)
        group = groups.get(pa, list())
        group.append((pb, pn))
        groups[pa] = group

    return groups


def build_decode_tree_by_fixed_bits(
    pats: list[Pattern],
) -> dict[Pattern, [Pattern]]:
    """
    Generate a hierarchical tree of Patterns grouped by shared fixed bits.

    This function organizes a list of Pattern objects into a tree structure based on
    their common fixed bits. It starts by wrapping each Pattern in a DecodeLeaf node
    and using these nodes as children of a root DecodeTree node. Then, in each
    iteration:

      1. It clears the current node's children and groups the patterns based on fixed
         bits by computing a common fixed mask and splitting them with 'split_by_mask'.
      2. For each group:

         - If the group has a single element, a DecodeLeaf node is created.
         - If the group's fixed portion (outer pattern) has a non-zero fixedmask, a new
           DecodeTree node is created with DecodeLeaf children, and that subtree is
           scheduled for further processing.
         - Otherwise, each pattern in the group becomes a DecodeLeaf node.

    Args:
        pats (list[Pattern]): A list of Pattern objects to be organized.

    Returns:
        DecodeTree: The root node of the generated pattern tree containing hierarchical
        grouping based on common fixed bits.

    Raises:
        ValueError: If 'split_by_mask' is invoked with a mask not contained in a
            Pattern's 'fixedmask'.

    Example:
        >>> # Assuming pattern1, pattern2, and pattern3 are valid Pattern objects with 'split_by_mask'
        >>> tree = build_decode_tree_by_fixed_bits([pattern1, pattern2, pattern3])
        >>> print(tree)
    """

    pats_unfolded = [DecodeLeaf(pat=i, origin=i) for i in pats]
    root = DecodeTree(pat=None, children=pats_unfolded)

    stack = []
    stack.append(root)

    while len(stack) != 0:
        current_tree = stack.pop()
        pats = [i for i in current_tree.children]

        if len(pats) == 0:
            continue

        current_tree.children.clear()

        # remember which patterns were orginated by which origin
        pats_to_origins = {i.pat: i.origin for i in pats}

        # split pats into groups with fixed bits
        fgrps = build_groups_by_fixed_bits([i.pat for i in pats])

        for outter_pat, inner_pats in fgrps.items():
            if len(inner_pats) == 1:
                src_pat = inner_pats[0][1]
                fpat = DecodeLeaf(pat=outter_pat, origin=pats_to_origins[src_pat])
                current_tree.children.append(fpat)
            else:
                if outter_pat.fixedmask != 0x0:  # catch all
                    children = [
                        DecodeLeaf(pat=i, origin=pats_to_origins[src_pat])
                        for (i, src_pat) in inner_pats
                    ]

                    fpat = DecodeTree(pat=outter_pat, children=children)
                    current_tree.children.append(fpat)
                    stack.append(fpat)  # process during next cycles
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

    stack = []
    stack.extend(((i, 0, idx == 0) for idx, i in enumerate(reversed(tree.children))))
    flattend_tree = []
    while len(stack) != 0:
        item, depth, last_child = stack.pop()
        if isinstance(item, DecodeLeaf):
            flattend_tree.append((item.pat, item.origin, depth, last_child))
        elif isinstance(item, DecodeTree):
            flattend_tree.append((item.pat, None, depth, last_child))
            stack.extend(
                (
                    (i, depth + 1, idx == 0)
                    for idx, i in enumerate(reversed(item.children))
                )
            )
    return flattend_tree
