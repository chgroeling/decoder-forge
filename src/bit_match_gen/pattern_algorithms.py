from bit_match_gen.pattern import Pattern
from functools import reduce


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


def group_patterns_by_common_fixedmask(
    pats: list[Pattern],
) -> dict[Pattern, [Pattern]]:
    """
    Group patterns by their common fixed parts.

    This function first computes the common fixed mask for the list of Pattern objects.
    Then, for each Pattern, it splits the pattern into two parts using its 'split_by_mask'
    method with the computed mask. The first part (pa) represents the fixed portion and
    serves as the key, while the second part (pb) is appended to a list corresponding to
    that key. This grouping is useful for organizing patterns by their shared fixed
    bits.

    Args:
        pats (list[Pattern]): A list of Pattern objects to be grouped.

    Returns:
        dict[Pattern, list[Pattern]]: A dictionary where each key is a Pattern
            representing the fixed portion after applying the common mask, and the
            associated value is a list of Pattern objects representing the remaining
            portion.

    Examples:
        >>> groups = group_patterns_by_common_fixedmask([pattern1, pattern2, pattern3])
        >>> for fixed_part, remainders in groups.items():
        ...     print(f"Fixed part: {fixed_part}, Remainders: {remainders}")
    """

    # find fixed parts
    mask = compute_common_fixedmask(pats)

    groups = {}
    for p in pats:
        pa, pb = p.split_by_mask(mask)

        group = groups.get(pa, [])
        group.append(pb)
        groups[pa] = group

    return groups
