import logging
import yaml

from decoder_forge.i_printer import IPrinter
from decoder_forge.i_template_engine import ITemplateEngine
from decoder_forge.bit_pattern import BitPattern
from decoder_forge.pattern_algorithms import build_decode_tree_by_fixed_bits
from decoder_forge.pattern_algorithms import flatten_decode_tree
from decoder_forge.associated_struct_repo import AssociatedStructRepo
from decoder_forge.associated_ops_repo import AssociatedOpsRepo
from decoder_forge import bit_utils

logger = logging.getLogger(__name__)


def uc_generate_code(printer: IPrinter, tengine: ITemplateEngine, input_yaml: str):
    """
    Generate and output a decoder in an specified language based on bit-patterns
    provided in a YAML string.

    This function decodes a YAML input (using a custom object hook) to extract
    BitPattern objects, builds a hierarchical decode tree, and then flattens this tree
    for easier processing. It uses a template engine (tengine) to generate code based
    on a context that includes the repository mapping, decode tree, and flattened tree.
    Each line of the generated code is printed using the provided printer.

    Args:
        printer (IPrinter): An instance of IPrinter responsible for printing output.
        tengine (ITemplateEngine): An instance of ITemplateEngine used for code
           generation.
        input_yaml (str): A YAML string representing a list of pattern dictionaries.

    Raises:
        yaml.YAMLError: If the input YAML is invalid.
        Exception: For any unexpected error during pattern processing or code
          generation.

    Example:
        >>> yaml_input = '[{"pattern": "1010", "name": "BitPatternA"}]'
        >>> uc_generate_code(printer, tengine, yaml_input)
    """
    logger.info("Call: uc_generate_code")
    ins = yaml.load(input_yaml, Loader=yaml.Loader)

    if ins is None:
        ins = {}

    if "patterns" not in ins:
        ins["patterns"] = dict()

    if "struct_def" not in ins:
        ins["struct_def"] = dict()

    # build pattern list
    pats = [BitPattern.parse_pattern(pat) for pat, dct in ins["patterns"].items()]

    # build pattern repo
    pat_repo = {
        BitPattern.parse_pattern(pat): dct for pat, dct in ins["patterns"].items()
    }

    if "operations" not in ins:
        ins["operations"] = dict()

    as_repo = AssociatedStructRepo.build(
        struct_def=ins["struct_def"], pat_repo=pat_repo
    )

    aops_repo = AssociatedOpsRepo.build(ops_def=ins["operations"], pat_repo=pat_repo)

    # build decode tree
    decode_tree = build_decode_tree_by_fixed_bits(pats)
    flat_decode_tree = flatten_decode_tree(decode_tree)

    tengine.load("python")
    context = {
        "pat_repo": pat_repo,
        "as_repo": as_repo,
        "aops_repo": aops_repo,
        "decode_tree": decode_tree,
        "flat_decode_tree": flat_decode_tree,

        # Add some conviniece functions
        "bit_utils": {"create_bit_mask": bit_utils.create_bit_mask},
    }
    rendered_code = tengine.generate(context)

    for i in rendered_code.splitlines():
        printer.print(i)
