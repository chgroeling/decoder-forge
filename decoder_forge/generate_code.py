import logging
import yaml

from decoder_forge.bit_pattern import BitPattern
from decoder_forge.associated_struct_repo import AssociatedStructRepo
from decoder_forge.transpiller import transpill
from decoder_forge.pattern_algorithms import (
    build_decode_tree_by_fixed_bits,
    flatten_decode_tree,
)
from decoder_forge.bit_utils import create_bit_mask

logger = logging.getLogger(__name__)


def generate_code(input_yaml, decoder_width, tengine, printer):
    """Generates and outputs decoder code in based on bit-patterns defined in a YAML
    string.

    This function parses a YAML input to extract bit pattern definitions, builds a
    decode tree based on fixed bit widths, and flattens the decode tree for easier
    handling. It also creates associated structures and a context dictionary that
    includes various helper functions and mappings. Lastly, it loads a language template
    using the provided template engine (tengine) to generate the final code, which is
    then printed line-by-line using the provided printer object.

    Args:
        input_yaml (str): A YAML string containing pattern definitions and additional
           context.
        decoder_width (int): The bit width to be used when constructing the decode tree.
        tengine (ITemplateEngine): A template engine instance used to generate code.
        printer (IPrinter): An output printer instance responsible for printing each
           line of the generated code.

    Raises:
        yaml.YAMLError: If the input YAML cannot be parsed.
        Exception: For any unexpected errors that occur during pattern processing or
           code generation.

    Example:
        >>> yaml_input = '''
        ... context: {}
        ... patterns:
        ...   '1010': {name: "BitPatternA"}
        ... struct_def: {}
        ... deffun: {}
        ... '''
        >>> generate_code(yaml_input, 16, my_template_engine, my_printer)
    """

    logger.info("Call: generate_code")
    ins = yaml.load(input_yaml, Loader=yaml.Loader)

    if ins is None:
        ins = {}

    if "context" not in ins:
        ins["context"] = dict()

    if "patterns" not in ins:
        ins["patterns"] = dict()

    if "struct_def" not in ins:
        ins["struct_def"] = dict()

    if "deffun" not in ins:
        ins["deffun"] = dict()

    # build pattern list
    pats = [BitPattern.parse_pattern(str(pat)) for pat, dct in ins["patterns"].items()]

    # build pattern repo
    pat_repo = {
        BitPattern.parse_pattern(str(pat)): dct for pat, dct in ins["patterns"].items()
    }

    # associated structs
    as_repo = AssociatedStructRepo.build(
        struct_def=ins["struct_def"], pat_repo=pat_repo
    )

    context = ins["context"]

    # build decode tree
    decode_tree = build_decode_tree_by_fixed_bits(pats, decoder_width=decoder_width)
    flat_decode_tree = flatten_decode_tree(decode_tree)

    tengine.load("python")

    deffun = ins["deffun"]

    def tcall(expr, placeholders=dict()):
        funname, rest = expr.split("(")
        rest = rest.strip(")")
        args = rest.split(",")
        arg_dict = dict()
        for a in args:
            if "=" not in a:
                continue
            dname, val = a.split("=")
            dname = dname.strip()
            val = val.strip()
            if val.startswith("$"):
                ph = val.strip("$")

                if ph in placeholders:
                    arg_dict[dname] = placeholders[ph]
            else:
                if val.startswith("&") and val[1:] in deffun:
                    val_func = val.strip("&")
                    func_ast_arg = deffun[val_func]
                    func_res = transpill(
                        yaml_ast=yaml.dump(func_ast_arg),
                        placeholders=arg_dict,
                        call=tcall,
                    )
                    arg_dict[dname] = func_res
                else:
                    arg_dict[dname] = val

        # code = deffun[name]

        func_ast = deffun[funname]
        return transpill(
            yaml_ast=yaml.dump(func_ast), placeholders=arg_dict, call=tcall
        )

    context = {
        "pat_repo": pat_repo,
        "as_repo": as_repo,
        "context": context,
        "tcall": tcall,
        "decode_tree": decode_tree,
        "flat_decode_tree": flat_decode_tree,
        # Add some conveniece functions
        "bit_utils": {"create_bit_mask": create_bit_mask},
    }
    rendered_code = tengine.generate(context)

    for i in rendered_code.splitlines():
        printer.print(i)
