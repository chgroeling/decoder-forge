from src.bit_match_gen.pattern import Pattern
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
