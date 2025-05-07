import copy


def is_undef_bit(ch: str):
    return ch in ("o", "O")


def is_wildcard_bit(ch: str):
    # undef bits are also wildcards
    return ch in ("x", "X", ".") or is_undef_bit(ch)


class BitPattern:
    """
    A class representing a bit pattern with fixed and wildcard (don't care) bits.

    The pattern is defined by:

    - fixedmask: a bitmask where each bit set to 1 indicates that the corresponding
      bit in the pattern is fixed.
    - fixedbits: a number that gives the fixed bits' values in positions indicated
      by fixedmask.
    - bit_length: the total number of bits in the pattern.

    The class provides utilities to parse a string representation of a bit pattern,
    convert the pattern back into a string, combine two patterns, and separate the
    pattern based on a given mask.
    """

    def __init__(self, fixedmask: int = 0x0, fixedbits: int = 0x0, bit_length: int = 1):
        """
        Initialize a BitPattern instance.

        Parameters:
            fixedmask (int): A bitmask indicating which bits are fixed (1) and which
              are wildcards (0).
            fixedbits (int): The fixed bit values corresponding to the fixedmask.
            bit_length (int): The total length of the bit pattern.

        Raises:
            AssertionError: If the parameters do not meet the required type, value
              conditions, or size constraints. Specifically, if fixedmask
              or fixedbits cannot be represented within the bit_length.
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

        # Set all bits to zero which are not part of mask
        self.fixedbits = fixedbits & self.fixedmask
        self.bit_length = bit_length

    @staticmethod
    def parse_pattern(pat_str: str) -> "BitPattern":
        """
        Parse a string representation of a bit pattern and return a corresponding
        BitPattern object.

        The input string should contain characters representing bits:

        - '0' or '1' indicate fixed bits.
        - 'x', 'X', '.', 'o', or 'O' represent wildcard/undefined bits.

        Parameters:
            pat_str (str): The string representation of the bit pattern.

        Returns:
            BitPattern: A BitPattern object containing the fixedmask, fixedbits, and bit
                     length derived from the input.

        Raises:
            ValueError: If the input string is empty.

        Example:
            >>> BitPattern.parse_pattern("10x1")
            BitPattern(fixedmask=0xD, fixedbits=0x9, bit_length=4)
        """

        assert isinstance(pat_str, str)
        bit_length = len(pat_str)
        if bit_length == 0:
            raise ValueError("No empty string allowed")

        # 1 if the bit is 0 or 1. 0 if wildcard
        def pat_to_fixedmask(i):
            return "0" if is_wildcard_bit(i) else "1"

        # 1 if the bit is 1, 0 if the bit is 0. 0 if wildcard
        def pat_to_fixedbits(i):
            return "0" if is_wildcard_bit(i) else i

        fixedmask_str = "".join(pat_to_fixedmask(i) for i in pat_str)
        fixedbits_str = "".join(pat_to_fixedbits(i) for i in pat_str)

        pat = BitPattern(
            fixedmask=int(fixedmask_str, 2),
            fixedbits=int(fixedbits_str, 2),
            bit_length=bit_length,
        )
        return pat

    @staticmethod
    def to_string(pat: "BitPattern") -> str:
        """
        Convert the given BitPattern object to its string representation.

        This method creates a binary string representation where for each bit:

        - If the corresponding bit in fixedmask is 0, the bit is represented by 'x'
          (denoting a wildcard).
        - If the bit is fixed (mask bit is 1), the corresponding bit from fixedbits is
          used.

        Parameters:
            pat (BitPattern): The BitPattern object to be converted into a string.

        Returns:
            str: The string representation of the bit pattern.

        Example:
            >>> p = BitPattern(6, 2, 3)  # Represents pattern "01x"
            >>> BitPattern.to_string(p)
            '01x'
        """

        assert isinstance(pat, BitPattern)

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
        return BitPattern.to_string(self)

    def __repr__(self) -> str:
        return (
            "BitPattern("
            + f"fixedmask=0x{self.fixedmask:x}, "
            + f"fixedbits=0x{self.fixedbits:x}, "
            + f"bit_length={self.bit_length}"
            + ")"
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            if other.fixedmask != self.fixedmask:
                return False

            if other.fixedbits != self.fixedbits:
                return False

            if other.bit_length != self.bit_length:
                return False

            return True
        else:
            return False

    def __hash__(self):
        return hash((self.fixedmask, self.fixedbits, self.bit_length))

    def combine(self, other: "BitPattern") -> "BitPattern":
        """
        Combine this BitPattern with another, creating a new BitPattern that represents
        the union of the fixed bits of both patterns.

        The resulting BitPattern's fixedmask is the bitwise OR of the fixedmasks, and
        its fixedbits is the bitwise OR of the fixedbits of both patterns. The method
        ensures that for each of the original patterns, their fixed bits remain
        unchanged within the combined pattern.

        Parameters:
            other (BitPattern): The BitPattern to combine with.

        Returns:
            BitPattern: A new BitPattern representing the combination of the two
            patterns.

        Raises:
            ValueError: If the fixedbits of either original BitPattern are modified
                during the combination.

        Example:
            >>> p1 = BitPattern.parse_pattern("10x1")
            >>> p2 = BitPattern.parse_pattern("x1x0")
            >>> p_combined = p1.combine(p2)
        """

        new_fixedmask = self.fixedmask | other.fixedmask
        new_fixedbits = self.fixedbits | other.fixedbits

        if self.bit_length != other.bit_length:
            raise ValueError("BitPatterns must match in length")

        if new_fixedbits & self.fixedmask != self.fixedbits:
            raise ValueError("Conflicting patterns should be combined")

        if new_fixedbits & other.fixedmask != other.fixedbits:
            raise ValueError("Conflicting patterns should be combined")

        return BitPattern(
            fixedmask=new_fixedmask,
            fixedbits=new_fixedbits,
            bit_length=self.bit_length,
        )

    def split_by_mask(self, mask: int) -> tuple["BitPattern", "BitPattern"]:
        """
        Splits the current BitPattern into two based on the given mask.

        The given mask must be fully contained within the fixedmask of this pattern.
        The function returns a tuple of two BitPattern objects:

        - The first BitPattern (pat_1) corresponds to the bits selected by the mask.
        - The second BitPattern (pat_2) corresponds to the remaining bits not selected
          by the mask.

        Parameters:
            mask (int): An integer mask indicating which bits to separate.

        Returns:
            (BitPattern, BitPattern): A tuple containing the separated BitPattern
            objects.

        Raises:
            ValueError: If the provided mask is not fully contained within the fixedmask
                        of this BitPattern.

        Example:
            >>> orig = BitPattern(0b111, 0b101, 3)
            >>> pat_a, pat_b = orig.separate(0b101)
            >>> pat_a
            BitPattern(fixedmask=0x5, fixedbits=0x5, bit_length=3)
            >>> pat_b
            BitPattern(fixedmask=0x2, fixedbits=0x0, bit_length=3)
        """

        # check if mask is contained in this pattern
        if (self.fixedmask | mask) != self.fixedmask:
            raise ValueError(
                "The provided mask is not fully contained within the "
                + "BitPattern's fixedmask"
            )

        pat_1 = BitPattern(
            fixedmask=mask,
            fixedbits=self.fixedbits & mask,
            bit_length=self.bit_length,
        )

        pat_2 = BitPattern(
            fixedmask=self.fixedmask & ~mask,
            fixedbits=self.fixedbits & ~mask,
            bit_length=self.bit_length,
        )

        return pat_1, pat_2

    def extend_and_shift_to_msb(self, bit_length: int) -> "BitPattern":
        """
        Extend the BitPattern to a new higher bit length and shift it so that the
        original bits occupy the most significant positions of the new representation.

        This method increases the total number of bits in the pattern by shifting both
        the fixedmask and fixedbits to the left. The effect is that the original pattern
        is "extended" and its bits are aligned to the upper (more significant) bits of
        the new bit length. If the provided bit_length equals the current bit_length,
        a copy of the current BitPattern is returned.

        Args:
           bit_length (int): The desired total bit length for the extended and shifted
             BitPattern.

        Returns:
          BitPattern: A new BitPattern instance with the pattern extended and aligned to
          the specified bit_length.

        Raises:
          ValueError: If the provided bit_length is smaller than the current bit_length.

        Example:
          >>> bp = BitPattern.parse_pattern("101x")
          >>> extended_bp = bp.extend_and_shift_to_msb(8)
          >>> print(extended_bp)
          101xxxxx
        """

        if bit_length < self.bit_length:
            raise ValueError("BitPattern bit length is to big")

        if bit_length == self.bit_length:  # exact representation
            return copy.copy(self)

        fixedmask = self.fixedmask << (bit_length - self.bit_length)
        fixedbits = self.fixedbits << (bit_length - self.bit_length)

        return BitPattern(
            fixedmask=fixedmask,
            fixedbits=fixedbits,
            bit_length=bit_length,
        )
