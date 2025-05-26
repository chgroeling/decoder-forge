import yaml
import logging
from uuid import uuid1
from decoder_forge.i_printer import IPrinter
from decoder_forge.bit_pattern import BitPattern
from decoder_forge.pattern_algorithms import build_decode_tree_by_fixed_bits
from decoder_forge.print_tree import print_tree

logger = logging.getLogger(__name__)


def uc_show_decode_tree(printer: IPrinter, input_yaml: str, decoder_width: int):
    """Decode a YAML string to build and display a decode tree.

    This function takes a YAML string which encodes a list of pattern dictionaries.
    It decodes the YAML into Python objects using the pattern_decoder, extracts
    bit patterns to build a repository mapping, organizes these patterns into a
    hierarchical tree based on fixed bits, and finally prints the tree using the
    provided printer.

    Args:
        printer (IPrinter): An instance of IPrinter used for printing the tree.
        input_yaml (str): A YAML string containing a list of pattern dictionaries.

    Raises:
        yaml.YAMLErrors: If the input YAML is not valid.
        Exception: Any exception raised during pattern processing or tree building.

    Examples:
        >>> yaml_input = '[{"pattern": "some pattern", "name": "BitPattern1"},
            {"pattern": "another pattern", "name": "BitPattern2"}]'
        >>> uc_show_decode_tree(printer, yaml_input)
    """

    logger.info("Call: uc_show_decode_tree")
    ins = yaml.load(input_yaml, Loader=yaml.Loader)

    if ins is None:
        ins = {}

    if "patterns" not in ins:
        ins["patterns"] = dict()

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

    pats_with_uid = [(i, pat_to_uid[i]) for i in pats]

    # build decode tree
    decode_tree = build_decode_tree_by_fixed_bits(
        pats_with_uid, decoder_width=decoder_width
    )

    def f_uid_to_pat(uid):
        if uid not in uid_to_pat:
            return uid

        pat = uid_to_pat[uid]

        if pat not in pat_repo:
            return uid
        origin_pat = pat_repo[pat]
        name = origin_pat["name"]

        return name

    print_tree(printer, decode_tree, f_uid_to_pat)
