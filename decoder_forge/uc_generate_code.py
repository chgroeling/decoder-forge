import logging

from decoder_forge.template_engine import ITemplateEngine
from decoder_forge.generate_code import generate_code

logger = logging.getLogger(__name__)


def uc_generate_code(
    printer,
    tengine: ITemplateEngine,
    input_yaml: str,
    auto_format: bool = True,
):
    logger.info("Call: uc_generate_code")
    generate_code(input_yaml, tengine, printer, auto_format=auto_format)
