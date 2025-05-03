import yaml
import logging
from decoder_forge.i_printer import IPrinter
from decoder_forge.pattern import Pattern
from decoder_forge.pattern_algorithms import build_decode_tree_by_fixed_bits
from decoder_forge.pattern_algorithms import flatten_decode_tree
from decoder_forge.pattern_algorithms import DecodeTree

logger = logging.getLogger(__name__)

TREE_INDENT_WIDTH = 20


def print_tree(printer: IPrinter, decode_tree: DecodeTree, repo):
    """
    Print a hierarchical tree of patterns in a formatted manner.

    This function first flattens the hierarchical DecodeTree into a list of tuples.
    Each tuple contains a Pattern, its origin, the depth in the tree, a flag
    indicating if it is the first child and a flag indicating if it is the last
    child at that level. It then formats each node with appropriate indentation
    and prints it using the provided printer.

    Args:
        printer (IPrinter): An instance of IPrinter used to output text.
        pat_tree (DecodeTree): The root of the DecodeTree to be printed.
        repo (dict): A repository mapping patterns to additional metadata (e.g., names).

    Examples:
        >>> # Assume printer is an object implementing IPrinter and repo is a proper
            dictionary
        >>> print_tree(printer, pattern_tree, repo)
    """

    flattend_tree = flatten_decode_tree(decode_tree)

    for item, origin_pat, depth, first_child, last_child in flattend_tree:
        indent = "│ " * depth
        if depth == 0:
            printer.print("")

        if origin_pat is not None:
            if not last_child:
                tree_node = f"{indent}├─ x"
            else:  # in case the next element will be one depth up
                tree_node = f"{indent}└─ x"

            fmt_tree_node = ("{:" + str(TREE_INDENT_WIDTH) + "}").format(tree_node)
            name = repo[origin_pat]["name"]
            printer.print(f"{fmt_tree_node}| {str(item)} | {name}")
        else:
            tree_node = f"{indent}├─┐"
            fmt_tree_node = ("{:" + str(TREE_INDENT_WIDTH) + "}").format(tree_node)
            printer.print(f"{fmt_tree_node}| {str(item)}")


def uc_show_decode_tree(printer: IPrinter, input_yaml: str):
    """Decode a YAML string to build and display a pattern tree.

    This function takes a YAML string which encodes a list of pattern dictionaries.
    It decodes the YAML into Python objects using the pattern_decoder, extracts patterns
    to build a repository mapping, organizes these patterns into a hierarchical tree
    based on fixed bits, and finally prints the tree using the provided printer.

    Args:
        printer (IPrinter): An instance of IPrinter used for printing the tree.
        input_yaml (str): A YAML string containing a list of pattern dictionaries.

    Raises:
        yaml.YAMLErrors: If the input YAML is not valid.
        Exception: Any exception raised during pattern processing or tree building.

    Examples:
        >>> yaml_input = '[{"pattern": "some pattern", "name": "Pattern1"},
            {"pattern": "another pattern", "name": "Pattern2"}]'
        >>> uc_show_decode_tree(printer, yaml_input)
    """

    logger.info("Call: uc_show_decode_tree")
    ins = yaml.load(input_yaml, Loader=yaml.Loader)

    if ins is None:
        ins = {}

    if "patterns" not in ins:
        ins["patterns"] = dict()

    # build pattern list
    pats = [Pattern.parse_pattern(pat) for pat, dct in ins["patterns"].items()]

    # build pattern repo
    pat_repo = {Pattern.parse_pattern(pat): dct for pat, dct in ins["patterns"].items()}

    # build decode tree
    decode_tree = build_decode_tree_by_fixed_bits(pats)

    print_tree(printer, decode_tree, pat_repo)
