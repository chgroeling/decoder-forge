import logging
import yaml

from decoder_forge.bit_pattern import BitPattern
from decoder_forge.associated_struct_repo import AssociatedStructRepo
from decoder_forge.transpiller import transpill
from decoder_forge.pattern_algorithms import (
    build_decode_tree_by_fixed_bits,
    flatten_decode_tree,
)
from copy import deepcopy
from decoder_forge.pattern_algorithms import DecodeLeaf
from decoder_forge.pattern_algorithms import DecodeTree
from decoder_forge.print_tree import print_tree
from uuid import uuid1
from decoder_forge.i_printer import IPrinter

logger = logging.getLogger(__name__)


class OutPrinter(IPrinter):

    def __init__(self):
        pass

    def print(self, out: str):
        print(out)


def create_or_get_duid(guid, f_guid_to_data, duid_to_data):

    if guid in duid_to_data:
        data_entry = duid_to_data[guid]
    else:
        data_entry = f_guid_to_data(guid)

    data_to_duid = {v: k for k, v in duid_to_data.items()}
    duid = data_to_duid.get(data_entry, uuid1())
    duid_to_data[duid] = duid_to_data.get(duid, data_entry)
    return duid


def minimalize_tree(pat, children, f_guid_to_data, duid_to_data):

    duid_list = []
    for i in children:
        duid = create_or_get_duid(i.uid, f_guid_to_data, duid_to_data)
        duid_list.append(duid)

    duid_set = set(duid_list)
    if len(duid_set) <= 1:
        duid = duid_list[0]
        return DecodeLeaf(pat=pat, uid=duid)

    children = deepcopy(children)
    return DecodeTree(pat=pat, uid="", children=children)


def minimalize_tree_with_data_algo(tree, f_guid_to_data, duid_to_data=dict()):

    children = []
    for item in tree.children:
        if isinstance(item, DecodeTree):
            tree_item = minimalize_tree_with_data_algo(
                item, f_guid_to_data, duid_to_data
            )
            children.append(tree_item)
        else:
            duid = create_or_get_duid(item.uid, f_guid_to_data, duid_to_data)
            tree_item = DecodeLeaf(pat=item.pat, uid=duid)
            children.append(tree_item)

    if all([isinstance(i, DecodeLeaf) for i in children]):
        return minimalize_tree(tree.pat, children, f_guid_to_data, duid_to_data)
    else:
        return DecodeTree(pat=tree.pat, uid="", children=children)


def minimalize_tree_with_data(tree, f_guid_to_data):
    duid_to_data = dict()
    data_tree = minimalize_tree_with_data_algo(tree, f_guid_to_data, duid_to_data)
    return data_tree, duid_to_data


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

    uid_to_pat = {
        uuid1(): BitPattern.parse_pattern(str(pat))
        for pat, dct in ins["patterns"].items()
    }
    pat_to_uid = {v: k for k, v in uid_to_pat.items()}

    # associated structs
    as_repo = AssociatedStructRepo.build(
        struct_def=ins["struct_def"], pat_repo=pat_repo
    )

    context = ins["context"]

    # build decode tree
    pats_with_uid = [(i, pat_to_uid[i]) for i in pats]

    decode_tree = build_decode_tree_by_fixed_bits(
        pats_with_uid, decoder_width=decoder_width
    )

    flat_decode_tree = flatten_decode_tree(decode_tree)

    size_tree, size_dict = minimalize_tree_with_data(
        decode_tree, lambda guid: uid_to_pat[guid].bit_length
    )

    op = OutPrinter()

    def uid_to_size(uid):
        if uid not in size_dict:
            return uid
        return f"{size_dict[uid]}"

    print_tree(op, size_tree, uid_to_size)
    print(size_dict)
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
        "uid_to_pat": uid_to_pat,
        "as_repo": as_repo,
        "context": context,
        "tcall": tcall,
        "flat_decode_tree": flat_decode_tree,
    }
    rendered_code = tengine.generate(context)

    for i in rendered_code.splitlines():
        printer.print(i)
