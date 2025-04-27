def is_undef_bit(ch: str):
    return ch in ("o", "O")


def is_wildcard_bit(ch: str):
    # undef bits are also wildcards
    return ch in ("x", "X", ".") or is_undef_bit(ch)


class Pattern:
    """
    A class representing a bit pattern with fixed and wildcard (don't care) bits.

    The pattern is defined by:
      - fixedmask: a bitmask where each bit set to 1 indicates that the corresponding bit in the pattern is fixed.
      - fixedbits: a number that gives the fixed bits' values in positions indicated by fixedmask.
      - bit_length: the total number of bits in the pattern.

    The class provides utilities to parse a string representation of a bit pattern and to convert the pattern
    back into a string form.
    """

    def __init__(self, fixedmask: int = 0x0, fixedbits: int = 0x0, bit_length: int = 1):
        """
        Initialize a Pattern instance.

        Parameters:
            fixedmask (int): A bitmask indicating which bits are fixed (1) and which are wildcards (0).
            fixedbits (int): The fixed bit values corresponding to the fixedmask.
            bit_length (int): The total length of the bit pattern.

        Raises:
            AssertionError: If the parameters do not meet the required type, value conditions, or size constraints.
            Specifically, if fixedmask or fixedbits cannot be represented within the bit_length.
        """

        assert isinstance(fixedmask, int)
        assert fixedmask >= 0
        assert isinstance(fixedbits, int)
        assert fixedbits >= 0
        assert isinstance(bit_length, int)
        assert bit_length > 0

        # Check if the numbers can be represented
        assert fixedmask.bit_length() <= bit_length
        assert fixedbits.bit_length() <= bit_length

        self.fixedmask = fixedmask
        self.fixedbits = fixedbits
        self.bit_length = bit_length

    @staticmethod
    def parse_pattern(pat_str: str) -> "Pattern":
        """
        Parse a string representation of a bit pattern and return a corresponding Pattern object.

        The input string should contain characters representing bits:
          - '0' or '1' indicate fixed bits.
          - 'x', 'X', '.', 'o', or 'O' represent wildcard/undefined bits.

        Parameters:
            pat_str (str): The string representation of the bit pattern.

        Returns:
            Pattern: A Pattern object containing the fixedmask, fixedbits, and bit length derived from the input.

        Raises:
            ValueError: If the input string is empty.

        Example:
            >>> Pattern.parse_pattern("10x1")
            Pattern(fixedmask=0xD, fixedbits=0x9, width=4)
        """

        assert isinstance(pat_str, str)
        width = len(pat_str)
        if width == 0:
            raise ValueError("No empty string allowed")

        # 1 if the bit is 0 or 1. 0 if wildcard
        def pat_to_fixedmask(i):
            return "0" if is_wildcard_bit(i) else "1"

        # 1 if the bit is 1, 0 if the bit is 0. 0 if wildcard
        def pat_to_fixedbits(i):
            return "0" if is_wildcard_bit(i) else i

        fixedmask_str = "".join(pat_to_fixedmask(i) for i in pat_str)
        fixedbits_str = "".join(pat_to_fixedbits(i) for i in pat_str)

        pat = Pattern(
            fixedmask=int(fixedmask_str, 2),
            fixedbits=int(fixedbits_str, 2),
            bit_length=width,
        )
        return pat

    @staticmethod
    def to_string(pat: "Pattern") -> str:
        """
        Convert the given Pattern object to its string representation.

        This method creates a binary string representation where for each bit:
          - If the corresponding bit in fixedmask is 0, the bit is represented by 'x' (denoting a wildcard).
          - If the bit is fixed (mask bit is 1), the corresponding bit from fixedbits is used.

        Parameters:
            pat (Pattern): The Pattern object to be converted into a string.

        Returns:
            str: The string representation of the bit pattern.

        Example:
            >>> p = Pattern(6, 2, 3)  # Represents pattern "01x"
            >>> Pattern.to_string(p)
            '01x'
        """

        assert isinstance(pat, Pattern)

        # represent number as binary with self.width digits
        format_str = f"{{:0{pat.bit_length}b}}"

        fixedmask_str = format_str.format(pat.fixedmask)
        fixedbits_str = format_str.format(pat.fixedbits)

        # Every 0 in the mask is X (dont care). It will be not evalutated
        pattern_str = [
            "x" if fm == "0" else fb for (fm, fb) in zip(fixedmask_str, fixedbits_str)
        ]

        return "".join(pattern_str)

    def __str__(self) -> str:
        return Pattern.to_string(self)

    def __repr__(self) -> str:
        return (
            "Pattern("
            + f"fixedmask=0x{self.fixedmask:x}, "
            + f"fixedbits=0x{self.fixedbits:x}, "
            + f"width={self.bit_length}"
            + ")"
        )
