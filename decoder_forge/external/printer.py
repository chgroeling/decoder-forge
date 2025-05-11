from decoder_forge.i_printer import IPrinter


class Printer(IPrinter):
    """
    A simple Printer implementation that writes output to a provided file-like object.

    This class implements the IPrinter interface and writes each output string followed
    by a newline to the specified file object.

    Example:
        >>> import sys
        >>> printer = Printer(sys.stdout)
        >>> printer.print("Hello, World!")
    """

    def __init__(self, file_object):
        self._file_object = file_object

    def print(self, out: str):
        self._file_object.write(out)
        self._file_object.write("\n")
