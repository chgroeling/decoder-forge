import logging

from decoder_forge.decoder_cache import load_decoder_source
from decoder_forge.template_engine import ITemplateEngine
from typing import Callable

logger = logging.getLogger(__name__)


def uc_decode(
    printer,
    tengine: ITemplateEngine,
    input_yaml: str,
    instr_hex: str,
    size: int,
    auto_format: bool = True,
    use_cache: bool = True,
):
    """Generate a decoder from ``input_yaml`` and decode a single instruction word.

    ``instr_hex`` is the instruction word written most-significant bit first, the way
    an encoding is spelled in an architecture manual -- ``f000f814`` for a 32-bit Thumb
    ``BL``, not the ``00f014f8`` those bytes are stored as in a little-endian image.

    Args:
        printer: Writable stream with a ``write(str)`` method.
        tengine (ITemplateEngine): Template engine used to generate the decoder.
        input_yaml (str): A YAML string with an ``instructions`` list.
        instr_hex (str): The instruction word as hexadecimal, MSB first.
        size (int): The instruction size to decode the word as, in bits.
        auto_format (bool): Whether to run ``ruff format`` on the generated code
            (default ``True``).
        use_cache (bool): Whether to reuse a previously generated decoder for this
            instruction set (default ``True``).

    Raises:
        ValueError: If ``instr_hex`` is not hexadecimal, does not fit in ``size`` bits,
            or if the instruction set has no encodings of that size.
    """

    logger.info("Call: uc_decode")
    # Decoding one word is dominated by building the decoder, which does not depend on
    # the word; a cached decoder is reused whenever the format and generator are
    # unchanged.
    code = load_decoder_source(
        input_yaml, tengine, auto_format=auto_format, use_cache=use_cache
    )
    compiled_code = compile(code, "", "exec")

    ns: dict[str, Callable] = {}

    exec(compiled_code, ns)

    Context = ns["Context"]
    InstructionSize = ns["InstructionSize"]
    decode = ns["decode"]

    try:
        instr = int(instr_hex, 16)
    except ValueError:
        raise ValueError(f"{instr_hex!r} is not a hexadecimal instruction word")
    if instr < 0:
        raise ValueError("The instruction word must not be negative")

    supported = ns["get_supported_sizes"]()
    if size not in supported:
        sizes = ", ".join(str(int(i)) for i in supported) or "none"
        raise ValueError(
            f"This instruction set has no {size}-bit encodings (it has: {sizes})"
        )

    # The word is decoded as exactly ``size`` bits, so anything above them is not part
    # of the instruction -- silently masking it off would decode something the caller
    # did not write.
    if instr.bit_length() > size:
        raise ValueError(f"0x{instr:x} does not fit in {size} bits")

    out = decode(instr, ctx=Context(), size=InstructionSize(size))

    printer.write(f"0x{instr:0{size // 4}x} {out}\n")
