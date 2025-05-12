import click
import logging
import sys

from typing import Optional
from decoder_forge.uc_show_decode_tree import uc_show_decode_tree
from decoder_forge.external.printer import Printer
from decoder_forge.external.template_engine import TemplateEngine
from decoder_forge.uc_generate_code import uc_generate_code
from contextlib import contextmanager

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


@contextmanager
def open_output_stream(output_file: Optional[str]):
    """
    Context manager for opening an output stream.

    This function yields sys.stdout if no output file is specified.
    Otherwise, it opens the specified file for writing and yields the file handle.

    Args:
        output_file (Optional[str]): Path to the output file. If None, sys.stdout is used.

    Yields:
        TextIO: A writable file-like object.

    Example:
        with open_output_stream('output.txt') as stream:
            stream.write("Hello World!")
    """

    if output_file is None:
        yield sys.stdout
    else:
        with open(output_file, "w") as f:
            yield f


@cli.command()
@click.argument("INPUT_PATH", type=str)
@click.option(
    "--decoder_width",
    help="Target bit width; patterns are extended to this width before decoding "
    + "(default: 32)",
    default=32,
    type=int,
)
@click.option(
    "--out_file",
    help="Output file to write the generated code. Defaults to None, which outputs to "
    + "stdout.",
    default=None,
    type=str,
)
@click.pass_context
def generate_code(
    self, input_path: str, decoder_width: int, out_file: Optional[str]
):
    """Generate decoder code from YAML instruction patterns.

    This command reads a YAML file from the provided INPUT_PATH which should contain
    binary instruction definitions. It then generates decoder code using a template
    engine and prints the output either to stdout or an output file if provided.

    Args:
        input_path (str): The file path to the YAML file containing instruction
          definitions.
        decoder_width (int): The target bit width for extending patterns
          (default is 32).
        output_file (Optional[str]): Optional file path to write the generated code.

    Raises:
        IOError: If reading the input file or writing to the output file fails.

    Example:
        $ python cli.py generate_code patterns.yaml --decoder_width 32
          --output_file decoder.py
    """

    yaml_buf = ""
    with open(input_path, "r", encoding="utf-8") as fp:
        yaml_buf = fp.read()

    tengine = TemplateEngine()
    with open_output_stream(out_file) as f:
        printer = Printer(f)
        uc_generate_code(printer, tengine, yaml_buf, decoder_width)


@cli.command()
@click.argument("INPUT_PATH", type=str)
@click.option(
    "--decoder_width",
    help="Target bit width; patterns are extended to this width before decoding "
    + "(default: 32)",
    default=32,
    type=int,
)
@click.pass_context
def show_tree(ctx, input_path: str, decoder_width: int):
    """
    Show the decode tree of an instruction set.

    This command reads a YAML file from the specified INPUT_PATH, which is expected to
    contain binary instruction definitions. It decodes these definitions to build their
    decode tree and outputs the tree using a printer.

    INPUT_PATH: The file path to a YAML file containing pattern definitions.

    Example:
        $ python cli.py show_tree instructions.yaml
    """

    yaml_buf = ""
    with open(input_path, "r", encoding="utf-8") as fp:
        yaml_buf = fp.read()

    printer = Printer(sys.stdout)
    uc_show_decode_tree(printer, yaml_buf, decoder_width)


def main():
    cli()

if __name__ == "__main__":
    main()
