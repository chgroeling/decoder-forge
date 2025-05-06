def create_bit_mask(width: int) -> int:
    """
    Create a bitmask with a specified number of bits set to 1.

    This function constructs a bitmask by shifting 1 left by the provided
    width and then subtracting 1, which results in a number where the lowest
    'width' bits are set to 1. For example, if width is 3, the bitmask will be 0b111
    (7 in decimal).

    Args:
        width (int): The number of bits in the mask. Must be a non-negative integer.

    Returns:
        int: An integer representing the bitmask with 'width' bits set to 1.

    Raises:
        ValueError: If width is a negative number.

    Examples:
        >>> create_bitmask(3)
        7
        >>> bin(create_bitmask(3))
        '0b111'
    """

    if width < 0:
        raise ValueError("Width must be non-negativ")

    mask = (1 << width) - 1
    return mask
