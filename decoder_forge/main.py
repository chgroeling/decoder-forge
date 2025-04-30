import click
import logging
from decoder_forge.uc_show_decode_tree import uc_show_decode_tree
from decoder_forge.external.printer import Printer

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
@click.pass_context
def show_tree(ctx):
    """ shows the decode tree of an instruction set.

    The instruction set is given by a file in json format.
    """
    printer = Printer()
    uc_show_decode_tree(printer, None)


def main():
    cli()
