
import io
import math
import struct

from . import _common



def decompress(data):
    """
    Decompress the Yaz0-compressed data.
    """
    if len(data) < 8 or data[:4] != b'Yaz0':
        raise ValueError('Data is not Yaz0-compressed!')
    decompressedSize, = struct.unpack_from('>I', data, 4)

    inputIO = io.BytesIO(data)
    inputIO.seek(16)

    outputIO = io.BytesIO(bytes(decompressedSize))

    while outputIO.tell() < decompressedSize:

        codeByte = inputIO.read(1)
        if not codeByte:
            raise RuntimeError('Unexpected EOF during decompression.')
        codeByte = codeByte[0]

        for bitVal in _common.byteBitIter(codeByte):

            if outputIO.tell() >= decompressedSize:
                break

            if bitVal:
                # Just read a byte and put it in the output.
                outputIO.write(inputIO.read(1))
            else:
                # The next two bytes tell us where to find the data to
                # copy and how much of it to copy.
                byte1 = inputIO.read(1)[0]
                byte2 = inputIO.read(1)[0]

                # Get the amount of data to copy
                byteCount = byte1 >> 4
                if byteCount == 0:
                    # We need to read a third byte which tells us how
                    # much data we have to read.
                    byteCount = inputIO.read(1)[0] + 0x12
                else:
                    byteCount += 2

                moveDistance = (((byte1 & 0xF) << 8) | byte2)

                currentPos = outputIO.tell()
                outputIO.seek(-moveDistance - 1, io.SEEK_CUR)
                toCopy = outputIO.read(byteCount)
                outputIO.seek(currentPos)

                if len(toCopy) < byteCount:
                    # Keep copying toCopy until it is byteCount bytes
                    # long
                    numCopies = byteCount // len(toCopy) + 1
                    toCopy = (toCopy * numCopies)[:byteCount]

                outputIO.write(toCopy)

    return outputIO.getvalue()


def compress(data, compressionLevel=3):
    if compressionLevel == 0:
        return _quickCompress(data)
    else:
        return _realCompress(data, compressionLevel)


def _quickCompress(indata):
    """
    Quickly "compress" this data. No actual compression is performed.
    """

    # Calculate the size of the output
    numBlocks = (len(indata) + 7) // 8
    compressedDataLen = len(indata) + numBlocks
    while compressedDataLen % 16: compressedDataLen += 1

    # Make a bytearray for that
    outdata = bytearray(16 + compressedDataLen)

    # Write header info
    outdata[:4] = b'Yaz0'
    outdata[4:8] = struct.pack('>I', len(indata))

    # Write each block
    i, j = 0, 16
    while i < len(indata):
        outdata[j : j+9] = b'\xFF' + indata[i : i+8]
        i += 8; j += 9

    return bytes(outdata)


def _realCompress(data, compressionLevel, padTo=16):
    """
    Perform actual Yaz0 compression on this data. The entire output file
    will be padded to multiples of `padTo`, which may improve
    compatibility in some situations.
    """

    # TODO:
    # - Use of the third byte to search for matches up to 256 bytes long

    # Create streams
    inputIO = io.BytesIO(data)
    outputIO = io.BytesIO()

    # Set up the header
    outputIO.write(b'Yaz0')
    outputIO.write(struct.pack('>I', len(data)))
    outputIO.write(b'\0' * 8)

    # These adjust the area in which the function will look for matches
    compressRatio = 0.1 * (compressionLevel + 1)
    maxSearch = 2**12 - 1
    adjustedSearch = int(maxSearch * compressRatio)
    adjustedMaxBytes = int(math.ceil(15 * compressRatio + 2))

    while inputIO.tell() < len(data):
        codeByte = 0
        thisBlock = bytearray()

        for bitNum in range(8):
            currentPos = inputIO.tell()

            # We are going to search for this many bytes to copy
            needleLen = min(adjustedMaxBytes, len(data) - currentPos)

            # Calculate a starting position and length for the search
            searchAreaStart = currentPos - adjustedSearch
            if searchAreaStart < 0:
                searchAreaStart = 0
                searchAreaLen = currentPos
            else:
                searchAreaLen = adjustedSearch

            # Here's the needle
            needle = inputIO.read(needleLen)

            # Here's the haystack
            inputIO.seek(searchAreaStart)
            haystack = inputIO.read(searchAreaLen)
            inputIO.seek(currentPos)

            # Search for this needle, and if it's not found, keep
            # shrinking the needle size until it hopefully is
            for actualNeedle in _iterNeedles(needle):
                needlePos = haystack.rfind(actualNeedle)
                if needlePos != -1:
                    # Found it!
                    relativePosition = searchAreaLen - needlePos - 1
                    byte1 = (len(actualNeedle) - 2) << 4 | relativePosition >> 8
                    byte2 = relativePosition & 0xFF
                    thisBlock.append(byte1); thisBlock.append(byte2)
                    inputIO.seek(len(actualNeedle), io.SEEK_CUR)
                    break
            else:
                # None of the needles were found. We'll have to just
                # do a single-byte copy.
                toCopy = inputIO.read(1)
                thisBlock.extend(toCopy)
                codeByte |= 128 >> bitNum

        # Now write the block to output.
        outputIO.write(bytes([codeByte]))
        outputIO.write(thisBlock)

    # Pad the output
    outputIO.write(b'\0' * (padTo - (outputIO.tell() % padTo)))

    # Return the whole thing
    output = outputIO.getvalue()
    assert len(output) % padTo == 0 # Should already be padded.
    return output


def _iterNeedles(needle):
    """
    Yield the needle and then continually yield copies of it with one
    byte shaved off of the right side. The last yield will be of length
    3 (because in Yaz0, using a back-reference for data of length < 3 is
    counterproductive).
    """
    while len(needle) >= 3:
        yield needle
        needle = needle[:-1]
