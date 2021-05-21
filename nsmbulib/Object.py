import copy
import io
import json
import os.path
import struct
import warnings

from PIL import Image

from . import _common
from . import _objectLayout
from . import Tile


iterLayoutStr = _objectLayout.iterLayoutStr



def _loadImgAndNml(imgPath):
    """
    Load the PNG image at imgPath, and the normal if it exists (or else
    return a reasonable default).
    """
    img = Image.open(imgPath)
    nmlPath = imgPath[:-4] + '_nml.png'

    if os.path.isfile(nmlPath):
        nml = Image.open(nmlPath)
    else:
        nml = Image.new('RGBA', img.size, _common.DEFAULT_NORMAL_MAP_COLOR)

    return img, nml


class Object:
    """
    A tileset object!
    """

    class Role(_common.SortableEnum):
        """
        A sortable Enum that represents an object's role.

        The first 13 entries can be explained like so:

        Imagine a square land block with a hole in the middle, so that
        it looks like the following:
            XXXXXXXXXXXX
            XXXXXXXXXXXX
            XXXXXXXXXXXX
            XXXXXXXXXXXX
            XXXX    XXXX
            XXXX    XXXX
            XXXX    XXXX
            XXXX    XXXX
            XXXXXXXXXXXX
            XXXXXXXXXXXX
            XXXXXXXXXXXX
            XXXXXXXXXXXX
        (Every X there is a single, square tile. The entire block of
        land forms a square.)
        If this is given the proper tiles around all of the edges,
        displaying the roles would look like this:
            tl  t   t   t   t   t   t   t   t   tr
            l   m   m   m   m   m   m   m   m   r
            l   m   m   m   m   m   m   m   m   r
            l   m   m   itl b   b   itr m   m   r
            l   m   m   r           l   m   m   r
            l   m   m   r           l   m   m   r
            l   m   m   ibl t   t   ibr m   m   r
            l   m   m   m   m   m   m   m   m   r
            l   m   m   m   m   m   m   m   m   r
            bl  b   b   b   b   b   b   b   b   br
        The inner corners are the tricky part. Just follow that diagram
        and you'll be fine.

        The other entries are self-explanatory.
        """

        top = 't'
        middle = 'm'
        bottom = 'b'
        left = 'l'
        right = 'r'
        top_left = 'tl'
        top_right = 'tr'
        bottom_left = 'bl'
        bottom_right = 'br'
        inner_top_left = 'itl'
        inner_top_right = 'itr'
        inner_bottom_left = 'ibl'
        inner_bottom_right = 'ibr'
        top_slope = 'ts'
        bottom_slope = 'bs'
        other = 'o'
        unknown = '?'

        def __str__(self):
            return {
                self.top: 'top ground',
                self.middle: 'middle ground',
                self.bottom: 'ceiling',
                self.left: 'left wall',
                self.right: 'right wall',
                self.top_left: 'top-left corner',
                self.top_right: 'top-right corner',
                self.bottom_left: 'bottom-left corner',
                self.bottom_right: 'bottom-right corner',
                self.inner_top_left: 'inner top-left corner',
                self.inner_top_right: 'inner top-right corner',
                self.inner_bottom_left: 'inner bottom-left corner',
                self.inner_bottom_right: 'inner bottom-right corner',
                self.top_slope: 'top sloped ground',
                self.bottom_slope: 'ceiling slope',
                self.other: 'other',
                self.unknown: 'unknown',
            }[self]

    width = 1
    height = 1
    randomizeX = False
    randomizeY = False
    role = Role.unknown
    decorative = False
    name = ''
    description = ''
    _tiles = []
    randomReplacementTiles = []
    _layoutstr = b'\0\0\0'

    @classmethod
    def fromRetail(
            cls, layoutstr, w, h, randomizeX, randomizeY, randN, alltiles, *,
            guessTilesetNum=False, name=None):
        """
        Load this object from retail data. If guessTilesetNum is True,
        tiles will be loaded from other tileset slots if not found in
        the slot they are supposed to be in.
        """
        obj = cls()

        obj.width = w
        obj.height = h
        obj.randomizeX = randomizeX
        obj.randomizeY = randomizeY

        obj._tiles, obj.randomReplacementTiles, obj._layoutstr = cls._pickTiles(
            layoutstr, randN, alltiles, guessTilesetNum=guessTilesetNum)

        if name:
            obj.name = name

        return obj


    @classmethod
    def fromNew(cls, name, layoutstr, jsonData, alltiles):
        """
        Load this object from new-style data. Much easier than from
        retail! jsonData is a string containing the JSON data, not a
        dict or something.
        """
        obj = cls()

        jsonDict = json.loads(jsonData)

        obj.name = name
        obj.width = jsonDict['width']
        obj.height = jsonDict['height']
        obj.randomizeX = jsonDict.get('replace_x', False)
        obj.randomizeY = jsonDict.get('replace_y', False)
        obj.role = cls.Role(jsonDict.get('role', '?'))
        obj.decorative = jsonDict.get('decorative', False)
        obj.description = jsonDict.get('description', '')

        obj._tiles, _, obj._layoutstr = cls._pickTiles(
            layoutstr, 0, alltiles, forcePa1=True)
        obj.randomReplacementTiles = []
        for idx in jsonDict.get('replace', []):
            obj.randomReplacementTiles.append(alltiles[idx])

        return obj


    @classmethod
    def fromPathNew(cls, jsonPath):
        """
        Load this object from new-style data. jsonPath should be the
        path to the .json file for the object.
        """

        # Check the JSON path
        if os.path.basename(jsonPath).count('.') != 2:
            raise ValueError('.json filename does not have exactly two "."s')
        if not os.path.isfile(jsonPath):
            raise ValueError('.json file does not exist')

        # Check the OBJLYT path
        objlytPath = os.path.splitext(jsonPath)[0] + '.objlyt'
        if not os.path.isfile(objlytPath):
            raise ValueError('.objlyt file does not exist')

        # Check the PNG path
        pngPath = os.path.join(
            os.path.dirname(jsonPath),
            os.path.basename(jsonPath).split('.')[0]) + '.png'
        if not os.path.isfile(pngPath):
            raise ValueError('.png file does not exist')

        # Check the COLLS path
        collsPath = os.path.splitext(pngPath)[0] + '.colls'
        if not os.path.isfile(collsPath):
            raise ValueError('.colls file does not exist')

        # Load all the data
        with open(jsonPath, 'r', encoding='utf-8') as f:
            jsonData = f.read()
        with open(objlytPath, 'rb') as f:
            objlytData = f.read()
        img, nml = _loadImgAndNml(pngPath)
        with open(collsPath, 'rb') as f:
            collsData = f.read()

        # Get the image name
        objName = os.path.basename(jsonPath).split('.')[0]

        # Load tiles
        tiles = Tile._makeTiles(img, nml, collsData, padded=False)

        # Actually put together the object now
        return cls.fromNew(objName, objlytData, jsonData, tiles)


    @staticmethod
    def _pickTiles(
            layoutstr, randN, alltiles, *,
            guessTilesetNum=False, forcePa1=False):
        """
        Pick out only the tiles/collisions this object needs, in order.
        Blank spots are filled in with blank Tiles.
        """

        tiles = []

        first = -1

        newLayoutStr = b''
        for step in iterLayoutStr(layoutstr):
            if step.type == 'tile':

                if step.tileNum or step.tilesetNum:
                    # The tile *should* be at the following index
                    tileIdx = step.tilesetNum * 256 + step.tileNum
                    foundTileIdx = tileIdx
                    if forcePa1 and step.tilesetNum == 1: # hack for
                                                          # OneTileset
                        tileIdx = step.tileNum

                    if alltiles[tileIdx] is not None:
                        # We found it -- good.
                        tiles.append(alltiles[tileIdx])

                    elif guessTilesetNum:
                        # We didn't find it, but we're supposed to be
                        # lenient in our search. Look in the other three
                        # tileset slots, in order. If we still don't
                        # find it, call it unavailable.
                        for tsetOffset in (0, 256, 512, 768):
                            foundTileIdx = tsetOffset + step.tileNum
                            if alltiles[foundTileIdx] is not None:
                                tiles.append(alltiles[foundTileIdx])
                                break
                        else:
                            warnings.warn(
                                'Cannot find tile %s.' % hex(tileIdx))
                            tiles.append(Tile.TileUnavailable)

                    else:
                        # We didn't find it, and we weren't told to be
                        # lenient. Call it unavailable.
                        warnings.warn('Cannot find tile %s.' % hex(tileIdx))
                        tiles.append(Tile.TileUnavailable)

                    step.tileNum = len(tiles) - 1
                    step.tilesetNum = 1

                else:
                    tiles.append(None)
                    foundTileIdx = 0

                if first == -1: first = foundTileIdx

            newLayoutStr += step.data

        randomtiles = []
        for i in range(first + 1, first + randN):
            randomtiles.append(alltiles[i])

        # Copy all the tiles. Deepcopy fails for PIL Image objects
        # (https://github.com/python-pillow/Pillow/issues/1769), so we
        # use copy() instead.
        newtiles, newrandomtiles = [], []
        for t in tiles:
            if t is Tile.TileUnavailable:
                newtiles.append(t)
            else:
                newtiles.append(copy.copy(t))
        for t in randomtiles:
            if t is Tile.TileUnavailable:
                newrandomtiles.append(t)
            else:
                newrandomtiles.append(copy.copy(t))

        return newtiles, newrandomtiles, newLayoutStr


    def _getLayoutStrAt(
            self, start, *, rectangular=False, normalizeSlopes=False):
        """
        Return the layout string, starting at offset start. If
        `rectangular` is `True`, `(16 - self.width)` tiles are skipped
        after each row, creating a rectangular shape. If
        `normalizeSlopes` is `True`, and this object is a ceiling slope,
        the order of the rows will be reversed.

        start is relative to (0, 0) of Pa0. Each tileset has 256 tiles,
        so if you want Pa[n], add 256 * n to start.
        """

        flipY = normalizeSlopes and self._shouldFlipY()

        newStr = b''

        x = y = 0
        if flipY: y = self.height - 1
        for step in iterLayoutStr(self._layoutstr):
            if step.type == 'lf' and rectangular:
                x = 0
                y += -1 if flipY else 1
            elif step.type == 'tile':
                if rectangular:
                    rowAdjust = 16 * y
                else:
                    rowAdjust = self.width * y

                step.tileNum = (start + rowAdjust + x) & 0xFF
                step.tilesetNum = (start + rowAdjust + x) >> 8

                x += 1

            newStr += step.data

        return newStr


    def annotatedLayoutStr(self):
        """
        An iterator over this object's annotated layout string. This
        differs from a normal layout string in that the `TileStep`s have
        a `.tile` attribute instead of `.tileNum` and `.tilesetNum`.
        `.tile` will be `None` for empty tiles, and
        `Tile.TileUnavailable` for unavailable tiles.
        """
        for step in iterLayoutStr(self._getLayoutStrAt(1)):
            if step.type != 'tile':
                yield step
                continue
            step.tile = (self._tiles[step.tileNum - 1]
                         if step.tileNum > 0 else None)
            step.tileNum = step.tilesetNum = 0
            yield step


    def _shouldFlipY(self):
        """
        Should we flip rows? (Aka, is this a ceiling slope?)
        """
        for step in iterLayoutStr(self._layoutstr):
            if step.type == 'slope' and not step.floor:
                return True
        return False


    def render(self, w=None, h=None):
        """
        Render this tile for the given width and height. Returns a 2D
        array of `Tile.Tile`s and `None`s.
        """
        if w is None or w < 1: w = self.width
        if h is None or h < 1: h = self.height

        s = list(self.annotatedLayoutStr())
        arr = _objectLayout.renderObject(
            s, w, h,
            normalizeTileStep=(lambda tileStep: tileStep.tile)
            )

        # Ensure that the rendering is the requested size. If it's not,
        # something went wrong in _objectLayout.renderObject().
        assert len(arr) == h
        assert len(arr[0]) == w
        assert all(len(arr[0]) == len(row) for row in arr)

        return arr


    def __eq__(self, other):
        """
        Checks if this object and another object are identical objects.
        Note that this does not compare object names, since two
        differently-named objects that are otherwise identical should
        compare equal.
        """
        if not isinstance(other, Object): return False

        if self.width != other.width: return False
        if self.height != other.height: return False
        if self.randomizeX != other.randomizeX: return False
        if self.randomizeY != other.randomizeY: return False

        for t1, t2 in zip(self.allTiles, other.allTiles):
            if t1 != t2:
                return False

        return True


    def __lt__(self, other):
        """
        Implements an intuitive sort order for objects.
        Objects are first sorted by role (top, middle,
        bottom, left-wall, etc), then by decorative-or-not
        (non-decorative objects before decorative ones),
        then by size, then:
            if these are top ground slope objects:
                upslopes come before downslopes
            else if these are ceiling slope objects:
                downslopes come before upslopes
            else pass
        then finally, alphabetically by name.
        """

        # Compare by role
        if self.role != other.role:
            if self.role < other.role:
                return True
            return False

        # Compare by Decorative flag
        if self.decorative != other.decorative:
            if (not self.decorative) and other.decorative:
                return True
            return False

        # Compare by size
        selfSize = self.width * self.height
        otherSize = other.width * other.height
        if selfSize != otherSize:
            if selfSize < otherSize:
                return True
            return False

        # Compare by slope "outward" flag
        if self.role in (self.Role.top_slope, self.Role.bottom_slope):
            for selfStep in self.annotatedLayoutStr():
                if selfStep.type == 'slope':
                    for otherStep in other.annotatedLayoutStr():
                        if otherStep.type == 'slope':
                            # Now we can finally compare them.

                            if selfStep.outward != otherStep.outward:
                                if selfStep.outward and (not otherStep.outward):
                                    return True
                                return False

        # Compare by name
        return self.name < other.name


    @property
    def allTiles(self):
        """
        An iterator returning all tiles this object uses, in the order in
        which they appear in the layout string. Tiles that appear more than
        once are only yielded once; however, identical tiles are each yielded
        separately.
        Randomization tiles are yielded after all others.
        """
        yielded = []
        for step in self.annotatedLayoutStr():
            if step.type != 'tile': continue
            if step.tile in yielded: continue
            yielded.append(step.tile)
            yield step.tile
        for t in self.randomReplacementTiles:
            if t in yielded: continue
            yielded.append(t)
            yield t


    def __str__(self):
        """
        Return a nice-looking string representing this Object.
        """
        return '<Object: %dx%d "%s">' % (self.width, self.height, self.name)


    def asNewFormat(self):
        """
        Return this object as a dictionary of filename -> filedata
        pairs
        """
        files = {}

        # First, the image, normal map and collisions.
        # Much of the reason this is so complicated is because of NSMBU Pa1_7-37_1.

        flipY = self._shouldFlipY()

        # Add to the width of the object if there are random replacements we need to put there
        actualW, actualH = self.width, self.height
        addrandomizeY = not self.randomizeX # If we only randomize vertically, this is probably a wall
                                  # object, so let's be nice and arrange the replacements
                                  # vertically, too :)
                                  # Also, check "not randomizeX" instead of "randomizeY" because fill tiles
                                  # will have both set, and we prefer those to remain horizontal.
        if len(self.randomReplacementTiles) > 0:
            if addrandomizeY:
                actualH += len(self.randomReplacementTiles) - 1
            else:
                actualW += len(self.randomReplacementTiles) - 1

        img = Image.new('RGBA', (actualW * 60, actualH * 60), _common.DEFAULT_IMAGE_COLOR)
        nml = Image.new('RGBA', (actualW * 60, actualH * 60), _common.DEFAULT_NORMAL_MAP_COLOR)
        mask = Image.new('1', (60, 60), 'white')

        # Find the actual number of tiles in each line
        lineWidths = [0] # ignoring flipY
        for step in iterLayoutStr(self._layoutstr):
            if step.type == 'lf':
                lineWidths.append(0)
            elif step.type == 'tile':
                lineWidths[-1] += 1
        if lineWidths[-1] == 0: lineWidths = lineWidths[:-1]

        actualTiles = []
        actualColls = []
        for a in range(actualH): # We can't do [...] * actualH because we get duplicate references
            actualColls.append([b'\0' * 8] * actualW)
        actualLayoutStr = b''

        x = y = i = 0
        weAlreadyAdjustedForRepeatDuringThisRow = False
        for step in iterLayoutStr(self._layoutstr):
            if step.type == 'lf':
                x = 0
                y += 1
                weAlreadyAdjustedForRepeatDuringThisRow = False
            elif step.type == 'tile':
                actualY = y
                if flipY: actualY = self.height - y - 1

                if self._tiles[i] is not None and not self._tiles[i].empty:
                    img.paste(self._tiles[i].image, (x * 60, actualY * 60), mask)
                    nml.paste(self._tiles[i].normal, (x * 60, actualY * 60), mask)
                    actualColls[actualY][x] = self._tiles[i].collisions

                step.tileNum = actualY * self.width + x
                step.tilesetNum = 1 # (0, 0) would be ambiguous otherwise

                if step.repeatX and not weAlreadyAdjustedForRepeatDuringThisRow:
                    x += self.width - lineWidths[y]
                    weAlreadyAdjustedForRepeatDuringThisRow = True

                x += 1
                i += 1

            actualLayoutStr += step.data

        i = 0
        randRepls = []
        if addrandomizeY:
            for y in range(self.height, self.height + len(self.randomReplacementTiles)):
                img.paste(self.randomReplacementTiles[i].image, (0, y * 60 - 60), mask)
                nml.paste(self.randomReplacementTiles[i].normal, (0, y * 60 - 60), mask)
                actualColls[y - 1][0] = self.randomReplacementTiles[i].collisions
                randRepls.append(actualW * (y - 1))
                i += 1
        else:
            for x in range(self.width, self.width + len(self.randomReplacementTiles)):
                img.paste(self.randomReplacementTiles[i].image, (x * 60 - 60, 0), mask)
                nml.paste(self.randomReplacementTiles[i].normal, (x * 60 - 60, 0), mask)
                actualColls[0][x - 1] = self.randomReplacementTiles[i].collisions
                randRepls.append(x - 1)
                i += 1

        randRepls = randRepls[1:] # The first replacement is the tile itself

        # Image -> bytes (PNG)
        imgPngArr = io.BytesIO()
        nmlPngArr = io.BytesIO()
        img.save(imgPngArr, format='PNG')
        nml.save(nmlPngArr, format='PNG')
        imgPng = imgPngArr.getvalue()
        nmlPng = nmlPngArr.getvalue()

        # Now, the collisions
        colls = b''.join([b''.join(row) for row in actualColls])

        # And, finally, the JSON
        j = {
            'width': self.width,
            'height': self.height,
            }
        if self.randomizeX:
            j['replace_x'] = True
        if self.randomizeY:
            j['replace_y'] = True
        if randRepls:
            j['replace'] = randRepls
        if self.role:
            j['role'] = self.role.value
        if self.decorative:
            j['decorative'] = True
        if self.description:
            j['description'] = self.description

        j = json.dumps(j).encode('utf-8')

        # Return the files
        name = self.name if self.name else 'object'
        return {
            name + '.png': imgPng,
            name + '_nml.png': nmlPng,
            name + '.colls': colls,
            name + '.' + name + '.objlyt': actualLayoutStr,
            name + '.' + name + '.json': j,
        }


# Aliases
fromPathNew = Object.fromPathNew
