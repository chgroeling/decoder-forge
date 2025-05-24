import logging

import io
from decoder_forge.i_printer import IPrinter
from decoder_forge.i_template_engine import ITemplateEngine
from decoder_forge.generate_code import generate_code
from enum import IntFlag

logger = logging.getLogger(__name__)


class InstrFlags(IntFlag):
    I32BIT = 0b0001  # 1
    SET = 0b0010  # 2
    ADD = 0b0100  # 4
    CARRY = 0b1000  # 8


class StrPrinter(IPrinter):

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
    code_printer = StrPrinter()
    generate_code(input_yaml, decoder_width, tengine, code_printer)
    code = code_printer.to_string()
    compiled_code = compile(code, "", "exec")

    ns = {}
    exec(compiled_code, ns)

    ISF = InstrFlags
    Context = ns["Context"]
    decode = ns["decode"]

    def translate_flags(flags):
        return ISF(flags)

    context = Context()

    adr = 0
    i = 0
    with open(bin_file, "rb") as fp:
        fp.seek(0xD2)

        for i in range(0,10):
            raw_code = fp.read(4)
            #print(f"{adr} 0x{raw_code.hex()}")
            code = int.from_bytes(raw_code,'little')
            #print(f"{adr} {hex(code)}")
            out = decode(code, context=context)

            print(f"{adr} 0x{raw_code.hex()} {out}")
            
            if translate_flags(out.flags) & ISF.I32BIT:
                adr += 4
            else:
                adr += 2
                fp.seek(-2, 1)

