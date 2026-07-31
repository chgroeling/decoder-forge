from decoder_forge.template_engine import TemplateEngine
from decoder_forge.uc_generate_code import uc_generate_code
from enum import IntEnum
from unittest.mock import Mock


# A minimal instructions/encodings fixture (8-bit decoder width).
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


def _generate(yaml_buf: str, decoder_width: int = 8):
    printer_mock = Mock(spec=["write"])
    tengine = TemplateEngine()
    uc_generate_code(printer_mock, tengine, yaml_buf, decoder_width=decoder_width)
    generated_code = extract_generated_code(printer_mock)
    test_namespace: dict = {}
    exec(generated_code, test_namespace)
    return test_namespace


def test_uc_generate_code_generate_and_eval__code_empty_format_outputs_None():
    ns = _generate("")

    context = ns["Context"]()

    # call the decoder; decode returns (result, n_bytes)
    decode_output = ns["decode"](0xFF, context)

    # returns NoMatch class, advancing by the minimum instruction width (1 byte)
    assert decode_output == (ns["NoMatch"](), 1)


def test_uc_generate_code_generate_and_eval_foo_extracts_field():
    ns = _generate(TEST_FORMAT)

    context = ns["Context"]()

    # 0x05 matches FOO/T1 (0000xxxx); operand a = 0x5 -> d = UInt(a)
    decode_output = ns["decode"](0x05, context)

    assert decode_output == (ns["FOO"](d=0x5), 1)


def test_uc_generate_code_generate_and_eval_bar_extracts_field_and_flags():
    ns = _generate(TEST_FORMAT)

    context = ns["Context"]()

    # 0x42 matches BAR/T1 (01xxxxxx); operand b = 0x02
    decode_output = ns["decode"](0x42, context)

    assert decode_output == (ns["BAR"](n=0x2, setflags=True), 1)


def test_uc_generate_code_generate_and_eval_no_match_returns_nomatch():
    ns = _generate(TEST_FORMAT)

    context = ns["Context"]()

    # 0x80 matches neither pattern
    decode_output = ns["decode"](0x80, context)

    assert decode_output == (ns["NoMatch"](), 1)


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
    assert ns["decode"](0x05, context) == (ns["FOO"](d=0x5), 1)

    # 0x0F (a == 0b1111) flags the SEE side effect -> See pseudo-instruction
    assert ns["decode"](0x0F, context) == (ns["See"](), 1)


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
    assert ns["decode"](0x15, context) == (ns["FOO"](cond=0x1, opt=0x5), 1)

    # cond == 0b11 still flags UNPREDICTABLE
    assert ns["decode"](0x35, context) == (ns["Unpredictable"](), 1)


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
    assert ns["decode"](0x05, context) == (ns["FOO"](wide=False, big=0, small=0x5), 1)
    assert ns["decode"](0x0F, context) == (ns["FOO"](wide=True, big=0xF, small=0), 1)


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
    assert ns["decode"](0x05, context) == (ns["FOO"](x=True, a=0x5), 1)
    assert ns["decode"](0x15, context) == (ns["FOO"](x=0x5, a=0x5), 1)


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


def test_uc_generate_code_opcode_empty_format_still_has_pseudo_entries():
    """An empty format still exports the Opcode enum with pseudo-instruction entries."""
    ns = _generate("")

    assert issubclass(ns["Opcode"], IntEnum)
    assert ns["Opcode"].OP_NO_MATCH == -1
    assert ns["Opcode"].OP_UNDEFINED == -2
    assert ns["Opcode"].OP_UNPREDICTABLE == -3
    assert ns["Opcode"].OP_SEE == -4
