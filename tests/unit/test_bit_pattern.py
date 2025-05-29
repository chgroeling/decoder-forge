from decoder_forge.bit_pattern import BitPattern
import pytest


def test_parse_pattern_with_empty_string_returns_correct_type():
    with pytest.raises(ValueError):
        _ = BitPattern.parse_pattern("")


def test_parse_pattern_with_0_returns_correct_type():
    pattern = BitPattern.parse_pattern("0")
    assert isinstance(pattern, BitPattern)


def test_parse_pattern_with_0000_initializes_fixedmask_correctly():
    pattern = BitPattern.parse_pattern("0000")
    assert pattern.fixedmask == 0xF


def test_parse_pattern_with_11x1_initializes_fixedmask_correctly():
    pattern = BitPattern.parse_pattern("11x1")
    assert pattern.fixedmask == 0xD


def test_parse_pattern_with_00x0_initializes_fixedmask_correctly():
    pattern = BitPattern.parse_pattern("00x0")
    assert pattern.fixedmask == 0xD


def test_parse_pattern_with_00x0_initializes_fixedbits_correctly():
    pattern = BitPattern.parse_pattern("00x0")
    assert pattern.fixedbits == 0x0


def test_parse_pattern_with_11x1_initializes_fixedbits_correctly():
    pattern = BitPattern.parse_pattern("11x1")
    assert pattern.fixedbits == 0xD


def test_parse_pattern_with_11x1_initializes_width_correctly():
    pattern = BitPattern.parse_pattern("11x1")
    assert pattern.bit_length == 4


def test_parse_pattern_with_11x1o_initializes_width_correctly():
    pattern = BitPattern.parse_pattern("11x1o")
    assert pattern.bit_length == 5


def test_str_with_default_constructor_returns_x():
    test_pattern = BitPattern()
    assert str(test_pattern) == "x"


def test_str_with_fixedmask_0_and_bit_length_4_set_returns_xxxx():
    pattern = BitPattern(fixedmask=0x0, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "xxxx"


def test_str_with_fixedmask_0xF_and_bit_length_4_set_returns_0000():
    pattern = BitPattern(fixedmask=0xF, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "0000"


def test_str_with_fixedbits_0xF_and_bit_length_4_set_returns_xxxx():
    pattern = BitPattern(fixedbits=0xF, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "xxxx"


def test_str_with_fixedmask_0xF_fixedbits_0x0_and_bit_length_4_set_returns_0000():
    pattern = BitPattern(fixedmask=0xF, fixedbits=0x0, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "0000"


def test_str_with_fixedmask_0xF_fixedbits_0xF_and_bit_length_4_set_returns_1111():
    pattern = BitPattern(fixedmask=0xF, fixedbits=0xF, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "1111"


def test_str_with_fixedmask_0xF_fixedbits_0xF_and_bit_length_5_set_returns_x1111():
    pattern = BitPattern(fixedmask=0xF, fixedbits=0xF, bit_length=5)
    pattern_str = str(pattern)
    assert pattern_str == "x1111"


def test_eq_equal_patterns_returns_true():
    pat_a = BitPattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)
    pat_b = BitPattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)

    assert pat_a == pat_b
    assert pat_b == pat_a


def test_eq_fixedmask_different_returns_false():
    pat_a = BitPattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)
    pat_b = BitPattern(fixedmask=0x4, fixedbits=0xA, bit_length=5)

    assert pat_a != pat_b
    assert pat_b != pat_a


def test_eq_fixedbits_different_returns_false():
    pat_a = BitPattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)
    pat_b = BitPattern(fixedmask=0x3, fixedbits=0xB, bit_length=5)

    assert pat_a != pat_b
    assert pat_b != pat_a


def test_eq_bit_length_different_returns_false():
    pat_a = BitPattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)
    pat_b = BitPattern(fixedmask=0x3, fixedbits=0xA, bit_length=6)

    assert pat_a != pat_b
    assert pat_b != pat_a


def test_separate_empty_fixedmask_return_matchall_same():
    # pat_a = "xx10"
    pat = BitPattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)
    fixedmask = 0x0

    pat_a, pat_b = pat.split_by_mask(fixedmask)

    assert pat_a == BitPattern(fixedmask=0x0, fixedbits=0x0, bit_length=4)
    assert pat_b == BitPattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)


def test_split_by_mask_one_bit_fixedmask_return_separate_bitmasks():
    # pat_a = "xx10"
    pat = BitPattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)
    fixedmask = 0x2

    pat_a, pat_b = pat.split_by_mask(fixedmask)

    assert pat_a == BitPattern(fixedmask=0x2, fixedbits=0x2, bit_length=4)
    assert pat_b == BitPattern(fixedmask=0x1, fixedbits=0x0, bit_length=4)


def test_split_by_mask_one_bit_fixedmask_2_return_separate_bitmasks():
    # pat_a = "xx10"
    pat = BitPattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)
    fixedmask = 0x1

    pat_a, pat_b = pat.split_by_mask(fixedmask)

    assert pat_a == BitPattern(fixedmask=0x1, fixedbits=0x0, bit_length=4)
    assert pat_b == BitPattern(fixedmask=0x2, fixedbits=0x2, bit_length=4)


def test_combine_exclusive_masks_correct_combination():
    # pat_a = "1x"
    pat_a = BitPattern(fixedmask=0x2, fixedbits=0x2, bit_length=4)
    # pat_b = "x0"
    pat_b = BitPattern(fixedmask=0x1, fixedbits=0x1, bit_length=4)

    pat_comb = pat_a.combine(pat_b)

    assert pat_comb == BitPattern(fixedmask=0x3, fixedbits=0x3, bit_length=4)


def test_combine_inclusive_masks_correct_combination():
    # pat_a = "1x"
    pat_a = BitPattern(fixedmask=0x2, fixedbits=0x2, bit_length=4)
    # pat_b = "10"
    pat_b = BitPattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)

    pat_comb = pat_a.combine(pat_b)

    assert pat_comb == BitPattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)


def test_combine_inclusive_masks_only_zeros_correct_combination():
    # pat_a = "0x"
    pat_a = BitPattern(fixedmask=0x2, fixedbits=0x0, bit_length=4)
    # pat_b = "00"
    pat_b = BitPattern(fixedmask=0x3, fixedbits=0x0, bit_length=4)

    pat_comb = pat_a.combine(pat_b)

    assert pat_comb == BitPattern(fixedmask=0x3, fixedbits=0x0, bit_length=4)


def test_combine_identical_masks_correct_combination():
    # pat_a = "10"
    pat_a = BitPattern(fixedmask=0x3, fixedbits=0x1, bit_length=4)
    # pat_b = "10"
    pat_b = BitPattern(fixedmask=0x3, fixedbits=0x1, bit_length=4)

    pat_comb = pat_a.combine(pat_b)

    assert pat_comb == BitPattern(fixedmask=0x3, fixedbits=0x1, bit_length=4)


def test_combine_incompatible_masks_raises_value_error():
    # pat_a = "x0"
    pat_a = BitPattern(fixedmask=0x1, fixedbits=0x0, bit_length=4)
    # pat_b = "x1"
    pat_b = BitPattern(fixedmask=0x1, fixedbits=0x1, bit_length=4)

    with pytest.raises(ValueError):
        _ = pat_a.combine(pat_b)


def test_trailing_wildcard_count_8_out_16():
    pat_a = BitPattern(fixedmask=0xFF00, fixedbits=0x0, bit_length=16)
    elen = pat_a.trailing_wildcard_count
    assert elen == 8


def test_trailing_wildcard_count_0_out_16():
    pat_a = BitPattern(fixedmask=0x1, fixedbits=0x0, bit_length=16)
    elen = pat_a.trailing_wildcard_count
    assert elen == 0


def test_trailing_wildcard_count_16_out_16():
    pat_a = BitPattern(fixedmask=0x0, fixedbits=0x0, bit_length=16)
    elen = pat_a.trailing_wildcard_count
    assert elen == 16


def test_extract_from_msb_6_out_8():
    pat_a = BitPattern(fixedmask=0xAA, fixedbits=0xAA, bit_length=8)
    pat_b = pat_a.extract_from_msb(6)
    assert pat_b.bit_length == 6
    assert pat_b.fixedmask == 0x2A
    assert pat_b.fixedbits == 0x2A


def test_extract_from_msb_3_out_8():
    pat_a = BitPattern(fixedmask=0xAA, fixedbits=0xAA, bit_length=8)
    pat_b = pat_a.extract_from_msb(3)
    assert pat_b.bit_length == 3
    assert pat_b.fixedmask == 0x5
    assert pat_b.fixedbits == 0x5
