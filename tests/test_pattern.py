from bit_match_gen.pattern import Pattern
import pytest


# Unit of work is parse_pattern and to_string
def test_round_trip_with_1x1x0_returns_1x1x0():
    pattern = Pattern.parse_pattern("1x1x0")
    pattern_str = Pattern.to_string(pattern)
    assert pattern_str == "1x1x0"


def test_parse_pattern_with_empty_string_returns_correct_type():
    with pytest.raises(ValueError):
        _ = Pattern.parse_pattern("")


def test_parse_pattern_with_0_returns_correct_type():
    pattern = Pattern.parse_pattern("0")
    assert isinstance(pattern, Pattern)


def test_parse_pattern_with_0000_initializes_fixedmask_correctly():
    pattern = Pattern.parse_pattern("0000")
    assert pattern.fixedmask == 0xF


def test_parse_pattern_with_11x1_initializes_fixedmask_correctly():
    pattern = Pattern.parse_pattern("11x1")
    assert pattern.fixedmask == 0xD


def test_parse_pattern_with_00x0_initializes_fixedmask_correctly():
    pattern = Pattern.parse_pattern("00x0")
    assert pattern.fixedmask == 0xD


def test_parse_pattern_with_00x0_initializes_fixedbits_correctly():
    pattern = Pattern.parse_pattern("00x0")
    assert pattern.fixedbits == 0x0


def test_parse_pattern_with_11x1_initializes_fixedbits_correctly():
    pattern = Pattern.parse_pattern("11x1")
    assert pattern.fixedbits == 0xD


def test_parse_pattern_with_11x1_initializes_width_correctly():
    pattern = Pattern.parse_pattern("11x1")
    assert pattern.bit_length == 4


def test_parse_pattern_with_11x1o_initializes_width_correctly():
    pattern = Pattern.parse_pattern("11x1o")
    assert pattern.bit_length == 5


def test_str_with_default_constructor_returns_x():
    test_pattern = Pattern()
    assert str(test_pattern) == "x"


def test_str_with_fixedmask_0_and_bit_length_4_set_returns_xxxx():
    pattern = Pattern(fixedmask=0x0, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "xxxx"


def test_str_with_fixedmask_0xF_and_bit_length_4_set_returns_0000():
    pattern = Pattern(fixedmask=0xF, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "0000"


def test_str_with_fixedbits_0xF_and_bit_length_4_set_returns_xxxx():
    pattern = Pattern(fixedbits=0xF, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "xxxx"


def test_str_with_fixedmask_0xF_fixedbits_0x0_and_bit_length_4_set_returns_0000():
    pattern = Pattern(fixedmask=0xF, fixedbits=0x0, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "0000"


def test_str_with_fixedmask_0xF_fixedbits_0xF_and_bit_length_4_set_returns_1111():
    pattern = Pattern(fixedmask=0xF, fixedbits=0xF, bit_length=4)
    pattern_str = str(pattern)
    assert pattern_str == "1111"


def test_str_with_fixedmask_0xF_fixedbits_0xF_and_bit_length_5_set_returns_x1111():
    pattern = Pattern(fixedmask=0xF, fixedbits=0xF, bit_length=5)
    pattern_str = str(pattern)
    assert pattern_str == "x1111"


def test_eq_equal_patterns_returns_true():
    pat_a = Pattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)
    pat_b = Pattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)

    assert pat_a == pat_b
    assert pat_b == pat_a


def test_eq_fixedmask_different_returns_false():
    pat_a = Pattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)
    pat_b = Pattern(fixedmask=0x4, fixedbits=0xA, bit_length=5)

    assert pat_a != pat_b
    assert pat_b != pat_a


def test_eq_fixedbits_different_returns_false():
    pat_a = Pattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)
    pat_b = Pattern(fixedmask=0x3, fixedbits=0xB, bit_length=5)

    assert pat_a != pat_b
    assert pat_b != pat_a


def test_eq_bit_length_different_returns_false():
    pat_a = Pattern(fixedmask=0x3, fixedbits=0xA, bit_length=5)
    pat_b = Pattern(fixedmask=0x3, fixedbits=0xA, bit_length=6)

    assert pat_a != pat_b
    assert pat_b != pat_a


def test_separate_empty_fixedmask_return_matchall_same():
    # pat_a = "xx10"
    pat = Pattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)
    fixedmask = 0x0

    pat_a, pat_b = pat.split_by_mask(fixedmask)

    assert pat_a == Pattern(fixedmask=0x0, fixedbits=0x0, bit_length=4)
    assert pat_b == Pattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)


def test_split_by_mask_one_bit_fixedmask_return_separate_bitmasks():
    # pat_a = "xx10"
    pat = Pattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)
    fixedmask = 0x2

    pat_a, pat_b = pat.split_by_mask(fixedmask)

    assert pat_a == Pattern(fixedmask=0x2, fixedbits=0x2, bit_length=4)
    assert pat_b == Pattern(fixedmask=0x1, fixedbits=0x0, bit_length=4)


def test_split_by_mask_one_bit_fixedmask_2_return_separate_bitmasks():
    # pat_a = "xx10"
    pat = Pattern(fixedmask=0x3, fixedbits=0x2, bit_length=4)
    fixedmask = 0x1

    pat_a, pat_b = pat.split_by_mask(fixedmask)

    assert pat_a == Pattern(fixedmask=0x1, fixedbits=0x0, bit_length=4)
    assert pat_b == Pattern(fixedmask=0x2, fixedbits=0x2, bit_length=4)
