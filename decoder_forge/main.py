import click
import logging
import sys

from typing import Optional
from decoder_forge.uc_show_decode_tree import uc_show_decode_tree
from decoder_forge.template_engine import TemplateEngine
from decoder_forge.uc_generate_code import uc_generate_code
from decoder_forge.uc_decode import uc_decode
from contextlib import contextmanager


logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", count=True)
@click.pass_context
def cli(ctx, verbose):
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    # Warnings report real defects in the input format (an operand whose type cannot be
    # determined, for instance), so they are shown without asking for -v.
    level = logging.WARNING
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
        output_file (Optional[str]): Path to the output file. If None, sys.stdout is
        used.

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


def read_text(path: str) -> str:
    """Read and return the full UTF-8 contents of ``path``."""

    with open(path, "r", encoding="utf-8") as fp:
        return fp.read()


@cli.command()
@click.argument("DECODER_PATH", type=str)
@click.argument("INSTR_HEX", type=str)
@click.option(
    "--size",
    help="Width of the instruction word, in bits. The decoder does not determine it; "
    + "an encoding is only matched by the decoder for its own size.",
    required=True,
    type=click.Choice(["8", "16", "32"]),
)
@click.option(
    "--out_file",
    help="Output file to write the decoded instruction. Defaults to None, which "
    + "outputs to stdout.",
    default=None,
    type=str,
)
@click.option(
    "--no_format",
    help="Disable auto-formatting of the generated code with ruff (default: format).",
    is_flag=True,
    default=False,
)
@click.pass_context
def decode(
    self,
    decoder_path: str,
    instr_hex: str,
    size: str,
    out_file: Optional[str],
    no_format: bool,
):
    """Decode one instruction word with a decoder generated from YAML patterns.

    DECODER_PATH: The file path to the YAML file containing instruction definitions.

    INSTR_HEX: The instruction word as hexadecimal, written most-significant bit first
    the way an architecture manual spells the encoding -- not the byte order a
    little-endian image stores it in.

    Example:
        $ python cli.py decode armv7-m.yaml f000f814 --size 32
    """

    yaml_buf = read_text(decoder_path)

    tengine = TemplateEngine()
    with open_output_stream(out_file) as f:
        try:
            uc_decode(
                f,
                tengine,
                yaml_buf,
                instr_hex,
                int(size),
                auto_format=not no_format,
            )
        except ValueError as e:
            raise click.BadParameter(str(e))


@cli.command()
@click.argument("INPUT_PATH", type=str)
@click.option(
    "--out_file",
    help="Output file to write the generated code. Defaults to None, which outputs to "
    + "stdout.",
    default=None,
    type=str,
)
@click.option(
    "--no_format",
    help="Disable auto-formatting of the generated code with ruff (default: format).",
    is_flag=True,
    default=False,
)
@click.pass_context
def generate_code(self, input_path: str, out_file: Optional[str], no_format: bool):
    """Generate decoder code from YAML instruction patterns.

    This command reads a YAML file from the provided INPUT_PATH which should contain
    binary instruction definitions. It then generates decoder code using a template
    engine and prints the output either to stdout or an output file if provided.

    Args:
        input_path (str): The file path to the YAML file containing instruction
          definitions.
        output_file (Optional[str]): Optional file path to write the generated code.

    Raises:
        IOError: If reading the input file or writing to the output file fails.

    Example:
        $ python cli.py generate_code patterns.yaml --out_file decoder.py
    """

    yaml_buf = read_text(input_path)

    tengine = TemplateEngine()
    with open_output_stream(out_file) as f:
        uc_generate_code(f, tengine, yaml_buf, auto_format=not no_format)


@cli.command()
@click.argument("INPUT_PATH", type=str)
@click.pass_context
def show_tree(ctx, input_path: str):
    """
    Show the decode trees of an instruction set.

    This command reads a YAML file from the specified INPUT_PATH, which is expected to
    contain binary instruction definitions. It decodes these definitions to build one
    decode tree per instruction size and outputs them using a printer.

    INPUT_PATH: The file path to a YAML file containing pattern definitions.

    Example:
        $ python cli.py show_tree instructions.yaml
    """

    yaml_buf = read_text(input_path)

    uc_show_decode_tree(sys.stdout, yaml_buf)


def main():
    cli()


if __name__ == "__main__":
    main()
