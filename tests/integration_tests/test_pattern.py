from decoder_forge.pattern import Pattern


def test_pattern_round_trip_with_1x1x0_returns_1x1x0():
    pattern = Pattern.parse_pattern("1x1x0")
    pattern_str = Pattern.to_string(pattern)
    assert pattern_str == "1x1x0"
