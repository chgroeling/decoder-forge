def is_undef_bit(ch: str):
    return ch in ("o", "O")


def is_wildcard_bit(ch: str):
    # undef bits are also wildcards
    return ch in ("x", "X", ".") or is_undef_bit(ch)


class Pattern:

    def __init__(self, fixedmask: int = 0x0, fixedbits: int = 0x0, bit_length: int = 1):
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
