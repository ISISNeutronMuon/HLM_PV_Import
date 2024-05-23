import collections
import itertools
import numbers
import sys
import zlib


def ints_to_string(integers):
    if isinstance(integers, collections.Sequence):
        stripped = itertools.takewhile(lambda x: x != 0, integers)
        if sys.hexversion < 0x03000000:
            value = ''.join([chr(c) for c in stripped])
        else:
            value = bytes(stripped).decode()
    elif isinstance(integers, numbers.Integral):
        if integers == 0:
            value = ''
        elif sys.hexversion < 0x03000000:
            # noinspection PyTypeChecker
            value = chr(integers)
        else:
            # noinspection PyTypeChecker
            value = bytes([integers]).decode()
    else:
        value = None

    return value


def dehex_and_decompress(value):
    """
    Decompress and dehex PV value.

    Args:
        value: Value to translate.

    Returns:
        Dehexed value.

    """
    try:
        # If it comes as bytes then cast to string
        value = value.decode('utf-8')
    except AttributeError:
        pass

    return zlib.decompress(bytes.fromhex(value)).decode("utf-8")
