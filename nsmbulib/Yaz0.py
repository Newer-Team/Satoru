
from . import _common
from . import _Yaz0_py
from . import _Yaz0_win


_Yaz0Implementations = [_Yaz0_win, _Yaz0_py]


def isCompressed(data):
    """
    Return True if data appears to be Yaz0-compressed.
    """
    return (data.startswith(b'Yaz0')
        and data[8:15] == b'\0' * 7
        and len(data) >= 16)


def decompress(data):
    """
    Decompress Yaz0-compressed data.
    """
    return _common.dispatchTo(_Yaz0Implementations, 'decompress', 'decompress', data)


def compress(data, compressionLevel=3):
    """
    Yaz0-compress data. compressionLevel is an int in [0, 9], with 0
    being no compression and 9 being compressed as much as possible.
    """
    return _common.dispatchTo(
        _Yaz0Implementations, 'compress', 'compress', data, compressionLevel)

