import struct


class InvalidSARCError(ValueError):
    """
    The SARC file is invalid.
    """


def load(data):
    """
    Convert a `bytes` object containing SARC archive data to a dict
    mapping filenames (strings -- directory names are included) to
    filedata (bytes). Raises InvalidSarcError if the data is not a valid
    SARC file.
    """

    # SARC Header ------------------------------------------------------

    # File magic (0x00 - 0x03)
    if not data.startswith(b'SARC'):
        raise InvalidSarcError('Incorrect SARC file magic '
            "(expected b'SARC', got %s)" % repr(data[:4]))

    # Come back to header length later, after we have endianness

    # Endianness/BOM (0x06 - 0x07)
    bom = data[0x06:0x08]
    endians = {b'\xFE\xFF': '>', b'\xFF\xFE': '<'}
    if bom not in endians:
        raise InvalidSarcError('Incorrect SARC BOM (got %s)' % repr(data[6:8]))
    endian = endians[bom]

    # Header length (0x04 - 0x05)
    headLen = struct.unpack(endian + 'H', data[0x04:0x06])[0]
    if headLen != 0x14:
        raise InvalidSarcError('Incorrect SARC header length '
            '(expected 0x14, got %s)' % hex(headLen))

    # File Length (0x08 - 0x0B)
    filelen = struct.unpack(endian + 'I', data[0x08:0x0C])[0]
    if len(data) != filelen:
        raise InvalidSarcError('Unexpected SARC file length '
            '(expected %s, got %s)' % (hex(len(data)), hex(filelen)))

    # Beginning Of Data offset (0x0C - 0x0F)
    begOfDat = struct.unpack(endian + 'I', data[0x0C:0x10])[0]

    # Unknown value (0x10 - 0x13)
    unkVal = struct.unpack(endian + 'I', data[0x10:0x14])[0]
    # This is always 0x10000000, but let's not check for that because we
    # ultimately don't know what this is.


    # SFAT Header ------------------------------------------------------

    # Sanity check (0x14 - 0x17)
    if data[0x14:0x18] != b'SFAT':
        raise InvalidSarcError('Incorrect SFAT magic '
            '(expected b\'SFAT\', got %s)' % repr(data[0x14:0x18]))

    # Header length (0x18 - 0x19)
    headLen = struct.unpack(endian + 'H', data[0x18:0x1A])[0]
    if headLen != 0x0C:
        raise InvalidSarcError('Unexpected SFAT header length '
            '(expected 0x0C, got %s)' % hex(headLen))

    # Node count (0x1A - 0x1B)
    nodeCount = struct.unpack(endian + 'H', data[0x1A:0x1C])[0]

    # Hash multiplier (0x1C - 0x1F)
    hashMultiplier = struct.unpack(endian + 'I', data[0x1C:0x20])[0]


    # SFAT Nodes (0x20 - 0x20+(0x10*nodeCount))
    SFATNodes = []

    SFATNodeOffset = 0x20
    for nodeNum in range(nodeCount):

        # SFAT Node ID: we don't really use this for anything.
        nodeID = struct.unpack(endian + 'I',
            data[SFATNodeOffset:SFATNodeOffset + 4])[0]

        if endian == '>':
            unkFlagOffset = SFATNodeOffset + 4
            fileNameTableEntryOffsetOffset = SFATNodeOffset + 5
        else:
            unkFlagOffset = SFATNodeOffset + 7
            fileNameTableEntryOffsetOffset = SFATNodeOffset + 4

        # Unknown flag: Could function as a file/folder flag.
        unkFlag = data[unkFlagOffset]

        # File Name Table Entry offset
        if endian == '>':
            fileNameTableEntryOffsetData = (b'\x00' +
                data[fileNameTableEntryOffsetOffset :
                    fileNameTableEntryOffsetOffset+3])
        else:
            fileNameTableEntryOffsetData = \
                data[fileNameTableEntryOffsetOffset :
                    fileNameTableEntryOffsetOffset+3] + b'\x00'
        fileNameTableEntryOffset = struct.unpack(
            endian + 'I',
            fileNameTableEntryOffsetData)[0]

        # Beginning of Node File Data
        fileDataStart = struct.unpack(
            endian + 'I', data[SFATNodeOffset + 8:SFATNodeOffset + 0x0C])[0]

        # End of Node File Data
        fileDataEnd = struct.unpack(
            endian + 'I', data[SFATNodeOffset + 0x0C:SFATNodeOffset + 0x10])[0]

        # Calculate file data length
        fileDataLength = fileDataEnd - fileDataStart

        # Add an entry to the node list
        SFATNodes.append(
            (unkFlag, fileNameTableEntryOffset, fileDataStart, fileDataLength))

        # Increment the offset counter
        SFATNodeOffset += 0x10


    # SFNT Header ------------------------------------------------------

    # From now on we need to keep track of an offset variable
    offset = 0x20 + (0x10 * nodeCount)

    # Sanity check (offset - offset+0x03)
    if data[offset:offset + 0x04] != b'SFNT':
        raise InvalidSarcError('Incorrect SFNT magic '
            '(expected b\'SFNT\', got %s)' % repr(data[offset:offset + 4]))

    # Header length (offset+0x04 - offset+0x05)
    headLen = struct.unpack(endian + 'H', data[offset + 0x04:offset + 0x06])[0]
    if headLen != 0x08:
        raise InvalidSarcError('Unexpected SFNT header length '
            '(expected 0x08, got %s)' % hex(headLen))

    # Unknown value (offset+0x06 - offset+0x07)
    unkVal = struct.unpack(endian + 'H', data[offset + 0x06:offset + 0x08])[0]
    # This is always 0x0000, but let's not check for that
    # because we ultimately don't know what this is.

    # Increment the offset
    offset += 0x08


    # Add the files to the contents dict -------------------------------
    contents = {}
    for unkFlag, fileNameTableEntryOffset, fileDataStart, fileDataLength \
            in SFATNodes:

        # Get the file name (search for the first null byte manually)
        nameOffset = offset + (fileNameTableEntryOffset * 4)
        nameLen = 0
        while True:
            if data[nameOffset + nameLen] > 0:
                nameLen += 1
            else:
                break
        name = data[nameOffset:nameOffset + nameLen].decode('utf-8')

        # Get the file data
        fileData = data[begOfDat + fileDataStart :
            begOfDat + fileDataStart + fileDataLength]

        # Add it to contents
        contents[name] = fileData

    # And finally, return contents
    return contents


def save(contents, padding=4, *,
         endianness = '>', minDataStart=None, hashMultiplier=0x65):
    """
    dict -> sarc
    """
    if minDataStart is None: minDataStart = padding

    for path, data in contents.items():
        if not (isinstance(data, bytes) or isinstance(data, bytearray)):
            raise ValueError('File contents must be bytes or bytearray')


    # Sort the files
    contents = sorted(
        contents.items(),
        key=lambda filetuple:
            struct.unpack(
                endianness + 'I',
                _sfatFilenameHash(filetuple[0], hashMultiplier),
                ),
        )

    # Create the File Names table
    fileNamesTableOffsets = {}
    fileNamesTable = b''
    for i, (path, data) in enumerate(contents):

        # Add the name offset, this will be used later
        fileNamesTableOffsets[path] = len(fileNamesTable)

        # Add the name to the table
        fileNamesTable += path.encode('utf-8')

        # Pad to 4 bytes
        fileNamesTable += b'\0' * (4 - (len(fileNamesTable) % 4))

    # Determine the length of the SFAT Nodes table
    SFATNodesTableLen = 0x10 * len(contents)

    # Determine the Beginning Of Data offset
    begOfDat = max(
        0x20 + SFATNodesTableLen + 0x08 + len(fileNamesTable), minDataStart)

    # Create the File Data table
    fileDataTableOffsets = {}
    fileDataTable = bytearray()
    for path, data in contents:

        # Pad it to 0x04, relative to file start (if we're not at the
        # very start)
        totalFileLen = len(fileDataTable) + begOfDat
        if totalFileLen % padding != 0:
            fileDataTable += b'\0' * (padding - (totalFileLen % padding))
        assert (begOfDat + len(fileDataTable)) % padding == 0

        # Add the data offset, this will be used later
        fileDataTableOffsets[path] = len(fileDataTable)

        # Add the data to the table
        fileDataTable.extend(data)

    # Calculate total file length
    totalFileLen = begOfDat + len(fileDataTable)


    # SARC Header ------------------------------------------------------

    # File magic
    sarcHead = b'SARC'

    # Header length (always 0x14)
    sarcHead += struct.pack(endianness + 'H', 0x14)

    # BOM
    sarcHead += b'\xFE\xFF' if endianness == '>' else b'\xFF\xFE'

    # File Length
    sarcHead += struct.pack(endianness + 'I', totalFileLen)

    # Beginning Of Data offset
    sarcHead += struct.pack(endianness + 'I', begOfDat)

    # Unknown value
    if endianness == '>':
        sarcHead += b'\1\0\0\0'
    else:
        sarcHead += b'\0\1\0\0'


    # SFAT Header ------------------------------------------------------

    # File magic
    sfatHead = b'SFAT'

    # Header length (always 0x0C)
    sfatHead += struct.pack(endianness + 'H', 0x0C)

    # Number of files
    sfatHead += struct.pack(endianness + 'H', len(contents))

    # Hash multiplier
    sfatHead += struct.pack(endianness + 'I', hashMultiplier)

    # SFAT Nodes
    sfat = b''
    for path, data in contents:
        filenameoffset = fileNamesTableOffsets[path]
        filedataoffset = fileDataTableOffsets[path]

        # File ID
        sfat += _sfatFilenameHash(path, hashMultiplier)
        # Filename Offset (4 bytes + a constant?)
        sfat += struct.pack(endianness + 'I',
                            (filenameoffset // 4) | 0x1000000)
        # Filedata Offset
        sfat += struct.pack(endianness + 'I', filedataoffset)
        # Filedata Length + Filedata Offset
        sfat += struct.pack(endianness + 'I', filedataoffset + len(data))


    # SFNT Header ------------------------------------------------------

    # File magic
    sfntHead = b'SFNT'

    # Header length (always 0x08)
    if endianness == '>': sfntHead += b'\0\x08'
    else: sfntHead += b'\x08\0'

    # 2-byte padding
    sfntHead += b'\0\0'


    # Put it All Together ----------------------------------------------

    sarcData = sarcHead + sfatHead + sfat + sfntHead + fileNamesTable

    # File Data Table padding
    headerSize = len(sarcData)
    if begOfDat > headerSize:
        sarcData += b'\0' * (begOfDat - headerSize)

    sarcData += fileDataTable

    # Return the data
    return sarcData



def _sfatFilenameHash(filename, multiplier):
    """
    Return the hash that should be used by an SFAT node.
    """
    result = 0

    for char in filename:
        result = (result * multiplier + ord(char)) & 0xFFFFFFFF

    return struct.pack('>I', result)
