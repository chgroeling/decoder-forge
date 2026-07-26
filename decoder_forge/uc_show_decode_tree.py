import yaml
import logging
from decoder_forge.bit_pattern import BitPattern
from decoder_forge.pattern_algorithms import (
    assign_uids,
    build_decode_tree_by_fixed_bits,
)
from decoder_forge.print_tree import print_tree

logger = logging.getLogger(__name__)


def uc_show_decode_tree(printer, input_yaml: str, decoder_width: int):
    """Decode a YAML string to build and display a decode tree.

    This function takes a YAML string which encodes a list of pattern dictionaries.
    It decodes the YAML into Python objects using the pattern_decoder, extracts
    bit patterns to build a repository mapping, organizes these patterns into a
    hierarchical tree based on fixed bits, and finally prints the tree using the
    provided printer.

    Args:
        printer: Writable stream with a ``write(str)`` method.
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

    instructions = ins.get("instructions", []) or []

    # build pattern repo (BitPattern -> {name})  from the instructions/encodings format
    pat_repo = {}
    for instr in instructions:
        for encoding in instr.get("encodings", []):
            pat = BitPattern.parse_pattern(str(encoding["pattern"]))
            name = f"{instr['id'].lower()}_{encoding['name'].lower()}"
            pat_repo[pat] = {"name": name}

    pats = list(pat_repo.keys())
    uid_to_pat, _, pats_with_uid = assign_uids(pats)

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
