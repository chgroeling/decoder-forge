import click
import logging
from decoder_forge.uc_show_decode_tree import uc_show_decode_tree
from decoder_forge.external.printer import Printer
from decoder_forge.external.template_engine import TemplateEngine
from decoder_forge.uc_generate_code import uc_generate_code

logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.pass_context
def cli(ctx, verbose):
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    level = logging.CRITICAL
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO

    logging.basicConfig(encoding="utf-8", level=level)

    ctx.obj["verbosity"] = verbose


@cli.command()
@click.argument("INPUT_PATH")
@click.pass_context
def generate_code(self, input_path: str):
    """Generate decoder code from JSON pattern definitions.

    This command reads a JSON file from the specified INPUT_PATH, which is expected to
    contain binary instruction definitions.It the generates decoder code based on the
    contained patterns using a template engine, and prints the generated code line by
    line to the standard output.

    INPUT_PATH: The file path to a JSON file containing pattern definitions.

    Example:
        $ python cli.py generate_code patterns.json
    """
    json_buf = ""
    with open(input_path, "r", encoding="utf-8") as fp:
        json_buf = fp.read()

    printer = Printer()
    tengine = TemplateEngine()
    uc_generate_code(printer, tengine, json_buf)


@cli.command()
@click.argument("INPUT_PATH")
@click.pass_context
def show_tree(ctx, input_path: str):
    """
    Show the decode tree of an instruction set.

    This command reads a JSON file from the specified INPUT_PATH, which is expected to
    contain binary instruction definitions. It decodes these definitions to build their
    decode tree and outputs the tree using a printer.

    INPUT_PATH: The file path to a JSON file containing pattern definitions.

    Example:
        $ python cli.py show_tree instructions.json
    """

    json_buf = ""
    with open(input_path, "r", encoding="utf-8") as fp:
        json_buf = fp.read()

    printer = Printer()
    uc_show_decode_tree(printer, json_buf)


def main():
    cli()
