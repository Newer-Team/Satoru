import binascii

from PIL import Image

from . import _common
from . import Texture
from . import Tileset



class _TileUnavailableType:
    """
    A class with a single instance that can be used to refer to a tile
    that exists but is currently unavailable.
    """
    @staticmethod
    def __str__():
        return '<Tile unavailable>'
    __repr__ = __str__

TileUnavailable = _TileUnavailableType()
_TileUnavailableType.__new__ = lambda *args, **kwargs: None


class Tile:
    """
    A tileset tile, complete with collisions and a normal map!
    """
    _image = None
    _normal = None
    _collisions = None
    override = None
    _contentsOverrides = {}
    rawImageData = None
    rawImageMipmapData = None
    rawNormalData = None
    rawNormalMipmapData = None

    def __init__(self, image=None, normal=None, collisions=b'\0\0\0\0\0\0\0\0'):
        """
        Set the properties, or give them reasonable defaults
        """
        self._image = image
        self._normal = normal
        self._collisions = collisions
        self._contentsOverrides = {}


    @property
    def image(self):
        """
        Return a good value for the current image
        """
        if self._image:
            return self._image
        else:
            return Image.new('RGBA', (60, 60), DEFAULT_IMAGE_COLOR)
    @image.setter
    def image(self, image):
        self._image = image
        self.rawImageData = None
        self.rawImageMipmapData = None
    @image.deleter
    def image(self):
        self._image = None
        self.rawImageData = None
        self.rawImageMipmapData


    @property
    def normal(self):
        """
        Return a good value for the current normal map
        """
        if self._normal:
            return self._normal
        else:
            return Image.new('RGBA', (60, 60), DEFAULT_NORMAL_MAP_COLOR)
    @normal.setter
    def normal(self, normal):
        self._normal = normal
        self.rawNormalData = None
        self.rawNormalMipmapData = None
    @normal.deleter
    def normal(self):
        self._normal = None
        self.rawNormalData = None
        self.rawNormalMipmapData = None


    @property
    def collisions(self):
        return self._collisions
    @collisions.setter
    def collisions(self, value):
        if len(value) != 8:
            raise ValueError('Collisions data must have a length of 8')
        self._collisions = value
    @collisions.deleter
    def collisions(self):
        self._collisions = b'\0'


    @property
    def empty(self):
        """
        Is this tile entirely empty?
        """
        if self.collisions != b'\0' * 8:
            return False

        if self._image is None and self._normal is None:
            return True

        colors = self._image.getcolors()
        if colors is None:
            # More than 256 colors; this probably isn't empty
            return False

        # Check each colors used in the image; if it's not transparent,
        # this tile isn't empty
        for count, c in colors:
            alpha = c[3]
            if alpha > _common.MAX_EMPTY_ALPHA:
                return False

        return True


    def __eq__(self, other):
        """
        Are this tile and that tile equivalent?
        """
        if not isinstance(other, Tile): return False

        if self.collisions != other.collisions:
            return False

        if not _common.imagesIdentical(self.image, other.image):
            return False
        if not _common.imagesIdentical(self.normal, other.normal):
            return False

        # Made it!
        return True


    def reprImage(self, contentsValue=0, *, collisions=False, item=False):
        """
        Return an image that can be used as a user-friendly representation
        of this Tile. This might involve, for example, overlaying collision
        information on top of it, or an icon indicating the item contained
        inside a ?-block. The specific directives can be given as arguments.

        The `contentsValue` argument is only useful for item blocks, but
        it is good practice to always pass a value for it anyway.
        """
        if contentsValue in self._contentsOverrides:
            return self._contentsOverrides[contentsValue]

        if self.override is not None:
            return self.override

        return self.image


    def __str__(self):
        """
        Return a nice-looking string representing the Tile.
        """
        return '<Tile collisions=' + repr(self.collisions) + '>'


    def setContentsOverride(self, contentsValue, overrideImage):
        """
        Set an override image for this particular contents value
        """
        self._contentsOverrides[contentsValue] = overrideImage



def _makeTiles(mainImage, normalMap, collisions, *, padded=True):
    """
    Split apart the images given into Tile objects.
    If mainImage and normalMap have the `bc3` attribute, the tiles
    will be given their `rawImageData` and `rawNormalData` attributes
    to prevent quality loss. So, please don't do any operations on the
    images before sending them here, such that the `bc3` attributes would
    be removed or made inaccurate. (If you really need to do preprocessing,
    do `del mainImage.bc3` and `del normalMap.bc3` before calling this
    function.)
    The same also applies to the `.bc3Mipmaps` attribute.
    `padded` should be `True` if each tile in the images is padded to 64x64
    and `False` if each tile is 60x60 with no padding.
    """

    # Sanity check
    if mainImage.size != normalMap.size:
        raise ValueError('Image sizes must match.')

    tiles = []
    tileIdx = 0
    for tileYIdx in range(mainImage.height // (64 if padded else 60)):
        for tileXIdx in range(mainImage.width // (64 if padded else 60)):

            # Get the collisions for this tile
            tileColls = collisions[tileIdx * 8 : tileIdx * 8 + 8]

            # Figure out where in the images this tile is
            if padded:
                imgX, imgY = tileXIdx * 64 + 2, tileYIdx * 64 + 2
            else:
                imgX, imgY = tileXIdx * 60, tileYIdx * 60

            # Make the actual tile
            tile = Tile(
                mainImage.crop((imgX, imgY, imgX + 60, imgY + 60)),
                normalMap.crop((imgX, imgY, imgX + 60, imgY + 60)),
                tileColls,
                )

            # Add BC3 image/normal data to it if applicable
            if hasattr(mainImage, 'bc3') and hasattr(normalMap, 'bc3'):
                tile.rawImageData = bytearray(64 ** 2)
                tile.rawNormalData = bytearray(64 ** 2)
                for texelY in range(0, 64, 4):
                    for texelX in range(0, 64, 4):
                        i, j = tileXIdx * 64 + texelX, tileYIdx * 64 + texelY
                        pointerA = ((2048 + 3) // 4 * (j // 4) + (i // 4)) * 16
                        pointerB = ((64 + 3) // 4 * (texelY // 4) + (texelX // 4)) * 16
                        tile.rawImageData[pointerB:pointerB+16] = mainImage.bc3[pointerA:pointerA+16]
                        tile.rawNormalData[pointerB:pointerB+16] = normalMap.bc3[pointerA:pointerA+16]
            if hasattr(mainImage, 'bc3Mipmaps') and hasattr(normalMap, 'bc3Mipmaps'):
                tile.rawImageMipmapData = []
                tile.rawNormalMipmapData = []
                for i, (imageMipmap, normalMipmap) in enumerate(zip(mainImage.bc3Mipmaps, normalMap.bc3Mipmaps)):
                    tileImageMipmap = bytearray(1024 // (4 ** i))
                    tileNormalMipmap = bytearray(1024 // (4 ** i))
                    for texelY in range(0, 32 // (2 ** i), 4):
                        for texelX in range(0, 32 // (2 ** i), 4):
                            i_, j = tileXIdx * (32 // (2 ** i)) + texelX, tileYIdx * (32 // (2 ** i)) + texelY
                            pointerA = ((1024 // 2 ** i + 3) // 4 * (j // 4) + (i_ // 4)) * 16
                            pointerB = ((32 // 2 ** i + 3) // 4 * (texelY // 4) + (texelX // 4)) * 16
                            tileImageMipmap[pointerB:pointerB+16] = imageMipmap[pointerA:pointerA+16]
                            tileNormalMipmap[pointerB:pointerB+16] = normalMipmap[pointerA:pointerA+16]
                    tile.rawImageMipmapData.append(tileImageMipmap)
                    tile.rawNormalMipmapData.append(tileNormalMipmap)

            # Finish stuff for the loop
            tiles.append(tile)
            tileIdx += 1

    # And return the tiles!
    return tiles



def _getRawDataForTiles(tiles, format):
    """
    Return a list like this:
    [ # Return value list
        ( # This is a single tile
            mainImageData,
            normalImageData,
            [ # Main image mipmaps
                mipmap1,
                mipmap2,
                ... # Repeat for each mipmap
            ],
            [ # Normal map mipmaps
                mipmap1,
                mipmap2,
                ... # Repeat for each mipmap
            ]
        ),
        ... # Repeat for each tile
    ]
    Each data entry will be of the padded variety
    (that is, 64x64 for the main image, and 32x32,
    16x16, 8x8, etc. for the mipmaps).
    Use the `Tileset.TilesetFormat` enum for the `format`
    argument. Original image data will be preserved if
    possible.
    Note that RGBA8 tilesets do not have mipmaps, so
    the mipmap lists will be empty if that format is
    requested.
    """

    # We'll put BC3 data in here. If we don't have it available just yet,
    # we'll instead put an integer there which is an index into
    # imagesToConvertToBC3. Later we'll come back and replace that with
    # the generated BC3 data.
    retVal = []

    # We'll be collecting all the images we don't yet have BC3 copies
    # of in here.
    imagesToConvertToBC3 = []
    imagesConvertedToBC3 = []

    for tile in tiles:
        mainData = normalData = mainMipmapData = normalMipmapData = None
        if tile in (None, TileUnavailable):
            if format is Tileset.TilesetFormat.RGBA8:
                mainData = normalData = b'\0\0\0\0' * 64 * 64
                mainMipmapData, normalMipmapData = [], []
            else:
                mainData = normalData = b'\0' * 64 * 64
                mips = []
                for i in range(6):
                    mips.append(b'\0' * (32 >> i) ** 2)
                mainMipmapData, normalMipmapData = mips, list(mips)
        else:
            if format is Tileset.TilesetFormat.RGBA8:
                # RGBA8 is not a lossy format, so we don't have to
                # do anything unusual except add the padding.

                img, nml = addPadding(tile.image), addPadding(tile.normal)

                # NOTE: if the internal image formats are not RGBA8,
                # this will fail silently! If you know of a way of
                # ensuring that they're actually RGBA8, let me know.
                mainData = tile.image.tobytes()
                normalData = tile.normal.tobytes()
                mainMipmapData, normalMipmapData = [], []
            else:
                # BC3 is lossy. Let's use the original tile data
                # if we can.

                # Main image
                if tile.rawImageData:
                    mainData = tile.rawImageData
                else:
                    imagesToConvertToBC3.append(addPadding(tile.image))
                    mainData = len(imagesToConvertToBC3) - 1

                # Normal map
                if tile.rawNormalData:
                    normalData = tile.rawNormalData
                else:
                    imagesToConvertToBC3.append(addPadding(tile.normal))
                    normalData = len(imagesToConvertToBC3) - 1

                # Main image (mipmaps)
                if tile.rawImageMipmapData:
                    mainMipmapData = tile.rawImageMipmapData
                else:
                    padImg = addPadding(tile.image)
                    mainMipmapData = []
                    for i in range(6):
                        imagesToConvertToBC3.append(padImg.resize((32 >> i, 32 >> i), Image.LANCZOS))
                        mainMipmapData.append(len(imagesToConvertToBC3) - 1)

                # Normal map (mipmaps)
                if tile.rawNormalMipmapData:
                    normalMipmapData = tile.rawNormalMipmapData
                else:
                    padImg = addPadding(tile.normal)
                    normalMipmapData = []
                    for i in range(6):
                        imagesToConvertToBC3.append(padImg.resize((32 >> i, 32 >> i), Image.LANCZOS))
                        normalMipmapData.append(len(imagesToConvertToBC3) - 1)

        # Stuff that all into the retVal list
        retVal.append((mainData, normalData, mainMipmapData, normalMipmapData))

    # Now we convert a ton of images to BC3 in one swoop, for efficiency.
    if imagesToConvertToBC3:

        # Make the giant image.
        # Every image in the imagesToConvertToBC3 list will be 64x64 or smaller.
        # Thus, we will make a large image 32*64 pixels wide (32 tiles wide),
        # and put one image in each grid square. Will this leave lots of empty
        # space? Yes. Is there a simpler, better way? Probably, but I don't want
        # to figure it out right now.
        w = 32
        h = len(imagesToConvertToBC3) // 32 + 1
        megaImage = Image.new('RGBA', (w*64, h*64), (0,0,0,0))
        for i, img in enumerate(imagesToConvertToBC3):
            megaImage.paste(img, ((i % w) * 64, (i // w) * 64))

        # Convert image -> BC3
        allBC3 = Texture.encodeBC3(megaImage)

        # Get the BC3 data for each tile from that
        for idx, originalImage in enumerate(imagesToConvertToBC3):
            size = originalImage.size

            bc3 = bytearray(size[0] * size[1])
            for y in range(0, size[1], 4):
                for x in range(0, size[0], 4):
                    i, j = (idx % 32) * 64 + x, (idx // 32) * 64 + y
                    pointerA = ((2048 + 3) // 4 * (j // 4) + (i // 4)) * 16
                    pointerB = ((size[0] + 3) // 4 * (y // 4) + (x // 4)) * 16
                    bc3[pointerB:pointerB+16] = allBC3[pointerA:pointerA+16]
            imagesConvertedToBC3.append(bytes(bc3))


        # Now, splice that into retVal
        newRetVal = []
        for mainData, normalData, mainMipmapData, normalMipmapData in retVal:

            # Replace each thing with its entry in imagesConvertedToBC3 if needed
            if isinstance(mainData, int):
                mainData = imagesConvertedToBC3[mainData]
            if isinstance(normalData, int):
                normalData = imagesConvertedToBC3[normalData]
            for i, mip in enumerate(mainMipmapData):
                if isinstance(mip, int):
                    mainMipmapData[i] = imagesConvertedToBC3[mip]
            for i, mip in enumerate(normalMipmapData):
                if isinstance(mip, int):
                    normalMipmapData[i] = imagesConvertedToBC3[mip]

            newRetVal.append((mainData, normalData, mainMipmapData, normalMipmapData))

        retVal = newRetVal

    return retVal



def addPadding(image):
    """
    Add padding to a 60x60 image to make it 64x64.
    """
    if image.size != (60, 60):
        raise ValueError('addPadding() input image size must be 60x60, not %dx%d!' % image.size)

    new = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    new.paste(image, (2, 2))

    for i in range(60):

        # Top
        color = image.getpixel((i, 0))
        for p in (0, 1):
            new.putpixel((i+2, p), color)

        # Bottom
        color = image.getpixel((i, 59))
        for p in (62, 63):
            new.putpixel((i+2, p), color)

        # Left
        color = image.getpixel((0, i))
        for p in (0, 1):
            new.putpixel((p, i+2), color)

        # Right
        color = image.getpixel((59, i))
        for p in (62, 63):
            new.putpixel((p, i+2), color)

    # Upper-left corner
    color = image.getpixel((0, 0))
    for x in (0, 1):
        for y in (0, 1):
            new.putpixel((x, y), color)

    # Upper-right corner
    color = image.getpixel((59, 0))
    for x in (62, 63):
        for y in (0, 1):
            new.putpixel((x, y), color)

    # Lower-left corner
    color = image.getpixel((0, 59))
    for x in (0, 1):
        for y in (62, 63):
            new.putpixel((x, y), color)

    # Lower-right corner
    color = image.getpixel((59, 59))
    for x in (62, 63):
        for y in (62, 63):
            new.putpixel((x, y), color)

    # Return that
    return new



def tilesToImage(arr, *, useRepr=False, contentsValue=0):
    """
    Convert a 2D array of Tiles to a PIL Image.
    If useRepr is True and obj is not None, the tiles'
    reprImage(contentsValue)s will be used instead of their .image's.
    See the documentation for Tile.reprImage() for an explanation of
    contentsValue.
    """
    h = len(arr)
    w = len(arr[0]) if h > 0 else 0

    img = Image.new('RGBA', (w * 60, h * 60), (0, 0, 0, 0))

    y = 0
    for row in arr:
        x = 0
        for tile in row:
            if tile is not None:
                img.paste(tile.reprImage(contentsValue) if useRepr else tile.image, (x, y))
            x += 60
        y += 60

    return img
