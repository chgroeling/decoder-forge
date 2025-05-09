from decoder_forge.transpiller import transpill


def test_transpil_empty_str():
    ast_yaml = ""

    tcode = transpill(ast_yaml)

    assert tcode == ""


def test_transpil_braces_returns_exectuable_python_code():
    ast_yaml = """type: unary
op: braces
expr: 10"""

    tcode = transpill(ast_yaml)

    assert tcode == "(10)"


def test_transpil_assert_equal_returns_exectuable_python_code():
    ast_yaml = """type: unary
op: assert
expr:
  type: binary
  op: is_equal
  left: a
  right: b"""

    tcode = transpill(ast_yaml)

    assert tcode == "assert(a == b)"


def test_transpil_add_returns_exectuable_python_code():
    ast_yaml = """type: binary
op: add
left: 10
right: 20"""

    tcode = transpill(ast_yaml)

    assert tcode == "10 + 20"


def test_transpil_shift_right_returns_exectuable_python_code():
    ast_yaml = """type: binary
op: shiftright
left: 10
right: 1"""

    tcode = transpill(ast_yaml)

    assert tcode == "10 >> 1"


def test_transpil_and_returns_exectuable_python_code():
    ast_yaml = """type: binary
op: and
left: 10
right: \"0x2\""""

    tcode = transpill(ast_yaml)

    assert tcode == "10 & 0x2"


def test_transpil_assign_returns_exectuable_python_code():
    ast_yaml = """type: assign
target: var
expr: 20"""

    tcode = transpill(ast_yaml)

    assert tcode == "var = 20"

def test_transpil_if_returns_exectuable_python_code():
    ast_yaml = """type: if
cond: var
then:
  type: assign
  target: a
  expr: 10
else:
  type: assign
  target: a
  expr: 20"""

    tcode = transpill(ast_yaml)

    assert tcode == """if var:
    a = 10
else:
    a = 20"""


def test_transpil_2adds_returns_exectuable_python_code():
    ast_yaml = """type: binary
op: add
left: 10
right:
  type: binary
  op: add
  left: 20
  right: 30"""

    tcode = transpill(ast_yaml)

    assert tcode == "10 + 20 + 30"


def test_transpil_assign_and_2adds_returns_exectuable_python_code():
    ast_yaml = """type: assign
target: var
expr:
  type: binary
  op: add
  left: 10
  right:
    type: binary
    op: add
    left: 20
    right: 30"""

    tcode = transpill(ast_yaml)

    assert tcode == "var = 10 + 20 + 30"


def test_transpil_assign_and_2adds_with_braces_returns_exectuable_python_code():
    ast_yaml = """type: assign
target: var
expr:
  type: binary
  op: add
  left: 10
  right:
    type: unary
    op: braces
    expr:
      type: binary
      op: add
      left: 20
      right: 30"""

    tcode = transpill(ast_yaml)

    assert tcode == "var = 10 + (20 + 30)"


def test_transpil_extract_bits_returns_exectuable_python_code():
    ast_yaml = """type: assign
target: result
expr:
  type: binary
  op: and
  left:
    type: unary
    op: braces
    expr:
      type: binary
      op: shiftright
      left: val
      right: arg_0
  right: arg_1"""

    tcode = transpill(ast_yaml)

    assert tcode == "result = (val >> arg_0) & arg_1"


def test_transpil_extract_bits_with_placeholders_returns_exectuable_python_code():
    ast_yaml = """type: assign
target: result
expr:
  type: binary
  op: and
  left:
    type: unary
    op: braces
    expr:
      type: binary
      op: shiftright
      left: code
      right: arg_0
  right: arg_1"""

    tcode = transpill(ast_yaml, {"result": "rd", "arg_0": "1U", "arg_1": "0x3ff"})

    assert tcode == "rd = (code >> 1U) & 0x3ff"


def test_transpil_extract_bits_with_placeholders_and_eval_returns_exectuable_python_code():
    ast_yaml = """type: assign
target: result
expr:
  type: binary
  op: and
  left:
    type: unary
    op: braces
    expr:
      type: binary
      op: shiftright
      left: code
      right: lsb
  right:
    type: eval
    expr:  \"hex((1 << (int(msb)-int(lsb)+1)) - 1)\""""

    tcode = transpill(ast_yaml, {"result": "rd", "msb": "5", "lsb": "2"})

    assert tcode == "rd = (code >> 2) & 0xf"
