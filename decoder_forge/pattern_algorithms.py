from decoder_forge.pattern import Pattern
from functools import reduce
from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class PatternNode:
    pass


@dataclass(eq=True, frozen=True)
class PatternUnfolded(PatternNode):
    to_unfold: Pattern
    origin: Pattern


@dataclass(eq=True, frozen=True)
class PatternLeaf(PatternNode):
    pat: Pattern
    origin: Pattern


@dataclass(eq=True, frozen=True)
class PatternTree(PatternNode):
    pat: Pattern
    children: list[PatternNode]


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


def generate_tree_by_common_bits(
    pats: list[Pattern],
) -> dict[Pattern, [Pattern]]:
    """
    Generate a hierarchical tree structure of Patterns based on common fixed bits.

    The function begins by wrapping every Pattern in a PatternUnfolded node so that they
    can be processed by splitting them using a common mask. For each iteration, it does
    the following:
      1. Computes a common fixed mask for all current unfolded Patterns.
      2. Splits each Pattern using its 'split_by_mask' method with the computed mask. The
         'split_by_mask' method divides a Pattern into two parts:
           - The first part represents the bits selected by the mask (fixed portion).
           - The second part contains the remaining bits.
         Note: The mask must be fully contained within the pattern's fixedmask, or a
         ValueError is raised.
      3. Groups the Patterns based on their fixed portion (pa).
      4. For each group:
           - If there is only one Pattern, a PatternLeaf node is created.
           - If multiple Patterns share a significant fixed portion (i.e., from_pat.fixedmask != 0),
             a new PatternTree node is created with children as PatternUnfolded nodes to be processed
             in the next iteration.
           - If the fixed portion is not significant (i.e., fixedmask is 0), each Pattern becomes
             a PatternLeaf node directly.

    Args:
        pats (list[Pattern]): A list of Pattern objects to be organized into a tree by their shared fixed bits.

    Returns:
        PatternTree: The root node of the generated pattern tree. The children of the root node
        represent the grouped Patterns as either PatternLeaf, PatternUnfolded, or nested PatternTree nodes.

    Raises:
        AttributeError: If a Pattern object lacks the required attributes or the method 'split_by_mask'.
        ValueError: If 'split_by_mask' is invoked with a mask that is not fully contained within
                    the Pattern's fixedmask.

    Example:
        >>> # Given valid Pattern objects pattern1, pattern2, and pattern3 with a 'split_by_mask' method
        >>> tree = generate_tree_by_common_bits([pattern1, pattern2, pattern3])
        >>> pprint.pprint(tree)
    """

    pats_unfolded = [PatternUnfolded(to_unfold=i, origin=i) for i in pats]
    root = PatternTree(pat=None, children=pats_unfolded)

    stack = []
    stack.append(root)

    while len(stack) != 0:
        current_tree = stack.pop()
        groups = {}
        unfolded = [i for i in current_tree.children if isinstance(i, PatternUnfolded)]

        if len(unfolded) == 0:
            continue

        # find fixed parts
        mask = compute_common_fixedmask((i.to_unfold for i in unfolded))

        for pn in unfolded:
            pa, pb = pn.to_unfold.split_by_mask(mask)
            group = groups.get(pa, list())
            group.append((pb, pn))
            groups[pa] = group

            # remove PatternUnfolded
            current_tree.children.remove(pn)

        for from_pat, to_pats in groups.items():
            if len(to_pats) == 1:
                fpat = PatternLeaf(pat=from_pat, origin=to_pats[0][1].origin)
                current_tree.children.append(fpat)
            else:
                if from_pat.fixedmask != 0x0:  # catch all
                    children = [
                        PatternUnfolded(to_unfold=i, origin=origin.origin)
                        for (i, origin) in to_pats
                    ]

                    fpat = PatternTree(pat=from_pat, children=children)
                    current_tree.children.append(fpat)
                    stack.append(fpat)  # process during next cycles
                else:
                    children = [
                        PatternLeaf(pat=i, origin=origin.origin)
                        for (i, origin) in to_pats
                    ]
                    current_tree.children.extend(children)

    return root
