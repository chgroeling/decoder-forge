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
from uuid import uuid1
from decoder_forge.i_printer import IPrinter
from math import ceil

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

    # all patterns match
    if isinstance(data_tree, DecodeLeaf):
        return None, duid_to_data

    return data_tree, duid_to_data


def call_expression(expr, placeholders=dict(), deffun=dict()):
    funname, rest = expr.split("(")
    rest = rest.strip(")")
    args = rest.split(",")
    arg_dict = dict()

    def call_short(expr, placeholders=dict()):
        # wraps deffun
        return call_expression(expr, placeholders=placeholders, deffun=deffun)

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
                    call=call_short,
                )
                arg_dict[dname] = func_res
            else:
                arg_dict[dname] = val

    func_ast = deffun[funname]
    return transpill(
        yaml_ast=yaml.dump(func_ast), placeholders=arg_dict, call=call_short
    )


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

    # only build decode tree when patterns are assigned
    if len(pats_with_uid) != 0:
        max_decoder_bits = max((i.bit_length for i in pats))
        min_decoder_bits = min((i.bit_length for i in pats))

        if max_decoder_bits > decoder_width:
            raise ValueError("Patterns are to long for given decoder width")

        decode_tree = build_decode_tree_by_fixed_bits(
            pats_with_uid, decoder_width=decoder_width
        )
        flat_decode_tree = flatten_decode_tree(decode_tree)
    else:
        decoder_width = 0
        max_decoder_bits = 0
        min_decoder_bits = 0

        decode_tree = None
        flat_decode_tree = list()

    sliced_flat_size_tree = list()
    size_dict = dict()
    default_size = decoder_width
    needed_bytes_for_size_eval = int(ceil(min_decoder_bits / 8))
    needed_bytes_for_code_eval = int(ceil(decoder_width / 8))

    # only build size tree if decode tree was created
    if decode_tree is not None:

        size_tree, size_dict = minimalize_tree_with_data(
            decode_tree, lambda guid: uid_to_pat[guid].bit_length
        )

        def uid_to_size(uid):
            if uid not in size_dict:
                return uid
            return f"{size_dict[uid]}"

        sliced_flat_size_tree = list()

        if size_tree is not None:

            flat_size_tree = flatten_decode_tree(size_tree)

            needed_bits_for_size_eval = decoder_width - max(
                (i.trailing_wildcard_count for i, _, _, _, _ in flat_size_tree)
            )

            required_bytes_for_size_eval = int(ceil(needed_bits_for_size_eval / 8))

            if required_bytes_for_size_eval > needed_bytes_for_size_eval:
                raise ValueError("Size decoder needs more bits than smalles pattern")

            sliced_flat_size_tree = [
                (pat.extract_from_msb(needed_bytes_for_size_eval * 8), a, b, c, d)
                for pat, a, b, c, d in flat_size_tree
            ]

            # with an existing size decoder the default is always wrong
            default_size = 0

    tengine.load("python")

    def call_expr(expr, placeholders=dict()):
        # wraps deffun
        deffun = ins["deffun"]
        return call_expression(expr, placeholders=placeholders, deffun=deffun)

    context = {
        "pat_repo": pat_repo,
        "size_dict": size_dict,
        "uid_to_pat": uid_to_pat,
        "as_repo": as_repo,
        "context": context,
        "call_expr": call_expr,
        "flat_decode_tree": flat_decode_tree,
        "default_size": default_size,
        "needed_bytes_for_size_eval": needed_bytes_for_size_eval,
        "needed_bytes_for_code_eval": needed_bytes_for_code_eval,
        "sliced_flat_size_tree": sliced_flat_size_tree,
    }
    rendered_code = tengine.generate(context)

    for i in rendered_code.splitlines():
        printer.print(i)
