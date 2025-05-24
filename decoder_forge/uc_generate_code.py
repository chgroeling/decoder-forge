import logging
import yaml

from decoder_forge.i_printer import IPrinter
from decoder_forge.i_template_engine import ITemplateEngine
from decoder_forge.bit_pattern import BitPattern
from decoder_forge.associated_struct_repo import AssociatedStructRepo
from decoder_forge.transpiller import transpill
from decoder_forge.pattern_algorithms import (
    build_decode_tree_by_fixed_bits,
    flatten_decode_tree,
)
from decoder_forge.bit_utils import create_bit_mask
from decoder_forge.generate_code import generate_code

logger = logging.getLogger(__name__)


def uc_generate_code(
    printer: IPrinter, tengine: ITemplateEngine, input_yaml: str, decoder_width: int
):
    logger.info("Call: uc_generate_code")
    generate_code(input_yaml, decoder_width, tengine, printer)
