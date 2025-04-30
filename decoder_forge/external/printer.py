from decoder_forge.i_printer import IPrinter


class Printer(IPrinter):
    def print(self, out: str):
        print(out)
