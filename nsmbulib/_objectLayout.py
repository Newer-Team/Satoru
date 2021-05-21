
import struct


EMPTY_TILE_VALUE = None



class _LayoutStrStep:
    # dummy ABC
    type = None


class _LinefeedStep(_LayoutStrStep):
    type = 'lf'
    data = b'\xFE'


class _TileStep(_LayoutStrStep):
    type = 'tile'
    def __init__(self, data):
        # Three bytes:
        #    Repeat: Bitfield (0000 00YX)
        #        Y: Y-repeat
        #        X: X-repeat
        #    Tilenum: Tile number within this tileset
        #    Other: Bitfield (PPPP PPNN)
        #        P: Parameter (item held)
        #        N: Tileset number (Pa_)
        self._value1, self.tileNum, self._value3 = data

    @property
    def repeatX(self):
        return self._value1 & 1
    @repeatX.setter
    def repeatX(self, value):
        if value:
            self._value1 |= 1
        else:
            self._value1 &= ~1

    @property
    def repeatY(self):
        return (self._value1 >> 1) & 1
    @repeatY.setter
    def repeatY(self, value):
        if value:
            self._value1 |= 2
        else:
            self._value1 &= ~2

    @property
    def parameter(self):
        return self._value3 >> 2
    @parameter.setter
    def parameter(self, value):
        self._value3 = (value << 2) | (self._value3 & 3)

    @property
    def tilesetNum(self):
        return self._value3 & 3
    @tilesetNum.setter
    def tilesetNum(self, value):
        self._value3 = (self._value3 & ~3) | value

    @property
    def data(self):
        if not 0 <= self._value1 <= 0xFF:
            raise ValueError('Byte 1 is out of range')
        if not 0 <= self.tileNum <= 0xFF:
            raise ValueError('Byte 2 is out of range')
        if not 0 <= self._value3 <= 0xFF:
            raise ValueError('Byte 3 is out of range')
        return struct.pack('>3B', self._value1, self.tileNum, self._value3)


class _SlopeStep(_LayoutStrStep):
    type = 'slope'
    def __init__(self, value):

        # One of these comes at the beginning of the "main" and "sub" rows
        # of slope objects.
        # 0b100A0BCD
        # A (self.sub): Identifies this row as the part that will be adjacent to the next "main" part
        # B (self.main): Identifies this row as the part with the actual slope
        # C (self.floor): 0 = floor slope; 1 = ceiling slope
        # D (self.outward): 0 for slopes that go outward as you go to the right
        # Leading bit identifies this as a slope step.
        # Other bits appear to be unused, though at least one of them must be required to be 0
        # to distinguish this step from LF and end-of-object steps.

        # self.floor and self.outward are negated for the purposes of this API.

        self._value = value

    @property
    def sub(self):
        return (self._value >> 4) & 1
    @sub.setter
    def sub(self, value):
        if value:
            self._value |= 16
        else:
            self.value &= ~16

    @property
    def main(self):
        return (self._value >> 2) & 1
    @main.setter
    def main(self, value):
        if value:
            self._value |= 4
        else:
            self._value &= ~4

    @property
    def floor(self):
        return not ((self._value >> 1) & 1)
    @floor.setter
    def floor(self, value):
        if not value:
            self._value |= 2
        else:
            self._value &= ~2

    @property
    def outward(self):
        return not (self._value & 1)
    @outward.setter
    def outward(self, value):
        if not value:
            self._value |= 1
        else:
            self._value &= ~1

    @property
    def data(self):
        return struct.pack('>B', self._value)


def iterLayoutStr(layoutStr):
    """
    Iterator over a layout bytestring, returning LayoutStrSteps for each steps.
    It's guaranteed that iterating over a layout bytestring and putting together
    step.data for each step will be identical to the original.
    """
    off = 0
    while off < len(layoutStr):
        next_ = layoutStr[off]

        if next_ == 0xFF: # End-of-object
            return
        elif next_ == 0xFE: # EOL
            yield _LinefeedStep()
        elif next_ & 0x80:
            # Slope
            yield _SlopeStep(next_)
        else:
            # Tile (3 bytes)
            yield _TileStep(layoutStr[off:off+3])
            off += 2
        off += 1


def renderObject(
        layoutStr, width, height, *,
        fullslope=False,
        normalizeTileStep=(lambda tileStep: tileStep.tilesetNum * 256 + tileStep.tileNum)
        ):
    """
    Render a tileset object into an array
    """

    if layoutStr[0].type == 'slope':
        return _renderDiagonalObject(layoutStr, width, height, fullslope, normalizeTileStep)

    # Identify repeating rows with respect to Y

    repeatExists = False
    thisRowRepeats = False
    rowsBeforeRepeat = []
    rowsInRepeat = []
    rowsAfterRepeat = []

    currentRow = []
    for step in layoutStr:
        if step.type == 'lf':
            if thisRowRepeats:
                rowsInRepeat.append(currentRow)
            elif not repeatExists:
                rowsBeforeRepeat.append(currentRow)
            else:
                rowsAfterRepeat.append(currentRow)
            currentRow = []
            thisRowRepeats = False
        else:
            if step.repeatY:
                repeatExists = True
                thisRowRepeats = True
            currentRow.append(step)

    # _render

    dest = []
    if not rowsInRepeat:
        # No Y-repeating
        for y in range(height):
            dest.append(_renderStandardRow(rowsBeforeRepeat[y % len(rowsBeforeRepeat)], width, normalizeTileStep))
    else:
        # Y-repeating
        for y in range(height):
            if y < len(rowsBeforeRepeat):
                dest.append(_renderStandardRow(rowsBeforeRepeat[y], width, normalizeTileStep))
            elif y >= height - len(rowsAfterRepeat):
                dest.append(_renderStandardRow(rowsAfterRepeat[y - height + len(rowsAfterRepeat)], width, normalizeTileStep))
            else:
                dest.append(_renderStandardRow(rowsInRepeat[(y - len(rowsBeforeRepeat)) % len(rowsInRepeat)], width, normalizeTileStep))

    return dest


def _renderStandardRow(steps, width, normalizeTileStep):
    """
    _render a row from an object
    """

    # Identify repeating steps

    repeatExists = False
    stepsBeforeRepeat = []
    stepsInRepeat = []
    stepsAfterRepeat = []

    for step in steps:
        if step.type != 'tile':
            continue

        if step.repeatX:
            repeatExists = True
            stepsInRepeat.append(step)
        elif not repeatExists:
            stepsBeforeRepeat.append(step)
        else:
            stepsAfterRepeat.append(step)

    # _render

    dest = []
    if not stepsInRepeat:
        # No X-repeating
        for x in range(width):
            dest.append(normalizeTileStep(stepsBeforeRepeat[x % len(stepsBeforeRepeat)]))
    else:
        # X-repeating
        for x in range(width):
            if x < len(stepsBeforeRepeat):
                dest.append(normalizeTileStep(stepsBeforeRepeat[x]))
            elif x >= width - len(stepsAfterRepeat):
                dest.append(normalizeTileStep(stepsAfterRepeat[x - width + len(stepsAfterRepeat)]))
            else:
                dest.append(normalizeTileStep(stepsInRepeat[(x - len(stepsBeforeRepeat)) % len(stepsInRepeat)]))

    return dest


def _renderDiagonalObject(layoutStr, width, height, fullslope, normalizeTileStep):
    """
    _render a diagonal object
    """

    # Get sections
    mainBlock, subBlock = _getSlopeSections(layoutStr, normalizeTileStep)

    # Get direction
    slopeStep = layoutStr[0]
    outward, floor = slopeStep.outward, slopeStep.floor

    # Decide on the amount to draw by seeing how much we can fit in each direction
    if fullslope:
        drawAmount = max(height // len(mainBlock), width // len(mainBlock[0]))
    else:
        drawAmount = min(height // len(mainBlock), width // len(mainBlock[0]))

    # If it's not going left and not going down:
    if outward and floor:
        # Slope going from SW => NE
        # Start off at the bottom left
        x = 0
        y = height - len(mainBlock) - (0 if subBlock is None else len(subBlock))
        xi = len(mainBlock[0])
        yi = -len(mainBlock)

    # ... and if it's going left and not going down:
    elif not outward and floor:
        # Slope going from SE => NW
        # Start off at the top left
        x = 0
        y = 0
        xi = len(mainBlock[0])
        yi = len(mainBlock)

    # ... and if it's not going left but it's going down:
    elif outward and not floor:
        # Slope going from NW => SE
        # Start off at the top left
        x = 0
        y = (0 if subBlock is None else len(subBlock))
        xi = len(mainBlock[0])
        yi = len(mainBlock)

    # ... and finally, if it's going left and going down:
    else:
        # Slope going from SW => NE
        # Start off at the bottom left
        x = 0
        y = height - len(mainBlock)
        xi = len(mainBlock[0])
        yi = -len(mainBlock)


    # Create a dest and initialize it to empty tiles
    dest = []
    for _ in range(height):
        dest.append([])
        for _ in range(width):
            dest[-1].append(EMPTY_TILE_VALUE)

    # Finally, draw it
    for i in range(drawAmount):
        _putObjectArray(dest, x, y, mainBlock, width, height)
        if subBlock is not None:
            xb = x
            if not outward: xb = x + len(mainBlock[0]) - len(subBlock[0])
            if not floor:
                _putObjectArray(dest, xb, y - len(subBlock), subBlock, width, height)
            else:
                _putObjectArray(dest, xb, y + len(mainBlock), subBlock, width, height)
        x += xi
        y += yi

    return dest



def _getSlopeSections(layoutStr, normalizeTileStep):
    """
    Sorts the slope data into sections
    """
    sections = []
    currentSection = None

    # Read steps
        # If we've hit a slope step:
            # If there's a current section, _render it
            # Make a new current section
        # Add to the current section

    # _render-section will need to parse its own linebreaks, then

    sections = []
    currentSection = None
    for step in layoutStr:
        if step.type == 'slope':
            # Begin new section
            if currentSection is not None:
                sections.append(_renderSection(currentSection, normalizeTileStep))
            currentSection = []
        currentSection.append(step)

    # Finalize the last section
    if currentSection is not None:
        sections.append(_renderSection(currentSection, normalizeTileStep))

    return sections[0], (None if len(sections) == 1 else sections[1])


def _renderSection(steps, normalizeTileStep):
    """
    _render a slope section
    """
    # Divide into rows
    rows = [[]]
    for step in steps:
        if step.type == 'lf':
            rows.append([])
        else:
            rows[-1].append(step)
    if not rows[-1]: rows = rows[:-1]

    # Calculate total width (that is, the width of the widest row)
    width = max(sum(step.type == 'tile' for step in row) for row in rows)

    isTile = lambda step: step.type == 'tile'

    # Create the actual section
    section = []
    for row in rows:
        newRow = list(map(normalizeTileStep, filter(isTile, row)))
        newRow += [EMPTY_TILE_VALUE] * (width - len(newRow)) # Right-pad
        section.append(newRow)

    return section


def _putObjectArray(dest, xo, yo, block, width, height):
    """
    Places a block of tiles into a larger tile array
    """
    for y in range(yo, yo + len(block)):
        if y < 0: continue
        if y >= height: continue
        drow = dest[y]
        srow = block[y - yo]
        for x in range(xo, xo + len(srow)):
            if x < 0: continue
            if x >= width: continue
            drow[x] = srow[x - xo]
