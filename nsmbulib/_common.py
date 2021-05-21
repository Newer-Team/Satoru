import contextlib
import enum
import itertools
import logging
import os
import os.path
import struct
import traceback


# Constants
TEMP_FILE_NAME = 'nsmbulibTempFile'
DEFAULT_IMAGE_COLOR = (0, 0, 0, 0)
DEFAULT_NORMAL_MAP_COLOR = (128, 127, 255, 255)
MAX_EMPTY_ALPHA = 2
MAX_CHANNEL_DELTA = 2



class SortableEnum(enum.Enum):
    """
    An Enum that can be sorted. The sorting order is the order in which
    the members were defined.
    """
    def __lt__(self, other):
        for member in type(self):
            if member is self:
                return True
            elif member is other:
                return False
        return True


def getDevNull():
    """
    Returns a handle to /dev/null/. (Cross-platform.)
    Please close the handle when you're done with it! (Even better: use
    this as a context manager.)
    """
    # http://stackoverflow.com/a/11269627/4718769
    return open(os.devnull, 'w')


def pairwise(iterable):
    """
    s -> (s0,s1), (s1,s2), (s2, s3), ...
    From https://docs.python.org/3/library/itertools.html
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    From https://docs.python.org/3/library/itertools.html
    """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def byteBitIter(byte):
    """
    Iterate over the bits of this byte, from most-significant to least-
    significant.
    """

    # We could do this in a loop, but this is slightly faster and no
    # less readable.
    yield (byte >> 7) & 1
    yield (byte >> 6) & 1
    yield (byte >> 5) & 1
    yield (byte >> 4) & 1
    yield (byte >> 3) & 1
    yield (byte >> 2) & 1
    yield (byte >> 1) & 1
    yield byte & 1


def dispatchTo(implementations, functionName, verb, *args, **kwargs):
    """
    Call implementation.functionName(*args, **kwargs) for each object in
    implementations until one of them doesn't raise an exception; return
    that one's return value. If all of the functions raise an exception,
    raise a RuntimeError complaining that we couldn't `verb` the data.
    (Hence, the `verb` argument is used solely for that error message.)
    """

    # Using logging here because this function can create hard-to-debug
    # situations sometimes
    logging.info('dispatchTo({}, {}, {}, *{}, **{}) called'.format(
        repr(implementations), repr(functionName), repr(verb),
        repr(args), repr(kwargs)))

    tracebacks = ''
    for implementation in implementations:
        try:
            logging.info('^ Attempting ' + repr(implementation))
            return getattr(implementation, functionName)(*args, **kwargs)
        except Exception:
            logging.info('^ Failed: ' + traceback.format_exc())
            tracebacks += (repr(implementation) + ':\n' +
                traceback.format_exc() + '\n')
    raise RuntimeError('All implementations failed to ' + verb + 'the '
        'data. All tracebacks:\n' + tracebacks)


@contextlib.contextmanager
def cwdAsPathTo(filepath):
    """
    A context manager that changes the current working directory to the
    directory containing the filepath given. The value bound to the
    target of the `as` clause is the full path to the new directory.
    """
    oldcwd = os.getcwd()
    newcwd = os.path.dirname(os.path.realpath(filepath))
    os.chdir(newcwd)
    yield newcwd
    os.chdir(oldcwd)


def imagesIdentical(first, second):
    """
    Compare these images to see if they're the same or not.
    """
    if first.size != second.size: return False

    if not first.mode == second.mode == 'RGBA':
        print("WARNING: These images aren't both in RGBA mode "
            "(first: %s; second: %s), so they can't be compared for equality!"
            % (first.mode, second.mode))
        return False

    firstBytes = first.tobytes()
    secondBytes = second.tobytes()

    for y in range(first.height):
        for x in range(first.width):
            idx = (y * first.width + x) * 4
            firstRgba = struct.unpack_from('>4B', firstBytes, idx)
            secondRgba = struct.unpack_from('>4B', secondBytes, idx)
            if firstRgba[3] < MAX_EMPTY_ALPHA and \
                    secondRgba[3] < MAX_EMPTY_ALPHA:
                # Both pixels are transparent
                continue
            for channelA, channelB in zip(firstRgba, secondRgba):
                if abs(channelA - channelB) > MAX_CHANNEL_DELTA:
                    return False
    return True


def halfToFloat(h):
    """
    Convert an int representing a half-precision float (16 bits) to its
    actual value.
    I've found this code in several places on the Internet
    independently.
    """
    s = int((h >> 15) & 0x00000001)  # sign
    e = int((h >> 10) & 0x0000001f)  # exponent
    f = int(h & 0x000003ff)          # fraction

    if e == 0:
       if f == 0:
          return int(s << 31)
       else:
          while not (f & 0x00000400):
             f <<= 1
             e -= 1
          e += 1
          f &= ~0x00000400
    elif e == 31:
       if f == 0:
          return int((s << 31) | 0x7f800000)
       else:
          return int((s << 31) | 0x7f800000 | (f << 13))

    e = e + (127 -15)
    f = f << 13

    return int((s << 31) | (e << 23) | f)


def loadNullTerminatedStringFrom(
        data, offset, charWidth=1, encoding='latin-1'):
    """
    Load a null-terminated string from data at offset, with the options
    given
    """
    end = data.find(b'\0' * charWidth, offset)
    return data[offset:end].decode(encoding)