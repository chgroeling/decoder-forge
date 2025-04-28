from bit_match_gen.pattern import Pattern
from functools import reduce


def compute_common_fixedmask(pats: list[Pattern]) -> int:
    """
    Compute the common fixed mask for a list of Pattern objects.

    This function calculates the bitwise AND (intersection) of the fixedmask
    attributes from all Pattern objects provided in the list. The result is an integer
    representing the bits that are fixed across all patterns.

    :param pats: A list of Pattern objects whose fixedmask values are to
        be combined.
    :type pats: list[Pattern]
    :returns: The resulting fixed mask after performing a bitwise AND on all
        Pattern.fixedmask values.
    :rtype: int

    Example:
        >>> p1 = Pattern(0b111, 0b101, 3)
        >>> p2 = Pattern(0b101, 0b001, 3)
        >>> compute_common_fixedmask([p1, p2])
        5  # Since 0b101 & 0b101 equals 0b101 (5 in decimal)
    """

    def logic_and(fma: int, fmb: int) -> int:
        return fma & fmb

    out = reduce(logic_and, (i.fixedmask for i in pats))
    return out


def group_patterns_by_common_fixedmask(
    pats: list[Pattern],
) -> dict[Pattern, [Pattern]]:
    """
    Group patterns based on their common fixed parts.

    This function first computes the common fixed mask for all provided Pattern
    objects. Then, for each Pattern, it splits the pattern into two parts using the
    computed mask via its 'split_by_mask' method. The first part (pa) serves as the key,
    while the second part (pb) is added to a list associated with that key in the group
    dictionary.

    Args:
        pats (list[Pattern]): A list of Pattern objects to be grouped.

    Returns:
        dict[Pattern, list[Pattern]]: A dictionary where each key is a Pattern
            representing the fixed portion (pa) after applying the common mask,
            and each value is a list of Pattern
        objects representing the corresponding remainder (pb).

    Example:
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
