import io

import pytest

from decoder_forge.template_engine import TemplateEngine
from decoder_forge.uc_decode import uc_decode


# A two-encoding fixture: one 8-bit instruction and one 16-bit one.
TEST_FORMAT = """
instructions:
- id: FOO
  mnemonic: FOO
  encodings:
  - name: T1
    length_bits: 8
    pattern: 0000xxxx
    bit_fields:
    - skip: 4
    - field: a
      width: 4
    decode: |
      d = UInt(a);
- id: BAR
  mnemonic: BAR
  encodings:
  - name: T1
    length_bits: 16
    pattern: 0001xxxxxxxxxxxx
    bit_fields:
    - skip: 4
    - field: b
      width: 12
    decode: |
      n = UInt(b);
"""


def _decode(instr_hex: str, size: int) -> str:
    printer = io.StringIO()
    uc_decode(printer, TemplateEngine(), TEST_FORMAT, instr_hex, size)
    return printer.getvalue()


def test_uc_decode_writes_the_decoded_instruction_to_the_printer():
    assert _decode("05", 8) == "0x05 FOO(d=5)\n"


def test_uc_decode_decodes_the_word_at_the_requested_size():
    # The same operand nibble, but the 16-bit encoding reads a 12-bit field.
    assert _decode("1abc", 16) == "0x1abc BAR(n=2748)\n"


def test_uc_decode_reports_a_word_that_does_not_fit_the_size():
    with pytest.raises(ValueError, match="does not fit in 8 bits"):
        _decode("1abc", 8)


def test_uc_decode_reports_a_size_the_format_does_not_use():
    with pytest.raises(ValueError, match="no 32-bit encodings"):
        _decode("00000000", 32)


def test_uc_decode_reports_a_non_hexadecimal_word():
    with pytest.raises(ValueError, match="not a hexadecimal"):
        _decode("nope", 8)


def test_uc_decode_no_match_is_a_result_not_an_error():
    assert _decode("f0", 8) == "0xf0 NoMatch()\n"
