import logging

import io
from decoder_forge.template_engine import ITemplateEngine
from decoder_forge.generate_code import generate_code
from typing import Callable

logger = logging.getLogger(__name__)


def uc_decode(
    printer,
    tengine: ITemplateEngine,
    input_yaml: str,
    decoder_width: int,
    bin_file: str,
    start_address: int = 0x0,
    auto_format: bool = True,
):
    """Generate a decoder from ``input_yaml`` and decode ``bin_file`` with it.

    Args:
        printer: Writable stream with a ``write(str)`` method.
        tengine (ITemplateEngine): Template engine used to generate the decoder.
        input_yaml (str): A YAML string with an ``instructions`` list.
        decoder_width (int): The bit width used when constructing the decode tree.
        bin_file (str): Path to the binary to decode.
        start_address (int): Offset into ``bin_file`` at which decoding starts.
        auto_format (bool): Whether to run ``ruff format`` on the generated code
            (default ``True``).
    """

    logger.info("Call: uc_decode")
    code_printer = io.StringIO()
    generate_code(
        input_yaml, decoder_width, tengine, code_printer, auto_format=auto_format
    )
    code = code_printer.getvalue()
    compiled_code = compile(code, "", "exec")

    ns: dict[str, Callable] = {}

    exec(compiled_code, ns)

    Context = ns["Context"]
    decode = ns["decode"]

    context = Context()

    # Maximum instruction width (bytes read per attempt) and the smallest instruction
    # width (read granularity / how few trailing bytes still form a decodable word).
    decoder_bytes = ns["get_decoder_eval_bytes"]()
    unit = ns["get_min_instr_bytes"]()

    adr = start_address
    with open(bin_file, "rb") as fp:

        while True:
            fp.seek(adr)
            raw = fp.read(decoder_bytes)
            if len(raw) < unit:
                break

            # Build the MSB-aligned instruction word from ``unit``-sized words (each
            # little-endian; the first word is the most significant, e.g. hw1<<16|hw2
            # for Thumb). A short tail is zero-padded so a trailing narrow instruction
            # still decodes.
            padded = raw.ljust(decoder_bytes, b"\x00")
            instr = 0
            for off in range(0, decoder_bytes, unit):
                instr = (instr << (unit * 8)) | int.from_bytes(
                    padded[off : off + unit], "little"
                )

            # ``decode`` reports how many bytes the matched instruction occupies; a
            # side effect yields a See/Undefined/Unpredictable pseudo-instruction and a
            # no-match a NoMatch.
            out, n_bytes = decode(instr, ctx=context)

            # Show only the bytes this instruction actually consumed, zero-padded to
            # its full width (4 hex digits for a 16-bit instruction, 8 for a 32-bit).
            consumed = instr >> ((decoder_bytes - n_bytes) * 8)
            consumed_hex = f"0x{consumed:0{n_bytes * 2}x}"
            print(f"{hex(adr):8} {consumed_hex:10} ", end="")
            print(out)

            adr += n_bytes
