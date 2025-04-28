from bit_match_gen.pattern_algorithms import (
    compute_common_fixedmask,
    group_patterns_by_common_fixedmask,
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


def test_group_patterns_by_common_fixedmask_one_pattern_returns_itself():
    # pat_a = "11x00x11"
    pat_a = Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    group = group_patterns_by_common_fixedmask([pat_a])

    assert group == {
        Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8): [  # pat1: "11x00x11"
            Pattern(fixedmask=0x0, fixedbits=0x0, bit_length=8)  # catchall
        ]
    }


def test_group_patterns_by_common_fixedmask_two_patterns_contained_returns_correct_dict():
    # pat_a = "11x00x11"
    pat_a = Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    # pat_b = "11xxx0xx"
    pat_b = Pattern(fixedmask=0xC4, fixedbits=0xC0, bit_length=8)

    group = group_patterns_by_common_fixedmask([pat_a, pat_b])

    assert group == {
        Pattern(fixedmask=0xC0, fixedbits=0xC0, bit_length=8): [  # pat1: "11xxxxxx"
            Pattern(fixedmask=0x1B, fixedbits=0x3, bit_length=8),  # pat2: "xxx00x11"
            Pattern(fixedmask=0x4, fixedbits=0x0, bit_length=8),  # pat2: "xxxxx0xx"
        ]
    }


def test_group_patterns_by_common_fixed_mask_three_patterns_two_with_exclusive_bits_returns_correct_dict():
    # pat_a = "11xxxxx0"
    pat_a = Pattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8)

    # pat_b = "11xxxx01"
    pat_b = Pattern(fixedmask=0xC3, fixedbits=0xC1, bit_length=8)

    # pat_c= "11xxxx11"
    pat_c = Pattern(fixedmask=0xC3, fixedbits=0xC3, bit_length=8)

    group = group_patterns_by_common_fixedmask([pat_a, pat_b, pat_c])

    assert group == {
        Pattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8): [  # pat1: "11xxxxx0"
            Pattern(fixedmask=0x0, fixedbits=0x0, bit_length=8)  # catchall
        ],
        Pattern(fixedmask=0xC1, fixedbits=0xC1, bit_length=8): [  # pat1: "11xxxxx1"
            Pattern(fixedmask=0x2, fixedbits=0x0, bit_length=8),  # pat2: "xxxxxx0x"
            Pattern(fixedmask=0x2, fixedbits=0x2, bit_length=8),  # pat2: "xxxxxx1x"
        ],
    }
