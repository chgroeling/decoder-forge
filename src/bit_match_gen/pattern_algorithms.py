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

    def logic_and(fma : int, fmb: int) -> int:
        return fma & fmb

    out = reduce(logic_and, (i.fixedmask for i in pats))
    return out
