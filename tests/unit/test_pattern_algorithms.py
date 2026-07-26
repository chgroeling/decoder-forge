from decoder_forge.pattern_algorithms import (
    compute_common_fixedmask,
    build_groups_by_fixed_bits,
    build_decode_tree_by_fixed_bits,
    DecodeTree,
    DecodeLeaf,
)
from decoder_forge.bit_pattern import BitPattern


def test_compute_common_fixedmask_with_2_equal_pats_returns_common_fixedmask():
    # pat_a = "11x00x11"
    pat_a = BitPattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    # pat_b = "11x00x11"
    pat_b = BitPattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    pat_common = compute_common_fixedmask([pat_a, pat_b])

    assert pat_common == 0xDB


def test_compute_common_fixedmask_with_2_different_pats_returns_common_fixedmask():
    # pat_a = "11x00x11"
    pat_a = BitPattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    # pat_b = "11xxxxxx"
    pat_b = BitPattern(fixedmask=0xC0, fixedbits=0xC0, bit_length=8)

    pat_common = compute_common_fixedmask([pat_a, pat_b])

    assert pat_common == 0xC0


def test_compute_common_fixedmask_with_3_different_pats_returns_common_fixedmask():
    # pat_a = "11x00x11"
    pat_a = BitPattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    # pat_b = "11xxxxxx"
    pat_b = BitPattern(fixedmask=0xC0, fixedbits=0xC0, bit_length=8)

    # pat_c = "01xxxxxx"
    pat_c = BitPattern(fixedmask=0x80, fixedbits=0x80, bit_length=8)

    pat_common = compute_common_fixedmask([pat_a, pat_b, pat_c])

    assert pat_common == 0x80


def test_build_groups_by_fixed_bits_three_patterns_two_with_exclusive_bits_returns_correct_dict():
    # pat_a = "11xxxxx0"
    pat_a = BitPattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8)

    # pat_b = "11xxxx01"
    pat_b = BitPattern(fixedmask=0xC3, fixedbits=0xC1, bit_length=8)

    # pat_c= "11xxxx11"
    pat_c = BitPattern(fixedmask=0xC3, fixedbits=0xC3, bit_length=8)

    groups = build_groups_by_fixed_bits([pat_a, pat_b, pat_c])

    assert groups == {
        BitPattern(fixedmask=0xC1, fixedbits=0xC1, bit_length=8): [  # pat: "11xxxxx1"
            (
                BitPattern(
                    fixedmask=0x2, fixedbits=0x0, bit_length=8
                ),  # pat: "xxxxxx0x"
                BitPattern(fixedmask=0xC3, fixedbits=0xC1, bit_length=8),
            ),
            (
                BitPattern(
                    fixedmask=0x2, fixedbits=0x2, bit_length=8
                ),  # pat: "xxxxxx1x"
                BitPattern(fixedmask=0xC3, fixedbits=0xC3, bit_length=8),
            ),
        ],
        BitPattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8): [  # pat: "11xxxxx0"
            (
                BitPattern(fixedmask=0x0, fixedbits=0x0, bit_length=8),  # catchall
                BitPattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8),
            )
        ],
    }


def test_build_decode_tree_by_fixed_bits_one_pattern_returns_correct_tree():
    # pat_a = "11x00x11"
    pat_a = BitPattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    tree = build_decode_tree_by_fixed_bits([(pat_a, "UIDA")], decoder_width=8)

    assert tree == DecodeTree(
        pat=None,
        uid="",
        children=[
            DecodeLeaf(
                pat=BitPattern(
                    fixedmask=0xDB, fixedbits=0xC3, bit_length=8
                ),  # pat: "11x00x11"
                uid="UIDA",
            )
        ],
    )


def test_build_decode_tree_by_fixed_bits_two_patterns_contained_returns_correct_tree():
    # pat_a = "11x00x11"
    pat_a = BitPattern(fixedmask=0xDB, fixedbits=0xC3, bit_length=8)

    # pat_b = "11xxx0xx"
    pat_b = BitPattern(fixedmask=0xC4, fixedbits=0xC0, bit_length=8)

    tree = build_decode_tree_by_fixed_bits(
        [(pat_a, "UIDA"), (pat_b, "UIDB")], decoder_width=8
    )
    assert tree == DecodeTree(
        pat=None,
        uid="",
        children=[
            DecodeTree(
                uid="",
                pat=BitPattern(
                    fixedmask=0xC0, fixedbits=0xC0, bit_length=8
                ),  # pat: "11xxxxxx"
                children=[
                    DecodeLeaf(
                        pat=BitPattern(
                            fixedmask=0x1B, fixedbits=0x3, bit_length=8
                        ),  # pat: "xxx00x11"
                        uid="UIDA",
                    ),
                    DecodeLeaf(
                        pat=BitPattern(
                            fixedmask=0x4, fixedbits=0x0, bit_length=8
                        ),  # pat: "xxxxx0xx"
                        uid="UIDB",
                    ),
                ],
            )
        ],
    )


def test_build_decode_tree_by_fixed_bits_two_patterns_one_longer_returns_correct_tree():
    # pat_a = "0x"
    pat_a = BitPattern(fixedmask=0x2, fixedbits=0x0, bit_length=2)

    # pat_b = "11"
    pat_b = BitPattern(fixedmask=0x3, fixedbits=0x3, bit_length=2)

    tree = build_decode_tree_by_fixed_bits(
        [(pat_a, "UIDA"), (pat_b, "UIDB")], decoder_width=2
    )

    assert tree == DecodeTree(
        pat=None,
        uid="",
        children=[
            DecodeLeaf(
                pat=BitPattern(
                    fixedmask=0x3, fixedbits=0x3, bit_length=2
                ),  # pat = "11" - longest pattern (no of ones and zeros) first
                uid="UIDB",
            ),
            DecodeLeaf(
                pat=BitPattern(
                    fixedmask=0x2, fixedbits=0x0, bit_length=2
                ),  # pat = "0x"
                uid="UIDA",
            ),
        ],
    )


def test_build_decode_tree_by_fixed_bits_three_patterns_two_with_exclusive_bits_returns_correct_tree():
    # pat_a = "11xxxxx0"
    pat_a = BitPattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8)

    # pat_b = "11xxxx01"
    pat_b = BitPattern(fixedmask=0xC3, fixedbits=0xC1, bit_length=8)

    # pat_c= "11xxxx11"
    pat_c = BitPattern(fixedmask=0xC3, fixedbits=0xC3, bit_length=8)

    tree = build_decode_tree_by_fixed_bits(
        [(pat_a, "UIDA"), (pat_b, "UIDB"), (pat_c, "UIDC")], decoder_width=8
    )

    assert tree == DecodeTree(
        pat=None,
        uid="",
        children=[
            DecodeLeaf(
                pat=BitPattern(
                    fixedmask=0xC1, fixedbits=0xC0, bit_length=8
                ),  # pat: "11xxxxx0"
                uid="UIDA",
            ),
            DecodeTree(
                uid="",
                pat=BitPattern(
                    fixedmask=0xC1, fixedbits=0xC1, bit_length=8
                ),  # pat: "11xxxxx1"
                children=[
                    DecodeLeaf(
                        pat=BitPattern(
                            fixedmask=0x2, fixedbits=0x0, bit_length=8
                        ),  # pat: "xxxxxx0x"
                        uid="UIDB",
                    ),
                    DecodeLeaf(
                        pat=BitPattern(
                            fixedmask=0x2, fixedbits=0x2, bit_length=8
                        ),  # pat: "xxxxxx1x"
                        uid="UIDC",
                    ),
                ],
            ),
        ],
    )


def test_build_decode_tree_by_fixed_bits_three_patterns_two_with_exclusive_bits_one_longer_returns_correct_tree():
    # pat_a = "11xxxxx0"
    pat_a = BitPattern(fixedmask=0xC1, fixedbits=0xC0, bit_length=8)

    # pat_b = "11xxxx01"
    pat_b = BitPattern(fixedmask=0xC3, fixedbits=0xC1, bit_length=8)

    # pat_c= "11xxx111"
    pat_c = BitPattern(fixedmask=0xC7, fixedbits=0xC7, bit_length=8)

    tree = build_decode_tree_by_fixed_bits(
        [(pat_a, "UIDA"), (pat_b, "UIDB"), (pat_c, "UIDC")], decoder_width=8
    )

    assert tree == DecodeTree(
        pat=None,
        uid="",
        children=[
            DecodeLeaf(
                pat=BitPattern(
                    fixedmask=0xC1, fixedbits=0xC0, bit_length=8
                ),  # pat: "11xxxxx0"
                uid="UIDA",
            ),
            DecodeTree(
                uid="",
                pat=BitPattern(
                    fixedmask=0xC1, fixedbits=0xC1, bit_length=8
                ),  # pat: "11xxxxx1"
                children=[
                    DecodeLeaf(
                        pat=BitPattern(
                            fixedmask=0x6, fixedbits=0x6, bit_length=8
                        ),  # pat: "xxxxx11x" - longest pattern (no of ones and zeros) first
                        uid="UIDC",
                    ),
                    DecodeLeaf(
                        pat=BitPattern(
                            fixedmask=0x2, fixedbits=0x0, bit_length=8
                        ),  # pat: "xxxxxx0x"
                        uid="UIDB",
                    ),
                ],
            ),
        ],
    )
