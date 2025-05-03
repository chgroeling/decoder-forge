import logging
import yaml

from decoder_forge.i_printer import IPrinter
from decoder_forge.i_template_engine import ITemplateEngine
from decoder_forge.pattern import Pattern
from decoder_forge.pattern_algorithms import build_decode_tree_by_fixed_bits
from decoder_forge.pattern_algorithms import flatten_decode_tree

logger = logging.getLogger(__name__)


def uc_generate_code(printer: IPrinter, tengine: ITemplateEngine, input_yaml: str):
    """
    Generate and output a decoder in an specified language based on patterns provided
    in a YAML string.

    This function decodes a YAML input (using a custom object hook) to extract Pattern
    objects, builds a hierarchical decode tree, and then flattens this tree for easier
    processing. It uses a template engine (tengine) to generate code based on a context
    that includes the repository mapping, decode tree, and flattened tree. Each line of
    the generated code is printed using the provided printer.

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
        >>> yaml_input = '[{"pattern": "1010", "name": "PatternA"}]'
        >>> uc_generate_code(printer, tengine, yaml_input)
    """

    def pattern_decoder(dct):
        """Decode a dictionary into a Pattern object if applicable."""
        if "pattern" in dct:
            dct["pattern"] = Pattern.parse_pattern(dct["pattern"])

        return dct  # fallback to default behavior

    logger.info("Call: uc_generate_code")
    ins = yaml.load(input_yaml, Loader=yaml.Loader)

    if ins is None:
        ins = {}

    if "patterns" not in ins:
        ins["patterns"] = []

    # convert
    ins = [pattern_decoder(dct) for dct in ins["patterns"]]

    # build pattern list and repository
    pats = [i["pattern"] for i in ins]
    repo = {i["pattern"]: {k: v for k, v in i.items() if k != "pattern"} for i in ins}

    # build decode tree
    decode_tree = build_decode_tree_by_fixed_bits(pats)
    flat_decode_tree = flatten_decode_tree(decode_tree)

    tengine.load("python")
    context = {
        "repo": repo,
        "decode_tree": decode_tree,
        "flat_decode_tree": flat_decode_tree,
    }
    rendered_code = tengine.generate(context)

    for i in rendered_code.splitlines():
        printer.print(i)
