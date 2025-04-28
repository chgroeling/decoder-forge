from bit_match_gen.pattern_algorithms import (
    compute_common_fixedmask,
)
from bit_match_gen.pattern import Pattern
import pytest


def test_compute_common_fixedmask_with_2_equal_pats_returns_common_fixedmask():
    # pat_a = "11x00x11"
    pat_a = Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    # pat_b = "11x00x11"
    pat_b = Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    pat_common = compute_common_fixedmask([pat_a, pat_b])

    assert pat_common == 0xDB


def test_compute_common_fixedmask_with_2_different_pats_returns_common_fixedmask():
    # pat_a = "11x00x11"
    pat_a = Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    # pat_b = "11xxxxxx"
    pat_b = Pattern(fixedmask=0xC0, fixedbits=0xC0, bit_length=8)

    pat_common = compute_common_fixedmask([pat_a, pat_b])

    assert pat_common == 0xC0


def test_compute_common_fixedmask_with_3_different_pats_returns_common_fixedmask():
    # pat_a = "11x00x11"
    pat_a = Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    # pat_b = "11xxxxxx"
    pat_b = Pattern(fixedmask=0xC0, fixedbits=0xC0, bit_length=8)

    # pat_c = "01xxxxxx"
    pat_c = Pattern(fixedmask=0x80, fixedbits=0x80, bit_length=8)

    pat_common = compute_common_fixedmask([pat_a, pat_b, pat_c])

    assert pat_common == 0x80
