
import io
import enum
import json
import os
import os.path
import struct

from PIL import Image

from . import _common
from . import Object
from . import Sarc
from . import Texture
from . import Tile


class TilesetFormat(enum.Enum):
    """
    Formats a tileset can be saved to.
    """
    RGBA8 = 1
    BC3 = 2


class TilesetSizeError(Exception):
    """
    The tileset cannot hold all of the objects requested.
    """
    pass


def loadAll(tileset0, tileset1, tileset2, tileset3):
    """
    Load a set of tilesets together. Since tilesets are able
    to reference each other, you should use this function
    instead of load() whenever possible, to avoid edge cases.
    """

    # Load the data from each tileset and stuff it into each of these lists.
    # It's done this way because any of the tilesets can be None.

    objidxs = [b''] * 4
    objstrs = [b''] * 4
    objinfo = [b'{}'] * 4
    tiles = [None] * 256 * 4

    if tileset0 is not None:
        objidxs[0], objstrs[0], tiles[:256], objinfo[0] = _loadTilesetArchiveData(tileset0)
    if tileset1 is not None:
        objidxs[1], objstrs[1], tiles[256:512], objinfo[1] = _loadTilesetArchiveData(tileset1)
    if tileset2 is not None:
        objidxs[2], objstrs[2], tiles[512:768], objinfo[2] = _loadTilesetArchiveData(tileset2)
    if tileset3 is not None:
        objidxs[3], objstrs[3], tiles[768:1024], objinfo[3] = _loadTilesetArchiveData(tileset3)

    # Load the objects for each tileset
    indexstruct = struct.Struct('>HBBH')
    objectsPerTileset = [[], [], [], []]
    for tsNum in range(4):
        objcount = len(objidxs[tsNum]) // 6
        for i in range(objcount):
            off, w, h, rand = indexstruct.unpack_from(objidxs[tsNum], i * 6)
            objectsPerTileset[tsNum].append(Object.Object.fromRetail(
                _breakOffEnd(objstrs[tsNum][off:]),
                w, h, (rand >> 4) & 1, (rand >> 5) & 1, rand & 0xF,
                tiles,
                name=objinfo[tsNum].get(i, None)
                ))

    return objectsPerTileset


def load(data):
    """
    Retail tileset SARC data -> list of objects
    Please use loadAll() instead if possible, as it handles edge cases
    more correctly!
    """

    objidxs, objstrs, tiles, info = _loadTilesetArchiveData(data)
    tiles *= 4 # Apply the tiles loaded to all 4 slots. This will
               # allow the tileset to load properly, no matter what
               # slot it is supposed to be in. That is, UNLESS it
               # references tiles outside of itself. In that case,
               # those tiles will be incorrect. This is why you're
               # supposed to use loadAll() and not load().

    objects = []
    objcount = len(objidxs) // 6
    indexstruct = struct.Struct('>HBBH')
    for i in range(objcount):
        off, w, h, rand = indexstruct.unpack_from(objidxs, i * 6)
        objects.append(Object.Object.fromRetail(
            _breakOffEnd(objstrs[off:]),
            w, h, (rand >> 4) & 1, (rand >> 5) & 1, rand & 0xF,
            tiles,
            guessTilesetNum = True, # Load in lenient mode (unnecessary due to our
                # tile-list multiplication, but will supress incorrect warnings)
            name=info.get(i, None)
            ))

    return objects


def _loadTilesetArchiveData(data):
    """
    Extract relevant tileset data. This exists to avoid duplicate
    code in loadAll() and load().
    """

    contents = Sarc.load(data)

    # Extract required files from the archive

    gtximg = None  # BG_tex/Pa****.gtx          The "Pa" isn't strictly required, but if
    gtxnml = None  # BG_tex/Pa****_nml.gtx      it's omitted, you could accidentally load
    colls = None   # BG_chk/d_bgchk_****.bin    animation data instead. Which is bad.
    objidxs = None # BG_unt/****_hd.bin
    objstrs = None # BG_unt/****.bin
    info = '{}'    # BG_unt/info.json  (nsmbulib metadata -- optional)

    for key, value in contents.items():
        if key.startswith('BG_tex/Pa'):
            if key.endswith('_nml.gtx'):
                gtxnml = value
            elif key.endswith('.gtx'):
                gtximg = value
        elif key.startswith('BG_chk/d_bgchk_'):
            colls = value
        elif key.startswith('BG_unt/'):
            if key.endswith('_hd.bin'):
                objidxs = value
            elif key.endswith('.bin'):
                objstrs = value
            elif key == 'BG_unt/info.json':
                info = value.decode('utf-8')

    if gtximg is None:
        raise ValueError('Could not find tileset image.')
    elif gtxnml is None:
        raise ValueError('Could not find tileset normal map.')
    elif colls is None:
        raise ValueError('Could not find tileset collision data.')
    elif objidxs is None:
        raise ValueError('Could not find tileset object index data.')
    elif objstrs is None:
        raise ValueError('Could not find tileset object definition data.')

    # Parse tile images
    imgmain = Image.open(io.BytesIO(gtximg))
    imgnml = Image.open(io.BytesIO(gtxnml))
    tiles = Tile._makeTiles(imgmain, imgnml, colls)

    # Info
    infoDict = {id: name for id, name in json.loads(info)}

    return objidxs, objstrs, tiles, infoDict


def _breakOffEnd(lytstr):
    """
    Break off extra object strings after this one
    """
    # This works because the iterator quits when it hits the end
    # of the object string.
    return b''.join([step.data for step in Object.iterLayoutStr(lytstr)])


def saveAll(objects0=None, objects1=None, objects2=None, objects3=None):
    """
    Four lists of objects -> four bytestrings containing retail tileset SARC data
    """
    raise NotImplementedError('This will be implemented later...')


def save(objects, name, slot=None, *, format=None):
    """
    List of objects -> retail tileset SARC data
    The `name` argument lets you choose an internal name for the tileset(s).
    (Don't add Pa*_ -- that will be prepended automatically.)
    If `slot` is `None`, the return value will be a list of tileset datas
        (beginning with Pa1).
    If `slot` is an int in `(0, 1, 2, 3)`, the return value will be a single
        `bytes` object.
    By default, Pa0 tilesets will be saved as RGBA8 and Pa1/2/3 tilesets
    will be saved as BC3. You can override this behavior with the
    `format` argument. (Pass it a member of the `TilesetFormat` enum in this
    module.)
    """
    # All right.

    # First, we need to throw away as many tiles as we possibly can.
    tiles, fromIdxs = _getMinimalTilesFromObjects(objects)

    # The game requires that there be at least one tileset per level
    if not tiles:
        tiles.append(None)

    # Next, we need to get the raw image data for each tile.
    # We use a helper function to do so.
    if format is None:
        format = TilesetFormat.RGBA8 if slot == 0 else TilesetFormat.BC3
    tilesRawData = Tile._getRawDataForTiles(tiles, format)

    # Quick checks here so we don't waste time and then throw an exception later
    if slot is not None and len(tilesRawData) > 256:
        raise TilesetSizeError('These objects cannot be fit into a single tileset slot.')
    if len(tilesRawData) > 768:
        raise TilesetSizeError('These objects cannot be fit into three tileset slots.')

    # All right. Now we assemble what we've got there into tileset images.
    tilesetImgGtxDatas = []
    tilesetNmlGtxDatas = []
    tilesetCollsDatas = []
    for tilesInThisTileset, tileObjsInThisTileset in zip(
            _common.grouper(tilesRawData, 256, fillvalue=(None, None, None, None)),
            _common.grouper(tiles, 256, fillvalue=None)
            ):

        # Put together the raw image/normal data
        allImgData = bytearray(1048576 if format is TilesetFormat.BC3 else 4194304)
        allNmlData = bytearray(1048576 if format is TilesetFormat.BC3 else 4194304)

        # Make blank mipmaps we will fill in in a minute
        allImgMipmaps = []
        allNmlMipmaps = []
        if format is TilesetFormat.BC3:
            for i in range(6):
                allImgMipmaps.append(bytearray(262144 // 4 ** i))
                allNmlMipmaps.append(bytearray(262144 // 4 ** i))

        # Add tiles to the raw image/normal data
        for idx, (tileImg, tileNml, tileImgMips, tileNmlMips) in enumerate(tilesInThisTileset):
            if tileImg is None: continue

            if format is TilesetFormat.BC3:
                for y in range(0, 64, 4):
                    for x in range(0, 64, 4):
                        i, j = (idx % 32) * 64 + x, (idx // 32) * 64 + y
                        pointerA = ((2048 + 3) // 4 * (j // 4) + (i // 4)) * 16
                        pointerB = ((64 + 3) // 4 * (y // 4) + (x // 4)) * 16
                        allImgData[pointerA:pointerA+16] = tileImg[pointerB:pointerB+16]
                        allNmlData[pointerA:pointerA+16] = tileNml[pointerB:pointerB+16]
                for mipIdx in range(6):
                    mipTileW = 32 >> mipIdx
                    for y in range(0, mipTileW, 4):
                        for x in range(0, mipTileW, 4):
                            i, j = (idx % 32) * mipTileW + x, (idx // 32) * mipTileW + y
                            pointerA = (((1024 >> mipIdx) + 3) // 4 * (j // 4) + (i // 4)) * 16
                            pointerB = ((mipTileW + 3) // 4 * (y // 4) + (x // 4)) * 16
                            allImgMipmaps[mipIdx][pointerA:pointerA+16] = tileImgMips[mipIdx][pointerB:pointerB+16]
                            allNmlMipmaps[mipIdx][pointerA:pointerA+16] = tileNmlMips[mipIdx][pointerB:pointerB+16]
            else:
                for row in range(64):
                    pointerA = (idx // 32) * 524288 + (idx % 32) + 256 + row * 8192
                    pointerB = row * 256
                    allImgData[pointerA:pointerA+256] = tileImg[pointerB:pointerB+256]
                    allNmlData[pointerA:pointerA+256] = tileNml[pointerB:pointerB+256]

                # RGBA8 tilesets don't have mipmaps for some reason.

        # OK, now we have the raw image/normal data ready to go.
        # We can use this handy function to add the proper headers and stuff:
        texFormat = Texture.Enums.GX2SurfaceFormat.UNORM_BC3 if format is TilesetFormat.BC3 else \
            Texture.Enums.GX2SurfaceFormat.UNORM_R8_G8_B8_A8
        j = 0
        for m in allImgMipmaps:
            j += len(m)

        imgGtx = Texture.makeGtx(texFormat, allImgData, 2048, 512, allImgMipmaps)
        nmlGtx = Texture.makeGtx(texFormat, allNmlData, 2048, 512, allNmlMipmaps)

        # Put those into the lists
        tilesetImgGtxDatas.append(imgGtx)
        tilesetNmlGtxDatas.append(nmlGtx)

        # Oh yeah, and the collisions.
        colls = b''
        for tile in tileObjsInThisTileset:
            if tile is not None:
                colls += tile.collisions
        colls += b'\0' * (2048 - len(colls))
        tilesetCollsDatas.append(colls)

    # Up next: make objects!
    objInfo = []
    layoutStrs = b''
    objIdxs = b''
    objIdxStruct = struct.Struct('>HBBH')
    for objIdx, obj in enumerate(objects):

        # Build up a layout string
        tilesSeen = []
        layoutStr = b''
        for step in obj.annotatedLayoutStr():
            if step.type == 'tile':
                if step.tile in tilesSeen:
                    tileNum = tilesSeen.index(step.tile)
                else:
                    tilesSeen.append(step.tile)
                    tileNum = len(tilesSeen) - 1
                from_ = fromIdxs[(objIdx, tileNum)]
                if from_ is None:
                    step.tileNum = step.tilesetNum = 0
                else:
                    step.tileNum = from_ % 256
                    step.tilesetNum = from_ // 256 + 1 # start with Pa1
            layoutStr += step.data

        offsetToLayoutStr = len(layoutStrs)
        layoutStrs += layoutStr + b'\xFF'

        # And now the header data
        rand = 0
        if obj.randomizeX: rand |= 16
        if obj.randomizeY: rand |= 32
        rand |= len(obj.randomReplacementTiles)
        objIdxs += objIdxStruct.pack(offsetToLayoutStr, obj.width, obj.height, rand)

        # And the OneTileset name, if it has one
        if obj.name:
            objInfo.append((objIdx, obj.name))

    # We can now put together the JSON with object info...
    objInfo = json.dumps(objInfo).encode('utf-8')

    # Then we put it all together into one or more SARCs.
    if slot is None:
        slots = [i+1 for i, _ in enumerate(tilesetImgGtxDatas)]
    else:
        slots = (slot,)
    first = True
    archives = []
    for slot_, img, nml, colls in zip(slots, tilesetImgGtxDatas, tilesetNmlGtxDatas, tilesetCollsDatas):
        files = {}

        # Images and collisions
        files['BG_tex/Pa%d_%s.gtx' % (slot_, name)] = img
        files['BG_tex/Pa%d_%s_nml.gtx' % (slot_, name)] = nml
        files['BG_chk/d_bgchk_Pa%d_%s.bin' % (slot_, name)] = colls

        # Objects
        if first:
            first = False
            tsetLayoutStrs = layoutStrs
            tsetObjIdxs = objIdxs
            tsetObjInfo = objInfo
        else:
            tsetLayoutStrs = b''
            tsetObjIdxs = b''
            tsetObjInfo = None
        files['BG_unt/Pa%d_%s.bin' % (slot_, name)] = tsetLayoutStrs
        files['BG_unt/Pa%d_%s_hd.bin' % (slot_, name)] = tsetObjIdxs
        if tsetObjInfo is not None:
            files['BG_unt/info.json'] = tsetObjInfo

        archives.append(Sarc.save(files, 0x2000))

    # Return time!
    return archives if slot is None else archives[0]


def tileCount(objects):
    """
    Return the number of tiles that would be used by saving these objects,
    after optimizations are applied. Remember, you can only fit 768 of them
    into Pa1/2/3!
    """
    return len(_getMinimalTilesFromObjects(objects)[0])


def _getMinimalTilesFromObjects(objects):
    """
    Return two things: a list containing all of the tiles needed by the
    objects, and a dict that you can use to connect them back to each object,
    which works like this:
    tiles, mapDict = _getMinimalTilesFromObjects(myObjects)
    for i, obj in enumerate(myObjects):
        for j, tile in enumerate(obj.allTiles):
            tileIdxInList = mapDict[(i, j)]
    Note that that index value may be None, indicating a blank tile that should
    be represented with Pa0 tile 0.
    """

    # This isn't too bad. We iterate over the objects and their allTiles-es,
    # and throw away any that are empty or match a tile already in the list.

    tiles = []
    fromIdxs = {}
    for i, obj in enumerate(objects):
        for j, tile in enumerate(obj.allTiles):

            myIdx = len(tiles)

            weDontWantThis = False
            if tile is None or tile.empty:
                weDontWantThis = True
                myIdx = None
            else:
                for i2, t2 in enumerate(tiles):
                    if t2 == tile:
                        weDontWantThis = True
                        myIdx = i2
                        break

            fromIdxs[(i, j)] = myIdx
            if not weDontWantThis:
                tiles.append(tile)


    # Then we return it.
    return tiles, fromIdxs


def loadFromNew(folder):
    """
    Folder path -> dict of objects and dict representing hierarchy
    Dict of objects: string (object name) -> Object instance
    How to parse the hierarchy:
        Just iterate over the dictionary keys at each level. Each
        represents a folder. Each value will be another dictionary
        you can parse recursively in the same way.
        EXCEPT: if one of the keys is '/'. (Chosen because it's an
        invalid folder name.) This points to a list of object names
        within this folder.
    If you don't care about where exactly each object is in the
    folder structure, the hierarchy can be ignored.
    """
    if not os.path.isdir(folder):
        raise ValueError('"%s" is not a folder.' % folder)

    objects = {}
    hierarchy = {} # For convenience

    def scanFolder(prependList, folder, outerLevelOfHierarchy, addThisFolder=True):
        nonlocal objects
        folderName = os.path.basename(folder)
        if addThisFolder:
            # += appends it in-place, causing issues
            prependList = prependList + [folderName]

        # Step 1: search for .colls/.png and .json/.objlyt
        collsAndPngs = []
        jsonAndObjlyts = []
        for itemName in os.listdir(folder):
            fullItemName = os.path.join(folder, itemName)
            if os.path.isdir(fullItemName) and not itemName.startswith('_'):
                outerLevelOfHierarchy[itemName] = {}
                scanFolder(prependList, fullItemName, outerLevelOfHierarchy[itemName])
            elif itemName.endswith('.json') and os.path.isfile(fullItemName[:-5] + '.objlyt'):
                jsonAndObjlyts.append(itemName[:-5])
            elif itemName.endswith('.colls') and os.path.isfile(fullItemName[:-6] + '.png'):
                collsAndPngs.append(itemName[:-6])

        # Step 2: load the .colls/.png files
        allTiles = {}
        for name in collsAndPngs:

            # Load collisions, the main image and (optionally) the normal map
            fullName = os.path.join(folder, name)
            with open(fullName + '.colls', 'rb') as f:
                collsData = f.read()
            imgmain, imgnml = Object._loadImgAndNml(fullName + '.png')

            # Create tiles
            allTiles[name] = Tile._makeTiles(imgmain, imgnml, collsData, padded=False)

        # Step 3: load the .json/.objlyt files, while
        # keeping track of the object names loaded
        outerLevelOfHierarchy['/'] = []
        objList = outerLevelOfHierarchy['/']
        for name in jsonAndObjlyts:

            # Ensure that we actually have the tiles for this object
            if name.count('.') != 1: continue
            imageName = name.split('.')[0]
            if imageName not in allTiles: continue
            objectName = name.split('.')[1]

            # Load files
            fullName = os.path.join(folder, name)
            with open(fullName + '.json', 'r', encoding='utf-8') as f:
                jsonData = f.read()
            with open(fullName + '.objlyt', 'rb') as f:
                lytData = f.read()

            # Create an object
            try:
                objects[objectName] = \
                    Object.Object.fromNew(objectName, lytData, jsonData, allTiles[imageName])
            except Exception:
                print('WARNING: Could not load "' + objectName + '" from ' + folder)
            objList.append(objectName)


        # If there are no objects at this level, we don't need the object list
        # in the hierarchy
        if not objList:
            del outerLevelOfHierarchy['/']

    scanFolder([], folder, hierarchy, False)

    return objects, hierarchy


def saveToNew(objects):
    """
    List of objects -> dictionary of "filename": filedata
    """
    raise NotImplementedError('This will be implemented later...')
