from decoder_forge.pattern_algorithms import (
    compute_common_fixedmask,
    build_groups_by_fixed_bits,
    build_decode_tree_by_fixed_bits,
    DecodeTree,
    DecodeLeaf,
)
from decoder_forge.pattern import Pattern
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


def test_build_groups_by_fixed_bits_three_patterns_two_with_exclusive_bits_returns_correct_dict():
    # pat_a = "11xxxxx0"
    pat_a = Pattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8)

    # pat_b = "11xxxx01"
    pat_b = Pattern(fixedmask=0xC3, fixedbits=0xC1, bit_length=8)

    # pat_c= "11xxxx11"
    pat_c = Pattern(fixedmask=0xC3, fixedbits=0xC3, bit_length=8)

    groups = build_groups_by_fixed_bits([pat_a, pat_b, pat_c])

    assert groups == {
        Pattern(fixedmask=0xC1, fixedbits=0xC1, bit_length=8): [  # pat: "11xxxxx1"
            (
                Pattern(fixedmask=0x2, fixedbits=0x0, bit_length=8),  # pat: "xxxxxx0x"
                Pattern(fixedmask=0xC3, fixedbits=0xC1, bit_length=8),
            ),
            (
                Pattern(fixedmask=0x2, fixedbits=0x2, bit_length=8),  # pat: "xxxxxx1x"
                Pattern(fixedmask=0xC3, fixedbits=0xC3, bit_length=8),
            ),
        ],
        Pattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8): [  # pat: "11xxxxx0"
            (
                Pattern(fixedmask=0x0, fixedbits=0x0, bit_length=8),  # catchall
                Pattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8),
            )
        ],
    }


def test_build_decode_tree_by_fixed_bits_one_pattern_returns_correct_tree():
    # pat_a = "11x00x11"
    pat_a = Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    tree = build_decode_tree_by_fixed_bits([pat_a])

    assert tree == DecodeTree(
        pat=None,
        children=[
            DecodeLeaf(
                pat=Pattern(
                    fixedmask=0xDB, fixedbits=0xC3, bit_length=8
                ),  # pat: "11x00x11"
                origin=Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8),
            )
        ],
    )


def test_build_decode_tree_by_fixed_bits_two_patterns_contained_returns_correct_tree():
    # pat_a = "11x00x11"
    pat_a = Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    # pat_b = "11xxx0xx"
    pat_b = Pattern(fixedmask=0xC4, fixedbits=0xC0, bit_length=8)

    tree = build_decode_tree_by_fixed_bits([pat_a, pat_b])
    assert tree == DecodeTree(
        pat=None,
        children=[
            DecodeTree(
                pat=Pattern(
                    fixedmask=0xC0, fixedbits=0xC0, bit_length=8
                ),  # pat: "11xxxxxx"
                children=[
                    DecodeLeaf(
                        pat=Pattern(
                            fixedmask=0x1B, fixedbits=0x3, bit_length=8
                        ),  # pat: "xxx00x11"
                        origin=Pattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8),
                    ),
                    DecodeLeaf(
                        pat=Pattern(
                            fixedmask=0x4, fixedbits=0x0, bit_length=8
                        ),  # pat: "xxxxx0xx"
                        origin=Pattern(fixedmask=0xC4, fixedbits=0xC0, bit_length=8),
                    ),
                ],
            )
        ],
    )


def test_build_decode_tree_by_fixed_bits_three_patterns_two_with_exclusive_bits_returns_correct_tree():
    # pat_a = "11xxxxx0"
    pat_a = Pattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8)

    # pat_b = "11xxxx01"
    pat_b = Pattern(fixedmask=0xC3, fixedbits=0xC1, bit_length=8)

    # pat_c= "11xxxx11"
    pat_c = Pattern(fixedmask=0xC3, fixedbits=0xC3, bit_length=8)

    tree = build_decode_tree_by_fixed_bits([pat_a, pat_b, pat_c])

    assert tree == DecodeTree(
        pat=None,
        children=[
            DecodeLeaf(
                pat=Pattern(
                    fixedmask=0xC1, fixedbits=0xC0, bit_length=8
                ),  # pat: "11xxxxx0"
                origin=Pattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8),
            ),
            DecodeTree(
                pat=Pattern(
                    fixedmask=0xC1, fixedbits=0xC1, bit_length=8
                ),  # pat: "11xxxxx1"
                children=[
                    DecodeLeaf(
                        pat=Pattern(
                            fixedmask=0x2, fixedbits=0x0, bit_length=8
                        ),  # pat: "xxxxxx0x"
                        origin=Pattern(fixedmask=0xC3, fixedbits=0xC1, bit_length=8),
                    ),
                    DecodeLeaf(
                        pat=Pattern(
                            fixedmask=0x2, fixedbits=0x2, bit_length=8
                        ),  # pat: "xxxxxx1x"
                        origin=Pattern(fixedmask=0xC3, fixedbits=0xC3, bit_length=8),
                    ),
                ],
            ),
        ],
    )
