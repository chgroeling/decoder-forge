from decoder_forge.bit_pattern import BitPattern


def test_bit_pattern_round_trip_with_1x1x0_returns_1x1x0():
    pattern = BitPattern.parse_pattern("1x1x0")
    pattern_str = BitPattern.to_string(pattern)
    assert pattern_str == "1x1x0"
