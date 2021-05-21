import io
import struct

from PIL import Image, ImageFile

from . import _gtxTextureFormats


GTX_FORMAT_RGBA8 = 0x1A
GTX_FORMAT_BC3 = 0x33

GFX2_MAGIC = b'Gfx2'
BLK_MAGIC = b'BLK{'


class GtxFile():
    """
    A class that contains basic info about a not-yet-decoded GXT file.
    Based on Wii U GTX Extractor.
    """
    width, height, padWidth, padHeight, format, dataSize = 0, 0, 0, 0, 0, 0
    data = b''

    def padSize(self):
        """
        Calculates the padded image size.
        """
        self.padWidth = (self.width + 63) & ~63
        self.padHeight = (self.height + 63) & ~63


class Gfx2HeaderStruct(struct.Struct):
    """
    Header struct for Gfx2.
    Based on Wii U GTX Extractor.
    """
    def __init__(self):
        super().__init__('>4s7I')
    def loadFrom(self, data, idx):
        (self.magic, self._04, self._08, self._0C,
        self._10, self._14, self._18, self._1C) = self.unpack_from(data, idx)


class BLKHeaderStruct(struct.Struct):
    """
    Header struct fot the BLK sections.
    Based on Wii U GTX Extractor.
    """
    def __init__(self):
        super().__init__('>4s7I')
    def loadFrom(self, data, idx):
        (self.magic, self._04, self._08, self._0C,
        self._10, self.sectionSize, self._18, self._1C) = self.unpack_from(data, idx)


class RawTexInfoStruct(struct.Struct):
    """
    Struct for raw tex info.
    Based on Wii U GTX Extractor.
    """
    def __init__(self):
        super().__init__('>39I')
    def loadFrom(self, data, idx):
        (self._0, self.width, self.height, self._C,
        self._10, self.format_, self._18, self._1C,
        self.sizeMaybe, self._24, self._28, self._2C,
        self._30, self._34, self._38, self._3C,
        self._40, self._44, self._48, self._4C,
        self._50, self._54, self._58, self._5C,
        self._60, self._64, self._68, self._6C,
        self._70, self._74, self._78, self._7C,
        self._80, self._84, self._88, self._8C,
        self._90, self._94, self._98) = self.unpack_from(data, idx)


class GtxImageFile(ImageFile.ImageFile):

    format = 'GTX'
    format_description = 'Nintendo Wii U GTX Texture'

    def _open(self):

        width, height, format = 0, 0, 0
        rawData = b''

        gfx2Header = self.fp.read(32)
        headStruct = Gfx2HeaderStruct()
        headStruct.loadFrom(gfx2Header, 0)
        if headStruct.magic != GFX2_MAGIC:
            raise ValueError('Not a GTX texture')

        idx = headStruct.size

        mipmapDataSplit = []

        # Parse each BLK section
        blkStruct = BLKHeaderStruct()
        rawTexInfoStruct = RawTexInfoStruct()
        while True:
            blkHeaderData = self.fp.read(blkStruct.size)

            if len(blkHeaderData) < blkStruct.size:
                break # EOF

            blkStruct.loadFrom(blkHeaderData, 0)

            if blkStruct.magic != BLK_MAGIC:
                raise ValueError('Wrong BLK section magic')

            if blkStruct._10 == 0x0B:
                # Raw texture info

                rawTexHeaderData = self.fp.read(rawTexInfoStruct.size)

                if len(rawTexHeaderData) < rawTexInfoStruct.size:
                    raise ValueError('Truncated BLK header')

                rawTexInfoStruct.loadFrom(rawTexHeaderData, 0)

                self._size = (rawTexInfoStruct.width, rawTexInfoStruct.height)
                format_ = rawTexInfoStruct.format_

            elif blkStruct._10 == 0x0C and not rawData:
                # Grab raw data

                rawData = self.fp.read(blkStruct.sectionSize)
                if len(rawData) < blkStruct.sectionSize:
                    raise ValueError('Truncated texture data')

            elif blkStruct._10 == 0x0D and not mipmapDataSplit:
                # Grab mipmap data

                mipmapData = self.fp.read(blkStruct.sectionSize)
                if len(mipmapData) < blkStruct.sectionSize:
                    raise ValueError('Truncated mipmap data')

                if mipmapData:
                    i = 0
                    sizeToGet = len(rawData) // 4
                    while sizeToGet >= 4:
                        mipmapDataSplit.append(mipmapData[i:i+sizeToGet])
                        i += sizeToGet
                        sizeToGet //= 4

            else:
                # Ignore.
                self.fp.read(blkStruct.sectionSize)

        # This is hardcoded because we're about to manually convert the
        # compressed texture to RGBA. PIL needs to know that what it's
        # looking at afterward will be RGBA.
        self.mode = 'RGBA'

        if format_ == GTX_FORMAT_RGBA8:
            decoded = _gtxTextureFormats.renderRGBA8(rawData, *self.size)
        elif format_ == GTX_FORMAT_BC3:
            decoded = _gtxTextureFormats.renderBC3(rawData, *self.size)
        else:
            # We should implement more of these sometime.
            raise NotImplementedError('Unsupported texture format: %X' % format)

        # This is magic. Don't ask me what it does. I don't know.
        self.tile = [
            ('raw', (0, 0) + self.size, 0, (self.mode, 0, 1))
        ]

        self.fp = io.BytesIO(decoded)

        # Annotate with the deswizzled BC3 data if we have it
        if format_ == GTX_FORMAT_BC3:
            self.bc3 = _gtxTextureFormats.deswizzleBC3(rawData, *self.size)
            if mipmapDataSplit:
                self.bc3Mipmaps = []
                for i, mip in enumerate(mipmapDataSplit):
                    self.bc3Mipmaps.append(_gtxTextureFormats.deswizzleBC3(
                        mip,
                        self.size[0] // (2 ** (i + 1)),
                        self.size[1] // (2 ** (i + 1)),
                        ))


def saveGtx(img, fp, filename, save_all=False):
    """
    Save an image to GTX format.
    """
    # keyword params are given in the img.encoderinfo dict

    compression = img.encoderinfo.get('compression', 'rgba8')
    numMipmaps = img.encoderinfo.get('num_mipmaps', 0)


def acceptGtx(f):
    """
    Quickly checks if this seems like a GTX or not
    """
    return f.startswith(GFX2_MAGIC)


Image.register_open(GtxImageFile.format, GtxImageFile, acceptGtx)
if _gtxTextureFormats.SavingAvailable:
    Image.register_save(GtxImageFile.format, saveGtx)
Image.register_extension(GtxImageFile.format, '.gtx')

# Image.register_open(GifImageFile.format, GifImageFile, _accept)
# Image.register_save(GifImageFile.format, _save)
# Image.register_save_all(GifImageFile.format, _save_all) # save-all animation frames
# Image.register_extension(GifImageFile.format, ".gif")
# Image.register_mime(GifImageFile.format, "image/gif")
