
import collections
import enum
import struct

from . import Shader



def load(data):
    """
    Load a sharcfb archive from raw data.
    """
    return Sharcfb._loadFromRawData(data)


class Sharcfb:
    """
    A class that represents a sharcfb binary shader archive.
    """
    unk04 = 8
    unk10 = 0

    programs = None


    @classmethod
    def _loadFromRawData(cls, data):
        sharcfb = cls()

        if data[:4] != b'BAHS' or len(data) < 0x18:
            raise ValueError('This is not correct sharcfb data.')

        # BAHS header
        (magic, sharcfb.unk04, fileLen, bom, sharcfb.unk10, filenameLen) = \
            struct.unpack_from('<4s5I', data, 0)
        filename = struct.unpack_from(
            '%ds' % (filenameLen - 1), data, 0x18)[0].decode('latin-1')
        progOffset, binCount = struct.unpack_from(
            '<II', data, 0x18 + filenameLen)
        offset = 0x20 + filenameLen

        # Shader binaries
        shaders = []
        for i in range(binCount):
            shaderLen, = struct.unpack_from('<I', data, offset)
            shaders.append(
                _loadShader(data[offset:offset+shaderLen]))
            offset += shaderLen

        # Shader programs (array header)
        offset = 0x18 + filenameLen + struct.unpack_from(
            '<I', data, 0x18 + filenameLen)[0]
        unkProg00, progCount = struct.unpack_from(
            '<II', data, offset)
        offset += 8

        # Shader programs (entries)
        programs = collections.OrderedDict()
        for i in range(progCount):
            progLen, = struct.unpack_from('<I', data, offset)
            progName, prog = ShaderProgram._loadFromRawData(
                data[offset:offset+progLen], shaders)
            programs[progName] = prog
            offset += progLen
        sharcfb.programs = programs

        return filename, sharcfb


    def save(self, filename):
        """
        Save the shader archive as binary data, with the filename given
        """
        bahsLen = 24 + len(filename) + 1 + 8

        # Shader data and program data
        shadersData = b''
        shadersCount = 0
        programsData = b''
        for progName, program in self.programs.items():
            programData, shaders = program.save(progName, shadersCount)

            # Handle shader stuff
            shadersCount += len(shaders)
            for shader in shaders:
                shadersData += _saveShader(shader, bahsLen + len(shadersData))

            # Handle program stuff
            programsData += programData

        # Programs header
        programsData = struct.pack(
            '<II', len(programsData) + 8, len(self.programs)) + programsData

        # BAHS header (file length and program offset will be spliced in
        # later)
        bahsHead = b''
        fnData = filename.encode('latin-1') + b'\0'
        fileLen = 0x18 + len(fnData) + 8 + len(shadersData) + len(programsData)
        bahsHead += struct.pack('<4s5I', b'BAHS', self.unk04, fileLen,
                                1, self.unk10, len(fnData))
        bahsHead += fnData
        bahsHead += struct.pack('<II', len(shadersData) + 8, shadersCount)

        return bahsHead + shadersData + programsData


def _loadShader(data):
    """
    Load a shader binary from raw data
    """
    shaderLen, shaderType, binOff, binLen = struct.unpack_from('<4I', data, 0)

    binDataStart = 0x10 + binOff
    shaderData = data[binDataStart : binDataStart + binLen]

    cls = {
        0: Shader.VertexShader,
        1: Shader.PixelShader,
        2: Shader.GeometryShader,
        }.get(shaderType)
    if cls is None:
        raise ValueError('%d is not a valid shader type' % shaderType)

    return cls.load(shaderData)


def _saveShader(shader, offset):
    """
    Save this shader back to binary data. offset should be the absolute
    offset at which the return value will be placed.
    """
    shaderData = shader.save(offset + 0x10)

    if isinstance(shader, Shader.VertexShader): typeValue = 0
    elif isinstance(shader, Shader.PixelShader): typeValue = 1
    elif isinstance(shader, Shader.GeometryShader): typeValue = 2
    else:
        typeValue = 0 # IDK what to do here.

    data = struct.pack('<4I', 0x10 + len(shaderData), typeValue, 0,
                       len(shaderData))
    data += shaderData

    return data


class ShaderProgram:
    """
    A class that represents a shader program.
    """
    variations = None
    symbolArray0 = None
    symbolArray1 = None
    symbolArray2 = None
    symbolArray3 = None
    symbolArray4 = None


    @classmethod
    def _loadFromRawData(cls, data, shaders):
        program = cls()

        # Program header
        progLen, progNameLen, shaderTypes, baseShaderIndex = \
            struct.unpack_from('<4I', data, 0)
        name = struct.unpack_from(
            '%ds' % (progNameLen - 1), data, 0x10)[0].decode('latin-1')
        symbArrsOff, variationCount = struct.unpack_from(
            '<II', data, 0x10 + progNameLen)

        # Variations
        program.variations = []
        if variationCount == 0:
            # This is a special case. We load a vertex shader and a
            # pixel shader, and that's all.
            var = ShaderProgramVariation()
            var.vertexShader = shaders[baseShaderIndex]
            var.pixelShader = shaders[baseShaderIndex + 1]
            program.variations.append(var)
        else:
            # Read each variation struct
            off = 0x10 + progNameLen + 8
            for i in range(variationCount):
                unk00, unkOffset, unk08 = struct.unpack_from(
                    '>3I', data, off)
                off += 0x0C
            # TODO: this is not really handled properly at all yet.

        # Symbol arrays
        offset_symbolArrs = 0x10 + progNameLen + symbArrsOff
        symbolArrays = []
        for i in range(5):
            symbArrLen, symbCount = struct.unpack_from(
                '<II', data, offset_symbolArrs)

            offset_symbol = offset_symbolArrs + 8
            symbols = collections.OrderedDict()
            for j in range(symbCount):
                symbLen, = struct.unpack_from('<I', data, offset_symbol)
                symbName, symb = ShaderProgramSymbol._loadFromRawData(
                    data[offset_symbol:offset_symbol+symbLen])
                symbols[symbName] = symb
                offset_symbol += symbLen

            symbolArrays.append(symbols)
            offset_symbolArrs += symbArrLen

        program.symbolArray0 = symbolArrays[0]
        program.symbolArray1 = symbolArrays[1]
        program.symbolArray2 = symbolArrays[2]
        program.symbolArray3 = symbolArrays[3]
        program.symbolArray4 = symbolArrays[4]

        return name, program


    def save(self, name, baseIndex):
        """
        Save the shader program as binary data, with the name given
        """
        # Shaders
        haveGeometryShaders = self.variations[0].geometryShader is not None
        shaders = []
        for var in self.variations:
            shaders.append(var.vertexShader)
            shaders.append(var.pixelShader)
            if haveGeometryShaders:
                shaders.append(var.geometryShader)

        # Symbol arrays
        symbolArrays = b''
        for symArr in (self.symbolArray0, self.symbolArray1, self.symbolArray2,
                self.symbolArray3, self.symbolArray4):

            symbolArray = b''
            for symName, symbol in symArr.items():
                symbolArray += symbol.save(symName)

            symbolArrayHead = struct.pack(
                '<II', len(symbolArray) + 8, len(symArr))
            symbolArrays += symbolArrayHead + symbolArray

        # Variations
        variationsData = b''
        saveVariations = len(self.variations) > 1 or haveGeometryShaders
        if saveVariations:
            # We have to actually save the variations :(
            # TODO: implement
            pass

        # Program header
        header = b''
        fnData = name.encode('latin-1') + b'\0'
        programLen = 0x10 + len(fnData) + 0x8 + len(symbolArrays)
        shaderTypesBitfield = 7 if haveGeometryShaders else 3
        header += struct.pack('<4I', programLen, len(fnData),
                              shaderTypesBitfield, baseIndex)
        header += fnData
        header += struct.pack('<II', 8 + len(variationsData),
                              len(self.variations) if saveVariations else 0)

        return header + variationsData + symbolArrays, shaders


class ShaderProgramSymbol:
    """
    A class that represents a symbol in a shader program.
    """
    unk04 = -1
    unk0C = 1
    unk10 = 0
    unk14 = 1
    unkEnd = 256


    @classmethod
    def _loadFromRawData(cls, data):

        symbol = cls()

        (symbLen, symbol.unk04, symbNameLen, symbol.unk0C, symbol.unk10,
            symbol.unk14) = struct.unpack_from('<Ii4I', data, 0)
        name = struct.unpack_from(
            '%ds' % (symbNameLen - 1), data, 0x18
            )[0].decode('latin-1')
        symbol.unkEnd, = struct.unpack_from(
            '<H', data, 0x18 + symbNameLen)

        return name, symbol


    def save(self, name):
        """
        Save the shader program symbol as binary data, with the name
        given
        """
        afterLength = b''
        fnData = name.encode('latin-1') + b'\0'
        afterLength += struct.pack('<i4I', self.unk04, len(fnData), self.unk0C,
                                   self.unk10, self.unk14)
        afterLength += fnData
        afterLength += struct.pack('<H', self.unkEnd)

        length = struct.pack('<I', len(afterLength) + 4)

        return length + afterLength


class ShaderProgramVariation:
    """
    A class that represents a variation of a shader program (a
    collection of specific shaders).
    """
    vertexShader = None
    pixelShader = None
    geometryShader = None
