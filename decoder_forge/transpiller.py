import yaml


class Visitor:

    def __init__(self, call):
        self._call = call

    # UNARY
    # ----------------
    def do_braces(self, expr):
        return f"({expr})"

    def do_assert(self, expr):
        return f"assert({expr})"

    # BINARY
    # ----------------
    def do_add(self, left, right):
        return f"{left} + {right}"

    def do_is_equal(self, left, right):
        return f"{left} == {right}"

    def do_shiftright(self, left, right):
        return f"{left} >> {right}"

    def do_and(self, left, right):
        return f"{left} & {right}"

    # SPECIAL
    # ----------------
    def do_assign(self, target, expr, comment):
        if comment is None:
            return f"{target} = {expr}"
        else:
            return f"{target} = {expr} # {comment}"

    def do_call(self, expr, comment):
        if comment is None:
            return f"{self._call(expr)}"
        else:
            return f"{self._call(expr)} # {comment}"

    def do_eval(self, expr, placeholders):
        return str(eval(expr, placeholders))


def transpill_recurse(visitor: Visitor, node, placeholders: dict[str, str]):
    code = ""

    if "type" not in node:
        return code

    if node["type"] == "binary":
        arg_right = None

        if isinstance(node["right"], dict):
            arg_right = transpill_recurse(visitor, node["right"], placeholders)
        else:
            right = node["right"]
            arg_right = right if right not in placeholders else placeholders[right]

        arg_left = None
        if isinstance(node["left"], dict):
            arg_left = transpill_recurse(visitor, node["left"], placeholders)
        else:
            left = node["left"]
            arg_left = left if left not in placeholders else placeholders[left]

        if node["op"] == "add":
            code += visitor.do_add(arg_left, arg_right)
        elif node["op"] == "shiftright":
            code += visitor.do_shiftright(arg_left, arg_right)
        elif node["op"] == "and":
            code += visitor.do_and(arg_left, arg_right)
        elif node["op"] == "is_equal":
            code += visitor.do_is_equal(arg_left, arg_right)

    elif node["type"] == "unary":
        arg_expr = None
        if isinstance(node["expr"], dict):
            arg_expr = transpill_recurse(visitor, node["expr"], placeholders)
        else:
            expr = node["expr"]
            arg_expr = expr if expr not in placeholders else placeholders[expr]

        if node["op"] == "braces":
            code += visitor.do_braces(arg_expr)

        elif node["op"] == "assert":
            code += visitor.do_assert(arg_expr)

    elif node["type"] == "assign":
        arg_expr = None
        if isinstance(node["expr"], dict):
            arg_expr = transpill_recurse(visitor, node["expr"], placeholders)
        else:
            expr = node["expr"]
            arg_expr = expr if expr not in placeholders else placeholders[expr]

        target = node["target"]
        ret_target = target if target not in placeholders else placeholders[target]
        comment = None if "comment" not in node else node["comment"]
        code += visitor.do_assign(ret_target, arg_expr, comment)

    elif node["type"] == "eval":
        code += visitor.do_eval(node["expr"], placeholders)

    elif node["type"] == "call":
        comment = None if "comment" not in node else node["comment"]
        code += visitor.do_call(node["expr"], comment)

    return code


def transpill(
    yaml_ast: str, placeholders: dict[str, str] = dict(), call=lambda name, args: ""
) -> list[str]:
    ast = yaml.load(yaml_ast, Loader=yaml.Loader)

    if ast is None:
        ast = dict()

    visitor = Visitor(call=call)
    code = transpill_recurse(visitor, ast, placeholders)

    return code
