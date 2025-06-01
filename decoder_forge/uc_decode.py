import logging

import io
from decoder_forge.i_printer import IPrinter
from decoder_forge.i_template_engine import ITemplateEngine
from decoder_forge.generate_code import generate_code
from math import ceil
from typing import Callable

logger = logging.getLogger(__name__)


class CodePrinter(IPrinter):
    def __init__(self):
        self._file_object = io.StringIO()

    def to_string(self):
        self._file_object.seek(0)
        return self._file_object.read()

    def print(self, out: str):
        self._file_object.write(out)
        self._file_object.write("\n")


def uc_decode(
    printer: IPrinter,
    tengine: ITemplateEngine,
    input_yaml: str,
    decoder_width: int,
    bin_file: str,
):
    logger.info("Call: uc_decode")
    code_printer = CodePrinter()
    generate_code(input_yaml, decoder_width, tengine, code_printer)
    code = code_printer.to_string()
    compiled_code = compile(code, "", "exec")

    ns: dict[str, Callable] = {}

    exec(compiled_code, ns)

    Context = ns["Context"]
    decode = ns["decode"]
    decode_size = ns["decode_size"]

    context = Context()

    size_bytes = ns["get_size_eval_bytes"]()
    decoder_bytes = ns["get_decoder_eval_bytes"]()

    adr = 0xD4
    with open(bin_file, "rb") as fp:

        fp.seek(adr)

        for i in range(0, 50):
            # read enough data to estimate the size of the following code
            raw_size_code = fp.read(size_bytes)

            if len(raw_size_code) < size_bytes:
                break

            # read the part of the code which is necessary to estimate its size
            data_for_size_eval = int.from_bytes(raw_size_code, "little")

            # calculate size of the following code
            act_instr_size = int(ceil(decode_size(data_for_size_eval) / 8))

            to_shift = decoder_bytes - act_instr_size

            # read the code
            if to_shift > 0:
                short_instr = data_for_size_eval
                instr = short_instr << (to_shift * 8)
                print(f"{hex(adr):8} {hex(short_instr):10} ", end="")
                adr += 2
            else:
                missing_bytes = decoder_bytes - size_bytes
                instr = data_for_size_eval << (missing_bytes * 8)
                instr |= int.from_bytes(fp.read(missing_bytes), "little")
                print(f"{hex(adr):8} {hex(instr):10} ", end="")
                adr += 4

            # decode
            out = decode(instr, context=context)
            print(out)
