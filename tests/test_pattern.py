
from src.bit_match_gen.pattern import Pattern
import unittest


class TestPattern(unittest.TestCase):
    def test_str_with_default_constructor_returns_xxxxxxxx(self):
        test_pattern = Pattern()
        assert str(test_pattern) == "xxxxxxxx"
