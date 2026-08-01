import yaml
import logging
from decoder_forge.bit_pattern import BitPattern
from decoder_forge.generate_code import INSTRUCTION_SIZES, encoding_size
from decoder_forge.pattern_algorithms import (
    assign_uids,
    build_decode_tree_by_fixed_bits,
)
from decoder_forge.print_tree import print_tree

logger = logging.getLogger(__name__)


def uc_show_decode_tree(printer, input_yaml: str):
    """Decode a YAML string to build and display its decode trees.

    Each instruction size is matched by a tree of its own, built at that size's width,
    so one tree is printed per size the instruction set uses.

    Args:
        printer: Writable stream with a ``write(str)`` method.
        input_yaml (str): A YAML string in the ``instructions``/``encodings`` format.

    Raises:
        yaml.YAMLError: If the input YAML is not valid.
        ValueError: If an encoding's length is not a supported instruction size.

    Examples:
        >>> uc_show_decode_tree(printer, yaml_input)
    """

    logger.info("Call: uc_show_decode_tree")
    ins = yaml.load(input_yaml, Loader=yaml.Loader)

    if ins is None:
        ins = {}

    instructions = ins.get("instructions", []) or []

    # build pattern repo (BitPattern -> {name}) per size, from the
    # instructions/encodings format
    pat_repo: dict[BitPattern, dict] = {}
    buckets: dict[int, list[BitPattern]] = {size: [] for size in INSTRUCTION_SIZES}
    for instr in instructions:
        for encoding in instr.get("encodings", []):
            pat = BitPattern.parse_pattern(str(encoding["pattern"]))
            size = encoding_size(instr, encoding, pat)
            name = f"{instr['id'].lower()}_{encoding['name'].lower()}"
            pat_repo[pat] = {"name": name}
            buckets[size].append(pat)

    for size in INSTRUCTION_SIZES:
        pats = buckets[size]
        if not pats:
            continue

        uid_to_pat, _, pats_with_uid = assign_uids(pats)

        decode_tree = build_decode_tree_by_fixed_bits(pats_with_uid, decoder_width=size)

        def f_uid_to_pat(uid, uid_to_pat=uid_to_pat):
            if uid not in uid_to_pat:
                return uid

            pat = uid_to_pat[uid]

            if pat not in pat_repo:
                return uid
            origin_pat = pat_repo[pat]
            name = origin_pat["name"]

            return name

        printer.write(f"--- {size}-bit instructions ---\n")
        print_tree(printer, decode_tree, f_uid_to_pat)
        printer.write("\n")
