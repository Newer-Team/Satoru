import collections
import struct

from . import _namespaceStruct


SHADER_ALIGNMENT = 0x100


class Shader:
    pass


class VertexShader(Shader):
    """
    Represents a GX2 vertex shader.
    """

    # So. The one I'm parsing supposedly begins at 3C.

    class _struct(_namespaceStruct.NamespaceStruct):
        ENDIAN = '<'

        # Registers
        sq_pgm_resources_vs = 'I'
        vgt_primitiveid_en = 'I'
        spi_vs_out_config = 'I'
        num_spi_vs_out_id = 'I'
        spi_vs_out_id = '10I'
        pa_cl_vs_out_cntl = 'I'
        sq_vtx_semantic_clear = 'I'
        num_sq_vtx_semantic = 'I'
        sq_vtx_semantic = '32I'
        vgt_strmout_buffer_en = 'I'
        vgt_vertex_reuse_block_cntl = 'I'
        vgt_hos_reuse_depth = 'I'

        size = 'I'
        dataPtr = 'I'
        mode = 'I'

        # Metadata
        uniformBlocksCount = 'I'
        uniformBlocksPtr = 'I'
        uniformVarsCount = 'I'
        uniformVarsPtr = 'I'
        initialValuesCount = 'I'
        initialValuesPtr = 'I'
        loopVarsCount = 'I'
        loopVarsPtr = 'I'
        samplerVarsCount = 'I'
        samplerVarsPtr = 'I'
        attribVarsCount = 'I'
        attribVarsPtr = 'I'

        ringItemSize = 'I'
        hasStreamOut = 'I'
        streamOutStride = '4I'

        # GX2R data buffer
        gx2r_data_flags = 'I'
        gx2r_data_elemSize = 'I'
        gx2r_data_elemCount = 'I'
        gx2r_data_bufferPtr = 'I'

    # Registers
    sq_pgm_resources_vs = 0
    vgt_primitiveid_en = 0
    spi_vs_out_config = 0
    num_spi_vs_out_id = 0
    spi_vs_out_id = None
    pa_cl_vs_out_cntl = 0
    sq_vtx_semantic_clear = 0
    num_sq_vtx_semantic = 0
    sq_vtx_semantic = None
    vgt_strmout_buffer_en = 0
    vgt_vertex_reuse_block_cntl = 0
    vgt_hos_reuse_depth = 0

    data = b''
    mode = 0

    # Metadata
    uniformBlocks = None
    uniformVars = None
    initialValues = None
    loopVars = None
    samplerVars = None
    attribVars = None

    ringItemSize = 0
    hasStreamOut = 0
    streamOutStride = None

    # GX2R data buffer
    gx2r_data_flags = 0
    gx2r_data_elemSize = 0
    gx2r_data_elemCount = 0
    gx2r_data_bufferPtr = 0

    def __init__(self):
        """
        Fill in the field values that default to None
        """
        self.spi_vs_out_id = [0] * 10
        self.sq_vtx_semantic = [0] * 32
        self.uniformBlocks = []
        self.uniformVars = []
        self.initialValues = []
        self.loopVars = []
        self.samplerVars = []
        self.attribVars = []
        self.streamOutStride = [0] * 4
    
    @classmethod
    def load(cls, data):
        """
        Load the data and return a VertexShader
        """
        s = cls._struct.loadFrom(data)
        vs = cls()

        # Registers
        vs.sq_pgm_resources_vs = s.sq_pgm_resources_vs
        vs.vgt_primitiveid_en = s.vgt_primitiveid_en
        vs.spi_vs_out_config = s.spi_vs_out_config
        vs.num_spi_vs_out_id = s.num_spi_vs_out_id
        vs.spi_vs_out_id = s.spi_vs_out_id
        vs.pa_cl_vs_out_cntl = s.pa_cl_vs_out_cntl
        vs.sq_vtx_semantic_clear = s.sq_vtx_semantic_clear
        vs.num_sq_vtx_semantic = s.num_sq_vtx_semantic
        vs.sq_vtx_semantic = s.sq_vtx_semantic
        vs.vgt_strmout_buffer_en = s.vgt_strmout_buffer_en
        vs.vgt_vertex_reuse_block_cntl = s.vgt_vertex_reuse_block_cntl
        vs.vgt_hos_reuse_depth = s.vgt_hos_reuse_depth

        vs.data = data[s.dataPtr:s.dataPtr+s.size]
        vs.mode = s.mode

        # Metadata
        vs.uniformBlocks = loadDictFrom(UniformBlock, data, s.uniformBlocksPtr, s.uniformBlocksCount)
        vs.uniformVars = loadDictFrom(UniformVar, data, s.uniformVarsPtr, s.uniformVarsCount)
        vs.initialValues = loadArrayFrom(UniformInitialValue, data, s.initialValuesPtr, s.initialValuesCount)
        vs.loopVars = loadArrayFrom(LoopVar, data, s.loopVarsPtr, s.loopVarsCount)
        vs.samplerVars = loadDictFrom(SamplerVar, data, s.samplerVarsPtr, s.samplerVarsCount)
        vs.attribVars = loadDictFrom(AttribVar, data, s.attribVarsPtr, s.attribVarsCount)

        # GX2R data buffer
        vs.gx2r_data_flags = s.gx2r_data_flags
        vs.gx2r_data_elemSize = s.gx2r_data_elemSize
        vs.gx2r_data_elemCount = s.gx2r_data_elemCount
        vs.gx2r_data_bufferPtr = s.gx2r_data_bufferPtr

        return vs

    def save(self, offset):
        """
        Save this VertexShader back to bytes. offset is the offset that
        the bytes output will be placed in in the output file (required
        to properly calculate alignment).
        """
        s = self._struct()

        # Registers
        s.sq_pgm_resources_vs = self.sq_pgm_resources_vs
        s.vgt_primitiveid_en = self.vgt_primitiveid_en
        s.spi_vs_out_config = self.spi_vs_out_config
        s.num_spi_vs_out_id = self.num_spi_vs_out_id
        s.spi_vs_out_id = self.spi_vs_out_id
        s.pa_cl_vs_out_cntl = self.pa_cl_vs_out_cntl
        s.sq_vtx_semantic_clear = self.sq_vtx_semantic_clear
        s.num_sq_vtx_semantic = self.num_sq_vtx_semantic
        s.sq_vtx_semantic = self.sq_vtx_semantic
        s.vgt_strmout_buffer_en = self.vgt_strmout_buffer_en
        s.vgt_vertex_reuse_block_cntl = self.vgt_vertex_reuse_block_cntl
        s.vgt_hos_reuse_depth = self.vgt_hos_reuse_depth

        s.size = len(self.data)
        # We'll fill in s.dataPtr later.
        s.mode = self.mode

        # Put all of the strings into a buffer
        strBuf = bytearray()
        strBufOffs = {}
        for key in self.uniformBlocks:
            strBufOffs[key] = len(strBuf)
            strBuf.extend(key.encode('latin-1') + b'\0')
        for key in self.uniformVars:
            strBufOffs[key] = len(strBuf)
            strBuf.extend(key.encode('latin-1') + b'\0')
        for key in self.samplerVars:
            strBufOffs[key] = len(strBuf)
            strBuf.extend(key.encode('latin-1') + b'\0')
        for key in self.attribVars:
            strBufOffs[key] = len(strBuf)
            strBuf.extend(key.encode('latin-1') + b'\0')

        # We need to find what the total length of the metadata is going
        # to be, so we can predict where the string buffer will end up.
        # We can also fill in the offsets and counts for each of these,
        # while we're at it.
        metadataLen = 0
        if self.uniformBlocks:
            s.uniformBlocksCount = len(self.uniformBlocks)
            s.uniformBlocksPtr = s.structSize + metadataLen
            for item in self.uniformBlocks.values():
                metadataLen += item.LENGTH
        if self.uniformVars:
            s.uniformVarsCount = len(self.uniformVars)
            s.uniformVarsPtr = s.structSize + metadataLen
            for item in self.uniformVars.values():
                metadataLen += item.LENGTH
        if self.initialValues:
            s.initialValuesCount = len(self.initialValues)
            s.initialValuesPtr = s.structSize + metadataLen
            for item in self.initialValues:
                metadataLen += item.LENGTH
        if self.loopVars:
            s.loopVarsCount = len(self.loopVars)
            s.loopVarsPtr = s.structSize + metadataLen
            for item in self.loopVars:
                metadataLen += item.LENGTH
        if self.samplerVars:
            s.samplerVarsCount = len(self.samplerVars)
            s.samplerVarsPtr = s.structSize + metadataLen
            for item in self.samplerVars.values():
                metadataLen += item.LENGTH
        if self.attribVars:
            s.attribVarsCount = len(self.attribVars)
            s.attribVarsPtr = s.structSize + metadataLen
            for item in self.attribVars.values():
                metadataLen += item.LENGTH
        strBufOff = s.structSize + metadataLen

        # Now that we know where the strings will go, we can actually
        # save the metadata.
        metadataBuf = bytearray()
        for name, item in self.uniformBlocks.items():
            metadataBuf.extend(item.save(strBufOffs[name] + strBufOff))
        for name, item in self.uniformVars.items():
            metadataBuf.extend(item.save(strBufOffs[name] + strBufOff))
        for item in self.initialValues:
            metadataBuf.extend(item.save())
        for item in self.loopVars:
            metadataBuf.extend(item.save())
        for name, item in self.samplerVars.items():
            metadataBuf.extend(item.save(strBufOffs[name] + strBufOff))
        for name, item in self.attribVars.items():
            metadataBuf.extend(item.save(strBufOffs[name] + strBufOff))

        # Now we add alignment padding.
        totalSize = s.structSize + len(metadataBuf) + len(strBuf)
        absOff = offset + totalSize
        padLen = SHADER_ALIGNMENT - (absOff % SHADER_ALIGNMENT)
        padding = b'\0' * padLen

        # Now we can finally set the data offset
        s.dataPtr = totalSize + padLen

        # And put it all together!
        return s.save() + metadataBuf + strBuf + padding + self.data


class PixelShader(Shader):
    """
    Represents a GX2 pixel shader.
    """

    class _struct(_namespaceStruct.NamespaceStruct):
        ENDIAN = '<'

        # Registers
        sq_pgm_resources_vs = 'I'
        sq_pgm_exports_ps = 'I'
        spi_ps_in_control_0 = 'I'
        spi_ps_in_control_1 = 'I'
        num_spi_ps_input_cntl = 'I'
        spi_ps_input_cntls = '32I'
        cb_shader_mask = 'I'
        cb_shader_control = 'I'
        db_shader_control = 'I'
        spi_input_z = 'I'

        size = 'I'
        dataPtr = 'I'
        mode = 'I'

        # Metadata
        uniformBlocksCount = 'I'
        uniformBlocksPtr = 'I'
        uniformVarsCount = 'I'
        uniformVarsPtr = 'I'
        initialValuesCount = 'I'
        initialValuesPtr = 'I'
        loopVarsCount = 'I'
        loopVarsPtr = 'I'
        samplerVarsCount = 'I'
        samplerVarsPtr = 'I'

        # GX2R data buffer
        gx2r_data_flags = 'I'
        gx2r_data_elemSize = 'I'
        gx2r_data_elemCount = 'I'
        gx2r_data_bufferPtr = 'I'

    # Registers
    sq_pgm_resources_vs = 0
    sq_pgm_exports_ps = 0
    spi_ps_in_control_0 = 0
    spi_ps_in_control_1 = 0
    num_spi_ps_input_cntl = 0
    spi_ps_input_cntls = None
    cb_shader_mask = 0
    cb_shader_control = 0
    db_shader_control = 0
    spi_input_z = 0

    data = b''
    mode = 0

    # Metadata
    uniformBlocks = None
    uniformVars = None
    initialValues = None
    loopVars = None
    samplerVars = None

    # GX2R data buffer
    gx2r_data_flags = 0
    gx2r_data_elemSize = 0
    gx2r_data_elemCount = 0
    gx2r_data_bufferPtr = 0

    def __init__(self):
        """
        Fill in the field values that default to None
        """
        self.spi_ps_input_cntls = [0] * 32
        self.uniformBlocks = []
        self.uniformVars = []
        self.initialValues = []
        self.loopVars = []
        self.samplerVars = []

    @classmethod
    def load(cls, data):
        """
        Load the data and return a PixelShader
        """
        s = cls._struct.loadFrom(data)
        ps = cls()

        # Registers
        ps.sq_pgm_resources_vs = s.sq_pgm_resources_vs
        ps.sq_pgm_exports_ps = s.sq_pgm_exports_ps
        ps.spi_ps_in_control_0 = s.spi_ps_in_control_0
        ps.spi_ps_in_control_1 = s.spi_ps_in_control_1
        ps.num_spi_ps_input_cntl = s.num_spi_ps_input_cntl
        ps.spi_ps_input_cntls = s.spi_ps_input_cntls
        ps.cb_shader_mask = s.cb_shader_mask
        ps.cb_shader_control = s.cb_shader_control
        ps.db_shader_control = s.db_shader_control
        ps.spi_input_z = s.spi_input_z

        ps.data = data[s.dataPtr:s.dataPtr+s.size]
        ps.mode = s.mode

        # Metadata
        ps.uniformBlocks = loadDictFrom(UniformBlock, data, s.uniformBlocksPtr, s.uniformBlocksCount)
        ps.uniformVars = loadDictFrom(UniformVar, data, s.uniformVarsPtr, s.uniformVarsCount)
        ps.initialValues = loadArrayFrom(UniformInitialValue, data, s.initialValuesPtr, s.initialValuesCount)
        ps.loopVars = loadArrayFrom(LoopVar, data, s.loopVarsPtr, s.loopVarsCount)
        ps.samplerVars = loadDictFrom(SamplerVar, data, s.samplerVarsPtr, s.samplerVarsCount)

        # GX2R data buffer
        ps.gx2r_data_flags = s.gx2r_data_flags
        ps.gx2r_data_elemSize = s.gx2r_data_elemSize
        ps.gx2r_data_elemCount = s.gx2r_data_elemCount
        ps.gx2r_data_bufferPtr = s.gx2r_data_bufferPtr

        return ps

    def save(self, offset):
        """
        Save this PixelShader back to bytes. offset is the offset that
        the bytes output will be placed in in the output file (required
        to properly calculate alignment).
        """
        s = self._struct()

        # Registers
        s.sq_pgm_resources_vs = self.sq_pgm_resources_vs
        s.sq_pgm_exports_ps = self.sq_pgm_exports_ps
        s.spi_ps_in_control_0 = self.spi_ps_in_control_0
        s.spi_ps_in_control_1 = self.spi_ps_in_control_1
        s.num_spi_ps_input_cntl = self.num_spi_ps_input_cntl
        s.spi_ps_input_cntls = self.spi_ps_input_cntls
        s.cb_shader_mask = self.cb_shader_mask
        s.cb_shader_control = self.cb_shader_control
        s.db_shader_control = self.db_shader_control
        s.spi_input_z = self.spi_input_z

        s.size = len(self.data)
        # We'll fill in s.dataPtr later.
        s.mode = self.mode

        # Put all of the strings into a buffer
        strBuf = bytearray()
        strBufOffs = {}
        for key in self.uniformBlocks:
            strBufOffs[key] = len(strBuf)
            strBuf.extend(key.encode('latin-1') + b'\0')
        for key in self.uniformVars:
            strBufOffs[key] = len(strBuf)
            strBuf.extend(key.encode('latin-1') + b'\0')
        for key in self.samplerVars:
            strBufOffs[key] = len(strBuf)
            strBuf.extend(key.encode('latin-1') + b'\0')

        # We need to find what the total length of the metadata is going
        # to be, so we can predict where the string buffer will end up.
        # We can also fill in the offsets and counts for each of these,
        # while we're at it.
        metadataLen = 0
        if self.uniformBlocks:
            s.uniformBlocksCount = len(self.uniformBlocks)
            s.uniformBlocksPtr = s.structSize + metadataLen
            for item in self.uniformBlocks.values():
                metadataLen += item.LENGTH
        if self.uniformVars:
            s.uniformVarsCount = len(self.uniformVars)
            s.uniformVarsPtr = s.structSize + metadataLen
            for item in self.uniformVars.values():
                metadataLen += item.LENGTH
        if self.initialValues:
            s.initialValuesCount = len(self.initialValues)
            s.initialValuesPtr = s.structSize + metadataLen
            for item in self.initialValues:
                metadataLen += item.LENGTH
        if self.loopVars:
            s.loopVarsCount = len(self.loopVars)
            s.loopVarsPtr = s.structSize + metadataLen
            for item in self.loopVars:
                metadataLen += item.LENGTH
        if self.samplerVars:
            s.samplerVarsCount = len(self.samplerVars)
            s.samplerVarsPtr = s.structSize + metadataLen
            for item in self.samplerVars.values():
                metadataLen += item.LENGTH
        strBufOff = s.structSize + metadataLen

        # Now that we know where the strings will go, we can actually
        # save the metadata.
        metadataBuf = bytearray()
        for name, item in self.uniformBlocks.items():
            metadataBuf.extend(item.save(strBufOffs[name] + strBufOff))
        for name, item in self.uniformVars.items():
            metadataBuf.extend(item.save(strBufOffs[name] + strBufOff))
        for item in self.initialValues:
            metadataBuf.extend(item.save())
        for item in self.loopVars:
            metadataBuf.extend(item.save())
        for name, item in self.samplerVars.items():
            metadataBuf.extend(item.save(strBufOffs[name] + strBufOff))

        # Now we add alignment padding.
        totalSize = s.structSize + len(metadataBuf) + len(strBuf)
        absOff = offset + totalSize
        padLen = SHADER_ALIGNMENT - (absOff % SHADER_ALIGNMENT)
        padding = b'\0' * padLen

        # Now we can finally set the data offset
        s.dataPtr = totalSize + padLen

        # And put it all together!
        return s.save() + metadataBuf + strBuf + padding + self.data


class GeometryShader(Shader):
    """
    Represents a GX2 geometry shader.
    """

    class _struct(_namespaceStruct.NamespaceStruct):
        ENDIAN = '<'

        # Registers
        sq_pgm_resources_gs = 'I'
        vgt_gs_out_prim_type = 'I'
        vgt_gs_mode = 'I'
        pa_cl_vs_out_cntl = 'I'
        sq_pgm_resources_vs = 'I'
        sq_gs_vert_itemsize = 'I'
        spi_vs_out_config = 'I'
        num_spi_vs_out_id = 'I'
        spi_vs_out_id = '10I'
        vgt_strmout_buffer_en = 'I'

        size = 'I'
        dataPtr = 'I'
        vertexShaderSize = 'I'
        vertexShaderDataPtr = 'I'
        mode = 'I'

        # Metadata
        uniformBlocksCount = 'I'
        uniformBlocksPtr = 'I'
        uniformVarsCount = 'I'
        uniformVarsPtr = 'I'
        initialValuesCount = 'I'
        initialValuesPtr = 'I'
        loopVarsCount = 'I'
        loopVarsPtr = 'I'
        samplerVarsCount = 'I'
        samplerVarsPtr = 'I'

        ringItemSize = 'I'
        hasStreamOut = 'I'
        streamOutStride = '4I'

        # GX2R data buffer
        gx2r_data_flags = 'I'
        gx2r_data_elemSize = 'I'
        gx2r_data_elemCount = 'I'
        gx2r_data_bufferPtr = 'I'

        # GX2R vertex shader data buffer
        gx2r_vertex_shader_data_flags = 'I'
        gx2r_vertex_shader_data_elemSize = 'I'
        gx2r_vertex_shader_data_elemCount = 'I'
        gx2r_vertex_shader_data_bufferPtr = 'I'

    # Registers
    sq_pgm_resources_gs = 0
    vgt_gs_out_prim_type = 0
    vgt_gs_mode = 0
    pa_cl_vs_out_cntl = 0
    sq_pgm_resources_vs = 0
    sq_gs_vert_itemsize = 0
    spi_vs_out_config = 0
    num_spi_vs_out_id = 0
    spi_vs_out_id = None
    vgt_strmout_buffer_en = 0

    data = b''
    vertexShaderData = b''
    mode = 0
    
    # Metadata
    uniformBlocks = None
    uniformVars = None
    initialValues = None
    loopVars = None
    samplerVars = None

    ringItemSize = 0
    hasStreamOut = 0
    streamOutStride = None

    # GX2R data buffer
    gx2r_data_flags = 0
    gx2r_data_elemSize = 0
    gx2r_data_elemCount = 0
    gx2r_data_bufferPtr = 0

    # GX2R vertex shader data buffer
    gx2r_vertex_shader_data_flags = 0
    gx2r_vertex_shader_data_elemSize = 0
    gx2r_vertex_shader_data_elemCount = 0
    gx2r_vertex_shader_data_bufferPtr = 0

    def __init__(self):
        """
        Fill in the field values that default to None
        """
        self.spi_vs_out_id = [0] * 10
        self.uniformBlocks = []
        self.uniformVars = []
        self.initialValues = []
        self.loopVars = []
        self.samplerVars = []
        self.streamOutStride = [0] * 4

    @classmethod
    def load(cls, data):
        """
        Load the data and return a GeometryShader
        """
        raise NotImplementedError("Uh, yeah. This one isn't done yet.")

    def save(self, offset):
        """
        Save this PixelShader back to bytes. offset is the offset that
        the bytes output will be placed in in the output file (required
        to properly calculate alignment).
        """
        raise NotImplementedError("Still nope.")


class UniformBlock:
    """
    Represents a GX2 uniform block.
    """
    LENGTH = 0x0C

    offset = 0
    size = 0

    @classmethod
    def loadFrom(cls, data, offset):
        """
        Load a UniformBlock from data at offset
        """
        ub = cls()
        namePtr, ub.offset, ub.size = struct.unpack_from('<3I', data, offset)
        name = loadStringFrom(data, namePtr)
        return name, ub

    def save(self, namePtr):
        """
        Save this UniformBlock back to bytes (referencing some name
        string at absolute offset namePtr)
        """
        return struct.pack('<3I', namePtr, self.offset, self.size)


class UniformVar:
    """
    Represents a GX2 uniform variable.
    """
    LENGTH = 0x14

    type = 0
    count = 0
    offset = 0
    block = 0

    @classmethod
    def loadFrom(cls, data, offset):
        """
        Load a UniformVar from data at offset
        """
        uv = cls()
        namePtr, uv.type, uv.count, uv.offset, uv.block = struct.unpack_from(
            '<4Ii', data, offset)
        name = loadStringFrom(data, namePtr)
        return name, uv

    def save(self, namePtr):
        """
        Save this UniformVar back to bytes (referencing some name string
        at absolute offset namePtr)
        """
        return struct.pack('<4Ii', namePtr, self.type, self.count, self.offset,
                           self.block)


class UniformInitialValue:
    """
    Represents a GX2 uniform initial value.
    """
    LENGTH = 0x14

    value = None
    offset = 0

    @classmethod
    def loadFrom(cls, data, offset):
        """
        Load a UniformInitialValue from data at offset
        """
        uiv = cls()
        values = struct.unpack_from('<4fI', data, offset)
        uiv.value = values[:4]
        uiv.offset = values[4]
        return uiv

    def save(self):
        """
        Save this UniformInitialValue back to bytes
        """
        return struct.pack('<4fi', *self.value, self.offset)


class LoopVar:
    """
    Represents a GX2 loop variable.
    """
    LENGTH = 0x08

    offset = 0
    value = 0

    @classmethod
    def loadFrom(cls, data, offset):
        """
        Load a LoopVar from data at offset
        """
        lv = cls()
        lv.offset, lv.value = struct.unpack_from('<II', data, offset)
        return lv

    def save(self):
        """
        Save this LoopVar back to bytes
        """
        return struct.pack('<II', self.offset, self.value)


class SamplerVar:
    """
    Represents a GX2 sampler variable.
    """
    LENGTH = 0x0C

    type = 0
    location = 0

    @classmethod
    def loadFrom(cls, data, offset):
        """
        Load a SamplerVar from data at offset
        """
        sv = cls()
        namePtr, sv.type, sv.location = struct.unpack_from('<3I', data, offset)
        name = loadStringFrom(data, namePtr)
        return name, sv

    def save(self, namePtr):
        """
        Save this SamplerVar back to bytes (referencing some name string
        at absolute offset namePtr)
        """
        return struct.pack('<3I', namePtr, self.type, self.location)


class AttribVar:
    """
    Represents a GX2 attribute variable.
    """
    LENGTH = 0x10

    type = 0
    count = 0
    location = 0

    @classmethod
    def loadFrom(cls, data, offset):
        """
        Load a AttribVar from data at offset
        """
        av = cls()
        namePtr, av.type, av.count, av.location = struct.unpack_from(
            '<4I', data, offset)
        name = loadStringFrom(data, namePtr)
        return name, av

    def save(self, namePtr):
        """
        Save this AttribVar back to bytes (referencing some name string
        at absolute offset namePtr)
        """
        return struct.pack('<4I', namePtr, self.type, self.count,
                           self.location)


def loadArrayFrom(cls, data, offset, count):
    """
    Load an array of count cls's from data at offset
    """
    L = []
    for _ in range(count):
        L.append(cls.loadFrom(data, offset))
        offset += cls.LENGTH
    return L


def loadDictFrom(cls, data, offset, count):
    """
    Load a dict of count cls's from data at offset
    """
    d = collections.OrderedDict()
    for _ in range(count):
        name, obj = cls.loadFrom(data, offset)
        d[name] = obj
        offset += cls.LENGTH
    return d


def loadStringFrom(data, offset):
    """
    Load a null-terminated string from offset
    """
    return data[offset:data.find(b'\0', offset)].decode('latin-1')