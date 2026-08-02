import pytest

from decoder_forge.template_engine import TemplateEngine
from decoder_forge.uc_generate_code import uc_generate_code
from enum import IntEnum
from unittest.mock import Mock


# A minimal instructions/encodings fixture (8-bit instructions).
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
    length_bits: 8
    pattern: 01xxxxxx
    bit_fields:
    - skip: 2
    - field: b
      width: 6
    decode: |
      n = UInt(b); setflags = TRUE;
"""


def extract_generated_code(printer_mock: Mock):
    # call[0] is the list of positional arg, call[0][0] is the first positional arg
    generated_code = [call[0][0] for call in printer_mock.write.call_args_list]

    # generated code is in a list ... join it to get a string
    generated_code_str = "".join(generated_code)

    return generated_code_str


def _generate(yaml_buf: str):
    printer_mock = Mock(spec=["write"])
    tengine = TemplateEngine()
    uc_generate_code(printer_mock, tengine, yaml_buf)
    generated_code = extract_generated_code(printer_mock)
    test_namespace: dict = {}
    exec(generated_code, test_namespace)
    return test_namespace


def _enc(ns):
    """The generated ``Encoding`` enum, naming which form of an instruction matched."""
    return ns["Encoding"]


def _decode(ns, instr: int, context, size: int = 8):
    """Decode ``instr`` as an instruction of ``size`` bits.

    The size is the caller's to supply; the fixtures above are 8-bit formats, so that
    is the default.
    """
    return ns["decode"](instr, context, ns["InstructionSize"](size))


def test_uc_generate_code_generate_and_eval__code_empty_format_outputs_None():
    ns = _generate("")

    context = ns["Context"]()

    decode_output = _decode(ns, 0xFF, context)

    # a format with no encodings matches nothing, at any size
    assert decode_output == ns["NoMatch"]()


def test_uc_generate_code_generate_and_eval_foo_extracts_field():
    ns = _generate(TEST_FORMAT)

    context = ns["Context"]()

    # 0x05 matches FOO/T1 (0000xxxx); operand a = 0x5 -> d = UInt(a)
    decode_output = _decode(ns, 0x05, context)

    assert decode_output == ns["FOO"](encoding=_enc(ns).T1, d=0x5)


def test_uc_generate_code_generate_and_eval_bar_extracts_field_and_flags():
    ns = _generate(TEST_FORMAT)

    context = ns["Context"]()

    # 0x42 matches BAR/T1 (01xxxxxx); operand b = 0x02
    decode_output = _decode(ns, 0x42, context)

    assert decode_output == ns["BAR"](encoding=_enc(ns).T1, n=0x2, setflags=True)


def test_uc_generate_code_generate_and_eval_no_match_returns_nomatch():
    ns = _generate(TEST_FORMAT)

    context = ns["Context"]()

    # 0x80 matches neither pattern
    decode_output = _decode(ns, 0x80, context)

    assert decode_output == ns["NoMatch"]()


# A fixture whose decode block redirects via ``SEE`` when the operand is all-ones.
SEE_FORMAT = """
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
      if a == '1111' then SEE BAR;
      d = UInt(a);
"""


def test_uc_generate_code_generate_and_eval_see_returns_see_pseudo():
    ns = _generate(SEE_FORMAT)

    context = ns["Context"]()

    # 0x05 does not trigger the redirect -> normal decode
    assert _decode(ns, 0x05, context) == ns["FOO"](encoding=_enc(ns).T1, d=0x5)

    # 0x0F (a == 0b1111) flags the SEE side effect -> See pseudo-instruction
    assert _decode(ns, 0x0F, context) == ns["See"]()


# A fixture whose decode block only *tests* one operand (``cond``) and ignores another
# (``opt``) -- neither becomes an output variable, yet both must reach the result.
PASSTHROUGH_FORMAT = """
instructions:
- id: FOO
  mnemonic: FOO
  encodings:
  - name: T1
    length_bits: 8
    pattern: 00xxxxxx
    bit_fields:
    - skip: 2
    - field: cond
      width: 2
    - field: opt
      width: 4
    decode: |
      if cond == '11' then UNPREDICTABLE;
"""


def test_uc_generate_code_generate_and_eval_unassigned_and_unused_fields_are_members():
    ns = _generate(PASSTHROUGH_FORMAT)

    context = ns["Context"]()

    # 0x15: cond = 0b01 (read but never assigned to an output), opt = 0x5 (never
    # mentioned by the decode block) -- both are carried into the instruction object.
    assert _decode(ns, 0x15, context) == ns["FOO"](
        encoding=_enc(ns).T1, cond=0x1, opt=0x5
    )

    # cond == 0b11 still flags UNPREDICTABLE
    assert _decode(ns, 0x35, context) == ns["Unpredictable"]()


def test_uc_generate_code_members_are_annotated_with_their_inferred_type():
    ns = _generate(TEST_FORMAT)

    # ``n = UInt(b)`` is a number, ``setflags = TRUE`` a truth value -- the annotations
    # follow arm-transpiller's inferred types (uint32 and bool).
    annotations = ns["BAR"].__annotations__
    assert annotations["n"] is int
    assert annotations["setflags"] is bool


def test_uc_generate_code_passthrough_members_are_annotated_as_int():
    ns = _generate(PASSTHROUGH_FORMAT)

    # Pass-through operands are raw encoded fields (``bits2`` / ``bits4``), so they are
    # plain ints rather than bools.
    annotations = ns["FOO"].__annotations__
    assert annotations["cond"] is int
    assert annotations["opt"] is int


# A fixture whose decode block assigns a different member in each branch -- the leaf
# hands both to the constructor, so the one the taken branch skipped must still exist.
BRANCHED_FORMAT = """
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
      wide = (a == '1111');
      if wide then
           big = UInt(a);
      else
           small = UInt(a);
"""


def test_uc_generate_code_members_assigned_in_one_branch_only():
    ns = _generate(BRANCHED_FORMAT)

    context = ns["Context"]()

    # Every member is required, so the member the taken branch skipped is pre-set to
    # the zero of its type instead of raising UnboundLocalError.
    assert _decode(ns, 0x05, context) == ns["FOO"](
        encoding=_enc(ns).T1, wide=False, big=0, small=0x5
    )
    assert _decode(ns, 0x0F, context) == ns["FOO"](
        encoding=_enc(ns).T1, wide=True, big=0xF, small=0
    )


# One instruction whose two encodings type the same member differently: a truth value
# in T1, a number in T2. Both share a single struct, so the member type has to hold
# either of them.
MERGED_TYPES_FORMAT = """
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
      x = TRUE;
  - name: T2
    length_bits: 8
    pattern: 0001xxxx
    bit_fields:
    - skip: 4
    - field: a
      width: 4
    decode: |
      x = UInt(a);
"""


def test_uc_generate_code_member_type_merges_across_encodings():
    ns = _generate(MERGED_TYPES_FORMAT)

    # bool joined with uint32 gives uint32, so the shared member is an int.
    assert ns["FOO"].__annotations__["x"] is int

    context = ns["Context"]()
    # T1 never reads ``a``, so it is carried through; T2 turns it into ``x`` and does
    # not contribute an ``a`` member of its own -- but the struct has one, which T2
    # fills from the operand it extracted anyway.
    assert _decode(ns, 0x05, context) == ns["FOO"](encoding=_enc(ns).T1, x=True, a=0x5)
    assert _decode(ns, 0x15, context) == ns["FOO"](encoding=_enc(ns).T2, x=0x5, a=0x5)


def test_uc_generate_code_emits_opcode_intenum():
    """The generated code exports an ``Opcode`` IntEnum with entries for every
    instruction, ordered by their assigned ID, plus pseudo-instruction entries."""
    ns = _generate(TEST_FORMAT)

    assert "Opcode" in ns
    assert issubclass(ns["Opcode"], IntEnum)

    assert ns["Opcode"].OP_NO_MATCH == -1
    assert ns["Opcode"].OP_UNDEFINED == -2
    assert ns["Opcode"].OP_UNPREDICTABLE == -3
    assert ns["Opcode"].OP_SEE == -4

    assert ns["Opcode"].OP_FOO == 0
    assert ns["Opcode"].OP_BAR == 1

    # The per-class ``opcode`` ClassVar must match the enum entry.
    assert ns["FOO"].opcode == ns["Opcode"].OP_FOO == 0
    assert ns["BAR"].opcode == ns["Opcode"].OP_BAR == 1
    assert ns["NoMatch"].opcode == ns["Opcode"].OP_NO_MATCH == -1


def test_uc_generate_code_emits_encoding_intenum():
    """The generated code exports an ``Encoding`` IntEnum naming the encoding forms."""
    ns = _generate(MERGED_TYPES_FORMAT)

    assert issubclass(ns["Encoding"], IntEnum)
    # The number in the name is the entry's value: T1 is 1, not the zero-based position
    # it occupies.
    assert ns["Encoding"].T1 == 1
    assert ns["Encoding"].T2 == 2


def test_uc_generate_code_instructions_name_the_encoding_they_matched():
    """Both encodings of an instruction share its class, so the object has to say."""
    ns = _generate(MERGED_TYPES_FORMAT)

    context = ns["Context"]()

    assert _decode(ns, 0x05, context).encoding is ns["Encoding"].T1
    assert _decode(ns, 0x15, context).encoding is ns["Encoding"].T2


def test_uc_generate_code_encoding_names_need_not_be_thumb_forms():
    """The number in the name is what counts, whatever letter precedes it."""
    ns = _generate(MERGED_TYPES_FORMAT.replace("name: T1", "name: A1"))

    assert ns["Encoding"].A1 == 1
    assert ns["Encoding"].T2 == 2


def test_uc_generate_code_encoding_ids_stay_unique_when_names_collide():
    """A number another name already claimed falls back to the lowest free ID."""
    # ``A1`` comes first and takes 1, so ``T1`` gets the next free ID instead.
    fmt = MERGED_TYPES_FORMAT.replace("name: T2", "name: T1", 1).replace(
        "name: T1", "name: A1", 1
    )
    ns = _generate(fmt)

    assert ns["Encoding"].A1 == 1
    assert ns["Encoding"].T1 == 2


def test_uc_generate_code_encoding_empty_format_has_no_entries():
    """An empty format still exports the enum, with nothing in it."""
    ns = _generate("")

    assert issubclass(ns["Encoding"], IntEnum)
    assert list(ns["Encoding"]) == []


def test_uc_generate_code_opcode_empty_format_still_has_pseudo_entries():
    """An empty format still exports the Opcode enum with pseudo-instruction entries."""
    ns = _generate("")

    assert issubclass(ns["Opcode"], IntEnum)
    assert ns["Opcode"].OP_NO_MATCH == -1
    assert ns["Opcode"].OP_UNDEFINED == -2
    assert ns["Opcode"].OP_UNPREDICTABLE == -3
    assert ns["Opcode"].OP_SEE == -4


# Two encodings of different lengths whose fixed bits overlap: the 16-bit form is
# ``0001`` followed by a 12-bit operand, the 32-bit form ``0001`` followed by 28 bits.
# Read as a 32-bit word, the 16-bit form's operand would sit in bits 27..16.
MIXED_SIZE_FORMAT = """
instructions:
- id: NARROW
  mnemonic: NARROW
  encodings:
  - name: T1
    length_bits: 16
    pattern: 0001xxxxxxxxxxxx
    bit_fields:
    - skip: 4
    - field: a
      width: 12
    decode: |
      d = UInt(a);
- id: WIDE
  mnemonic: WIDE
  encodings:
  - name: T1
    length_bits: 32
    pattern: 0001xxxxxxxxxxxxxxxxxxxxxxxxxxxx
    bit_fields:
    - skip: 4
    - field: b
      width: 28
    decode: |
      n = UInt(b);
"""


def test_uc_generate_code_narrow_encoding_reads_its_own_width():
    """A 16-bit encoding's operands sit at the offsets its own layout gives them.

    The word handed to the 16-bit decoder is 16 bits wide and nothing else, so ``a``
    occupies bits 11..0 -- not bits 27..16 of a word padded out to the width of the
    widest instruction.
    """
    ns = _generate(MIXED_SIZE_FORMAT)

    context = ns["Context"]()

    assert _decode(ns, 0x1ABC, context, size=16) == ns["NARROW"](
        encoding=_enc(ns).T1, d=0xABC
    )


def test_uc_generate_code_same_word_decodes_differently_per_size():
    """The size selects the decoder, so one word can mean two different things."""
    ns = _generate(MIXED_SIZE_FORMAT)

    context = ns["Context"]()

    # As a 32-bit word this is WIDE with a 28-bit operand ...
    assert _decode(ns, 0x1000ABCD, context, size=32) == ns["WIDE"](
        encoding=_enc(ns).T1, n=0x000ABCD
    )
    # ... while its low half read as a 16-bit instruction is NARROW.
    assert _decode(ns, 0xABCD, context, size=16) == ns["NoMatch"]()
    assert _decode(ns, 0x1BCD, context, size=16) == ns["NARROW"](
        encoding=_enc(ns).T1, d=0xBCD
    )


def test_uc_generate_code_unused_size_answers_no_match():
    """Asking for a size the instruction set has no encodings for is not an error."""
    ns = _generate(MIXED_SIZE_FORMAT)

    context = ns["Context"]()

    assert _decode(ns, 0x1A, context, size=8) == ns["NoMatch"]()


def test_uc_generate_code_supported_sizes_lists_the_populated_ones():
    ns = _generate(MIXED_SIZE_FORMAT)

    size = ns["InstructionSize"]
    assert ns["get_supported_sizes"]() == (size.SIZE_16BIT, size.SIZE_32BIT)

    ns = _generate(TEST_FORMAT)
    assert ns["get_supported_sizes"]() == (ns["InstructionSize"].SIZE_8BIT,)


def test_uc_generate_code_rejects_an_unsupported_encoding_length():
    """A 12-bit encoding has no instruction size a caller could ask for it under."""
    fmt = TEST_FORMAT.replace("pattern: 0000xxxx", "pattern: 0000xxxxxxxx")

    with pytest.raises(ValueError, match="12 bits long"):
        _generate(fmt)


def test_uc_generate_code_rejects_length_bits_disagreeing_with_the_pattern():
    """The pattern is the authority; a contradicting length_bits is a format bug."""
    fmt = TEST_FORMAT.replace("length_bits: 8", "length_bits: 16", 1)

    with pytest.raises(ValueError, match="length_bits is 16"):
        _generate(fmt)
