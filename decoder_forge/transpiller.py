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

    # VARIADIC
    # ----------------
    def do_add(self, *args):
        """Generates a string representing the addition of two operands."""
        return " + ".join(args)

    def do_sub(self, *args):
        """Generates a string representing the subtraction of two operands."""
        return " - ".join(args)

    def do_mul(self, *args):
        """Generates a string representing the subtraction of two operands."""
        return " * ".join(args)

    def do_mod(self, *args):
        """Generates a string representing the modulo of multiple operands."""
        return " % ".join(args)

    def do_and(self, *args):
        """Generates a string representing the bitwise AND operation."""
        return " & ".join(args)

    def do_logical_and(self, *args):
        """Generates a string representing the bitwise AND operation."""
        return " and ".join(args)

    def do_logical_or(self, *args):
        """Generates a string representing the bitwise AND operation."""
        return " or ".join(args)

    def do_xor(self, *args):
        """Generates a string representing the bitwise XOR operation."""
        return " ^ ".join(args)

    def do_or(self, *args):
        """Generates a string representing the bitwise OR operation."""
        return " | ".join(args)

    # BINARY
    # ----------------

    def do_is_equal(self, left, right):
        """Generates a string representing the equality check between two operands."""
        return f"{left} == {right}"

    def do_less(self, left, right):
        return f"{left} < {right}"
    
    def do_is_not_equal(self, left, right):
        """Generates a string representing the not equality check between two operands."""
        return f"{left} != {right}"

    def do_shiftright(self, left, right):
        """Generates a string representing the right bit-shift operation."""
        return f"{left} >> {right}"

    def do_shiftleft(self, left, right):
        """Generates a string representing the left bit-shift operation."""
        return f"{left} << {right}"

    # UNARY
    # ----------------
    def do_braces(self, expr):
        """Wraps an expression in parentheses."""
        return f"({expr})"

    def do_not(self, expr):
        return f"~{expr}"

    def do_logical_not(self, expr):
        return f"not {expr}"

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

    def do_return(self, expr, comment):
        """Generates a string representing an return operation, optionally with a
        comment.
        """
        if comment is None:
            return f"return {expr}"
        else:
            return f"return {expr} # {comment}"

    def do_call(self, expr, placeholders, comment):
        """Generates a string representing a function call, optionally with a
        comment."""
        if comment is None:
            return f"{self._call(expr, placeholders)}"
        else:
            return f"{self._call(expr, placeholders)} # {comment}"

    def do_eval(self, expr, placeholders):
        """Evaluates an expression using the provided placeholders."""
        py_expr = expr.replace("$", "_ph_")
        return str(eval(py_expr, {"_ph_" + k: v for k, v in placeholders.items()}))

    def do_switch(self, var, *cond_then):
        out = ""
        first = True
        for cond, then in cond_then:
            if first:
                out += f"if {var} == {cond}:\n"
            else:
                out += f"elif {var} == {cond}:\n"

            first = False
            then_lines = then.split("\n")
            for line in then_lines:
                out += f"    {line}\n"
        return out

    def do_if(self, cond, then, el):
        """Generates a string representing an if-else statement."""
        out = f"if {cond}:\n"

        if el is not None:
            then_lines = then.split("\n")
            for line in then_lines:
                out += f"    {line}\n"
            out += "else:\n"
            else_lines = el.split("\n")
            for line in else_lines:
                out += f"    {line}\n"

        else:
            then_lines = then.split("\n")
            for line in then_lines:
                out += f"    {line}\n"
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
        ...   "op": "add",
        ...   "args": [
        ...     "a",
        ...     "b"
        ... ]}
        >>> transpill_recurse(visitor, ast_node, {})
        "a + b"
    """
    code = ""

    if "op" not in node:
        return code

    def replace_placeholders(expr):
        if str(expr).startswith("$"):
            ph = expr.strip("$")
            return expr if ph not in placeholders else placeholders[ph]
        else:
            return expr

    def transpill_or_eval(node):
        arg = None
        if isinstance(node, dict):
            arg = transpill_recurse(visitor, node, placeholders)
        else:
            expr = node
            arg = replace_placeholders(expr)
        return arg

    # VARIADIC
    # ----------------

    if node["op"] == "add":
        args = list()
        for arg_expr in node["args"]:
            args.append(transpill_or_eval(arg_expr))

        code += visitor.do_add(*args)

    elif node["op"] == "sub":
        args = list()
        for arg_expr in node["args"]:
            args.append(transpill_or_eval(arg_expr))

        code += visitor.do_sub(*args)

    elif node["op"] == "mul":
        args = list()
        for arg_expr in node["args"]:
            args.append(transpill_or_eval(arg_expr))

        code += visitor.do_mul(*args)

    elif node["op"] == "mod":
        args = list()
        for arg_expr in node["args"]:
            args.append(transpill_or_eval(arg_expr))

        code += visitor.do_mod(*args)

    elif node["op"] == "and":
        args = list()
        for arg_expr in node["args"]:
            args.append(transpill_or_eval(arg_expr))

        code += visitor.do_and(*args)

    elif node["op"] == "logical_and":
        args = list()
        for arg_expr in node["args"]:
            args.append(transpill_or_eval(arg_expr))

        code += visitor.do_logical_and(*args)

    elif node["op"] == "logical_or":
        args = list()
        for arg_expr in node["args"]:
            args.append(transpill_or_eval(arg_expr))

        code += visitor.do_logical_or(*args)

    elif node["op"] == "xor":
        args = list()
        for arg_expr in node["args"]:
            args.append(transpill_or_eval(arg_expr))

        code += visitor.do_xor(*args)
    elif node["op"] == "or":
        args = list()
        for arg_expr in node["args"]:
            args.append(transpill_or_eval(arg_expr))

        code += visitor.do_or(*args)

    # BINARY
    # ----------------

    elif node["op"] == "is_equal":
        arg_right = transpill_or_eval(node["right"])
        arg_left = transpill_or_eval(node["left"])

        code += visitor.do_is_equal(arg_left, arg_right)

    elif node["op"] == "is_not_equal":
        arg_right = transpill_or_eval(node["right"])
        arg_left = transpill_or_eval(node["left"])

        code += visitor.do_is_not_equal(arg_left, arg_right)

    elif node["op"] == "is_less":
        arg_right = transpill_or_eval(node["right"])
        arg_left = transpill_or_eval(node["left"])

        code += visitor.do_less(arg_left, arg_right)

    elif node["op"] == "shiftright":
        arg_right = transpill_or_eval(node["right"])
        arg_left = transpill_or_eval(node["left"])

        code += visitor.do_shiftright(arg_left, arg_right)
    elif node["op"] == "shiftleft":
        arg_right = transpill_or_eval(node["right"])
        arg_left = transpill_or_eval(node["left"])

        code += visitor.do_shiftleft(arg_left, arg_right)

    # UNARY
    # ----------------

    elif node["op"] == "braces":
        arg_expr = transpill_or_eval(node["expr"])
        code += visitor.do_braces(arg_expr)
    elif node["op"] == "not":
        arg_expr = transpill_or_eval(node["expr"])
        code += visitor.do_not(arg_expr)
    elif node["op"] == "logical_not":
        arg_expr = transpill_or_eval(node["expr"])
        code += visitor.do_logical_not(arg_expr)

    elif node["op"] == "assert":
        arg_expr = transpill_or_eval(node["expr"])
        code += visitor.do_assert(arg_expr)

    # SPECIAL
    # ----------------

    elif node["op"] == "assign":
        arg_expr = transpill_or_eval(node["expr"])

        target = node["target"]
        ret_target = replace_placeholders(target)

        comment = None if "comment" not in node else node["comment"]
        code += visitor.do_assign(ret_target, arg_expr, comment)

    elif node["op"] == "return":
        arg_expr = transpill_or_eval(node["expr"])
        comment = None if "comment" not in node else node["comment"]
        code += visitor.do_return(arg_expr, comment)

    elif node["op"] == "eval":
        code += visitor.do_eval(node["expr"], placeholders)

    elif node["op"] == "call":
        comment = None if "comment" not in node else node["comment"]
        code += visitor.do_call(node["expr"], placeholders, comment)

    elif node["op"] == "seq":
        for idx, expr in enumerate(node["exprs"]):
            arg_expr = transpill_or_eval(expr)
            code += f"{arg_expr}"

            if idx != len(node["exprs"]) - 1:
                code += "\n"

    elif node["op"] == "if":
        cond = transpill_or_eval(node["cond"])
        then = transpill_or_eval(node["then"])
        el = None
        if "else" in node:
            el = transpill_or_eval(node["else"])
        code += visitor.do_if(cond, then, el)

    elif node["op"] == "switch":
        var = transpill_or_eval(node["var"])
        args = []
        for i in node["case"]:
            when = transpill_or_eval(i["when"])
            then = transpill_or_eval(i["then"])
            args.append((when, then))

        code += visitor.do_switch(var, *args)

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
