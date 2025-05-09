import yaml


class VisitorPython:
    """A visitor class for generating Python code from an AST-like structure.

    This class contains methods that represent various operations (binary, unary,
    assignment, function call, etc.) and translates them into Python code strings.  The
    methods follow the order of operations as they might appear in a simple expression
    tree.
    """

    def __init__(self, call):
        """Initializes the VisitorPython instance.

        Args:
            call (Callable): A function to handle function call translations.  It should
                accept two arguments: the expression to call and a dictionary of
                placeholder values.
        """
        self._call = call

    # BINARY
    # ----------------
    def do_add(self, left, right):
        """Generates a string representing the addition of two operands."""
        return f"{left} + {right}"

    def do_is_equal(self, left, right):
        """Generates a string representing the equality check between two operands."""
        return f"{left} == {right}"

    def do_shiftright(self, left, right):
        """Generates a string representing the right bit-shift operation."""
        return f"{left} >> {right}"

    def do_shiftleft(self, left, right):
        """Generates a string representing the left bit-shift operation."""
        return f"{left} << {right}"

    def do_and(self, left, right):
        """Generates a string representing the bitwise AND operation."""
        return f"{left} & {right}"

    def do_or(self, left, right):
        """Generates a string representing the bitwise OR operation."""
        return f"{left} | {right}"

    # UNARY
    # ----------------
    def do_braces(self, expr):
        """Wraps an expression in parentheses."""
        return f"({expr})"

    def do_assert(self, expr):
        """Generates a string representing an assert statement."""
        return f"assert({expr})"

    # SPECIAL
    # ----------------
    def do_assign(self, target, expr, comment):
        """Generates a string representing an assignment operation, optionally with a
        comment.
        """
        if comment is None:
            return f"{target} = {expr}"
        else:
            return f"{target} = {expr} # {comment}"

    def do_call(self, expr, placeholders, comment):
        """Generates a string representing a function call, optionally with a comment.
        """
        if comment is None:
            return f"{self._call(expr, placeholders)}"
        else:
            return f"{self._call(expr, placeholders)} # {comment}"

    def do_eval(self, expr, placeholders):
        """Evaluates an expression using the provided placeholders."""
        return str(eval(expr, placeholders))

    def do_if(self, cond, then, el):
        """Generates a string representing an if-else statement."""
        out = f"if {cond}:\n"

        if el is not None:
            out += f"    {then}\n"
            out += "else:\n"
            out += f"    {el}"
        else:
            out += f"    {then}"
        return out


def transpill_recurse(visitor: VisitorPython, node, placeholders: dict[str, str]):
    """Recursively traverses the AST and translates nodes into Python code.

    The function inspects the 'type' of each node and delegates the translation to
    appropriate methods in the VisitorPython instance. It supports binary operations,
    unary operations, assignments, evaluations, function calls, and conditional
    statements.

    Args:
        visitor (VisitorPython): An instance of VisitorPython to handle code generation.
        node (dict): The current node from the AST. Expected to have a 'type' key.
        placeholders (dict[str, str]): A mapping of placeholders to their replacement
            values.

    Returns:
        str: The generated Python code string corresponding to the provided AST node.

    Example:
        >>> ast_node = {
        ...   "type": "binary",
        ...   "op": "add",
        ...   "left": "a",
        ...   "right": "b"
        ... }
        >>> transpill_recurse(visitor, ast_node, {})
        "a + b"
    """
    code = ""

    if "type" not in node:
        return code

    def transpill_or_eval(node):
        arg = None
        if isinstance(node, dict):
            arg = transpill_recurse(visitor, node, placeholders)
        else:
            expr = node
            arg = expr if expr not in placeholders else placeholders[expr]
        return arg

    if node["type"] == "binary":
        arg_right = transpill_or_eval(node["right"])
        arg_left = transpill_or_eval(node["left"])

        if node["op"] == "add":
            code += visitor.do_add(arg_left, arg_right)
        elif node["op"] == "shiftright":
            code += visitor.do_shiftright(arg_left, arg_right)
        elif node["op"] == "shiftleft":
            code += visitor.do_shiftleft(arg_left, arg_right)
        elif node["op"] == "and":
            code += visitor.do_and(arg_left, arg_right)
        elif node["op"] == "or":
            code += visitor.do_or(arg_left, arg_right)
        elif node["op"] == "is_equal":
            code += visitor.do_is_equal(arg_left, arg_right)

    elif node["type"] == "unary":
        arg_expr = transpill_or_eval(node["expr"])

        if node["op"] == "braces":
            code += visitor.do_braces(arg_expr)

        elif node["op"] == "assert":
            code += visitor.do_assert(arg_expr)

    elif node["type"] == "assign":
        print("assign")
        arg_expr = transpill_or_eval(node["expr"])

        target = node["target"]
        ret_target = target if target not in placeholders else placeholders[target]

        comment = None if "comment" not in node else node["comment"]
        code += visitor.do_assign(ret_target, arg_expr, comment)

    elif node["type"] == "eval":
        code += visitor.do_eval(node["expr"], placeholders)

    elif node["type"] == "call":
        print("call")
        comment = None if "comment" not in node else node["comment"]
        code += visitor.do_call(node["expr"], placeholders, comment)

    elif node["type"] == "if":

        cond = transpill_or_eval(node["cond"])
        then = transpill_or_eval(node["then"])
        el = None
        if "else" in node:
            el = transpill_or_eval(node["else"])
        code += visitor.do_if(cond, then, el)

    return code


def transpill(
    yaml_ast: str, placeholders: dict[str, str] = dict(), call=lambda name, args: ""
) -> list[str]:
    """Transpiles a YAML AST representation into Python code.

    This function loads a YAML string as an AST, initializes a VisitorPython instance,
    and then recursively traverses the AST to generate the corresponding Python code.
    If the YAML AST is empty or invalid, an empty AST is used instead.

    Args:
        yaml_ast (str): A YAML-formatted string representing the AST of the code.
        placeholders (dict[str, str], optional): A mapping for placeholder replacement
            in expressions.  Defaults to an empty dictionary.
        call (Callable, optional): A function to handle function call translation.
            It should accept two parameters: the expression and the placeholders.
            Defaults to a lambda function returning an empty string.

    Returns:
        list[str]: A list containing the generated Python code string representing the
        transpiled AST.

    Example:
        >>> yaml_input = '''
        ... type: binary
        ... op: add
        ... left: a
        ... right: b
        ... '''
        >>> transpill(yaml_input)
        ['a + b']
    """

    ast = yaml.load(yaml_ast, Loader=yaml.Loader)

    if ast is None:
        ast = dict()

    visitor = VisitorPython(call=call)
    code = transpill_recurse(visitor, ast, placeholders)

    return code
