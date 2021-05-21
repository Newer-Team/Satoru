import os
import os.path
import struct
import subprocess
import warnings

from PIL import Image

from . import _common
from . import _cAlgorithms


# If this is somehow causing conflicts, feel free to change it
TEMP_FILE_NAME = 'tempGtxConversionFile'


AmdCompressAvailable = False
AmdCompressFolder = ''
def findAmdCompress():
    """
    Locate AMD Compress, if possible.
    """

    # The executable used to be in the /CLI subfolder until
    # v2.2, but now it's just in the main folder.

    # Method 1: the user can specify the folder manually using amdcompress.txt
    txtFn = os.path.join(os.path.dirname(__file__), 'amdcompress.txt')
    if os.path.isfile(txtFn):
        with open(txtFn, 'r', encoding='utf-8') as f:
            txt = f.read()
        if os.path.isdir(txt) and os.path.isfile(os.path.join(txt, 'AMDCompressCLI.exe')):
            return txt

    # Method 2: we can check the environment variable set by AMD Compress setup
    if 'AMDCOMPRESS_ROOT' in os.environ and os.path.isfile(os.path.join(os.environ['AMDCOMPRESS_ROOT'], 'AMDCompressCLI.exe')):
        return os.environ['AMDCOMPRESS_ROOT']

AmdCompressFolder = findAmdCompress()
AmdCompressAvailable = bool(AmdCompressFolder)
if not AmdCompressAvailable:
    warnings.warn("""
nsmbulib: AMD Compress could not be found. Saving as GTX will not be available!
You can manually specify the location of AMD Compress's folder by creating
a file called amdcompress.txt in """ + os.path.dirname(__file__) + """
and putting the path to AMD Compress's folder within it.
Example: "C:\Program Files (x86)\AMDCompress\" (without quotes)""")


# We can only save using AMD Compress right now.
SavingAvailable = AmdCompressAvailable


def deswizzleRGBA8(data, w, h):
    """
    Swizzled RGBA8 -> unswizzled RGBA8
    """
    try:
        return _cAlgorithms.decodeRGBA8(w, h, data)
    except Exception: pass

    return _deswizzleRGBA8_py(data, w, h)


renderRGBA8 = deswizzleRGBA8


def _deswizzleRGBA8_py(data, w, h):
    """
    Swizzled RGBA8 -> unswizzled RGBA8
    Based on Wii U GTX Extractor.
    """
    output = bytearray(w * h * 4)

    for y in range(h):
        for x in range(w):
            pos = (y & ~15) * w
            pos ^= (x & 3)
            pos ^= (x & 4) << 1
            pos ^= (x & 8) << 3
            pos ^= (x & ~7) << 4
            pos ^= (y & 0xE) << 3
            pos ^= (y & 0x10) << 4
            pos ^= (y & 0x21) << 2
            pos *= 4

            toPos = (y * w + x) * 4
            output[toPos:toPos + 4] = data[pos:pos + 4]

    return bytes(output)


def swizzleRGBA8(data, w, h):
    """
    Unswizzled RGBA8 -> swizzled RGBA8
    """
    # This is only here for consistency with the deswizzle functions
    return _swizzleRGBA8_py(data, w, h)


def _swizzleRGBA8_py(data, w, h):
    """
    Unswizzled RGBA8 -> swizzled RGBA8
    Based on Wii U GTX Extractor.
    """
    output = bytearray(w * h * 4)

    for y in range(h):
        for x in range(w):
            toPos = (y & ~15) * w
            toPos ^= (x & 3)
            toPos ^= (x & 4) << 1
            toPos ^= (x & 8) << 3
            toPos ^= (x & ~7) << 4
            toPos ^= (y & 0xE) << 3
            toPos ^= (y & 0x10) << 4
            toPos ^= (y & 0x21) << 2
            toPos *= 4

            pos = (y * w + x) * 4
            output[toPos:toPos + 4] = data[pos:pos + 4]

    return bytes(output)


def renderBC3(data, w, h):
    """
    Swizzled BC3 -> unswizzled RGBA8
    """
    try:
        return _cAlgorithms.decodeBC3(w, h, data)
    except Exception: pass

    return _renderBC3_py(data, w, h)


def _renderBC3_py(data, w, h):
    """
    Swizzled BC3 -> unswizzled RGBA8
    Based on Wii U GTX Extractor.
    """
    work = deswizzleBC3(data, w, h)

    try:
        # AMDCompress is much faster than the pure-Python implementation,
        # but it isn't always available.
        return _renderBC3_AmdCompress(work, w, h)
    except Exception:
        raise
        # Slow Python fallback.

        output = bytearray(w * h * 4)

        for y in range(h):
            for x in range(w):
                outValue = _calculateRGBAFromBC3AtPosition(w, work, x, y, False)

                outputPos = (y * w + x) * 4
                output[outputPos:outputPos + 4] = outValue

        return bytes(output)


def swizzleBC3(data, w, h):
    """
    Standard BC3 -> GTX-swizzled BC3.
    This is the inverse of deswizzleBC3().
    """
    blobWidth = w // 4
    blobHeight = h // 4
    work = bytearray(w * h)

    for y in range(blobHeight):
        for x in range(blobWidth):
            toPos = ((y >> 4) * (blobWidth * 16)) & 0xFFFF
            toPos ^= (y & 1)
            toPos ^= (x & 7) << 1
            toPos ^= (x & 8) << 1
            toPos ^= (x & 8) << 2
            toPos ^= (x & 0x10) << 2
            toPos ^= (x & ~0x1F) << 4
            toPos ^= (y & 2) << 6
            toPos ^= (y & 4) << 6
            toPos ^= (y & 8) << 1
            toPos ^= (y & 0x10) << 2
            toPos ^= (y & 0x20)

            pos = (y * blobWidth + x) * 16
            toPos *= 16
            work[toPos:toPos + 16] = data[pos:pos + 16]

    return bytes(work)


def deswizzleBC3(data, w, h):
    """
    GTX-swizzled BC3 -> standard BC3.
    This is the inverse of swizzleBC3().
    """
    blobWidth = w // 4
    blobHeight = h // 4
    work = bytearray(w * h)

    for y in range(blobHeight):
        for x in range(blobWidth):
            pos = ((y >> 4) * (blobWidth * 16)) & 0xFFFF
            pos ^= (y & 1)
            pos ^= (x & 7) << 1
            pos ^= (x & 8) << 1
            pos ^= (x & 8) << 2
            pos ^= (x & 0x10) << 2
            pos ^= (x & ~0x1F) << 4
            pos ^= (y & 2) << 6
            pos ^= (y & 4) << 6
            pos ^= (y & 8) << 1
            pos ^= (y & 0x10) << 2
            pos ^= (y & 0x20)

            toPos = (y * blobWidth + x) * 16
            pos *= 16
            work[toPos:toPos + 16] = data[pos:pos + 16]

    return bytes(work)


def _calculateRGBAFromBC3AtPosition(width, pixdata, i, j, noalpha):
    """
    Fetches a RGBA texel from position (i, j) in a BC3 texture.
    Based on libtxc_dxtn.
    """
    pointer = ((width + 3) // 4 * (j // 4) + (i // 4)) * 16
    alpha0 = pixdata[pointer]
    alpha1 = pixdata[pointer + 1]

    bit_pos = ((j & 3) * 4 + (i & 3)) * 3
    acodelow = pixdata[pointer + 2 + bit_pos // 8]
    acodehigh = pixdata[pointer + 3 + bit_pos // 8]
    code = (acodelow >> (bit_pos & 0x07) |
        (acodehigh << (8 - (bit_pos & 0x07)))) & 0x07

    a, r, g, b = _calculateRGBFromDxtAtPosition(pixdata, pointer + 8, i & 3, j & 3, 2)

    if code == 0:
        a = alpha0
    elif code == 1:
        a = alpha1
    elif alpha0 > alpha1:
        a = (alpha0 * (8 - code) + (alpha1 * (code - 1))) // 7
    elif code < 6:
        a = (alpha0 * (6 - code) + (alpha1 * (code - 1))) // 5
    elif code == 6:
        a = 0
    else:
        a = 255

    return bytes([r, g, b, 255 if noalpha else a])


def _calculateRGBFromDxtAtPosition(pixdata, pointer, i, j, dxt_type):
    """
    Fetches a RGB texel from position (i, j) in a DXT1, DXT3 or DXT5 texture.
    Based on libtxc_dxtn.
    """
    color0 = pixdata[pointer] | (pixdata[pointer + 1] << 8)
    color1 = pixdata[pointer + 2] | (pixdata[pointer + 3] << 8)
    bits = (pixdata[pointer + 4] | (pixdata[pointer + 5] << 8) |
        (pixdata[pointer + 6] << 16) | (pixdata[pointer + 7] << 24))

    bit_pos = 2 * (j * 4 + i)
    code = (bits >> bit_pos) & 3

    a = 255

    # Expand r0, b0, r1 and g1 from 5 to 8 bits, and g0 and g1 from 6 to 8 bits.
    r0Expanded = int((color0 >> 11) * 0xFF / 0x1F)
    g0Expanded = int(((color0 >> 5) & 0x3F) * 0xFF / 0x3F)
    b0Expanded = int((color0 & 0x1F) * 0xFF / 0x1F)
    r1Expanded = int((color1 >> 11) * 0xFF / 0x1F)
    g1Expanded = int(((color1 >> 5) & 0x3F) * 0xFF / 0x3F)
    b1Expanded = int((color1 & 0x1F) * 0xFF / 0x1F)

    if code == 0:
        r = r0Expanded
        g = g0Expanded
        b = b0Expanded
    elif code == 1:
        r = r1Expanded
        g = g1Expanded
        b = b1Expanded
    elif code == 2:
        if (dxt_type > 1) or (color0 > color1):
            r = (r0Expanded * 2 + r1Expanded) // 3
            g = (g0Expanded * 2 + g1Expanded) // 3
            b = (b0Expanded * 2 + b1Expanded) // 3
        else:
            r = (r0Expanded + r1Expanded) // 2
            g = (g0Expanded + g1Expanded) // 2
            b = (b0Expanded + b1Expanded) // 2
    elif code == 3:
        if (dxt_type > 1) or (color0 > color1):
            r = (r0Expanded + r1Expanded * 2) // 3
            g = (g0Expanded + g1Expanded * 2) // 3
            b = (b0Expanded + b1Expanded * 2) // 3
        else:
            r, g, b = 0, 0, 0
            if dxt_type == 1: a = 0
    return a, r, g, b


def _renderBC3_AmdCompress(bc3, w, h):
    """
    Unswizzled BC3 -> unswizzled RGBA8, powered by AMD Compress:
    http://developer.amd.com/tools-and-sdks/graphics-development/amdcompress/
    """
    if not AmdCompressAvailable:
        raise RuntimeError('AMD Compress could not be found')

    # Put together a DDS

    heightwidthlength = struct.pack('<III', h, w, len(bc3))
    # Shamelessly splice together a DDS header so AMDCompress will accept this
    header = b'DDS |\0\0\0\7\x10\x08\0' + heightwidthlength + b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0 \0\0\0\4\0\0\0DXT5\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x10\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'
    assert len(header) == 0x80

    # AMD Compress can convert directly to PNG, but loading a PIL
    # Image while... loading a PIL image... causes issues for
    # whatever reason. So, strategy: instead, convert to another
    # DDS, but with the RGBA8 texture format. Then we can blindly
    # read whatever it gives us and call it a day.

    # AMDCompressCLI requires that the cwd be its own folder. Sigh.
    tempIn = os.path.abspath(TEMP_FILE_NAME + '.dds')
    tempOut = os.path.abspath(TEMP_FILE_NAME + '2.dds')

    with open(tempIn, 'wb') as f:
        f.write(header + bc3)

    origcwd = os.getcwd()
    os.chdir(AmdCompressFolder)

    with subprocess.Popen(
        [
            'AMDCompressCLI.exe',
            '-fd ARGB_8888',
            '-nomipmap',
            tempIn,
            tempOut,
        ],
        stdout=_common.getDevNull(),
        ) as proc:

        proc.communicate() # lets us wait for AMDCompress to finish

    os.chdir(origcwd)

    with open(tempOut, 'rb') as f:
        rgba = f.read()[0x80:] # strip DDS header

    os.remove(tempIn)
    os.remove(tempOut)

    return rgba


def encodeBC3(image):
    """
    Convert an image to a bytestring of BC3 data.
    Image -> unswizzled BC3
    """
    try:
        return _encodeBC3_AmdCompress(image)
    except Exception:
        return _encodeBC3_py(image)


def _encodeBC3_AmdCompress(image):
    """
    Encode BC3 data using AMDCompress
    http://developer.amd.com/tools-and-sdks/graphics-development/amdcompress/
    """
    if not AmdCompressAvailable:
        raise RuntimeError('AMD Compress could not be found')

    # Pick file paths
    tempIn = os.path.abspath(TEMP_FILE_NAME + '.png')
    tempOut = os.path.abspath(TEMP_FILE_NAME + '.dds')

    # Make the PNG
    image.save(tempIn)

    # Change directory to AMD Compress's folder
    origcwd = os.getcwd()
    os.chdir(AmdCompressFolder)

    with subprocess.Popen(
        [
            'AMDCompressCLI.exe',
            '-fd',
            'BC3',
            '-nomipmap',
            tempIn,
            tempOut,
        ],
        stdout=_common.getDevNull(),
        ) as proc:

        proc.communicate() # lets us wait for AMDCompress to finish

    os.chdir(origcwd)

    with open(tempOut, 'rb') as f:
        data = f.read()

    type_ = data[0x54:0x58].decode('latin-1')
    if type_ != 'DXT5':
        raise RuntimeError('AMD Compress failed to produce BC3 output -- it instead gave "%s".' % type_)
    bc3 = data[0x80:] # strip DDS header

    os.remove(tempIn)
    os.remove(tempOut)

    return bc3


def _encodeBC3_py(image):
    """
    Encode BC3 data in pure Python
    """
    raise NotImplementedError('BC3 cannot be encoded in pure Python yet. Sorry! Try installing AMD Compress.')
