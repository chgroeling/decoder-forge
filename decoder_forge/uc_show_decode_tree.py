import json
import logging
from decoder_forge.i_printer import IPrinter

logger = logging.getLogger(__name__)


def uc_show_decode_tree(printer: IPrinter, input_json: str):
    logger.info("Call: uc_show_decode_tree")
    # decode json

    # build pattern list

    # build tree

    # create template
    printer.print("hello world")
