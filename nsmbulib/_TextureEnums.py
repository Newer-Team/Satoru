
# All of these enums are directly from
# https://github.com/decaf-emu/decaf-emu/blob/master/src/libdecaf/src/modules/gx2/gx2_enum.h
# Please update this file whenever more discoveries are made in that file. Thank you.

import enum


class GX2AAMode(enum.IntEnum):
    Mode1X = 0
    Mode2X = 1
    Mode4X = 2
    Mode8X = 3


class GX2AspectRatio(enum.IntEnum):
    Normal     = 0
    Widescreen = 1


class GX2AttribFormatType(enum.IntEnum):
    TYPE_8                 = 0
    TYPE_4_4               = 1
    TYPE_16                = 2
    TYPE_16_FLOAT          = 3
    TYPE_8_8               = 4
    TYPE_32                = 5
    TYPE_32_FLOAT          = 6
    TYPE_16_16             = 7
    TYPE_16_16_FLOAT       = 8
    TYPE_10_11_11_FLOAT    = 9
    TYPE_8_8_8_8           = 10
    TYPE_10_10_10_2        = 11
    TYPE_32_32             = 12
    TYPE_32_32_FLOAT       = 13
    TYPE_16_16_16_16       = 14
    TYPE_16_16_16_16_FLOAT = 15
    TYPE_32_32_32          = 16
    TYPE_32_32_32_FLOAT    = 17
    TYPE_32_32_32_32       = 18
    TYPE_32_32_32_32_FLOAT = 19


class GX2AttribFormatFlags(enum.IntEnum):
    INTEGER = 0x100
    SIGNED  = 0x200
    DEGAMMA = 0x400
    SCALED  = 0x800


class GX2AttribFormat(enum.IntEnum):
    UNORM_8           = 0x00
    UNORM_8_8         = 0x04
    UNORM_8_8_8_8     = 0x0A

    UINT_8            = 0x100
    UINT_8_8          = 0x104
    UINT_8_8_8_8      = 0x10A

    SNORM_8           = 0x200
    SNORM_8_8         = 0x204
    SNORM_8_8_8_8     = 0x20A

    SINT_8            = 0x300
    SINT_8_8          = 0x304
    SINT_8_8_8_8      = 0x30A

    FLOAT_32          = 0x806
    FLOAT_32_32       = 0x80d
    FLOAT_32_32_32    = 0x811
    FLOAT_32_32_32_32 = 0x813


class GX2AttribIndexType(enum.IntEnum):
    PerVertex   = 0
    PerInstance = 1


class GX2AlphaToMaskMode(enum.IntEnum):
    NonDithered = 0
    Dither0     = 1
    Dither90    = 2
    Dither180   = 3
    Dither270   = 4


class GX2BlendMode(enum.IntEnum):
    Zero            = 0
    One             = 1
    SrcColor        = 2
    InvSrcColor     = 3
    SrcAlpha        = 4
    InvSrcAlpha     = 5
    DestAlpha       = 6
    InvDestAlpha    = 7
    DestColor       = 8
    InvDestColor    = 9
    SrcAlphaSat     = 10
    BothSrcAlpha    = 11
    BothInvSrcAlpha = 12
    BlendFactor     = 13
    InvBlendFactor  = 14
    Src1Color       = 15
    InvSrc1Color    = 16
    Src1Alpha       = 17
    InvSrc1Alpha    = 18


class GX2BlendCombineMode(enum.IntEnum):
    Add         = 0
    Subtract    = 1
    Min         = 2
    Max         = 3
    RevSubtract = 4


class GX2BufferingMode(enum.IntEnum):
    Single = 1
    Double = 2
    Triple = 3


class GX2ChannelMask(enum.IntEnum):
    R    = 0b0001
    G    = 0b0010
    RG   = 0b0011
    B    = 0b0100
    RB   = 0b0101
    GB   = 0b0110
    RGB  = 0b0111
    A    = 0b1000
    RA   = 0b1001
    GA   = 0b1010
    RGA  = 0b1011
    BA   = 0b1100
    RBA  = 0b1101
    GBA  = 0b1110
    RGBA = 0b1111


class GX2CompareFunction(enum.IntEnum):
    Never          = 0
    Less           = 1
    Equal          = 2
    LessOrEqual    = 3
    Greater        = 4
    NotEqual       = 5
    GreaterOrEqual = 6
    Always         = 7


class GX2Component(enum.IntEnum):
    Mem0 = 0
    Mem1 = 1
    Mem2 = 2
    Mem3 = 3
    Zero = 4
    One  = 5


class GX2ClearFlags(enum.IntEnum):
    Depth   = 1
    Stencil = 2


class GX2DrcRenderMode(enum.IntEnum):
    Disabled = 0
    Single   = 1


class GX2EndianSwapMode(enum.IntEnum):
    None_     = 0
    Swap8In16 = 1
    Swap8In32 = 2
    Default   = 3


class GX2EventType(enum.IntEnum):
    Vsync              = 2
    Flip               = 3
    DisplayListOverrun = 4
    Max                = 5


class GX2FetchShaderType(enum.IntEnum):
    NoTessellation       = 0
    LineTessellation     = 1
    TriangleTessellation = 2
    QuadTessellation     = 3


class GX2FrontFace(enum.IntEnum):
    CounterClockwise = 0
    Clockwise        = 1


class GX2IndexType(enum.IntEnum):
    U16_LE = 0x0
    U32_LE = 0x1
    U16    = 0x4
    U32    = 0x9


class GX2InvalidateMode(enum.IntEnum):
    AttributeBuffer = 0b000000001
    Texture         = 0b000000010
    UniformBlock    = 0b000000100
    Shader          = 0b000001000
    ColorBuffer     = 0b000010000
    DepthBuffer     = 0b000100000
    CPU             = 0b001000000
    StreamOutBuffer = 0b010000000
    ExportBuffer    = 0b100000000


class GX2LogicOp(enum.IntEnum):
    Clear        = 0x00
    Nor          = 0x11
    InvertedAnd  = 0x22
    InvertedCopy = 0x33
    ReverseAnd   = 0x44
    Invert       = 0x55
    Xor          = 0x66
    NotAnd       = 0x77
    And          = 0x88
    Equiv        = 0x99
    NoOp         = 0xAA
    InvertedOr   = 0xBB
    Copy         = 0xCC
    ReverseOr    = 0xDD
    Or           = 0xEE
    Set          = 0xFF


class GX2PrimitiveMode(enum.IntEnum):
    Triangles     = 0x04
    TriangleStrip = 0x06
    Quads         = 0x13
    QuadStrip     = 0x14


class GX2PolygonMode(enum.IntEnum):
    Point    = 0
    Line     = 1
    Triangle = 2


class GX2RenderTarget(enum.IntEnum):
    Target0 = 0
    Target1 = 1
    Target2 = 2
    Target3 = 3
    Target4 = 4
    Target5 = 5
    Target6 = 6
    Target7 = 7


class GX2ResourceFlags(enum.IntEnum):
    BindTexture       = 1 << 0
    BindColorBuffer   = 1 << 1
    BindDepthBuffer   = 1 << 2
    BindScanBuffer    = 1 << 3
    BindVertexBuffer  = 1 << 4
    BindIndexBuffer   = 1 << 5
    BindUniformBlock  = 1 << 6
    BindShaderProgram = 1 << 7
    BindStreamOutput  = 1 << 8
    BindDisplayList   = 1 << 9
    BindGSRing        = 1 << 10
    UsageCpuRead      = 1 << 11
    UsageCpuWrite     = 1 << 12
    UsageCpuReadWrite = UsageCpuRead | UsageCpuWrite
    UsageGpuRead      = 1 << 13
    UsageGpuWrite     = 1 << 14
    UsageGpuReadWrite = UsageGpuRead | UsageGpuWrite
    UsageDmaRead      = 1 << 15
    UsageDmaWrite     = 1 << 16
    UsageForceMEM1    = 1 << 17
    UsageForceMEM2    = 1 << 18
    UserMemory        = 1 << 29
    Locked            = 1 << 30



class GX2RoundingMode(enum.IntEnum):
    RoundToEven = 0
    Truncate    = 1


class GX2ScanTarget(enum.IntEnum):
    TV  = 1
    DRC = 4


class GX2SurfaceDim(enum.IntEnum):
    Texture1D          = 0
    Texture2D          = 1
    Texture3D          = 2
    TextureCube        = 3
    Texture1DArray     = 4
    Texture2DArray     = 5
    Texture2DMSAA      = 6
    Texture2DMSAAArray = 7


class GX2SurfaceFormat(enum.IntEnum):
    INVALID               = 0x00
    UNORM_R4_G4           = 0x02
    UNORM_R4_G4_B4_A4     = 0x0b
    UNORM_R8              = 0x01
    UNORM_R8_G8           = 0x07
    UNORM_R8_G8_B8_A8     = 0x01a
    UNORM_R16             = 0x05
    UNORM_R16_G16         = 0x0f
    UNORM_R16_G16_B16_A16 = 0x01f
    UNORM_R5_G6_B5        = 0x08
    UNORM_R5_G5_B5_A1     = 0x0a
    UNORM_A1_B5_G5_R5     = 0x0c
    UNORM_R24_X8          = 0x011
    UNORM_A2_B10_G10_R10  = 0x01b
    UNORM_R10_G10_B10_A2  = 0x019
    UNORM_BC1             = 0x031
    UNORM_BC2             = 0x032
    UNORM_BC3             = 0x033
    UNORM_BC4             = 0x034
    UNORM_BC5             = 0x035
    UNORM_NV12            = 0x081

    UINT_R8               = 0x101
    UINT_R8_G8            = 0x107
    UINT_R8_G8_B8_A8      = 0x11a
    UINT_R16              = 0x105
    UINT_R16_G16          = 0x10f
    UINT_R16_G16_B16_A16  = 0x11f
    UINT_R32              = 0x10d
    UINT_R32_G32          = 0x11d
    UINT_R32_G32_B32_A32  = 0x122
    UINT_A2_B10_G10_R10   = 0x11b
    UINT_R10_G10_B10_A2   = 0x119
    UINT_X24_G8           = 0x111
    UINT_G8_X24           = 0x11c

    SNORM_R8              = 0x201
    SNORM_R8_G8           = 0x207
    SNORM_R8_G8_B8_A8     = 0x21a
    SNORM_R16             = 0x205
    SNORM_R16_G16         = 0x20f
    SNORM_R16_G16_B16_A16 = 0x21f
    SNORM_R10_G10_B10_A2  = 0x219
    SNORM_BC4             = 0x234
    SNORM_BC5             = 0x235

    SINT_R8               = 0x301
    SINT_R8_G8            = 0x307
    SINT_R8_G8_B8_A8      = 0x31a
    SINT_R16              = 0x305
    SINT_R16_G16          = 0x30f
    SINT_R16_G16_B16_A16  = 0x31f
    SINT_R32              = 0x30d
    SINT_R32_G32          = 0x31d
    SINT_R32_G32_B32_A32  = 0x322
    SINT_R10_G10_B10_A2   = 0x319

    SRGB_R8_G8_B8_A8      = 0x41a
    SRGB_BC1              = 0x431
    SRGB_BC2              = 0x432
    SRGB_BC3              = 0x433

    FLOAT_R32             = 0x80e
    FLOAT_R32_G32         = 0x81e
    FLOAT_R32_G32_B32_A32 = 0x823
    FLOAT_R16             = 0x806
    FLOAT_R16_G16         = 0x810
    FLOAT_R16_G16_B16_A16 = 0x820
    FLOAT_R11_G11_B10     = 0x816
    FLOAT_D24_S8          = 0x811
    FLOAT_X8_X24          = 0x81c


class GX2SurfaceUse(enum.IntEnum):
    Texture     = 0b0001
    ColorBuffer = 0b0010
    DepthBuffer = 0b0100
    ScanBuffer  = 0b1000


class GX2StencilFunction(enum.IntEnum):
    Keep      = 0
    Zero      = 1
    Replace   = 2
    IncrClamp = 3
    DecrClamp = 4
    Invert    = 5
    IncrWrap  = 6
    DecrWrap  = 7


class GX2TessellationMode(enum.IntEnum):
    Discrete   = 0
    Continuous = 1
    Adaptive   = 2


class GX2TexBorderType(enum.IntEnum):
    TransparentBlack = 0
    Black            = 1
    White            = 2
    Variable         = 3


class GX2TexClampMode(enum.IntEnum):
    Wrap        = 0
    Mirror      = 1
    Clamp       = 2
    MirrorOnce  = 3
    ClampBorder = 6


class GX2TexMipFilterMode(enum.IntEnum):
    None_  = 0
    Point  = 1
    Linear = 2


class GX2TexMipPerfMode(enum.IntEnum):
    Disable = 0


class GX2TexXYFilterMode(enum.IntEnum):
    Point  = 0
    Linear = 1


class GX2TexAnisoRatio(enum.IntEnum):
    None_ = 0


class GX2TexZFilterMode(enum.IntEnum):
    None_  = 0
    Point  = 1
    Linear = 2


class GX2TexZPerfMode(enum.IntEnum):
    Disabled = 0


class GX2TileMode(enum.IntEnum):
    Default       = 0
    LinearAligned = 1
    Tiled1DThin1  = 2
    Tiled1DThick  = 3
    Tiled2DThin1  = 4
    Tiled2DThin2  = 5
    Tiled2DThin4  = 6
    Tiled2DThick  = 7
    Tiled2BThin1  = 8
    Tiled2BThin2  = 9
    Tiled2BThin4  = 10
    Tiled2BThick  = 11
    Tiled3DThin1  = 12
    Tiled3DThick  = 13
    Tiled3BThin1  = 14
    Tiled3BThick  = 15
    LinearSpecial = 16


class GX2TVRenderMode(enum.IntEnum):
    Standard480p = 1
    Wide480p     = 2
    Wide720p     = 3
    Wide1080p    = 5


class GX2TVScanMode(enum.IntEnum):
    None_  = 0
    I480   = 1
    P480   = 2
    P720   = 3
    I1080  = 5
    P1080  = 6


class GX2SamplerVarType(enum.IntEnum):
    Sampler1D   = 0
    Sampler2D   = 1
    Sampler3D   = 3
    SamplerCube = 4


class GX2ShaderMode(enum.IntEnum):
    UniformRegister = 0
    UniformBlock    = 1
    GeometryShader  = 2
    ComputeShader   = 3


class GX2ShaderVarType(enum.IntEnum):
    Int       = 2
    Float     = 4
    Float2    = 9
    Float3    = 10
    Float4    = 11
    Int2      = 15
    Int3      = 16
    Int4      = 17
    Matrix4x4 = 29
