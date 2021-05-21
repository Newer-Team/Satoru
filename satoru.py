#!/usr/bin/python

# Satoru - New Super Mario Bros. U Level Editor
# Version v0.1
# Copyright (C) 2009-2016 Treeki, Tempus, angelsl, JasonP27, Kinnay,
# MalStar1000, RoadrunnerWMC, MrRean, Grop

# This file is part of Satoru.

# Satoru is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Satoru is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Satoru.  If not, see <http://www.gnu.org/licenses/>.

# satoru.py
# This is the main executable for Satoru


################################################################
################################################################

# Python version: sanity check
minimum = 3.5

import sys

currentRunningVersion = sys.version_info.major + (0.1 * sys.version_info.minor)
if currentRunningVersion < minimum:
    errormsg = 'Please update your copy of Python to ' + str(minimum) + \
        ' or greater. Currently running on: ' + sys.version[:5]
    raise Exception(errormsg)

# Stdlib imports
import base64
import importlib
import io
from math import floor as math_floor
import os
import os.path
import pickle
import struct
import subprocess
import threading
import time
import urllib.request
from xml.etree import ElementTree as etree
import zipfile

# nsmbulib
import nsmbulib.Object
import nsmbulib.Sarc
import nsmbulib.Tile
import nsmbulib.Tileset
import nsmbulib.Yaz0

import PIL.Image, PIL.ImageQt

# PyQt5: import, and error msg if not installed
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except (ImportError, NameError):
    errormsg = 'PyQt5 is not installed for this Python installation. Go online and download it.'
    raise Exception(errormsg) from None
Qt = QtCore.Qt


# Local imports
import gibberish
import spritelib as SLib
import sprites
from strings import *

SatoruID = 'Satoru Level Editor by Treeki, Tempus, RoadrunnerWMC, MrRean and Grop'
SatoruVersion = '0.1'
SatoruVersionShort = 'v0.1 (a)'
UpdateURL = 'http://rvlution.net/satoru/updates.xml'

FileTypes = ''
FileTypes += 'Level Archives (*.sarc *.szs);;'
FileTypes += 'Compressed Level Archives (*.szs);;'
FileTypes += 'Uncompressed Level Archives (*.sarc);;'
FileTypes += 'All Files (*)'

if not hasattr(QtWidgets.QGraphicsItem, 'ItemSendsGeometryChanges'):
    # enables itemChange being called on QGraphicsItem
    QtWidgets.QGraphicsItem.ItemSendsGeometryChanges = QtWidgets.QGraphicsItem.GraphicsItemFlag(0x800)


# Globals
TileWidth = 60
generateStringsXML = False
app = None
mainWindow = None
settings = None
defaultStyle = None
defaultPalette = None
compressed = False
LevelNames = None
ObjDesc = None
SpriteCategories = None
SpriteListData = None
EntranceTypeNames = None
MainObjects = [] # Pa0
OneTilesetObjects = {}
OneTilesetHierarchy = {}
EmbeddedObjects = [] # Pa1/2/3
EmbeddedObjectsLoadedFrom = {} # (tilesetnum, objectnum): index
Area = None
Dirty = False
DirtyOverride = 0
AutoSaveDirty = False
OverrideSnapping = False
CurrentPaintType = -1
CurrentObject = -1
CurrentSprite = -1
CurrentLayer = 1
Layer0Shown = True
Layer1Shown = True
Layer2Shown = True
SpritesShown = True
SpriteImagesShown = True
RealViewEnabled = False
LocationsShown = True
CommentsShown = True
PathsShown = True
ObjectsFrozen = False
SpritesFrozen = False
EntrancesFrozen = False
LocationsFrozen = False
PathsFrozen = False
CommentsFrozen = False
PaintingEntrance = None
PaintingEntranceListIndex = None
NumberFont = None
GridType = None
RestoredFromAutoSave = False
AutoSavePath = ''
AutoSaveData = b''
AutoOpenScriptEnabled = False
CurrentLevelNameForAutoOpenScript = 'AAAAAAAAAAAAAAAAAAAAAAAAAA'
OBJECT_FROM_MAIN = 1
OBJECT_FROM_MEGA = 2
OBJECT_FROM_EMBED = 3
Pa0Path = ""

# Game enums
NewSuperMarioBrosU = 0
NewSuperLuigiU = 1
FileExtensions = {
    NewSuperMarioBrosU: ('.szs', '.sarc'),
    NewSuperLuigiU: ('.szs', '.sarc'),
    }
FirstLevels = {
    NewSuperMarioBrosU: '1-1',
    NewSuperLuigiU: '1-1',
    }

#####################################################################
############################# UI-THINGS #############################
#####################################################################

class SatoruSplashScreen(QtWidgets.QSplashScreen):
    """
    Splash screen class for Satoru.
    """
    cfgData = {}
    currentDesc = ''
    currentPos = 0
    posLimit = 0

    def __init__(self):
        """
        Initializes the splash screen.
        super().__init__(QPixmap) has to be called with the pixmap you want or
        else transparency is messed up. self.setPixmap(QPixmap) doesn't seem to
        work properly.
        """
        self.loadCfg()
        self.loadResources()
        super().__init__(self.basePix)

    def loadCfg(self):
        """
        Loads the raw data from splash_config.txt
        """
        cfgData = {}
        with open('satorudata/splash_config.txt', encoding='utf-8') as cfg:
            for line in cfg:
                lsplit = line.replace('\n', '').split(':')
                key = lsplit[0].lower()
                value = ':'.join(lsplit[1:])
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif ',' in value:
                    value = value.split(',')
                    for i, entry in enumerate(value):
                        try:
                            value[i] = int(entry)
                        except ValueError: pass
                if isinstance(value, str):
                    try:
                        value = int(value)
                    except ValueError: pass
                cfgData[key] = value
        self.cfgData = cfgData


    def loadResources(self):
        """
        Reads the info from self.cfgData and loads stuff
        """
        self.basePix = QtGui.QPixmap(os.path.join('satorudata', self.cfgData['base_image']))

        def loadFont(name):
            fname = self.cfgData.get(name + '_font', 'sans-serif')
            bold = self.cfgData.get(name + '_font_bold', False)
            color = '#' + self.cfgData.get(name + '_font_color', '000000')
            size = self.cfgData.get(name + '_font_size', 12)
            weight = self.cfgData.get(name + '_font_weight', 12)
            wLim = self.cfgData.get(name + '_wrap_limit', 1024)
            position = self.cfgData.get(name + '_position', (0, 0))
            centered = self.cfgData.get(name + '_centered', False)

            font = QtGui.QFont()
            font.setFamily(fname)
            font.setBold(bold)
            font.setPointSize(size)
            font.setWeight(weight)
            return font, position, color, centered, wLim

        self.versionFontInfo = loadFont('version')
        self.loadingFontInfo = loadFont('loading')
        self.copyrightFontInfo = loadFont('copyright')

        mNameL = self.cfgData.get('meter_left', '')
        mNameM = self.cfgData.get('meter_mid', '')
        mNameR = self.cfgData.get('meter_right', '')
        self.meterPos = self.cfgData.get('meter_position', (0, 0))
        self.meterWidth = self.cfgData.get('meter_width', 64)

        self.meterL = QtGui.QPixmap(os.path.join('satorudata', mNameL))
        self.meterM = QtGui.QPixmap(os.path.join('satorudata', mNameM))
        self.meterR = QtGui.QPixmap(os.path.join('satorudata', mNameR))


    def setProgressLimit(self, limit):
        """
        Sets the maximum progress, used to calculate the progress bar
        """
        self.posLimit = limit


    def setProgress(self, desc, pos):
        """
        Sets the current progress
        """
        self.currentDesc = desc
        self.currentPos = pos
        self.repaint()
        app.processEvents()


    def drawContents(self, painter):
        """
        Draws the contents of the splash screen
        """
        painter.setRenderHint(painter.Antialiasing)

        totalWidthSoFar = self.meterWidth * (self.currentPos / self.posLimit)
        painter.drawPixmap(
            self.meterPos[0],
            self.meterPos[1],
            min(self.meterL.width(), self.meterWidth * (self.currentPos / self.posLimit)),
            self.meterL.height(),
            self.meterL,
            )
        painter.drawTiledPixmap(
            self.meterPos[0] + self.meterL.width(),
            self.meterPos[1],
            min(self.meterWidth - self.meterL.width() - self.meterR.width(), totalWidthSoFar - self.meterL.width()),
            self.meterM.height(),
            self.meterM,
            )
        painter.drawTiledPixmap(
            self.meterPos[0] + self.meterWidth - self.meterR.width(),
            self.meterPos[1],
            totalWidthSoFar - self.meterWidth + self.meterR.width(),
            self.meterR.height(),
            self.meterR,
            )

        def drawText(text, font, position, color, centered, wLim):
            """
            Draws some text
            """
            rect = QtCore.QRectF(
                position[0] - (wLim / 2 if centered else 0),
                position[1],
                wLim,
                512,
                )
            flags = (Qt.AlignHCenter if centered else Qt.AlignLeft) | Qt.AlignTop | Qt.TextWordWrap

            painter.save()
            painter.setFont(font)
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            painter.setPen(QtGui.QPen(QtGui.QColor(r, g, b)))
            painter.drawText(rect, flags, text)
            painter.restore()

        drawText(SatoruVersionShort, *self.versionFontInfo)
        drawText(self.currentDesc, *self.loadingFontInfo)
        try:
            with open('license_short.txt', 'r') as copyFile:
                text = copyFile.read()
        except FileNotFoundError:
            # No idea why this happens sometimes.
            text = 'LICENSE NOT FOUND'
        drawText(text, *self.copyrightFontInfo)


class ChooseLevelNameDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose a level from a list
    """
    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('OpenFromNameDlg', 0))
        self.setWindowIcon(GetIcon('open'))
        LoadLevelNames()
        self.currentlevel = None

        # create the tree
        tree = QtWidgets.QTreeWidget()
        tree.setColumnCount(1)
        tree.setHeaderHidden(True)
        tree.setIndentation(16)
        tree.currentItemChanged.connect(self.HandleItemChange)
        tree.itemActivated.connect(self.HandleItemActivated)

        # add items (LevelNames is effectively a big category)
        tree.addTopLevelItems(self.ParseCategory(LevelNames))

        # assign it to self.leveltree
        self.leveltree = tree

        # create the buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # create the layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.leveltree)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        self.layout = layout

        self.setMinimumWidth(320) # big enough to fit "World 5: Freezeflame Volcano/Freezeflame Glacier"
        self.setMinimumHeight(384)

    def ParseCategory(self, items):
        """
        Parses a XML category
        """
        nodes = []
        for item in items:
            node = QtWidgets.QTreeWidgetItem()
            node.setText(0, item[0])
            # see if it's a category or a level
            if isinstance(item[1], str):
                # it's a level
                node.setData(0, Qt.UserRole, item[1])
                node.setToolTip(0, item[1] + '.szs')
            else:
                # it's a category
                children = self.ParseCategory(item[1])
                for cnode in children:
                    node.addChild(cnode)
                node.setToolTip(0, item[0])
            nodes.append(node)
        return tuple(nodes)


    def HandleItemChange(self, current, previous):
        """
        Catch the selected level and enable/disable OK button as needed
        """
        self.currentlevel = current.data(0, Qt.UserRole)
        if self.currentlevel is None:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            self.currentlevel = str(self.currentlevel)


    def HandleItemActivated(self, item, column):
        """
        Handle a doubleclick on a level
        """
        self.currentlevel = item.data(0, Qt.UserRole)
        if self.currentlevel is not None:
            self.currentlevel = str(self.currentlevel)
            self.accept()


class SatoruTheme():
    """
    Class that represents a Satoru theme
    """
    def __init__(self, file=None):
        """
        Initializes the theme
        """
        self.initAsClassic()
        if file is not None: self.initFromFile(file)


    def initAsClassic(self):
        """
        Initializes the theme as the hardcoded Classic theme
        """
        self.fileName = 'Classic'
        self.formatver = 1.0
        self.version = 1.0
        self.themeName = trans.string('Themes', 0)
        self.creator = trans.string('Themes', 1)
        self.description = trans.string('Themes', 2)
        self.iconCacheSm = {}
        self.iconCacheLg = {}
        self.style = None

        # Add the colours                                             # Descriptions:
        self.colors = {
            'bg':                      QtGui.QColor(119,136,153),     # Main scene background fill
            'comment_fill':            QtGui.QColor(220,212,135,120), # Unselected comment fill
            'comment_fill_s':          QtGui.QColor(254,240,240,240), # Selected comment fill
            'comment_lines':           QtGui.QColor(192,192,192,120), # Unselected comment lines
            'comment_lines_s':         QtGui.QColor(220,212,135,240), # Selected comment lines
            'depth_highlight':         QtGui.QColor(243,243,21,191),  # Tileset 3D effect highlight (NSMBU)
            'entrance_fill':           QtGui.QColor(190,0,0,120),     # Unselected entrance fill
            'entrance_fill_s':         QtGui.QColor(190,0,0,240),     # Selected entrance fill
            'entrance_lines':          QtGui.QColor(0,0,0),           # Unselected entrance lines
            'entrance_lines_s':        QtGui.QColor(255,255,255),     # Selected entrance lines
            'grid':                    QtGui.QColor(255,255,255,100), # Grid
            'location_fill':           QtGui.QColor(114,42,188,70),   # Unselected location fill
            'location_fill_s':         QtGui.QColor(170,128,215,100), # Selected location fill
            'location_lines':          QtGui.QColor(0,0,0),           # Unselected location lines
            'location_lines_s':        QtGui.QColor(255,255,255),     # Selected location lines
            'location_text':           QtGui.QColor(255,255,255),     # Location text
            'object_fill_s':           QtGui.QColor(255,255,255,64),  # Select object fill
            'object_lines_s':          QtGui.QColor(255,255,255),     # Selected object lines
            'overview_entrance':       QtGui.QColor(255,0,0),         # Overview entrance fill
            'overview_location_fill':  QtGui.QColor(114,42,188,50),   # Overview location fill
            'overview_location_lines': QtGui.QColor(0,0,0),           # Overview location lines
            'overview_object':         QtGui.QColor(255,255,255),     # Overview object fill
            'overview_sprite':         QtGui.QColor(0,92,196),        # Overview sprite fill
            'overview_viewbox':        QtGui.QColor(0,0,255),         # Overview background fill
            'overview_zone_fill':      QtGui.QColor(47,79,79,120),    # Overview zone fill
            'overview_zone_lines':     QtGui.QColor(0,255,255),       # Overview zone lines
            'path_connector':          QtGui.QColor(6,249,20),        # Path node connecting lines
            'path_fill':               QtGui.QColor(6,249,20,120),    # Unselected path node fill
            'path_fill_s':             QtGui.QColor(6,249,20,240),    # Selected path node fill
            'path_lines':              QtGui.QColor(0,0,0),           # Unselected path node lines
            'path_lines_s':            QtGui.QColor(255,255,255),     # Selected path node lines
            'smi':                     QtGui.QColor(255,255,255,80),  # Sprite movement indicator
            'sprite_fill_s':           QtGui.QColor(255,255,255,64),  # Selected sprite w/ image fill
            'sprite_lines_s':          QtGui.QColor(255,255,255),     # Selected sprite w/ image lines
            'spritebox_fill':          QtGui.QColor(0,92,196,120),    # Unselected sprite w/o image fill
            'spritebox_fill_s':        QtGui.QColor(0,92,196,240),    # Selected sprite w/o image fill
            'spritebox_lines':         QtGui.QColor(0,0,0),           # Unselected sprite w/o image fill
            'spritebox_lines_s':       QtGui.QColor(255,255,255),     # Selected sprite w/o image fill
            'zone_entrance_helper':    QtGui.QColor(190,0,0,120),     # Zone entrance-placement left border indicator
            'zone_lines':              QtGui.QColor(145,200,255,176), # Zone lines
            'zone_corner':             QtGui.QColor(255,255,255),     # Zone grabbers/corners
            'zone_dark_fill':          QtGui.QColor(0,0,0,48),        # Zone fill when dark
            'zone_text':               QtGui.QColor(44,64,84),        # Zone text
            }

    def initFromFile(self, file):
        """
        Initializes the theme from the file
        """
        try:
            zipf = zipfile.ZipFile(file, 'r')
            zipfList = zipf.namelist()
        except Exception:
            # Can't load the data for some reason
            return
        try:
            mainxmlfile = zipf.open('main.xml')
        except KeyError:
            # There's no main.xml in the file
            return

        # Create a XML ElementTree
        try: maintree = etree.parse(mainxmlfile)
        except Exception: return
        root = maintree.getroot()

        # Parse the attributes of the <theme> tag
        if not self.parseMainXMLHead(root):
            # The attributes are messed up
            return

        # Parse the other nodes
        for node in root:
            if node.tag.lower() == 'colors':
                if 'file' not in node.attrib: continue

                # Load the colors XML
                try:
                    self.loadColorsXml(zipf.open(node.attrib['file']))
                except Exception: continue

            elif node.tag.lower() == 'stylesheet':
                if 'file' not in node.attrib: continue

                # Load the stylesheet
                try:
                    self.loadStylesheet(zipf.open(node.attrib['file']))
                except Exception: continue

            elif node.tag.lower() == 'icons':
                if not all(thing in node.attrib for thing in ['size', 'folder']): continue

                foldername = node.attrib['folder']
                big = node.attrib['size'].lower()[:2] == 'lg'
                cache = self.iconCacheLg if big else self.iconCacheSm

                # Load the icons
                for iconfilename in zipfList:
                    iconname = iconfilename
                    if not iconname.startswith(foldername + '/'): continue
                    iconname = iconname[len(foldername)+1:]
                    if len(iconname) <= len('icon-.png'): continue
                    if not iconname.startswith('icon-') or not iconname.endswith('.png'): continue
                    iconname = iconname[len('icon-'): -len('.png')]

                    icodata = zipf.open(iconfilename).read()
                    pix = QtGui.QPixmap()
                    if not pix.loadFromData(icodata): continue
                    ico = QtGui.QIcon(pix)

                    cache[iconname] = ico

    def parseMainXMLHead(self, root):
        """
        Parses the main attributes of main.xml
        """
        MaxSupportedXMLVersion = 1.0

        # Check for required attributes
        if root.tag.lower() != 'theme': return False
        if 'format' in root.attrib:
            formatver = root.attrib['format']
            try: self.formatver = float(formatver)
            except ValueError: return False
        else: return False

        if self.formatver > MaxSupportedXMLVersion: return False
        if 'name' in root.attrib: self.themeName = root.attrib['name']
        else: return False

        # Check for optional attributes
        self.creator = trans.string('Themes', 3)
        self.description = trans.string('Themes', 4)
        self.style = None
        self.version = 1.0
        if 'creator'     in root.attrib: self.creator = root.attrib['creator']
        if 'description' in root.attrib: self.description = root.attrib['description']
        if 'style'       in root.attrib: self.style = root.attrib['style']
        if 'version'     in root.attrib:
            try: self.version = float(root.attrib['style'])
            except ValueError: pass

        return True

    def loadColorsXml(self, file):
        """
        Loads a colors.xml file
        """
        try: tree = etree.parse(file)
        except Exception: return

        root = tree.getroot()
        if root.tag.lower() != 'colors': return False

        colorDict = {}
        for colorNode in root:
            if colorNode.tag.lower() != 'color': continue
            if not all(thing in colorNode.attrib for thing in ['id', 'value']): continue

            colorval = colorNode.attrib['value']
            if colorval.startswith('#'): colorval = colorval[1:]
            a = 255
            try:
                if len(colorval) == 3:
                    # RGB
                    r = int(colorval[0], 16)
                    g = int(colorval[1], 16)
                    b = int(colorval[2], 16)
                elif len(colorval) == 4:
                    # RGBA
                    r = int(colorval[0], 16)
                    g = int(colorval[1], 16)
                    b = int(colorval[2], 16)
                    a = int(colorval[3], 16)
                elif len(colorval) == 6:
                    # RRGGBB
                    r = int(colorval[0:2], 16)
                    g = int(colorval[2:4], 16)
                    b = int(colorval[4:6], 16)
                elif len(colorval) == 8:
                    # RRGGBBAA
                    r = int(colorval[0:2], 16)
                    g = int(colorval[2:4], 16)
                    b = int(colorval[4:6], 16)
                    a = int(colorval[6:8], 16)
            except ValueError: continue
            colorobj = QtGui.QColor(r, g, b, a)
            colorDict[colorNode.attrib['id']] = colorobj

        # Merge dictionaries
        self.colors.update(colorDict)


    def loadStylesheet(self, file):
        """
        Loads a stylesheet
        """
        print(file)

    def color(self, name):
        """
        Returns a color
        """
        return self.colors[name]

    def GetIcon(self, name, big=False):
        """
        Returns an icon
        """

        cache = self.iconCacheLg if big else self.iconCacheSm

        if name not in cache:
            path = 'satorudata/ico/lg/icon-' if big else 'satorudata/ico/sm/icon-'
            path += name
            cache[name] = QtGui.QIcon(path)

        return cache[name]

    def ui(self):
        """
        Returns the UI style
        """
        return self.uiStyle

def toQColor(*args):
    """
    Usage: toQColor(r, g, b[, a]) OR toQColor((r, g, b[, a]))
    """
    if len(args) == 1: args = args[0]
    r = args[0]
    g = args[1]
    b = args[2]
    a = args[3] if len(args) == 4 else 255
    return QtGui.QColor(r, g, b, a)

def SetAppStyle():
    """
    Set the application window color
    """
    global app
    global theme

    # Change the color if applicable
    #if theme.color('ui') is not None: app.setPalette(QtGui.QPalette(theme.color('ui')))

    # Change the style
    styleKey = setting('uiStyle')
    style = QtWidgets.QStyleFactory.create(styleKey)
    app.setStyle(style)

def createHorzLine():
    f = QtWidgets.QFrame()
    f.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Sunken)
    return f

def createVertLine():
    f = QtWidgets.QFrame()
    f.setFrameStyle(QtWidgets.QFrame.VLine | QtWidgets.QFrame.Sunken)
    return f

def LoadNumberFont():
    """
    Creates a valid font we can use to display the item numbers
    """
    global NumberFont
    if NumberFont is not None: return

    # this is a really crappy method, but I can't think of any other way
    # normal Qt defines Q_WS_WIN and Q_WS_MAC but we don't have that here
    s = QtCore.QSysInfo()
    if hasattr(s, 'WindowsVersion'):
        NumberFont = QtGui.QFont('Tahoma', (7/24) * TileWidth)
    elif hasattr(s, 'MacintoshVersion'):
        NumberFont = QtGui.QFont('Lucida Grande', (9/24) * TileWidth)
    else:
        NumberFont = QtGui.QFont('Sans', (8/24) * TileWidth)

def GetDefaultStyle():
    """
    Stores a copy of the default app style upon launch, which can then be accessed later
    """
    global defaultStyle, defaultPalette, app
    if (defaultStyle, defaultPalette) != (None, None): return
    defaultStyle = app.style()
    defaultPalette = QtGui.QPalette(app.palette())

def GetIcon(name, big=False):
    """
    Helper function to grab a specific icon
    """
    return theme.GetIcon(name, big)

#####################################################################
########################### VERIFICATIONS ###########################
#####################################################################

def checkContent(data):
    if not data.startswith(b'SARC'): return False

    required = (b'course/', b'course1.bin')
    return all([(r in data) for r in required])

def IsNSMBULevel(filename):
    global compressed
    """
    Does some basic checks to confirm that a file is a NSMBU level
    """
    if not os.path.isfile(filename):
        return False

    with open(filename, 'rb') as f:
        data = f.read()

    if nsmbulib.Yaz0.isCompressed(data):
        # Probably OK; decompressing it to actually check would
        # take too long
        return True
    else:
        return checkContent(data)

def SetDirty(noautosave=False):
    global Dirty, DirtyOverride, AutoSaveDirty
    if DirtyOverride > 0: return

    if not noautosave: AutoSaveDirty = True
    if Dirty: return

    Dirty = True
    try:
        mainWindow.UpdateTitle()
    except Exception:
        pass

def MapPositionToZoneID(zones, x, y, useid=False):
    """
    Returns the zone ID containing or nearest the specified position
    """
    id = 0
    minimumdist = -1
    rval = -1

    for zone in zones:
        r = zone.ZoneRect
        if   r.contains(x,y) and     useid: return zone.id
        elif r.contains(x,y) and not useid: return id

        xdist = 0
        ydist = 0
        if x <= r.left(): xdist = r.left() - x
        if x >= r.right(): xdist = x - r.right()
        if y <= r.top(): ydist = r.top() - y
        if y >= r.bottom(): ydist = y - r.bottom()

        dist = (xdist ** 2 + ydist ** 2) ** 0.5
        if dist < minimumdist or minimumdist == -1:
            minimumdist = dist
            rval = zone.id

        id += 1

    return rval

def FilesAreMissing():
    """
    Checks to see if any of the required files for Satoru are missing
    """

    if not os.path.isdir('satorudata'):
        QtWidgets.QMessageBox.warning(None, trans.string('Err_MissingFiles', 0), trans.string('Err_MissingFiles', 1))
        return True

    required = ['entrances.png', 'entrancetypes.txt', 'icon.png', 'levelnames.xml', 'overrides.png',
                'spritedata.xml', 'tilesets.xml', 'about.png', 'spritecategories.xml']

    missing = []

    for check in required:
        if not os.path.isfile('satorudata/' + check):
            missing.append(check)

    if len(missing) > 0:
        QtWidgets.QMessageBox.warning(None, trans.string('Err_MissingFiles', 0), trans.string('Err_MissingFiles', 2, '[files]', ', '.join(missing)))
        return True

    return False

def isValidGamePath(check='ug'):
    """
    Checks to see if the path for NSMBU contains a valid game
    """
    if check == 'ug': check = gamedef.GetGamePath()

    if check is None or check == '': return False
    if not os.path.isdir(check): return False
    if not (os.path.isfile(os.path.join(check, '1-1.szs')) or os.path.isfile(os.path.join(check, '1-1.sarc'))): return False

    return True

#####################################################################
############################## LOADING ##############################
#####################################################################

def LoadTheme():
    """
    Loads the theme
    """
    global theme

    id = setting('Theme')
    if id is None: id = 'Classic'
    if id != 'Classic':

        path = str('satorudata\\themes\\'+id).replace('\\', '/')
        with open(path, 'rb') as f:
            theme = SatoruTheme(f)

    else: theme = SatoruTheme()

def LoadLevelNames():
    """
    Ensures that the level name info is loaded
    """
    global LevelNames

    # Parse the file
    tree = etree.parse(GetPath('levelnames'))
    root = tree.getroot()

    # Parse the nodes (root acts like a large category)
    LevelNames = LoadLevelNames_Category(root)

def LoadLevelNames_Category(node):
    """
    Loads a LevelNames XML category
    """
    cat = []
    for child in node:
        if child.tag.lower() == 'category':
            cat.append((str(child.attrib['name']), LoadLevelNames_Category(child)))
        elif child.tag.lower() == 'level':
            cat.append((str(child.attrib['name']), str(child.attrib['file'])))
    return tuple(cat)

def LoadObjDescriptions(reload_=False):
    """
    Ensures that the object description is loaded
    """
    global ObjDesc
    if (ObjDesc is not None) and not reload_: return

    paths, isPatch = gamedef.recursiveFiles('ts1_descriptions', True)
    if isPatch:
        new = []
        new.append(trans.files['ts1_descriptions'])
        for path in paths: new.append(path)
        paths = new

    ObjDesc = {}
    for path in paths:
        f = open(path)
        raw = [x.strip() for x in f.readlines()]
        f.close()

        for line in raw:
            w = line.split('=')
            ObjDesc[int(w[0])] = w[1]

def LoadConstantLists():
    """
    Loads some lists of constants
    """
    global BgScrollRates
    global BgScrollRateStrings
    global ZoneThemeValues
    global ZoneTerrainThemeValues
    global Sprites
    global SpriteCategories

    BgScrollRates = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0, 0.0, 1.2, 1.5, 2.0, 4.0]
    BgScrollRateStrings = []
    s = trans.stringList('BGDlg', 1)
    for i in s:
        BgScrollRateStrings.append(i)

    ZoneThemeValues = trans.stringList('ZonesDlg', 1)

    ZoneTerrainThemeValues = trans.stringList('ZonesDlg', 2)

    Sprites = None
    SpriteListData = None

def LoadSpriteData():
    """
    Ensures that the sprite data info is loaded
    """
    global Sprites

    Sprites = [None] * 724
    errors = []
    errortext = []

    # It works this way so that it can overwrite settings based on order of precedence
    paths = []
    paths.append((trans.files['spritedata'], None))
    for pathtuple in gamedef.multipleRecursiveFiles('spritedata', 'spritenames'): paths.append(pathtuple)


    for sdpath, snpath in paths:

        # Add XML sprite data, if there is any
        if sdpath not in (None, ''):
            path = sdpath if isinstance(sdpath, str) else sdpath.path
            tree = etree.parse(path)
            root = tree.getroot()

            for sprite in root:
                if sprite.tag.lower() != 'sprite': continue

                try: spriteid = int(sprite.attrib['id'])
                except ValueError: continue
                spritename = sprite.attrib['name']
                notes = None
                relatedObjFiles = None

                if 'notes' in sprite.attrib:
                    notes = trans.string('SpriteDataEditor', 2, '[notes]', sprite.attrib['notes'])

                if 'files' in sprite.attrib:
                    relatedObjFiles = trans.string('SpriteDataEditor', 8, '[list]', sprite.attrib['files'].replace(';', '<br>'))

                sdef = SpriteDefinition()
                sdef.id = spriteid
                sdef.name = spritename
                sdef.notes = notes
                sdef.relatedObjFiles = relatedObjFiles

                try:
                    sdef.loadFrom(sprite)
                except Exception as e:
                    errors.append(str(spriteid))
                    errortext.append(str(e))

                Sprites[spriteid] = sdef

        # Add TXT sprite names, if there are any
        # This code is only ever run when a custom
        # gamedef is loaded, because spritenames.txt
        # is a file only ever used by custom gamedefs.
        if (snpath is not None) and (snpath.path is not None):
            snfile = open(snpath.path)
            data = snfile.read()
            snfile.close()
            del snfile

            # Split the data
            data = data.split('\n')
            for i, line in enumerate(data): data[i] = line.split(':')

            # Apply it
            for spriteid, name in data:
                Sprites[int(spriteid)].name = name

    # Warn the user if errors occurred
    if len(errors) > 0:
        QtWidgets.QMessageBox.warning(None, trans.string('Err_BrokenSpriteData', 0), trans.string('Err_BrokenSpriteData', 1, '[sprites]', ', '.join(errors)), QtWidgets.QMessageBox.Ok)
        QtWidgets.QMessageBox.warning(None, trans.string('Err_BrokenSpriteData', 2), repr(errortext))

def LoadSpriteCategories(reload_=False):
    """
    Ensures that the sprite category info is loaded
    """
    global Sprites, SpriteCategories
    if (SpriteCategories is not None) and not reload_: return

    paths, isPatch = gamedef.recursiveFiles('spritecategories', True)
    if isPatch:
        new = []
        new.append(trans.files['spritecategories'])
        for path in paths: new.append(path)
        paths = new

    SpriteCategories = []
    for path in paths:
        tree = etree.parse(path)
        root = tree.getroot()

        CurrentView = None
        for view in root:
            if view.tag.lower() != 'view': continue

            viewname = view.attrib['name']

            # See if it's in there already
            CurrentView = []
            for potentialview in SpriteCategories:
                if potentialview[0] == viewname: CurrentView = potentialview[1]
            if CurrentView == []: SpriteCategories.append((viewname, CurrentView, []))

            CurrentCategory = None
            for category in view:
                if category.tag.lower() != 'category': continue

                catname = category.attrib['name']

                # See if it's in there already
                CurrentCategory = []
                for potentialcat in CurrentView:
                    if potentialcat[0] == catname: CurrentCategory = potentialcat[1]
                if CurrentCategory == []: CurrentView.append((catname, CurrentCategory))

                for attach in category:
                    if attach.tag.lower() != 'attach': continue

                    sprite = attach.attrib['sprite']
                    if '-' not in sprite:
                        if int(sprite) not in CurrentCategory:
                            CurrentCategory.append(int(sprite))
                    else:
                        x = sprite.split('-')
                        for i in range(int(x[0]), int(x[1])+1):
                            if i not in CurrentCategory:
                                CurrentCategory.append(i)

    # Add a Search category
    SpriteCategories.append((trans.string('Sprites', 19), [(trans.string('Sprites', 16), list(range(0, 724)))], []))
    SpriteCategories[-1][1][0][1].append(9999) # 'no results' special case

def LoadSpriteListData(reload_=False):
    """
    Ensures that the sprite list modifier data is loaded
    """
    global SpriteListData
    if (SpriteListData is not None) and not reload_: return

    paths = gamedef.recursiveFiles('spritelistdata')
    new = []
    new.append('satorudata/spritelistdata.txt')
    for path in paths: new.append(path)
    paths = new

    SpriteListData = []
    for i in range(24): SpriteListData.append([])
    for path in paths:
        f = open(path)
        data = f.read()
        f.close()

        split = data.replace('\n', '').split(';')
        for lineidx in range(24):
            line = split[lineidx]
            splitline = line.split(',')
            splitlinelist = []

            # Add them
            for item in splitline:
                try: newitem = int(item)
                except ValueError: continue
                if newitem in SpriteListData[lineidx]: continue
                SpriteListData[lineidx].append(newitem)
            SpriteListData[lineidx].sort()

def LoadEntranceNames(reload_=False):
    """
    Ensures that the entrance names are loaded
    """
    global EntranceTypeNames
    if (EntranceTypeNames is not None) and not reload_: return

    paths, isPatch = gamedef.recursiveFiles('entrancetypes', True)
    if isPatch:
        new = []
        new.append(trans.files['entrancetypes'])
        for path in paths: new.append(path)
        paths = new

    NameList = {}
    for path in paths:
        getit = open(path, 'r')
        newNames = {}
        for line in getit.readlines(): newNames[int(line.split(':')[0])] = line.split(':')[1].replace('\n', '')
        for idx in newNames: NameList[idx] = newNames[idx]

    EntranceTypeNames = []
    idx = 0
    while idx in NameList:
        EntranceTypeNames.append(trans.string('EntranceDataEditor', 28, '[id]', idx, '[name]', NameList[idx]))
        idx += 1

def LoadBackgroundNames():
    """
    Load background names
    """
    global BackgroundNames

    BackgroundNames = {}
    with open('satorudata/bgs.txt') as bgfile:
        for entry in bgfile:
            BackgroundNames[entry.split(':')[0]] = entry.split(':')[1][:-1]

def LoadOverrides():
    """
    Load overrides
    """
    global Overrides

    OverrideImage = PIL.Image.open('satorudata/overrides.png')
    Overrides = [None] * 256
    idx = 0
    xcount = OverrideImage.width // TileWidth
    ycount = OverrideImage.height // TileWidth
    sourcex = 0
    sourcey = 0

    for y in range(ycount):
        for x in range(xcount):
            tile = OverrideImage.crop((sourcex, sourcey, sourcex + TileWidth, sourcey + TileWidth))
            Overrides[idx] = tile

            idx += 1
            sourcex += TileWidth
        sourcex = 0
        sourcey += TileWidth
        if idx % 16 != 0:
            idx -= (idx % 16)
            idx += 16

def LoadTranslation():
    """
    Loads the translation
    """
    global trans

    name = setting('Translation')
    eng = (None, 'None', 'English', '', 0)
    if name in eng: trans = SatoruTranslation(None)
    else: trans = SatoruTranslation(name)

    if generateStringsXML: trans.generateXML()

def LoadGameDef(name=None, dlg=None):
    """
    Loads a game definition
    """
    global gamedef
    if dlg: dlg.setMaximum(7)

    # Put the whole thing into a try-except clause
    # to catch whatever errors may happen
    try:

        # Load the gamedef
        if dlg: dlg.setLabelText(trans.string('Gamedefs', 1)) # Loading game patch...
        gamedef = SatoruGameDefinition(name)
        if gamedef.custom and (not settings.contains('GamePath_' + gamedef.name)):
            # First-time usage of this gamedef. Have the
            # user pick a stage folder so we can load stages
            # and tilesets from there
            QtWidgets.QMessageBox.information(None, trans.string('Gamedefs', 2), trans.string('Gamedefs', 3, '[game]', gamedef.name), QtWidgets.QMessageBox.Ok)
            result = mainWindow.HandleChangeGamePath(True)
            if result is not True: QtWidgets.QMessageBox.information(None, trans.string('Gamedefs', 4), trans.string('Gamedefs', 5, '[game]', gamedef.name), QtWidgets.QMessageBox.Ok)
            else: QtWidgets.QMessageBox.information(None, trans.string('Gamedefs', 6), trans.string('Gamedefs', 7, '[game]', gamedef.name), QtWidgets.QMessageBox.Ok)
        if dlg: dlg.setValue(1)

        # Load spritedata.xml and spritecategories.xml
        if dlg: dlg.setLabelText(trans.string('Gamedefs', 8)) # Loading sprite data...
        LoadSpriteData()
        LoadSpriteListData(True)
        LoadSpriteCategories(True)
        if mainWindow:
            mainWindow.spriteViewPicker.clear()
            for cat in SpriteCategories:
                mainWindow.spriteViewPicker.addItem(cat[0])
            mainWindow.sprPicker.LoadItems() # Reloads the sprite picker list items
            mainWindow.spriteViewPicker.setCurrentIndex(0) # Sets the sprite picker to category 0 (enemies)
            mainWindow.spriteDataEditor.setSprite(mainWindow.spriteDataEditor.spritetype, True) # Reloads the sprite data editor fields
            mainWindow.spriteDataEditor.update()
        if dlg: dlg.setValue(2)

        # Reload tilesets
        if dlg: dlg.setLabelText(trans.string('Gamedefs', 10)) # Reloading tilesets...
        LoadObjDescriptions(True) # reloads ts1_descriptions
        if dlg: dlg.setValue(4)

        # Load sprites.py
        if dlg: dlg.setLabelText(trans.string('Gamedefs', 11)) # Loading sprite image data...
        if Area is not None:
            SLib.SpritesFolders = gamedef.recursiveFiles('sprites', False, True)

            SLib.ImageCache.clear()
            SLib.SpriteImagesLoaded.clear()
            SLib.LoadBasicSuite()

            spriteClasses = gamedef.getImageClasses()

            for s in Area.sprites:
                if s.type in SLib.SpriteImagesLoaded: continue
                if s.type not in spriteClasses: continue

                spriteClasses[s.type].loadImages()

                SLib.SpriteImagesLoaded.add(s.type)

            for s in Area.sprites:
                if s.type in spriteClasses:
                    s.setImageObj(spriteClasses[s.type])
                else:
                    s.setImageObj(SLib.SpriteImage)

        if dlg: dlg.setValue(5)

        # Reload the sprite-picker text
        if dlg: dlg.setLabelText(trans.string('Gamedefs', 12)) # Applying sprite image data...
        if Area is not None:
            for spr in Area.sprites:
                spr.UpdateListItem() # Reloads the sprite-picker text
        if dlg: dlg.setValue(6)

        # Load entrance names
        if dlg: dlg.setLabelText(trans.string('Gamedefs', 16)) # Loading entrance names...
        LoadEntranceNames(True)
        if dlg: dlg.setValue(7)

    except Exception as e: raise
    #    # Something went wrong.
    #    if dlg: dlg.setValue(7) # autocloses it
    #    QtWidgets.QMessageBox.information(None, trans.string('Gamedefs', 17), trans.string('Gamedefs', 18, '[error]', str(e)))
    #    if name is not None: LoadGameDef(None)
    #    return False


    # Success!
    if dlg: setSetting('LastGameDef', name)
    return True

def LoadActionsLists():
    # Define the menu items, their default settings and their mainWindow.actions_ keys
    # These are used both in the Preferences Dialog and when init'ing the toolbar.
    global FileActions
    global EditActions
    global ViewActions
    global SettingsActions
    global HelpActions

    FileActions = (
        (trans.string('MenuItems', 0),  True,  'newlevel'),
        (trans.string('MenuItems', 2),  True,  'openfromname'),
        (trans.string('MenuItems', 4),  False, 'openfromfile'),
        (trans.string('MenuItems', 6),  False, 'openrecent'),
        (trans.string('MenuItems', 8),  True,  'save'),
        (trans.string('MenuItems', 10), False, 'saveas'),
        (trans.string('MenuItems', 12), False, 'metainfo'),
        (trans.string('MenuItems', 14), True,  'screenshot'),
        (trans.string('MenuItems', 16), False, 'changegamepath'),
        (trans.string('MenuItems', 134), False, 'changeonetileset'),
        (trans.string('MenuItems', 18), False, 'preferences'),
        (trans.string('MenuItems', 20), False, 'exit'),
        )
    EditActions = (
        (trans.string('MenuItems', 22), False, 'selectall'),
        (trans.string('MenuItems', 24), False, 'deselect'),
        (trans.string('MenuItems', 26), True,  'cut'),
        (trans.string('MenuItems', 28), True,  'copy'),
        (trans.string('MenuItems', 30), True,  'paste'),
        (trans.string('MenuItems', 32), False, 'shiftitems'),
        (trans.string('MenuItems', 34), False, 'mergelocations'),
        (trans.string('MenuItems', 38), False, 'freezeobjects'),
        (trans.string('MenuItems', 40), False, 'freezesprites'),
        (trans.string('MenuItems', 42), False, 'freezeentrances'),
        (trans.string('MenuItems', 44), False, 'freezelocations'),
        (trans.string('MenuItems', 46), False, 'freezepaths'),
        )
    ViewActions = (
        (trans.string('MenuItems', 48), True,  'showlay0'),
        (trans.string('MenuItems', 50), True,  'showlay1'),
        (trans.string('MenuItems', 52), True,  'showlay2'),
        (trans.string('MenuItems', 54), True,  'showsprites'),
        (trans.string('MenuItems', 56), False, 'showspriteimages'),
        (trans.string('MenuItems', 58), True,  'showlocations'),
        (trans.string('MenuItems', 60), True,  'grid'),
        (trans.string('MenuItems', 62), True,  'zoommax'),
        (trans.string('MenuItems', 64), True,  'zoomin'),
        (trans.string('MenuItems', 66), True,  'zoomactual'),
        (trans.string('MenuItems', 68), True,  'zoomout'),
        (trans.string('MenuItems', 70), True,  'zoommin'),
        )
    SettingsActions = (
        (trans.string('MenuItems', 72), True, 'areaoptions'),
        (trans.string('MenuItems', 74), True, 'zones'),
        (trans.string('MenuItems', 76), True, 'backgrounds'),
        (trans.string('MenuItems', 78), False, 'addarea'),
        (trans.string('MenuItems', 80), False, 'importarea'),
        (trans.string('MenuItems', 82), False, 'deletearea'),
        (trans.string('MenuItems', 84), False, 'reloadgfx'),
        ("Testing string 1", False, 'reloaddata'),
        )
    HelpActions = (
        (trans.string('MenuItems', 86), False, 'infobox'),
        (trans.string('MenuItems', 88), False, 'helpbox'),
        (trans.string('MenuItems', 90), False, 'tipbox'),
        (trans.string('MenuItems', 92), False, 'aboutqt'),
        )

#############
# UNSORTED
#############

class LevelScene(QtWidgets.QGraphicsScene):
    """
    GraphicsScene subclass for the level scene
    """
    def __init__(self, *args):
        global theme

        self.bgbrush = QtGui.QBrush(theme.color('bg'))
        super().__init__(*args)

    def drawTiles(self, painter):
        """
        Draws all visible tiles (only used when sprites are supposed to go behind layer 0)
        """
        showlayer = [Layer0Shown, Layer1Shown, Layer2Shown]
        for layernum in range(len(Area.layers)):
            if not showlayer[layernum]:
                continue
            layer = Area.layers[layernum]

            for obj in layer:
                # Check if the object exists
                if obj.from_ == OBJECT_FROM_MAIN:
                    exists = obj.idx < len(MainObjects)
                elif obj.from_ == OBJECT_FROM_MEGA:
                    exists = obj.idx in OneTilesetObjects
                else:
                    exists = obj.idx < len(EmbeddedObjects)

                if exists:
                    # Paint the object
                    obj.paint(painter)
                else:
                    # Paint an image indicating the tile is unavailable
                    im = PIL.ImageQt.ImageQt(Overrides[0])
                    painter.drawImage(obj.objx, obj.objy, im)

    def drawBackground(self, painter, rect):
        """
        Draws all visible tiles
        """
        painter.fillRect(rect, self.bgbrush)
        if not hasattr(Area, 'layers'): return

        if setting('drawSpritesBehindL0'):
            self.drawTiles(painter)
        else:
            drawrect = QtCore.QRectF(rect.x() / TileWidth, rect.y() / TileWidth, rect.width() / TileWidth + 1, rect.height() / TileWidth + 1)
            isect = drawrect.intersects

            layer0 = []
            l0add = layer0.append
            layer1 = []
            l1add = layer1.append
            layer2 = []
            l2add = layer2.append

            type_obj = ObjectItem
            ii = isinstance

            x1 = 1024
            y1 = 512
            x2 = 0
            y2 = 0

            # iterate through each object
            funcs = [layer0.append, layer1.append, layer2.append]
            show = [Layer0Shown, Layer1Shown, Layer2Shown]
            for layer, add, process in zip(Area.layers, funcs, show):
                if not process: continue
                for item in layer:
                    if not isect(item.LevelRect): continue
                    add(item)
                    xs = item.objx
                    xe = xs+item.width
                    ys = item.objy
                    ye = ys+item.height
                    if xs < x1: x1 = xs
                    if xe > x2: x2 = xe
                    if ys < y1: y1 = ys
                    if ye > y2: y2 = ye

            width = x2 - x1
            height = y2 - y1
            # All variables up to and including here are CORRECT.

            layernum = 2
            # create and draw the tilemaps
            for layer in [layer2, layer1, layer0]:
                if len(layer) == 0:
                    continue

                tmap = []
                i = 0
                while i < height:
                    tmap.append([None] * width)
                    i += 1

                for item in layer:
                    startx = item.objx - x1
                    desty = item.objy - y1

                    if item.from_ == OBJECT_FROM_MAIN:
                        exists = item.idx < len(MainObjects)
                    elif item.from_ == OBJECT_FROM_MEGA:
                        exists = item.idx in OneTilesetObjects
                    else:
                        exists = item.idx < len(EmbeddedObjects)

                    for row in item.objdata:
                        destrow = tmap[desty]
                        destx = startx
                        for tile in row:
                            if exists:
                                if tile is not None:
                                    destrow[destx] = tile.reprImage(item.data, item=True)
                            else:
                                destrow[destx] = nsmbulib.Tile.TileUnavailable
                            destx += 1
                        desty += 1

                painter.save()
                painter.translate(x1 * TileWidth, y1 * TileWidth)
                desty = 0
                for row in tmap:
                    destx = 0
                    for tileImage in row:
                        if tileImage not in (nsmbulib.Tile.TileUnavailable, None): # TileUnavailable = unavailable tile, None = blank tile
                            im = PIL.ImageQt.ImageQt(tileImage)
                            painter.drawImage(destx, desty, im)
                        elif tileImage is nsmbulib.Tile.TileUnavailable:
                            im = PIL.ImageQt.ImageQt(Overrides[0])
                            painter.drawImage(destx, desty, im)

                        destx += TileWidth
                    desty += TileWidth
                painter.restore()


class HexSpinBox(QtWidgets.QSpinBox):
    class HexValidator(QtGui.QValidator):
        def __init__(self, min, max):
            super().__init__()
            self.valid = set('0123456789abcdef')
            self.min = min
            self.max = max

        def validate(self, input, pos):
            try:
                input = str(input).lower()
            except Exception:
                return (self.Invalid, input, pos)
            valid = self.valid

            for char in input:
                if char not in valid:
                    return (self.Invalid, input, pos)

            try:
                value = int(input, 16)
            except ValueError:
                # If value == '' it raises ValueError
                return (self.Invalid, input, pos)

            if value < self.min or value > self.max:
                return (self.Intermediate, input, pos)

            return (self.Acceptable, input, pos)


    def __init__(self, format='%04X', *args):
        self.format = format
        super().__init__(*args)
        self.validator = self.HexValidator(self.minimum(), self.maximum())

    def setMinimum(self, value):
        self.validator.min = value
        QtWidgets.QSpinBox.setMinimum(self, value)

    def setMaximum(self, value):
        self.validator.max = value
        QtWidgets.QSpinBox.setMaximum(self, value)

    def setRange(self, min, max):
        self.validator.min = min
        self.validator.max = max
        QtWidgets.QSpinBox.setMinimum(self, min)
        QtWidgets.QSpinBox.setMaximum(self, max)

    def validate(self, text, pos):
        return self.validator.validate(text, pos)

    def textFromValue(self, value):
        return self.format % value

    def valueFromText(self, value):
        return int(str(value), 16)


class SpriteDefinition():
    """
    Stores and manages the data info for a specific sprite
    """

    class ListPropertyModel(QtCore.QAbstractListModel):
        """
        Contains all the possible values for a list property on a sprite
        """

        def __init__(self, entries, existingLookup, max):
            """
            Constructor
            """
            super().__init__()
            self.entries = entries
            self.existingLookup = existingLookup
            self.max = max

        def rowCount(self, parent=None):
            """
            Required by Qt
            """
            #return self.max
            return len(self.entries)

        def data(self, index, role=Qt.DisplayRole):
            """
            Get what we have for a specific row
            """
            if not index.isValid(): return None
            n = index.row()
            if n < 0: return None
            #if n >= self.max: return None
            if n >= len(self.entries): return None

            if role == Qt.DisplayRole:
                #entries = self.entries
                #if n in entries:
                #    return '%d: %s' % (n, entries[n])
                #else:
                #    return '%d: <unknown/unused>' % n
                return '%d: %s' % self.entries[n]

            return None


    def loadFrom(self, elem):
        """
        Loads in all the field data from an XML node
        """
        self.fields = []
        fields = self.fields

        for field in elem:
            if field.tag not in ['checkbox', 'list', 'value', 'bitfield']: continue

            attribs = field.attrib

            if 'comment' in attribs:
                comment = trans.string('SpriteDataEditor', 1, '[name]', attribs['title'], '[note]', attribs['comment'])
            else:
                comment = None

            if field.tag == 'checkbox':
                # parameters: title, nybble, mask, comment
                snybble = attribs['nybble']
                if '-' not in snybble:
                    nybble = int(snybble) - 1
                else:
                    getit = snybble.split('-')
                    nybble = (int(getit[0]) - 1, int(getit[1]))

                fields.append((0, attribs['title'], nybble, int(attribs['mask']) if 'mask' in attribs else 1, comment))
            elif field.tag == 'list':
                # parameters: title, nybble, model, comment
                snybble = attribs['nybble']
                if '-' not in snybble:
                    nybble = int(snybble) - 1
                    max = 16
                else:
                    getit = snybble.split('-')
                    nybble = (int(getit[0]) - 1, int(getit[1]))
                    max = (16 << ((nybble[1] - nybble[0] - 1) * 4))

                entries = []
                existing = [None for i in range(max)]
                for e in field:
                    if e.tag != 'entry': continue

                    i = int(e.attrib['value'])
                    entries.append((i, e.text))
                    existing[i] = True

                fields.append((1, attribs['title'], nybble, SpriteDefinition.ListPropertyModel(entries, existing, max), comment))
            elif field.tag == 'value':
                # parameters: title, nybble, max, comment
                snybble = attribs['nybble']

                # if it's 5-12 skip it
                # fixes tobias's crashy 'unknown values'
                if snybble == '5-12': continue

                if '-' not in snybble:
                    nybble = int(snybble) - 1
                    max = 16
                else:
                    getit = snybble.split('-')
                    nybble = (int(getit[0]) - 1, int(getit[1]))
                    max = (16 << ((nybble[1] - nybble[0] - 1) * 4))

                fields.append((2, attribs['title'], nybble, max, comment))
            elif field.tag == 'bitfield':
                # parameters: title, startbit, bitnum, comment
                startbit = int(attribs['startbit'])
                bitnum = int(attribs['bitnum'])

                fields.append((3, attribs['title'], startbit, bitnum, comment))


class Metadata():
    """
    Class for the new level metadata system
    """
    # This new system is much more useful and flexible than the old
    # system, but is incompatible with older versions of Satoru.
    # They will fail to understand the data, and skip it like it
    # doesn't exist. The new system is written with forward-compatibility
    # in mind. Thus, when newer versions of Satoru are created
    # with new metadata values, they will be easily able to add to
    # the existing ones. In addition, the metadata system is lossless,
    # so unrecognized values will be preserved when you open and save.

    # Type values:
    # 0 = binary
    # 1 = string
    # 2+ = undefined as of now - future Satorus can use them
    # Theoretical limit to type values is 4,294,967,296

    def __init__(self, data=None):
        """
        Creates a metadata object with the data given
        """
        self.DataDict = {}
        if data is None: return

        if data[0:4] != b'MD2_':
            # This is old-style metadata - convert it
            try:
                strdata = ''
                for d in data: strdata += chr(d)
                level_info = pickle.loads(strdata)
                for k, v in level_info.iteritems():
                    self.setStrData(k, v)
            except Exception: pass
            if ('Website' not in self.DataDict) and ('Webpage' in self.DataDict):
                self.DataDict['Website'] = self.DataDict['Webpage']
            return

        # Iterate through the data
        idx = 4
        while idx < len(data) - 4:

            # Read the next (first) four bytes - the key length
            rawKeyLen = data[idx:idx+4]
            idx += 4

            keyLen = (rawKeyLen[0] << 24) | (rawKeyLen[1] << 16) | (rawKeyLen[2] << 8) | rawKeyLen[3]

            # Read the next (key length) bytes - the key (as a str)
            rawKey = data[idx:idx+keyLen]
            idx += keyLen

            key = ''
            for b in rawKey: key += chr(b)

            # Read the next four bytes - the number of type entries
            rawTypeEntries = data[idx:idx+4]
            idx += 4

            typeEntries = (rawTypeEntries[0] << 24) | (rawTypeEntries[1] << 16) | (rawTypeEntries[2] << 8) | rawTypeEntries[3]

            # Iterate through each type entry
            typeData = {}
            for entry in range(typeEntries):

                # Read the next four bytes - the type
                rawType = data[idx:idx+4]
                idx += 4

                type = (rawType[0] << 24) | (rawType[1] << 16) | (rawType[2] << 8) | rawType[3]

                # Read the next four bytes - the data length
                rawDataLen = data[idx:idx+4]
                idx += 4

                dataLen = (rawDataLen[0] << 24) | (rawDataLen[1] << 16) | (rawDataLen[2] << 8) | rawDataLen[3]

                # Read the next (data length) bytes - the data (as bytes)
                entryData = data[idx:idx+dataLen]
                idx += dataLen

                # Add it to typeData
                self.setOtherData(key, type, entryData)


    def binData(self, key):
        """
        Returns the binary data associated with key
        """
        return self.otherData(key, 0)

    def strData(self, key):
        """
        Returns the string data associated with key
        """
        data = self.otherData(key, 1)
        if data is None: return
        s = ''
        for d in data: s += chr(d)
        return s

    def otherData(self, key, type):
        """
        Returns unknown data, with the given type value, associated with key (as binary data)
        """
        if key not in self.DataDict: return
        if type not in self.DataDict[key]: return
        return self.DataDict[key][type]

    def setBinData(self, key, value):
        """
        Sets binary data, overwriting any existing binary data with that key
        """
        self.setOtherData(key, 0, value)

    def setStrData(self, key, value):
        """
        Sets string data, overwriting any existing string data with that key
        """
        data = []
        for char in value: data.append(ord(char))
        self.setOtherData(key, 1, data)

    def setOtherData(self, key, type, value):
        """
        Sets other (binary) data, overwriting any existing data with that key and type
        """
        if key not in self.DataDict: self.DataDict[key] = {}
        self.DataDict[key][type] = value

    def save(self):
        """
        Returns a bytes object that can later be loaded from
        """

        # Sort self.DataDict
        dataDictSorted = []
        for dataKey in self.DataDict: dataDictSorted.append((dataKey, self.DataDict[dataKey]))
        dataDictSorted.sort(key=lambda entry: entry[0])

        data = []

        # Add 'MD2_'
        data.append(ord('M'))
        data.append(ord('D'))
        data.append(ord('2'))
        data.append(ord('_'))

        # Iterate through self.DataDict
        for dataKey, types in dataDictSorted:

            # Add the key length (4 bytes)
            keyLen = len(dataKey)
            data.append(keyLen >> 24)
            data.append((keyLen >> 16) & 0xFF)
            data.append((keyLen >> 8) & 0xFF)
            data.append(keyLen & 0xFF)

            # Add the key (key length bytes)
            for char in dataKey: data.append(ord(char))

            # Sort the types
            typesSorted = []
            for type in types: typesSorted.append((type, types[type]))
            typesSorted.sort(key=lambda entry: entry[0])

            # Add the number of types (4 bytes)
            typeNum = len(typesSorted)
            data.append(typeNum >> 24)
            data.append((typeNum >> 16) & 0xFF)
            data.append((typeNum >> 8) & 0xFF)
            data.append(typeNum & 0xFF)

            # Iterate through typesSorted
            for type, typeData in typesSorted:

                # Add the type (4 bytes)
                data.append(type >> 24)
                data.append((type >> 16) & 0xFF)
                data.append((type >> 8) & 0xFF)
                data.append(type & 0xFF)

                # Add the data length (4 bytes)
                dataLen = len(typeData)
                data.append(dataLen >> 24)
                data.append((dataLen >> 16) & 0xFF)
                data.append((dataLen >> 8) & 0xFF)
                data.append(dataLen & 0xFF)

                # Add the data (data length bytes)
                for d in typeData: data.append(d)

        return data

def clipStr(text, idealWidth, font=None):
    """
    Returns a shortened string, or None if it need not be shortened
    """
    if font is None: font = QtGui.QFont()
    width = QtGui.QFontMetrics(font).width(text)
    if width <= idealWidth: return None

    while width > idealWidth:
        text = text[:-1]
        width = QtGui.QFontMetrics(font).width(text)

    return text

def setting(name, default=None):
    """
    Thin wrapper around QSettings, fixes the type=bool bug
    """
    result = settings.value(name, default)
    if result == 'false': return False
    elif result == 'true': return True
    elif result == 'none': return None
    else: return result

def setSetting(name, value):
    """
    Thin wrapper around QSettings
    """
    return settings.setValue(name, value)

def module_path():
    """
    This will get us the program's directory, even if we are frozen using cx_Freeze
    """
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    if __name__ == '__main__':
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return None

def SetGamePath(newpath):
    """
    Sets the NSMBU game path
    """
    global gamedef

    # you know what's fun?
    # isValidGamePath crashes in os.path.join if QString is used..
    # so we must change it to a Python string manually
    # you know what else is fun?
    # it's the future now, and we migrated to PyQt5, so QStrings
    # no longer exist. so we don't need the str() wrapper anymore
    gamedef.SetGamePath(newpath)

#####################################################################
########################## TILESET-RELATED ##########################
#####################################################################

def LoadMainTileset(data, name):
    global MainObjects
    try:
        MainObjects = nsmbulib.Tileset.load(data)
    except:
        import traceback
        QtWidgets.QMessageBox.warning(None, 'Error', 'The Pa0 tileset could not be loaded:\n' + traceback.format_exc())
        MainObjects = []

    SLib.Tiles = MainObjects

    ProcessOverrides(MainObjects, name)
    ProcessPa0Descriptions(MainObjects, name)

def LoadLevelTilesets(data1, data2, data3):
    global EmbeddedObjects, EmbeddedObjectsLoadedFrom

    ts1, ts2, ts3 = [], [], []
    try:
        _, ts1, ts2, ts3 = nsmbulib.Tileset.loadAll(None, data1, data2, data3)
    except:
        import traceback
        QtWidgets.QMessageBox.warning(None, 'Error', 'The Pa1/2/3 tilesets could not be loaded:\n' + traceback.format_exc())

    EmbeddedObjects = []
    EmbeddedObjectsLoadedFrom = {}

    for i, obj in enumerate(ts1):
        if obj.name and obj.name in OneTilesetObjects:
            place = obj.name
        else:
            place = len(EmbeddedObjects)
            EmbeddedObjects.append(obj)
        EmbeddedObjectsLoadedFrom[(1, i)] = place
    for i, obj in enumerate(ts2):
        if obj.name and obj.name in OneTilesetObjects:
            place = obj.name
        else:
            place = len(EmbeddedObjects)
            EmbeddedObjects.append(obj)
        EmbeddedObjectsLoadedFrom[(2, i)] = place
    for i, obj in enumerate(ts3):
        if obj.name and obj.name in OneTilesetObjects:
            place = obj.name
        else:
            place = len(EmbeddedObjects)
            EmbeddedObjects.append(obj)
        EmbeddedObjectsLoadedFrom[(3, i)] = place

def LoadOneTileset():
    """
    What the function name says.
    """
    global OneTilesetObjects, OneTilesetHierarchy
    path = setting('OneTilesetPath')
    if not path or not os.path.isdir(path):
        path = getOneTilesetPath()
        if not path:
            # The user wouldn't pick one. So we quit.
            sys.exit()

    # Make a "Loading" box
    loadingBox = QtWidgets.QMessageBox()
    loadingBox.setWindowTitle('Loading')
    loadingBox.setText('Loading OneTileset... please wait...')
    loadingBox.show()
    loadingBox.update()

    # Load it
    OneTilesetObjects, OneTilesetHierarchy = nsmbulib.Tileset.loadFromNew(path)

    # Hide the loading box
    loadingBox.hide()

def getOneTilesetPath():
    """
    Prompt the user for a new path for OneTileset, and
    save it to settings if one is chosen. Then return it,
    or False if none was chosen.
    """

    dirArg = []
    currentDir = setting('OneTilesetPath')
    if currentDir:
        dirArg = [currentDir]

    path = QtWidgets.QFileDialog.getExistingDirectory(None, 'Choose your OneTileset folder', *dirArg)

    if not path:
        return False

    setSetting('OneTilesetPath', path)
    return path

def getPa0Path():
    """
    Prompt the user for a new path for OneTileset, and
    save it to settings if one is chosen. Then return it,
    or False if none was chosen.
    """

    dirArg = []
    currentDir = setting('Pa0Path')
    if currentDir:
        dirArg = [currentDir]

    path = QtWidgets.QFileDialog.getExistingDirectory(None, 'Choose your Pa0 folder', *dirArg)

    if not path:
        return False

    setSetting('Pa0Path', path)
    return path

def importOneTilesetObject():
    """
    Import a OneTileset object, or return False if
    the user aborts or there's an error.
    """
    path = QtWidgets.QFileDialog.getOpenFileName(None, 'Import OneTileset Object', '', 'OneTileset objects (*.json)')[0]
    if not path: return False

    # Try to load the object from there; if it can't be loaded,
    # show an error message
    try:
        obj = nsmbulib.Object.fromPathNew(path)
    except:
        import traceback
        tb = traceback.format_exc()
        QtWidgets.QMessageBox.critical(None, 'Error', 'Could not load the object: \n\n' + tb)
        return False

    return obj

def ProcessOverrides(objects, name):
    """
    Load overridden tiles, if there are any
    """
    if name not in ['Pa0_jyotyu', 'Pa0_jyotyu_chika', 'Pa0_jyotyu_yougan', 'Pa0_jyotyu_yougan2']:
        return

    try:

        def setOverride(idx, override):
            """
            A helper function to set overrides on a particular object:
            - Pass an int n and the override will be set to the nth override
            - Pass a PIL Image and the override will be set to that
            - Pass an iterable of ints and False's, and the override will be set
                to the overrides at those indices (False's will be skipped).
            """
            if isinstance(override, int):
                # Set the override to the override at that index
                next(objects[idx].allTiles).override = Overrides[override]
            elif isinstance(override, PIL.Image.Image):
                # Set the override to that image
                next(objects[idx].allTiles).override = override
            else:
                # Set the overrides to these indices
                for tile, overrideInner in zip(objects[idx].allTiles, override):
                    if overrideInner is False: continue # Don't check "if not override" b/c it can be 0, too
                    if isinstance(overrideInner, int):
                        tile.override = Overrides[overrideInner]
                    elif isinstance(overrideInner, PIL.Image.Image):
                        tile.override = overrideInner

        # Images
        warningImage = 0
        brickImage = next(objects[15].allTiles).image

        # Invisible blocks
        for i in range(5, 15):
            setOverride(i, i - 2)

        # All bricks minus the first
        for i in range(16, 28):
            setOverride(i, warningImage)

        # Another brick block
        setOverride(83, brickImage) # 83 is a duplicate of object 15

        # Question/brick block (object 28)
        questTile = next(objects[28].allTiles)
        def setQBlockOverride(contents, override):
            questTile.setContentsOverride(contents, Overrides[override])
        # 0: ? block: One coin (no override needed)
        setQBlockOverride(1, 26) # Brick block: One coin
        setQBlockOverride(2, 27) # Brick block: Ten coins
        setQBlockOverride(3, 16) # Brick block: Fire flower
        setQBlockOverride(4, 17) # Brick block: Invincibility star
        setQBlockOverride(5, 18) # Brick block: 1-UP
        setQBlockOverride(6, 19) # Brick block: Vine
        setQBlockOverride(7, 20) # Brick block: Mini mushroom
        setQBlockOverride(8, 21) # Brick block: Propeller suit
        setQBlockOverride(9, 22) # Brick block: Penguin suit
        setQBlockOverride(10, 25) # Brick block: Yoshi
        setQBlockOverride(11, 23) # Brick block: Ice flower
        setQBlockOverride(12, 24) # Brick block: Acorn mushroom
        # 13: ? block: One coin (No override needed)
        setQBlockOverride(14, 32) # ? block: Fire flower
        setQBlockOverride(15, 33) # ? block: Invincibility Star
        setQBlockOverride(16, 34) # ? block: Continuous Star
        setQBlockOverride(17, 35) # ? block: Vine
        setQBlockOverride(18, 42) # ? block: Spring
        setQBlockOverride(19, 36) # ? block: Mini mushroom
        setQBlockOverride(20, 37) # ? block: Propeller Suit
        setQBlockOverride(21, 38) # ? block: Penguin Suit
        setQBlockOverride(22, 41) # ? block: Yoshi
        setQBlockOverride(23, 39) # ? block: Ice flower
        setQBlockOverride(24, 40) # ? block: Acorn Mushroom

        # Other (useless) question block objects
        for i in range(29, 40):
            setOverride(i, warningImage)

        # Colisions
        setOverride(1, 1)    # Full block
        setOverride(4, 2)    # Vine stopper
        setOverride(2, 13)   # Solid-on-top
        setOverride(3, 14)   # Half block
        setOverride(82, 45)  # Muncher (hit)
        setOverride(144, 44) # Muncher (hit) 2
        setOverride(43, 43)  # Donut lift

        # Conveyor belts
        # Right, left, right-fast, left-fast
        for objNum, overrideStart in ((113, 96), (114, 99), (115, 112), (116, 115)):
            setOverride(objNum, range(overrideStart, overrideStart + 3))

        # Pipes
        def addToListItems(list, num):
            for elem in list:
                yield elem + num

        for color in (0, 1, 2): # Regular pipes (green / yellow / red)
            setOverride(56 + 6 * color, addToListItems([0, 1, 16, 17], 48 + 2 * color)) # Up
            setOverride(57 + 6 * color, addToListItems([0, 1, 16, 17], 64 + 2 * color)) # Down
            setOverride(58 + 6 * color, addToListItems([0, 1, 16, 17], 71 + 3 * color)) # Left
            setOverride(59 + 6 * color, addToListItems([0, 1, 16, 17], 72 + 3 * color)) # Right
            setOverride(60 + 6 * color, addToListItems([0, 1], 64 + 2 * color)) # Vertical center
            setOverride(61 + 6 * color, addToListItems([0, 16], 72 + 3 * color)) # Horiz. center

        setOverride(75, [54, 70]) # Mini pipes (green)
        setOverride(76, [70, 86])
        setOverride(77, [104, 105])
        setOverride(78, [105, 121]) # yes, 121
        setOverride(79, 70)
        setOverride(80, 105)

        # Pipe joint: normal/mini
        setOverride(74, [102, 103, 118, 119])
        setOverride(81, 120)

        # Coins
        setOverride(47, 30) # Coin
        setOverride(48, [30, False, 30]) # NW/SE coin pattern
        setOverride(49, 30) # Vertical lines of coins
        setOverride(50, 30) # Horizontal lines of coins
        setOverride(51, 46) # Blue coin with black background
        setOverride(52, 29) # Coin outline
        setOverride(53, [29, False, 29]) # NW/SE coin outline pattern
        setOverride(54, 28) # Multiplayer coin outline
        setOverride(55, [28, False, 28]) # NW/SE multiplayer coin outline pattern

        # Flowers / Grass
        setOverride(117, range(58, 63)) # Grass
        setOverride(118, 55) # Flowers
        setOverride(119, 56)
        setOverride(120, 57)
        setOverride(121, 106) # Flowers + grass
        setOverride(122, 107)
        setOverride(123, 108)
        setOverride(124, 58) # Grass
        setOverride(125, 59)
        setOverride(126, 60)
        setOverride(127, 61)
        setOverride(128, 62)

        # Lines
        setOverride(84, 128) # Horizontal
        setOverride(85, 63)  # Vertical
        setOverride(86, 122) # SE corner
        setOverride(87, 123) # NW corner
        setOverride(88, [False, 125, 124]) # 1x3 upslope
        setOverride(89, [False, 126, 127]) # 1x3 downslope
        setOverride(90, [False, 129]) # 1x2 upslope
        setOverride(91, [False, 130]) # 1x2 downslope
        setOverride(92, [False, False, 131, 132]) # 2x2 upslope
        setOverride(93, [False, False, 133, 134]) # 2x2 downslope
        setOverride(94, 135) # 1x1 circle
        setOverride(95, [False, False, False, False, 136, 137, False, 138, 139]) # 3x3 circle
        setOverride(96,
            [140, 141, 142, 143, 144, False, False, 145, 146, False, False, 147, 148, 149, 150, 151],
            ) # 4x4 circle
        setOverride(97, 136) # 1x1 circle top-left
        setOverride(98, 137) # 1x1 circle top-right
        setOverride(99, 138) # 1x1 circle bottom-left
        setOverride(100, 139) # 1x1 circle bottom-right
        setOverride(101, [140, 141, 144, False]) # 2x2 circle top-left
        setOverride(102, [142, 143, False, 145]) # 2x2 circle top-right
        setOverride(103, [146, False, 148, 149]) # 2x2 circle bottom-left
        setOverride(104, [False, 147, 150, 151]) # 2x2 circle bottom-right
        for i in range(8): # Stoppers
            setOverride(105 + i, 152 + i)
        setOverride(105, 152) # Stopper -- top
        setOverride(106, 153) # Stopper -- bottom
        setOverride(107, 154) # Stopper -- left
        setOverride(108, 155) # Stopper -- right
        setOverride(109, 156) # Stopper -- top-left
        setOverride(110, 158) # Stopper -- bottom-left
        setOverride(111, 157) # Stopper -- top-right
        setOverride(112, 159) # Stopper -- bottom-right

    except Exception:
        QtWidgets.QMessageBox.warning(None, 'Error', 'The overrides could not be fully applied to ' + str(name) + '.')
        raise

def ProcessPa0Descriptions(objects, name):
    """
    Appply the Pa0 descriptions to these objects
    """
    if name not in ['Pa0_jyotyu', 'Pa0_jyotyu_chika', 'Pa0_yougan', 'Pa0_yougan2']:
        return

    for idx, desc in ObjDesc.items():
        try:
            objects[idx].description = desc
        except IndexError: pass

#####################################################################
############################### LEVEL ###############################
#####################################################################

class AbstractLevel():
    """
    Class for an abstract level from any game. Defines the API.
    """
    def __init__(self):
        """
        Initializes the level with default settings
        """
        self.filepath = None
        self.name = 'untitled'

        self.areas = []

    def load(self, data, areaNum, progress=None):
        """
        Loads a level from bytes data. You MUST reimplement this in subclasses!
        """
        pass

    def save(self, innerfilename, outerfilename, separateTilesets):
        """
        Returns the level as a bytes object. You MUST reimplement this in subclasses!
        """
        return b''

    def addArea(self):
        """
        Adds an area to the level, and returns it.
        """
        new = Area_NSMBU()
        self.areas.append(new)

        return new

    def deleteArea(self, number):
        """
        Removes the area specified. Number is a 1-based value, not 0-based;
        so you would pass a 1 if you wanted to delete the first area.
        """
        del self.areas[number - 1]
        return True


class Level_NSMBU(AbstractLevel):
    """
    Class for a level from New Super Mario Bros. U
    """
    def __init__(self):
        """
        Initializes the level with default settings
        """
        super().__init__()
        global Area

        self.areas.append(Area_NSMBU())
        Area = self.areas[0]

    def load(self, data, areaNum, progress=None):
        """
        Loads a NSMBU level from bytes data.
        """
        super().load(data, areaNum, progress)

        global Area

        sarc = nsmbulib.Sarc.load(data)

        # Sort the area data
        areaData = {}
        for name, val in sarc.items():
            if name.count('/') != 1: continue
            if not name.startswith('course/'): continue
            if val is None: continue

            fn = name.split('/')[-1]

            if not fn.startswith('course'): continue
            if not fn.endswith('.bin'): continue
            if '_bgdatL' in fn:
                # It's a layer file
                if len(fn) != 19: continue
                try:
                    thisArea = int(fn[6])
                    laynum = int(fn[14])
                except ValueError: continue
                if not (0 < thisArea < 5): continue

                if thisArea not in areaData: areaData[thisArea] = [None] * 4
                areaData[thisArea][laynum + 1] = val
            else:
                # It's the course file
                if len(fn) != 11: continue
                try:
                    thisArea = int(fn[6])
                except ValueError: continue
                if not (0 < thisArea < 5): continue

                if thisArea not in areaData: areaData[thisArea] = [None] * 4
                areaData[thisArea][0] = val

        # Create area objects
        self.areas = []
        thisArea = 1
        while thisArea in areaData:
            course = areaData[thisArea][0]
            L0 = areaData[thisArea][1]
            L1 = areaData[thisArea][2]
            L2 = areaData[thisArea][3]

            if thisArea == areaNum:
                newarea = Area_NSMBU()
                Area = newarea
                SLib.Area = Area
            else:
                newarea = AbstractArea()

            newarea.areanum = thisArea
            newarea.load(course, L0, L1, L2, progress)
            self.areas.append(newarea)

            thisArea += 1


        return True

    def save(self, innerfilename, outerfilename, separateTilesets, compress):
        """
        Save the level back to a file
        """

        # Make a new archive
        newArchive = {}

        # Go through the areas, save them and add them back to the archive
        tilesets = {}
        for areanum, area in enumerate(self.areas):
            course, L0, L1, L2, tilesets_ = area.save(areanum, separateTilesets)

            if course is not None:
                newArchive['course/course%d.bin' % (areanum + 1)] = course
            if L0 is not None:
                newArchive['course/course%d_bgdatL0.bin' % (areanum + 1)] = L0
            if L1 is not None:
                newArchive['course/course%d_bgdatL1.bin' % (areanum + 1)] = L1
            if L2 is not None:
                newArchive['course/course%d_bgdatL2.bin' % (areanum + 1)] = L2
            tilesets.update(tilesets_)

        # Here we have the new inner-SARC savedata
        innersarc = nsmbulib.Sarc.save(newArchive, 0x04, minDataStart=0x170)

        # Now set up an outer SARC containing the inner SARC, the level name
        # and the rest of the SZS stuff we loaded but didn't know what to do with
        outerArchive = {
            innerfilename: innersarc,
            'levelname': innerfilename.encode('utf-8'),
            }
        for szsThingName, szsThingData in szsData.items():
            try:
                # Skip the course file
                spl = szsThingName.split('-')
                int(spl[0])
                int(spl[1])
                continue
            except: pass

            outerArchive[szsThingName] = szsThingData

        # Add tilesets if needed
        if not separateTilesets:
            outerArchive.update(tilesets)

        # Save the outer sarc and return it
        outerSarc = nsmbulib.Sarc.save(outerArchive, 0x2000)

        # Compress the level if we need to
        if compress:
            outerSarc = nsmbulib.Yaz0.compress(outerSarc)

        # Populate the return files dict
        retVal = {}
        retVal[outerfilename] = outerSarc
        if separateTilesets:
            retVal.update(tilesets)
        return retVal

    def addArea(self):
        """
        Adds an area to the level, and returns it.
        """
        new = Area_NSMBU()
        self.areas.append(new)

        return new

#####################################################################
############################### AREAS ###############################
#####################################################################

class AbstractArea():
    """
    An extremely basic abstract area. Implements the basic function API.
    """
    def __init__(self):
        self.areanum = 1
        self.course = None
        self.L0 = None
        self.L1 = None
        self.L2 = None

    def load(self, course, L0, L1, L2, progress=None):
        self.course = course
        self.L0 = L0
        self.L1 = L1
        self.L2 = L2

    def save(self, areaNum, separateTilesets):
        return (self.course, self.L0, self.L1, self.L2, {})


class AbstractParsedArea(AbstractArea):
    """
    An area that is parsed to load sprites, entrances, etc. Still abstracted among games.
    Don't instantiate this! It could blow up because many of the functions are only defined
    within subclasses. If you want an area object, use a game-specific subclass.
    """
    def __init__(self):
        """
        Creates a completely new area
        """

        # Default area number
        self.areanum = 1

        # Settings
        self.defEvents = 0
        self.wrapFlag = 0
        self.timeLimit = 300
        self.unk1 = 0
        self.startEntrance = 0
        self.unk2 = 0
        self.unk3 = 0

        # Lists of things
        self.entrances = []
        self.sprites = []
        self.zones = []
        self.locations = []
        self.pathdata = []
        self.paths = []
        self.comments = []
        self.layers = [[], [], []]

        # Metadata
        self.LoadSatoruInfo(None)

    def load(self, course, L0, L1, L2, progress=None):
        """
        Loads an area from the archive files
        """

        # Load in the course file and blocks
        self.LoadBlocks(course)

        # Load stuff from individual blocks
        self.tileset0name, ts1, ts2, ts3 = self.LoadTilesetNames() # block 1
        self.LoadOptions() # block 2
        self.LoadEntrances() # block 7
        self.LoadSprites() # block 8
        self.LoadZones() # block 10 (also blocks 3, 5, and 6)
        self.LoadLocations() # block 11
        self.LoadPaths() # block 12 and 13

        # Load the editor metadata
        if self.block1pos[0] != 0x70:
            rdsize = self.block1pos[0] - 0x70
            rddata = course[0x70:self.block1pos[0]]
            self.LoadSatoruInfo(rddata)
        else:
            self.LoadSatoruInfo(None)
        del self.block1pos

        # Now, load the comments
        self.LoadComments()

        # Load the tilesets
        try: # Crashes when changing areas
            app.splashScreen.setProgress(trans.string('Splash', 3), 1)
        except:
            pass

        try: # Crashes when changing areas
            app.splashScreen.setProgress(trans.string('Splash', 3), 2)
        except:
            pass

        ts0data = ts1data = ts2data = ts3data = None
        if self.tileset0name in szsData:
            ts0data = szsData[self.tileset0name]
        if ts1 in szsData:
            ts1data = szsData[ts1]
            del szsData[ts1]
        if ts2 in szsData:
            ts2data = szsData[ts2]
            del szsData[ts2]
        if ts3 in szsData:
            ts3data = szsData[ts3]
            del szsData[ts3]

        if ts0data:
            LoadMainTileset(ts0data, self.tileset0name)
        try: # Crashes when changing areas
            app.splashScreen.setProgress(trans.string('Splash', 3), 3)
        except:
            pass

        LoadLevelTilesets(ts1data, ts2data, ts3data)
        try: # Crashes when changing areas
            app.splashScreen.setProgress(trans.string('Splash', 3), 4)
        except:
            pass


        # Load the object layers
        self.layers = [[], [], []]

        if L0 is not None:
            self.LoadLayer(0, L0)
        if L1 is not None:
            self.LoadLayer(1, L1)
        if L2 is not None:
            self.LoadLayer(2, L2)

        # Delete self.blocks
        #del self.blocks

        return True

    def save(self, areaNum, separateTilesets):
        """
        Save the area back to a file
        """
        # Prepare this first because otherwise the game refuses to load some sprites
        self.SortSpritesByZone()

        # Also this
        tilesets = self.RegenerateTilesets(areaNum, separateTilesets)

        # Save each block
        self.SaveTilesetNames() # block 1
        self.SaveOptions() # block 2
        self.SaveEntrances() # block 7
        self.SaveSprites() # block 8
        self.SaveLoadedSprites() # block 9
        self.SaveZones() # block 10 (and 3 and 5)
        self.SaveLocations() # block 11
        self.SavePaths() # blocks 14 and 15

        # Save the metadata
        rdata = bytearray(self.Metadata.save())
        if len(rdata) % 4 != 0:
            for i in range(4 - (len(rdata) % 4)):
                rdata.append(0)
        rdata = b''#bytes(rdata)

        # Save the main course file
        # We'll be passing over the blocks array two times.
        # Using bytearray here because it offers mutable bytes
        # and works directly with struct.pack_into(), so it's a
        # win-win situation
        FileLength = (len(self.blocks) * 8) + len(rdata)
        for block in self.blocks:
            FileLength += len(block)

        course = bytearray()
        for i in range(FileLength): 
            course.append(0)
        saveblock = struct.Struct('>II')

        HeaderOffset = 0
        FileOffset = (len(self.blocks) * 8) + len(rdata)
        for block in self.blocks:
            blocksize = len(block)
            saveblock.pack_into(course, HeaderOffset, FileOffset, blocksize)
            if blocksize > 0:
                course[FileOffset:FileOffset + blocksize] = block
            HeaderOffset += 8
            FileOffset += blocksize

        # Return stuff
        return (
            bytes(course),
            self.SaveLayer(0),
            self.SaveLayer(1),
            self.SaveLayer(2),
            tilesets,
            )

    def RemoveFromLayer(self, obj):
        """
        Removes a specific object from the level and updates Z-indices accordingly
        """
        layer = self.layers[obj.layer]
        idx = layer.index(obj)
        del layer[idx]
        for i in range(idx,len(layer)):
            upd = layer[i]
            upd.setZValue(upd.zValue() - 1)

    def SortSpritesByZone(self):
        """
        Sorts the sprite list by zone ID so it will work in-game
        """

        split = {}
        zones = []

        f_MapPositionToZoneID = MapPositionToZoneID
        zonelist = self.zones

        for sprite in self.sprites:
            zone = f_MapPositionToZoneID(zonelist, sprite.objx, sprite.objy)
            sprite.zoneID = zone
            if not zone in split:
                split[zone] = []
                zones.append(zone)
            split[zone].append(sprite)

        newlist = []
        zones.sort()
        for z in zones:
            newlist += split[z]

        self.sprites = newlist

    def LoadSatoruInfo(self, data):
        if (data is None) or (len(data) == 0):
            self.Metadata = Metadata()
            return

        try: self.Metadata = Metadata(data)
        except Exception: self.Metadata = Metadata() # fallback


class Area_NSMBU(AbstractParsedArea):
    """
    Class for a parsed NSMBU level area
    """
    def __init__(self):
        """
        Make a blank area
        """
        super().__init__()

        self.blocks = [b''] * 15

        (self.tileset0name, self.tileset1name,
            self.tileset2name, self.tileset3name) = 'Pa0_jyotyu', '', '', ''
        (self.unk1, self.unk2, self.wrapedges, self.timelimit, self.unk3,
            self.unk4, self.unk5, self.unk6, self.unk7, self.timelimit2,
            self.timelimit3) = 0, 0, 0, 400, 0, 0, 0, 0, 0, 300, 300
        self.entrances = []
        self.sprites = []
        self.zones = []
        self.locations = []
        self.pathdata = []
        self.pathinfo = []
        self.layers = [[], [], []]

    def LoadBlocks(self, course):
        """
        Loads self.blocks from the course file
        """
        self.blocks = [None] * 15
        getblock = struct.Struct('>II')
        for i in range(15):
            data = getblock.unpack_from(course, i * 8)
            if data[1] == 0:
                self.blocks[i] = b''
            else:
                self.blocks[i] = course[data[0]:data[0] + data[1]]

        self.block1pos = getblock.unpack_from(course, 0)

    def LoadTilesetNames(self):
        """
        Loads block 1, the tileset names
        """
        data = struct.unpack_from('32s32s32s32s', self.blocks[0])
        tileset0 = data[0].strip(b'\0').decode('latin-1')
        tileset1 = data[1].strip(b'\0').decode('latin-1')
        tileset2 = data[2].strip(b'\0').decode('latin-1')
        tileset3 = data[3].strip(b'\0').decode('latin-1')
        return tileset0, tileset1, tileset2, tileset3

    def LoadOptions(self):
        """
        Loads block 2, the general options
        """
        optdata = self.blocks[1]
        optstruct = struct.Struct('>xxBBxxxxxBHxBBBBxxBHH')
        offset = 0
        data = optstruct.unpack_from(optdata,offset)
        self.unk1, self.unk2, self.wrapedges, self.timelimit, self.unk3, self.unk4, self.unk5, self.unk6, self.unk7, self.timelimit2, self.timelimit3 = data

    def LoadEntrances(self):
        """
        Loads block 7, the entrances
        """
        entdata = self.blocks[6]
        entcount = len(entdata) // 24
        entstruct = struct.Struct('>HHxBxxBBBBBBxBxBBBBBBx')
        offset = 0
        entrances = []
        for i in range(entcount):
            data = entstruct.unpack_from(entdata,offset)
            entrances.append(EntranceItem(*data))
            offset += 24
        self.entrances = entrances

    def LoadSprites(self):
        """
        Loads block 8, the sprites
        """
        spritedata = self.blocks[7]
        sprcount = len(spritedata) // 24
        sprstruct = struct.Struct('>HHH10sxx2sxxxx')
        offset = 0
        sprites = []

        unpack = sprstruct.unpack_from
        append = sprites.append
        obj = SpriteItem
        for i in range(sprcount):
            data = unpack(spritedata, offset)
            append(obj(data[0], data[1], data[2], data[3] + data[4]))
            offset += 24
        self.sprites = sprites

    def LoadZones(self):
        """
        Loads blocks 3, 5, 6 and 10 - the bounding, background and zone data
        """

        # Block 3 - bounding data
        bdngdata = self.blocks[2]
        count = len(bdngdata) // 28
        bdngstruct = struct.Struct('>llllHHxxxxxxxx')
        offset = 0
        bounding = []
        for i in range(count):
            datab = bdngstruct.unpack_from(bdngdata, offset)
            bounding.append([datab[0], datab[1], datab[2], datab[3], datab[4], datab[5]])
            offset += 28
        self.bounding = bounding

        # Block 5 - Bg data
        bgData = self.blocks[4]
        bgCount = len(bgData) // 28
        bgStruct = struct.Struct('>HxBxxxx16sHxx')
        offset = 0
        bgs = {}
        for i in range(bgCount):
            bg = bgStruct.unpack_from(bgData, offset)
            bgs[bg[0]] = bg[1:]
            offset += 28

        # Block 10 - zone data
        zonedata = self.blocks[9]
        zonestruct = struct.Struct('>HHHHxBxBBBBBxBBxBxBBxBxx')
        count = len(zonedata) // 28
        offset = 0
        zones = []
        for i in range(count):
            dataz = zonestruct.unpack_from(zonedata, offset)

            # Find the proper bounding
            boundObj = None
            id = dataz[6] # still correct, value 7
            for checkb in self.bounding:
                if checkb[4] == id: boundObj = checkb

            # Find the proper bg
            bgObj = None
            if dataz[11] in bgs:
                bgObj = bgs[dataz[11]]
            else: print('WARNING: BACKGROUND DATA NOT FOUND! THIS IS VERY VERY VERY VERY BAD!!!!!!!!!!!!!')

            zones.append(ZoneItem(
                dataz[0], dataz[1], dataz[2], dataz[3],
                dataz[4], dataz[5], dataz[6], dataz[7],
                dataz[8], dataz[9], dataz[10], dataz[11],
                dataz[12], dataz[13], dataz[14], dataz[15],
                boundObj, bgObj, i))
            offset += 28
        self.zones = zones

    def LoadLocations(self):
        """
        Loads block 11, the locations
        """
        locdata = self.blocks[10]
        locstruct = struct.Struct('>HHHHBxxx')
        count = len(locdata) // 12
        offset = 0
        locations = []
        for i in range(count):
            data = locstruct.unpack_from(locdata, offset)
            locations.append(LocationItem(data[0], data[1], data[2], data[3], data[4]))
            offset += 12
        self.locations = locations

    def LoadLayer(self, tileidx, layerdata):
        """
        Loads a specific object layer from a bytes object
        """
        objcount = len(layerdata) // 16
        objstruct = struct.Struct('>HhhHHB')
        offset = 0
        z = (2 - tileidx) * 8192

        layer = self.layers[tileidx]
        append = layer.append
        unpack = objstruct.unpack_from
        for i in range(objcount):
            data    = unpack(layerdata, offset)
            # Just for clarity, assigning these things to variables explaining what they are
            tileset = data[0] >> 12
            idx     = data[0] & 4095
            layer   = tileidx
            x       = data[1]
            y       = data[2]
            width   = data[3]
            height  = data[4]
            objdata = data[5]

            if tileset == 0:
                from_ = OBJECT_FROM_MAIN
                objidx = idx
            else:
                where = (tileset, idx)
                if where in EmbeddedObjectsLoadedFrom:
                    objidx = EmbeddedObjectsLoadedFrom[where]
                else:
                    objidx = 0

                if isinstance(objidx, int):
                    from_ = OBJECT_FROM_EMBED
                else:
                    from_ = OBJECT_FROM_MEGA

            append(ObjectItem(from_, objidx, layer, x, y, width, height, z, objdata))
            z += 1
            offset += 16

    def LoadPaths(self):
        """
        Loads block 13, the paths
        """
        # Path struct: >BbHHxBxxxx
        pathdata = self.blocks[13]
        pathcount = len(pathdata) // 12
        pathstruct = struct.Struct('>BbHHxBxxxx')
        offset = 0
        unpack = pathstruct.unpack_from
        pathinfo = []
        paths = []
        for i in range(pathcount):
            data = unpack(pathdata, offset)
            nodes = self.LoadPathNodes(data[2], data[3])
            add2p = {'id': int(data[0]),
                     'unk1': int(data[1]), # no idea what this is
                     'nodes': [],
                     'loops': data[4] == 2,
                     }
            for node in nodes:
                add2p['nodes'].append(node)
            pathinfo.append(add2p)

            offset += 12

        for i in range(pathcount):
            xpi = pathinfo[i]
            for j, xpj in enumerate(xpi['nodes']):
                paths.append(PathItem(xpj['x'], xpj['y'], xpi, xpj, 0, 0, 0, 0))


        self.pathdata = pathinfo
        self.paths = paths

    def LoadPathNodes(self, startindex, count):
        """
        Loads block 14, the path nodes
        """
        # PathNode struct: >HHffhHBBBx
        ret = []
        nodedata = self.blocks[14]
        nodestruct = struct.Struct('>HHffhHBBBx') # updated struct -- MrRean
        offset = startindex * 20
        unpack = nodestruct.unpack_from
        for i in range(count):
            data = unpack(nodedata, offset)
            ret.append({'x': int(data[0]),
                        'y': int(data[1]),
                        'speed': float(data[2]),
                        'accel': float(data[3]),
                        'delay': int(data[4]),
                        'unk1': int(data[5]), # unknowns, probably really not ints, just setting to 0 for now
                        'unk2': int(data[6]),
                        'unk3': int(data[7]),
                        'unk4': int(data[8]),
            })
            offset += 20
        return ret

    def LoadComments(self):
        """
        Loads the comments from self.Metadata
        """
        self.comments = []
        b = self.Metadata.binData('InLevelComments_A%d' % self.areanum)
        if b is None: return
        idx = 0
        while idx < len(b):
            xpos  = b[idx]   << 24
            xpos |= b[idx+1] << 16
            xpos |= b[idx+2] << 8
            xpos |= b[idx+3]
            idx += 4
            ypos  = b[idx]   << 24
            ypos |= b[idx+1] << 16
            ypos |= b[idx+2] << 8
            ypos |= b[idx+3]
            idx += 4
            tlen  = b[idx]   << 24
            tlen |= b[idx+1] << 16
            tlen |= b[idx+2] << 8
            tlen |= b[idx+3]
            idx += 4
            s = ''
            for char in range(tlen):
                s += chr(b[idx])
                idx += 1

            com = CommentItem(xpos, ypos, s)
            com.listitem = QtWidgets.QListWidgetItem()

            self.comments.append(com)

            com.UpdateListItem()

    def SaveTilesetNames(self):
        """
        Saves the tileset names back to block 1
        """
        self.blocks[0] = ''.join([
            self.tileset0name.ljust(32, '\0'),
            self.tileset1name.ljust(32, '\0'),
            self.tileset2name.ljust(32, '\0'),
            self.tileset3name.ljust(32, '\0'),
            ]).encode('latin-1')

    def SaveOptions(self):
        """
        Saves block 2, the general options
        """
        optstruct = struct.Struct('>xxBBxxxxxBHxBBBBxxBHH')
        buffer = bytearray(24)
        optstruct.pack_into(buffer, 0, self.unk1, self.unk2, self.wrapedges, self.timelimit, self.unk3, self.unk4, self.unk5, self.unk6, self.unk7, self.timelimit2, self.timelimit3)
        self.blocks[1] = bytes(buffer)

    def SaveLayer(self, idx):
        """
        Saves an object layer to a bytes object
        """
        layer = self.layers[idx]
        if not layer:
            return None

        offset = 0
        objstruct = struct.Struct('>HhhHHB')
        buffer = bytearray((len(layer) * 16) + 2)
        for obj in layer:
            if obj.from_ == OBJECT_FROM_MAIN:
                tset, type = 0, obj.idx
            else:
                tset, type = 1, self.compiledTilesetIdxs[(obj.from_, obj.idx)]
            objstruct.pack_into(buffer,
                                offset,
                                int((tset << 12) | type),
                                int(obj.objx),
                                int(obj.objy),
                                int(obj.width),
                                int(obj.height),
                                int(obj.data))
            offset += 16
        buffer[offset] = 0xFF
        buffer[offset + 1] = 0xFF
        return bytes(buffer)

    def SaveEntrances(self):
        """
        Saves the entrances back to block 7
        """
        offset = 0
        entstruct = struct.Struct('>HHxBxxBBBBBBxBxBBBBBBx')
        buffer = bytearray(len(self.entrances) * 24)
        zonelist = self.zones
        for entrance in self.entrances:
            zoneID = MapPositionToZoneID(zonelist, entrance.objx, entrance.objy)
            entstruct.pack_into(buffer, offset, int(entrance.objx), int(entrance.objy), int(entrance.unk05), int(entrance.entid), int(entrance.destarea), int(entrance.destentrance), int(entrance.enttype), int(entrance.unk0C), zoneID, int(entrance.unk0F), int(entrance.entsettings), int(entrance.unk12), int(entrance.unk13), int(entrance.unk14), int(entrance.unk15), int(entrance.unk16))
            offset += 24
        self.blocks[6] = bytes(buffer)

    def SavePaths(self):
        """
        Saves the paths back to block 13
        """
        pathstruct = struct.Struct('>BbHHxBxxxx')
        nodecount = 0
        for path in self.pathdata:
            nodecount += len(path['nodes'])
        nodebuffer = bytearray(nodecount * 20)
        nodeoffset = 0
        nodeindex = 0
        offset = 0
        buffer = bytearray(len(self.pathdata) * 12)

        for path in self.pathdata:
            if(len(path['nodes']) < 1): continue
            self.WritePathNodes(nodebuffer, nodeoffset, path['nodes'])

            pathstruct.pack_into(buffer, offset, int(path['id']), 0, int(nodeindex), int(len(path['nodes'])), 2 if path['loops'] else 0)
            offset += 12
            nodeoffset += len(path['nodes']) * 20
            nodeindex += len(path['nodes'])

        self.blocks[13] = bytes(buffer)
        self.blocks[14] = bytes(nodebuffer)

    def WritePathNodes(self, buffer, offst, nodes):
        """
        Writes the pathnode data to the block 14 bytearray
        """
        offset = int(offst)

        nodestruct = struct.Struct('>HHffhHBBBx')
        for node in nodes:
            nodestruct.pack_into(buffer, offset, int(node['x']), int(node['y']), float(node['speed']), float(node['accel']), int(node['delay']), 0, 0, 0, 0)
            offset += 20

    def SaveSprites(self):
        """
        Saves the sprites back to block 8
        """
        offset = 0
        sprstruct = struct.Struct('>HHH10sBB3sxxx')
        buffer = bytearray((len(self.sprites) * 24) + 4)
        f_int = int
        for sprite in self.sprites:
            try:
                sprstruct.pack_into(buffer, offset, f_int(sprite.type), f_int(sprite.objx), f_int(sprite.objy), sprite.spritedata[:10], MapPositionToZoneID(self.zones, sprite.objx, sprite.objy, True), 0, sprite.spritedata[10:] + b'\0')
            except struct.error:
                # Hopefully this will solve the mysterious bug, and will
                # soon no longer be necessary.
                raise ValueError('SaveSprites struct.error. Current sprite data dump:\n' + \
                    str(offset) + '\n' + \
                    str(sprite.type) + '\n' + \
                    str(sprite.objx) + '\n' + \
                    str(sprite.objy) + '\n' + \
                    str(sprite.spritedata[:6]) + '\n' + \
                    str(sprite.zoneID) + '\n' + \
                    str(bytes([sprite.spritedata[7],])) + '\n',
                    )
            offset += 24
        buffer[offset] = 0xFF
        buffer[offset + 1] = 0xFF
        buffer[offset + 2] = 0xFF
        buffer[offset + 3] = 0xFF
        self.blocks[7] = bytes(buffer)

    def SaveLoadedSprites(self):
        """
        Saves the list of loaded sprites back to block 9
        """
        ls = []
        for sprite in self.sprites:
            if sprite.type not in ls: ls.append(sprite.type)
        ls.sort()

        offset = 0
        sprstruct = struct.Struct('>Hxx')
        buffer = bytearray(len(ls) * 4)
        for s in ls:
            sprstruct.pack_into(buffer, offset, int(s))
            offset += 4
        self.blocks[8] = bytes(buffer)

    def SaveZones(self):
        """
        Saves blocks 10, 3, and 5; the zone data, boundings, and bg data respectively
        """
        bdngstruct = struct.Struct('>llllHHxxxxxxxx')
        bgStruct = struct.Struct('>HxBxxxx16sHxx')
        zonestruct = struct.Struct('>HHHHxBxBBBBBxBBxBxBBxBxx')
        offset = 0
        i = 0
        zcount = len(self.zones)
        buffer2 = bytearray(28 * zcount)
        buffer4 = bytearray(28 * zcount)
        buffer9 = bytearray(28 * zcount)
        for z in self.zones:
            bdngstruct.pack_into(buffer2, offset, z.yupperbound, z.ylowerbound, z.yupperbound2, z.ylowerbound2, i, z.unknownbnf)
            bgStruct.pack_into(buffer4, offset, i, z.bgUnk1, z.bgName.encode('latin-1').ljust(16, b'\0'), z.bgUnk2)
            zonestruct.pack_into(buffer9, offset,
                z.objx, z.objy, z.width, z.height,
                z.modeldark, z.unk1, z.id, i,
                z.cammode, z.camzoom, z.visibility, i,
                z.unk2, z.music, z.unk3, z.unk4)
            offset += 28
            i += 1

        self.blocks[2] = bytes(buffer2)
        self.blocks[4] = bytes(buffer4)
        self.blocks[9] = bytes(buffer9)

    def SaveLocations(self):
        """
        Saves block 11, the location data
        """
        locstruct = struct.Struct('>HHHHBxxx')
        offset = 0
        locationcount = len(self.locations)
        buffer = bytearray(12 * locationcount)

        for location in self.locations:
            locstruct.pack_into(buffer, offset, int(location.objx), int(location.objy), int(location.width), int(location.height), int(location.id))
            offset += 12

        self.blocks[10] = bytes(buffer)

    def RegenerateTilesets(self, areaNum, separateTilesets):
        """
        Regenerates the tileset data. Call this before the other
        SaveXxxx functions!
        """

        self.compiledTilesetIdxs = {} # (mega/embed, name/idx) -> num

        # Get all of the OneTileset objects used in the level
        oneTsetObjNames = set()
        for layer in self.layers:
            for obj in layer:
                if obj.from_ == OBJECT_FROM_MEGA:
                    oneTsetObjNames.add(obj.idx)

        # Nuke the names on the embedded objects and keep track of their indexes in the compiled tileset
        for i, obj in enumerate(EmbeddedObjects):
            obj.name = ''
            self.compiledTilesetIdxs[(OBJECT_FROM_EMBED, i)] = i

        # Add the OneTileset objects used and also keep track of their indexes in the compiled tileset
        oneTsetObjs = []
        for i, name in enumerate(oneTsetObjNames):
            oneTsetObjs.append(OneTilesetObjects[name])
            self.compiledTilesetIdxs[(OBJECT_FROM_MEGA, name)] = len(EmbeddedObjects) + i

        if separateTilesets:
            baseTilesetName = 'level'
        else:
            baseTilesetName = gibberish.generate_word()
        baseTilesetName += '_' + str(areaNum + 1)

        # Save
        allObjs = EmbeddedObjects + oneTsetObjs
        tilesets = nsmbulib.Tileset.save(allObjs, baseTilesetName)

        # Pick tileset names
        self.tileset0name = ['Pa0_jyotyu', 'Pa0_jyotyu_chika', 'Pa0_jyotyu_yougan', 'Pa0_jyotyu_yougan2'][mainWindow.objPicker.mainTilesetDropdown.currentIndex()]
        self.tileset1name = 'Pa1_' + baseTilesetName
        self.tileset2name = self.tileset3name = ''
        if len(tilesets) >= 2:
            self.tileset2name = 'Pa2_' + baseTilesetName
        if len(tilesets) == 3:
            self.tileset3name = 'Pa3_' + baseTilesetName

        # Put everything in a dict
        tilesetsDict = {self.tileset1name: tilesets[0]}
        if len(tilesets) >= 2:
            tilesetsDict[self.tileset2name] = tilesets[1]
        if len(tilesets) == 3:
            tilesetsDict[self.tileset3name] = tilesets[2]

        # Return
        return tilesetsDict

#####################################################################
############################ BACKGROUNDS ############################
#####################################################################

class AbstractBackground():
    """
    A class that represents an abstract background for a zone (both bgA and bgB)
    """
    def __init__(self, xScroll=1, yScroll=1, xPos=1, yPos=1):
        self.xScroll = xScroll
        self.yScroll = yScroll
        self.xPos = xPos
        self.yPos = yPos

    def save(idnum=0):
        return b''


class Background_NSMBU(AbstractBackground):
    """
    A class that represents a background from New Super Mario Bros. U
    """
    def __init__(self, xScroll=1, yScroll=1, xPos=1, yPos=1, name=''):
        super().__init__(xScroll, yScroll, xPos, yPos)
        self.name = name

    def loadFrom(self, data):
        if len(data) != 28:
            raise ValueError('Wrong data length: must be 28 bytes exactly')

        bgstruct = struct.Struct('>Hbbbbxx15sbxxxx')
        bgvalues = bgstruct.unpack(data)
        id = bgvalues[0]
        self.xScroll = bgvalues[1]
        self.yScroll = bgvalues[2]
        self.xPos = bgvalues[3]
        self.yPos = bgvalues[4]
        self.name = bgvalues[5].split(b'\0')[0].decode('utf-8')
        self.unk1 = bgvalues[6]

        return id

    def save(idnum=0):
        bgstruct = struct.struct('>Hbbbbxx15sbxxxx')
        return # not yet implemented properly; ignore the stuff below
        settings = struct.pack('>Hbbbbxx', idnum, self.xScroll, self.yScroll, self.xPos, self.yPos)
        name = self.name.encode('utf-8') + b'\0' * (20 - len(self.name))
        return settings + name

#####################################################################
######################### LEVELEDITOR ITEMS #########################
#####################################################################

class LevelEditorItem(QtWidgets.QGraphicsItem):
    """
    Class for any type of item that can show up in the level editor control
    """
    positionChanged = None # Callback: positionChanged(LevelEditorItem obj, int oldx, int oldy, int x, int y)
    autoPosChange = False
    dragoffsetx = 0
    dragoffsety = 0

    def __init__(self):
        """
        Generic constructor for level editor items
        """
        super().__init__()
        self.setFlag(self.ItemSendsGeometryChanges, True)


    def __lt__(self, other):
        return (self.objx * 100000 + self.objy) < (other.objx * 100000 + other.objy)

    def itemChange(self, change, value):
        """
        Makes sure positions don't go out of bounds and updates them as necessary
        """

        tileWidthMult = TileWidth / 16
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            # snap to 24x24
            newpos = value

            # snap even further if Alt isn't held
            # but -only- if OverrideSnapping is off
            if (not OverrideSnapping) and (not self.autoPosChange):
                if self.scene() is None: objectsSelected = False
                else: objectsSelected = any([isinstance(thing, ObjectItem) for thing in mainWindow.CurrentSelection])
                if QtWidgets.QApplication.keyboardModifiers() == Qt.AltModifier:
                    # Alt is held; don't snap
                    newpos.setX(int(int((newpos.x() + 0.75) / tileWidthMult) * tileWidthMult))
                    newpos.setY(int(int((newpos.y() + 0.75) / tileWidthMult) * tileWidthMult))
                elif not objectsSelected and self.isSelected() and len(mainWindow.CurrentSelection) > 1:
                    # Snap to 8x8, but with the dragoffsets
                    dragoffsetx, dragoffsety = int(self.dragoffsetx), int(self.dragoffsety)
                    if dragoffsetx < -(TileWidth / 2): dragoffsetx += TileWidth / 2
                    if dragoffsety < -(TileWidth / 2): dragoffsety += TileWidth / 2
                    if dragoffsetx == 0: dragoffsetx = -(TileWidth / 2)
                    if dragoffsety == 0: dragoffsety = -(TileWidth / 2)
                    referenceX = int((newpos.x() + TileWidth / 4 + TileWidth / 2 + dragoffsetx) / (TileWidth / 2)) * TileWidth / 2
                    referenceY = int((newpos.y() + TileWidth / 4 + TileWidth / 2 + dragoffsety) / (TileWidth / 2)) * TileWidth / 2
                    newpos.setX(referenceX - (TileWidth / 2 + dragoffsetx))
                    newpos.setY(referenceY - (TileWidth / 2 + dragoffsety))
                elif objectsSelected and self.isSelected():
                    # Objects are selected, too; move in sync by snapping to whole blocks
                    dragoffsetx, dragoffsety = int(self.dragoffsetx), int(self.dragoffsety)
                    if dragoffsetx == 0: dragoffsetx = -TileWidth
                    if dragoffsety == 0: dragoffsety = -TileWidth
                    referenceX = int((newpos.x() + TileWidth / 2 + TileWidth + dragoffsetx) / TileWidth) * TileWidth
                    referenceY = int((newpos.y() + TileWidth / 2 + TileWidth + dragoffsety) / TileWidth) * TileWidth
                    newpos.setX(referenceX - (TileWidth + dragoffsetx))
                    newpos.setY(referenceY - (TileWidth + dragoffsety))
                else:
                    # Snap to 8x8
                    newpos.setX(int(int((newpos.x() + TileWidth / 4) / (TileWidth / 2)) * TileWidth / 2))
                    newpos.setY(int(int((newpos.y() + TileWidth / 4) / (TileWidth / 2)) * TileWidth / 2))

            x = newpos.x()
            y = newpos.y()

            # don't let it get out of the boundaries
            if x < 0: newpos.setX(0)
            if x > 1023 * TileWidth: newpos.setX(1023 * TileWidth)
            if y < 0: newpos.setY(0)
            if y > 511 * TileWidth: newpos.setY(511 * TileWidth)

            # update the data
            x = int(newpos.x() / tileWidthMult)
            y = int(newpos.y() / tileWidthMult)
            if x != self.objx or y != self.objy:
                updRect = QtCore.QRectF(
                    self.x() + self.BoundingRect.x(),
                    self.y() + self.BoundingRect.y(),
                    self.BoundingRect.width(),
                    self.BoundingRect.height(),
                    )
                if self.scene() is not None:
                    self.scene().update(updRect)

                oldx = self.objx
                oldy = self.objy
                self.objx = x
                self.objy = y
                if self.positionChanged is not None:
                    self.positionChanged(self, oldx, oldy, x, y)

                SetDirty()

            return newpos

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def getFullRect(self):
        """
        Basic implementation that returns self.BoundingRect
        """
        return self.BoundingRect.translated(self.pos())

    def UpdateListItem(self, updateTooltipPreview=False):
        """
        Updates the list item
        """
        if not hasattr(self, 'listitem'): return
        if self.listitem is None: return

        if updateTooltipPreview:
            # It's just like Qt to make this overly complicated. XP
            img = self.renderInLevelIcon()
            byteArray = QtCore.QByteArray()
            buf = QtCore.QBuffer(byteArray)
            img.save(buf, 'PNG')
            byteObj = bytes(byteArray)
            b64 = base64.b64encode(byteObj).decode('utf-8')

            self.listitem.setToolTip('<img src="data:image/png;base64,' + b64 + '" />')

        self.listitem.setText(self.ListString())

    def renderInLevelIcon(self):
        """
        Renders an icon of this item as it appears in the level
        """
        # Constants:
        # Maximum size of the preview (it will be shrunk if it exceeds this)
        maxSize = QtCore.QSize(256, 256)
        # Percentage of the size to use for margins
        marginPct = 0.75
        # Maximum margin (24 = 1 block)
        maxMargin = 96

        # Get the full bounding rectangle
        br = self.getFullRect()

        # Expand the rect to add extra margins around the edges
        marginX = br.width() * marginPct
        marginY = br.height() * marginPct
        marginX = min(marginX, maxMargin)
        marginY = min(marginY, maxMargin)
        br.setX(br.x() - marginX)
        br.setY(br.y() - marginY)
        br.setWidth(br.width() + marginX)
        br.setHeight(br.height() + marginY)

        # Take the screenshot
        ScreenshotImage = QtGui.QImage(br.width(), br.height(), QtGui.QImage.Format_ARGB32)
        ScreenshotImage.fill(Qt.transparent)

        RenderPainter = QtGui.QPainter(ScreenshotImage)
        mainWindow.scene.render(
            RenderPainter,
            QtCore.QRectF(0, 0, br.width(), br.height()),
            br,
            )
        RenderPainter.end()

        # Shrink it if it's too big
        final = ScreenshotImage
        if ScreenshotImage.width() > maxSize.width() or ScreenshotImage.height() > maxSize.height():
            final = ScreenshotImage.scaled(
                maxSize,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
                )

        return final

    def boundingRect(self):
        """
        Required for Qt
        """
        return self.BoundingRect


class ObjectItem(LevelEditorItem):
    """
    Level editor item that represents an ingame object
    """

    def __init__(self, from_, idx, layer, x, y, width, height, z, data=13):
        """
        Creates an object with specific data
        """
        super().__init__()

        self.from_ = from_
        self.idx = idx

        self.objx = x
        self.objy = y
        self.layer = layer
        self.width = width
        self.height = height
        self.data = data
        self.objdata = None


        self.setFlag(self.ItemIsMovable, not ObjectsFrozen)
        self.setFlag(self.ItemIsSelectable, not ObjectsFrozen)
        self.UpdateRects()

        self.dragging = False
        self.dragstartx = -1
        self.dragstarty = -1
        self.objsDragging = {}

        global DirtyOverride
        DirtyOverride += 1
        self.setPos(x * TileWidth, y * TileWidth)
        DirtyOverride -= 1

        self.setZValue(z)
        self.UpdateTooltip()

        if layer == 0:
            self.setVisible(Layer0Shown)
        elif layer == 1:
            self.setVisible(Layer1Shown)
        elif layer == 2:
            self.setVisible(Layer2Shown)

        self.updateObjCache()
        self.UpdateTooltip()

    def SetType(self, from_, idx):
        """
        Sets the type of the object
        """
        self.from_ = from_
        self.idx = idx
        self.updateObjCache()
        self.update()

        self.UpdateTooltip()

    def UpdateTooltip(self):
        """
        Updates the tooltip
        """
        typeStrId = {OBJECT_FROM_MAIN: 4, OBJECT_FROM_MEGA: 5, OBJECT_FROM_EMBED: 6}[self.from_]
        type = trans.string('Objects', typeStrId, '[id]', self.idx)
        self.setToolTip(trans.string('Objects', 0, '[type]', type, '[width]', self.width, '[height]', self.height, '[layer]', self.layer))

    def updateObjCache(self):
        """
        Updates the rendered object data
        """
        self.objdata = self.getObjectDefinition().render(self.width, self.height)

    def getObjectDefinition(self):
        """
        Helper method to get the object definition that
        this object is an instance of
        """
        if self.from_ == OBJECT_FROM_MAIN:
            return MainObjects[self.idx]
        elif self.from_ == OBJECT_FROM_EMBED:
            return EmbeddedObjects[self.idx]
        elif self.from_ == OBJECT_FROM_MEGA:
            return OneTilesetObjects[self.idx]

    def UpdateRects(self):
        """
        Recreates the bounding and selection rects
        """
        self.prepareGeometryChange()
        GrabberSide = 5 / 24 * TileWidth
        self.BoundingRect = QtCore.QRectF(0, 0, TileWidth * self.width, TileWidth * self.height)
        self.SelectionRect = QtCore.QRectF(0, 0, (TileWidth * self.width) - 1, (TileWidth * self.height) - 1)
        self.GrabberRect = QtCore.QRectF((TileWidth * self.width) - GrabberSide, (TileWidth * self.height) - GrabberSide, GrabberSide, GrabberSide)
        self.LevelRect = QtCore.QRectF(self.objx, self.objy, self.width, self.height)

    def itemChange(self, change, value):
        """
        Makes sure positions don't go out of bounds and updates them as necessary
        """

        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            scene = self.scene()
            if scene is None: return value

            # snap to 24x24
            newpos = value
            newpos.setX(int((newpos.x() + TileWidth / 2) / TileWidth) * TileWidth)
            newpos.setY(int((newpos.y() + TileWidth / 2) / TileWidth) * TileWidth)
            x = newpos.x()
            y = newpos.y()

            # don't let it get out of the boundaries
            if x < 0: newpos.setX(0)
            if x > TileWidth * 1023: newpos.setX(TileWidth * 1023)
            if y < 0: newpos.setY(0)
            if y > TileWidth * 511: newpos.setY(TileWidth * 511)

            # update the data
            x = int(newpos.x() / TileWidth)
            y = int(newpos.y() / TileWidth)
            if x != self.objx or y != self.objy:
                self.LevelRect.moveTo(x, y)

                oldx = self.objx
                oldy = self.objy
                self.objx = x
                self.objy = y
                if self.positionChanged is not None:
                    self.positionChanged(self, oldx, oldy, x, y)

                SetDirty()

                #updRect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
                #scene.invalidate(updRect)

                scene.invalidate(self.x(), self.y(), self.width * TileWidth, self.height * TileWidth, QtWidgets.QGraphicsScene.BackgroundLayer)
                #scene.invalidate(newpos.x(), newpos.y(), self.width * TileWidth, self.height * TileWidth, QtWidgets.QGraphicsScene.BackgroundLayer)

            return newpos

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def paint(self, painter, option=0, widget=0):
        """
        Paints the object
        """
        global theme
        
        if setting('drawSpritesBehindL0'):
            # Paint the tile
            desty = 0
            for row in self.objdata:
                destx = 0
                for tile in row:
                    if tile is not None:
                        image = tile.reprImage(self.data, item=True)
                        if image is not None: # None = Blank tile
                            painter.drawImage(destx * TileWidth, desty * TileWidth, PIL.ImageQt.ImageQt(image))
                    destx += 1
                desty += 1

        if self.isSelected():
            painter.setPen(QtGui.QPen(theme.color('object_lines_s'), 1, Qt.DotLine))
            painter.drawRect(self.SelectionRect)
            painter.fillRect(self.SelectionRect, theme.color('object_fill_s'))

            painter.fillRect(self.GrabberRect, theme.color('object_lines_s'))


    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for resizing
        """
        if event.button() == Qt.LeftButton:
            if QtWidgets.QApplication.keyboardModifiers() == Qt.ControlModifier:
                layer = Area.layers[self.layer]
                if len(layer) == 0:
                    newZ = (2 - self.layer) * 8192
                else:
                    newZ = layer[-1].zValue() + 1

                currentZ = self.zValue()
                self.setZValue(newZ) # swap the Z values so it doesn't look like the cloned item is the old one
                newitem = ObjectItem(self.from_, self.idx, self.layer, self.objx, self.objy, self.width, self.height, currentZ, 0)
                layer.append(newitem)
                mainWindow.scene.addItem(newitem)
                mainWindow.scene.clearSelection()
                self.setSelected(True)

                SetDirty()

        if self.isSelected() and self.GrabberRect.contains(event.pos()):
            # start dragging
            self.dragging = True
            self.dragstartx = int((event.pos().x() - TileWidth / 2) / TileWidth)
            self.dragstarty = int((event.pos().y() - TileWidth / 2) / TileWidth)
            self.objsDragging = {}
            for selitem in mainWindow.scene.selectedItems():
                if not isinstance(selitem, ObjectItem): continue
                self.objsDragging[selitem] = [selitem.width, selitem.height]
            event.accept()
        else:
            LevelEditorItem.mousePressEvent(self, event)
            self.dragging = False
            self.objsDragging = {}
        self.UpdateTooltip()


    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed for resizing
        """
        if event.buttons() != Qt.NoButton and self.dragging:
            # resize it
            dsx = self.dragstartx
            dsy = self.dragstarty

            clickedx = int((event.pos().x() - TileWidth / 2) / TileWidth)
            clickedy = int((event.pos().y() - TileWidth / 2) / TileWidth)

            cx = self.objx
            cy = self.objy

            if clickedx < 0: clickedx = 0
            if clickedy < 0: clickedy = 0

            if clickedx != dsx or clickedy != dsy:
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                for obj in self.objsDragging:

                    self.objsDragging[obj][0] += clickedx - dsx
                    self.objsDragging[obj][1] += clickedy - dsy
                    newWidth = self.objsDragging[obj][0]
                    newHeight = self.objsDragging[obj][1]
                    if newWidth < 1: newWidth = 1
                    if newHeight < 1: newHeight = 1
                    obj.width = newWidth
                    obj.height = newHeight

                    obj.updateObjCache()

                    oldrect = obj.BoundingRect
                    oldrect.translate(cx * TileWidth, cy * TileWidth)
                    newrect = QtCore.QRectF(obj.x(), obj.y(), obj.width * TileWidth, obj.height * TileWidth)
                    updaterect = oldrect.united(newrect)

                    obj.UpdateRects()
                    obj.scene().update(updaterect)
                SetDirty()

            event.accept()
        else:
            LevelEditorItem.mouseMoveEvent(self, event)
        self.UpdateTooltip()


    def delete(self):
        """
        Delete the object from the level
        """
        Area.RemoveFromLayer(self)
        self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        mainWindow.updateTileCountLabel()


class ZoneItem(LevelEditorItem):
    """
    Level editor item that represents a zone
    """

    def __init__(self, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, bounding=None, bg=None, id=None):
        """
        Creates a zone with specific data
        """
        super().__init__()

        self.font = NumberFont
        self.TitlePos = QtCore.QPointF(10, 10 + QtGui.QFontMetrics(self.font).height())

        # Hey, you. Yeah, you, reading this script. You should help out and get these unknowns documented.
        # Seriously. Give us a hand here.
        self.objx = a
        self.objy = b
        self.width = c
        self.height = d
        self.modeldark = e
        self.unk1 = f # self.terraindark, possibly?
        self.terraindark = 0 # TEMPORARY
        self.id = g
        boundingblockid = h
        self.cammode = i
        self.camzoom = j
        self.visibility = k
        bgblockid = l
        self.unk2 = m # Multiplayer tracking, maybe?
        self.camtrack = 0 # TEMPORARY
        self.music = n
        self.unk3 = o # One of these is probably self.sfxmod
        self.unk4 = p
        self.sfxmod = 0 # TEMPORARY
        self.UpdateRects()

        self.aux = set()

        if id is not None:
            self.id = id

        self.UpdateTitle()

        if bounding is not None:
            self.yupperbound = bounding[0]
            self.ylowerbound = bounding[1]
            self.yupperbound2 = bounding[2]
            self.ylowerbound2 = bounding[3]
            self.entryid = bounding[4]
            self.unknownbnf = bounding[5]
        else:
            self.yupperbound = 0
            self.ylowerbound = 0
            self.yupperbound2 = 0
            self.ylowerbound2 = 0
            self.entryid = 0
            self.unknownbnf = 0

        if bg is not None:
            self.bgUnk1 = bg[0]
            self.bgName = bg[1].rstrip(b'\0').decode('latin-1')
            self.bgUnk2 = bg[2]
        else:
            self.bgUnk1 = 0
            self.bgName = 'blank'
            self.bgUnk2 = 0

        self.dragging = False
        self.dragstartx = -1
        self.dragstarty = -1

        global DirtyOverride
        DirtyOverride += 1
        self.setPos(int(a * TileWidth / 16), int(b * TileWidth / 16))
        DirtyOverride -= 1
        self.setZValue(50000)


    def UpdateTitle(self):
        """
        Updates the zone's title
        """
        self.title = trans.string('Zones', 0, '[num]', self.id + 1)


    def UpdateRects(self):
        """
        Updates the zone's bounding rectangle
        """
        if hasattr(mainWindow, 'ZoomLevel'):
            grabberWidth = 500 / mainWindow.ZoomLevel
            if grabberWidth < 5: grabberWidth = 5
        else: grabberWidth = 5
        grabberWidth *= TileWidth / 24

        self.prepareGeometryChange()
        mult = TileWidth / 16
        self.BoundingRect = QtCore.QRectF(0, 0, self.width * mult, self.height * mult)
        self.ZoneRect = QtCore.QRectF(self.objx, self.objy, self.width, self.height)
        self.DrawRect = QtCore.QRectF(3, 3, int(self.width * mult) - 6, int(self.height * mult) - 6)
        self.GrabberRectTL = QtCore.QRectF(0, 0, grabberWidth, grabberWidth)
        self.GrabberRectTR = QtCore.QRectF(int(self.width * mult) - grabberWidth, 0, grabberWidth, grabberWidth)
        self.GrabberRectBL = QtCore.QRectF(0, int(self.height * mult) - grabberWidth, grabberWidth, grabberWidth)
        self.GrabberRectBR = QtCore.QRectF(int(self.width * mult) - grabberWidth, int(self.height * mult) - grabberWidth, grabberWidth, grabberWidth)


    def paint(self, painter, option, widget):
        """
        Paints the zone on screen
        """
        global theme

        #painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Paint an indicator line to show the leftmost edge o
        # where entrances can be safely placed
        if TileWidth * 13 < self.DrawRect.width():
            painter.setPen(QtGui.QPen(theme.color('zone_entrance_helper'), 2 * TileWidth / 24))
            lineStart = QtCore.QPointF(self.DrawRect.x() + (TileWidth * 13), self.DrawRect.y())
            lineEnd = QtCore.QPointF(self.DrawRect.x() + (TileWidth * 13), self.DrawRect.y() + self.DrawRect.height())
            #painter.drawLine(lineStart, lineEnd)

        # Now paint the borders
        painter.setPen(QtGui.QPen(theme.color('zone_lines'), 3 * TileWidth / 24))
        if (self.visibility >= 32) and RealViewEnabled:
            painter.setBrush(QtGui.QBrush(theme.color('zone_dark_fill')))
        painter.drawRect(self.DrawRect)

        # And text
        painter.setPen(QtGui.QPen(theme.color('zone_text'), 3 * TileWidth / 24))
        painter.setFont(self.font)
        painter.drawText(self.TitlePos, self.title)

        # And corners ("grabbers")
        GrabberColor = theme.color('zone_corner')
        painter.fillRect(self.GrabberRectTL, GrabberColor)
        painter.fillRect(self.GrabberRectTR, GrabberColor)
        painter.fillRect(self.GrabberRectBL, GrabberColor)
        painter.fillRect(self.GrabberRectBR, GrabberColor)


    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for resizing
        """

        if self.GrabberRectTL.contains(event.pos()):
            # start dragging
            self.dragging = True
            self.dragstartx = int(event.pos().x() / TileWidth * 16)
            self.dragstarty = int(event.pos().y() / TileWidth * 16)
            self.dragcorner = 1
            event.accept()
        elif self.GrabberRectTR.contains(event.pos()):
            self.dragging = True
            self.dragstartx = int(event.pos().x() / TileWidth * 16)
            self.dragstarty = int(event.pos().y() / TileWidth * 16)
            self.dragcorner = 2
            event.accept()
        elif self.GrabberRectBL.contains(event.pos()):
            self.dragging = True
            self.dragstartx = int(event.pos().x() / TileWidth * 16)
            self.dragstarty = int(event.pos().y() / TileWidth * 16)
            self.dragcorner = 3
            event.accept()
        elif self.GrabberRectBR.contains(event.pos()):
            self.dragging = True
            self.dragstartx = int(event.pos().x() / TileWidth * 16)
            self.dragstarty = int(event.pos().y() / TileWidth * 16)
            self.dragcorner = 4
            event.accept()
        else:
            LevelEditorItem.mousePressEvent(self, event)
            self.dragging = False


    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed for resizing
        """

        if event.buttons() != Qt.NoButton and self.dragging:
            # resize it
            dsx = self.dragstartx
            dsy = self.dragstarty
            clickedx = int(event.pos().x() / TileWidth * 16)
            clickedy = int(event.pos().y() / TileWidth * 16)
            corner = self.dragcorner

            cx = self.objx
            cy = self.objy

            checkwidth = self.width - 128
            checkheight = self.height - 128
            if corner == 1:
                if clickedx >= checkwidth: clickedx = checkwidth - 1
                if clickedy >= checkheight: clickedy = checkheight - 1
            elif corner == 2:
                if clickedx < 0: clickedx = 0
                if clickedy >= checkheight: clickedy = checkheight - 1
            elif corner == 3:
                if clickedx >= checkwidth: clickedx = checkwidth - 1
                if clickedy < 0: clickedy = 0
            elif corner == 4:
                if clickedx < 0: clickedx = 0
                if clickedy < 0: clickedy = 0

            if clickedx != dsx or clickedy != dsy:
                #if (cx + clickedx - dsx) < 16: clickedx += (16 - (cx + clickedx - dsx))
                #if (cy + clickedy - dsy) < 16: clickedy += (16 - (cy + clickedy - dsy))

                self.dragstartx = clickedx
                self.dragstarty = clickedy
                xdelta = clickedx - dsx
                ydelta = clickedy - dsy

                if corner == 1:
                    self.objx += xdelta
                    self.objy += ydelta
                    self.dragstartx -= xdelta
                    self.dragstarty -= ydelta
                    self.width -= xdelta
                    self.height -= ydelta
                elif corner == 2:
                    self.objy += ydelta
                    self.dragstarty -= ydelta
                    self.width += xdelta
                    self.height -= ydelta
                elif corner == 3:
                    self.objx += xdelta
                    self.dragstartx -= xdelta
                    self.width -= xdelta
                    self.height += ydelta
                elif corner == 4:
                    self.width += xdelta
                    self.height += ydelta

                if self.width < 16 * TileWidth / 24:
                    self.objx -= (16 * TileWidth / 24 - self.width)
                    self.width = 16 * TileWidth / 24
                if self.height < 16 * TileWidth / 24:
                    self.objy -= (16 * TileWidth / 24 - self.height)
                    self.height = 16 * TileWidth / 24

                if self.objx < 16 * TileWidth / 24:
                    self.width -= (16 * TileWidth / 24 - self.objx)
                    self.objx = 16 * TileWidth / 24
                if self.objy < 16 * TileWidth / 24:
                    self.height -= (16 * TileWidth / 24 - self.objy)
                    self.objy = 16 * TileWidth / 24

                oldrect = self.BoundingRect
                oldrect.translate(cx * TileWidth / 16, cy * TileWidth / 16)
                newrect = QtCore.QRectF(self.x(), self.y(), self.width * TileWidth / 16, self.height * TileWidth / 16)
                updaterect = oldrect.united(newrect)
                updaterect.setTop(updaterect.top() - 3)
                updaterect.setLeft(updaterect.left() - 3)
                updaterect.setRight(updaterect.right() + 3)
                updaterect.setBottom(updaterect.bottom() + 3)

                self.UpdateRects()
                self.setPos(int(self.objx * TileWidth / 16), int(self.objy * TileWidth / 16))
                self.scene().update(updaterect)

                mainWindow.levelOverview.update()

                # Call the zoneRepositioned function of all
                # the sprite auxs for this zone
                for a in self.aux:
                    a.zoneRepositioned()

                SetDirty()

            event.accept()
        else:
            LevelEditorItem.mouseMoveEvent(self, event)

    def itemChange(self, change, value):
        """
        Avoids snapping for zones
        """
        return QtWidgets.QGraphicsItem.itemChange(self, change, value)


class LocationItem(LevelEditorItem):
    """
    Level editor item that represents a sprite location
    """
    sizeChanged = None # Callback: sizeChanged(SpriteItem obj, int width, int height)

    def __init__(self, x, y, width, height, id):
        """
        Creates a location with specific data
        """
        super().__init__()

        self.font = NumberFont
        self.TitlePos = QtCore.QPointF(TileWidth / 4, TileWidth / 4)
        self.objx = x
        self.objy = y
        self.width = width
        self.height = height
        self.id = id
        self.listitem = None
        self.UpdateTitle()
        self.UpdateRects()

        self.setFlag(self.ItemIsMovable, not LocationsFrozen)
        self.setFlag(self.ItemIsSelectable, not LocationsFrozen)

        global DirtyOverride
        DirtyOverride += 1
        self.setPos(int(x * TileWidth / 16), int(y * TileWidth / 16))
        DirtyOverride -= 1

        self.dragging = False
        self.setZValue(20000)

        self.setVisible(LocationsShown)


    def ListString(self):
        """
        Returns a string that can be used to describe the location in a list
        """
        return trans.string('Locations', 2, '[id]', self.id, '[width]', int(self.width), '[height]', int(self.height), '[x]', int(self.objx), '[y]', int(self.objy))


    def UpdateTitle(self):
        """
        Updates the location's title
        """
        self.title = trans.string('Locations', 0, '[id]', self.id)
        self.UpdateListItem()


    def __lt__(self, other):
        return self.id < other.id


    def UpdateRects(self):
        """
        Updates the location's bounding rectangle
        """
        self.prepareGeometryChange()
        if self.width == 0: self.width == 1
        if self.height == 0: self.height == 1
        GrabberSide = 5 * TileWidth / 24
        self.BoundingRect = QtCore.QRectF(0, 0, self.width * TileWidth / 16, self.height * TileWidth / 16)
        self.SelectionRect = QtCore.QRectF(self.objx * TileWidth / 16, self.objy * TileWidth / 16, self.width * TileWidth / 16, self.height * TileWidth / 16)
        self.ZoneRect = QtCore.QRectF(self.objx, self.objy, self.width, self.height)
        self.DrawRect = QtCore.QRectF(1, 1, (self.width * TileWidth / 16) - 2, (self.height * TileWidth / 16) - 2)
        self.GrabberRect = QtCore.QRectF(((TileWidth / 16) * self.width) - GrabberSide, ((TileWidth / 16) * self.height) - GrabberSide, GrabberSide, GrabberSide)
        self.UpdateListItem()


    def paint(self, painter, option, widget):
        """
        Paints the location on screen
        """
        global theme

        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw the purple rectangle
        if not self.isSelected():
            painter.setBrush(QtGui.QBrush(theme.color('location_fill')))
            painter.setPen(QtGui.QPen(theme.color('location_lines'), TileWidth / 24))
        else:
            painter.setBrush(QtGui.QBrush(theme.color('location_fill_s')))
            painter.setPen(QtGui.QPen(theme.color('location_lines_s'), TileWidth / 24, Qt.DotLine))
        painter.drawRect(self.DrawRect)

        # Draw the ID
        painter.setPen(QtGui.QPen(theme.color('location_text')))
        painter.setFont(self.font)
        painter.drawText(QtCore.QRectF(0, 0, TileWidth / 2, TileWidth / 2), Qt.AlignCenter, self.title)

        # Draw the resizer rectangle, if selected
        if self.isSelected(): painter.fillRect(self.GrabberRect, theme.color('location_lines_s'))


    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for resizing
        """
        if self.isSelected() and self.GrabberRect.contains(event.pos()):
            # start dragging
            self.dragging = True
            self.dragstartx = int(event.pos().x() / TileWidth * 16)
            self.dragstarty = int(event.pos().y() / TileWidth * 16)
            event.accept()
        else:
            LevelEditorItem.mousePressEvent(self, event)
            self.dragging = False


    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed for resizing
        """
        if event.buttons() != Qt.NoButton and self.dragging:
            # resize it
            dsx = self.dragstartx
            dsy = self.dragstarty
            clickedx = event.pos().x() / TileWidth * 16
            clickedy = event.pos().y() / TileWidth * 16

            cx = self.objx
            cy = self.objy

            if clickedx < 0: clickedx = 0
            if clickedy < 0: clickedy = 0

            if clickedx != dsx or clickedy != dsy:
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                self.width += clickedx - dsx
                self.height += clickedy - dsy

                oldrect = self.BoundingRect
                oldrect.translate(cx * TileWidth / 16, cy * TileWidth / 16)
                newrect = QtCore.QRectF(self.x(), self.y(), self.width * TileWidth / 16, self.height * TileWidth / 16)
                updaterect = oldrect.united(newrect)

                self.UpdateRects()
                self.scene().update(updaterect)
                SetDirty()

                if self.sizeChanged is not None:
                    self.sizeChanged(self, self.width, self.height)

            event.accept()
        else:
            LevelEditorItem.mouseMoveEvent(self, event)


    def delete(self):
        """
        Delete the location from the level
        """
        loclist = mainWindow.locationList
        mainWindow.UpdateFlag = True
        loclist.takeItem(loclist.row(self.listitem))
        mainWindow.UpdateFlag = False
        loclist.selectionModel().clearSelection()
        Area.locations.remove(self)
        self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())


class SpriteItem(LevelEditorItem):
    """
    Level editor item that represents a sprite
    """
    BoundingRect = QtCore.QRectF(0, 0, TileWidth, TileWidth)
    SelectionRect = QtCore.QRectF(0, 0, TileWidth - 1, TileWidth - 1)

    def __init__(self, type, x, y, data):
        """
        Creates a sprite with specific data
        """
        super().__init__()

        self.font = NumberFont
        self.type = type
        self.objx = x
        self.objy = y
        self.spritedata = data
        self.listitem = None
        self.LevelRect = QtCore.QRectF(self.objx / 16, self.objy / 16, TileWidth / 16, TileWidth / 16)
        self.ChangingPos = False

        SLib.SpriteImage.loadImages()
        self.ImageObj = SLib.SpriteImage(self)

        try:
            sname = Sprites[type].name
            self.name = sname
        except:
            self.name = 'UNKNOWN'

        self.InitializeSprite()

        self.setFlag(self.ItemIsMovable, not SpritesFrozen)
        self.setFlag(self.ItemIsSelectable, not SpritesFrozen)

        global DirtyOverride
        DirtyOverride += 1
        self.setPos(
            int((self.objx + self.ImageObj.xOffset) * TileWidth / 16),
            int((self.objy + self.ImageObj.yOffset) * TileWidth / 16),
            )
        DirtyOverride -= 1

        self.setVisible(SpritesShown)
        self.updateScene()

    def SetType(self, type):
        """
        Sets the type of the sprite
        """
        self.type = type
        self.InitializeSprite()

    def ListString(self):
        """
        Returns a string that can be used to describe the sprite in a list
        """
        baseString = trans.string('Sprites', 1, '[name]', self.name, '[x]', self.objx, '[y]', self.objy)

        global SpriteListData
        SpritesThatActivateAnEvent = set(SpriteListData[0])
        SpritesThatActivateAnEventNyb0 = set(SpriteListData[1])
        SpritesTriggeredByAnEventNyb1 = set(SpriteListData[2])
        SpritesTriggeredByAnEventNyb0 = set(SpriteListData[3])
        StarCoinNumbers = set(SpriteListData[4])
        SpritesWithSetIDs = set(SpriteListData[5])
        SpritesWithMovementIDsNyb2 = set(SpriteListData[6])
        SpritesWithMovementIDsNyb3 = set(SpriteListData[7])
        SpritesWithMovementIDsNyb5 = set(SpriteListData[8])
        SpritesWithRotationIDs = set(SpriteListData[9])
        SpritesWithLocationIDsNyb5 = set(SpriteListData[10])
        SpritesWithLocationIDsNyb5and0xF = set(SpriteListData[11])
        SpritesWithLocationIDsNyb4 = set(SpriteListData[12])
        AndController = set(SpriteListData[13])
        OrController = set(SpriteListData[14])
        MultiChainer = set(SpriteListData[15])
        Random = set(SpriteListData[16])
        Clam = set(SpriteListData[17])
        Coin = set(SpriteListData[18])
        MushroomScrewPlatforms = set(SpriteListData[19])
        SpritesWithMovementIDsNyb5Type2 = set(SpriteListData[20])
        BowserFireballArea = set(SpriteListData[21])
        CheepCheepArea = set(SpriteListData[22])
        PoltergeistItem = set(SpriteListData[23])

        # Triggered by an Event
        if self.type in SpritesTriggeredByAnEventNyb1 and self.spritedata[1] != '\0':
            baseString += trans.string('Sprites', 2, '[event]', self.spritedata[1])
        elif self.type in SpritesTriggeredByAnEventNyb0 and self.spritedata[0] != '\0':
            baseString += trans.string('Sprites', 2, '[event]', self.spritedata[0])
        elif self.type in AndController:
            baseString += trans.string('Sprites', 3, '[event1]', self.spritedata[0], '[event2]', self.spritedata[2], '[event3]', self.spritedata[3], '[event4]', self.spritedata[4])
        elif self.type in OrController:
            baseString += trans.string('Sprites', 4, '[event1]', self.spritedata[0], '[event2]', self.spritedata[2], '[event3]', self.spritedata[3], '[event4]', self.spritedata[4])

        # Activates an Event
        if (self.type in SpritesThatActivateAnEvent)and (self.spritedata[1] != '\0'):
            baseString += trans.string('Sprites', 5, '[event]', self.spritedata[1])
        elif (self.type in SpritesThatActivateAnEventNyb0) and (self.spritedata[0] != '\0'):
            baseString += trans.string('Sprites', 5, '[event]', self.spritedata[0])
        elif (self.type in MultiChainer):
            baseString += trans.string('Sprites', 6, '[event1]', self.spritedata[0], '[event2]', self.spritedata[1])
        elif (self.type in Random):
            baseString += trans.string('Sprites', 7, '[event1]', self.spritedata[0], '[event2]', self.spritedata[2], '[event3]', self.spritedata[3], '[event4]', self.spritedata[4])

        # Star Coin
        if (self.type in StarCoinNumbers):
            number = (self.spritedata[4] & 15) + 1
            baseString += trans.string('Sprites', 8, '[num]', number)
        elif (self.type in Clam) and (self.spritedata[5] & 15) == 1:
            baseString += trans.string('Sprites', 9)

        # Set ID
        if self.type in SpritesWithSetIDs:
            baseString += trans.string('Sprites', 10, '[id]', self.spritedata[5] & 15)
        elif self.type in Coin and self.spritedata[2] != '\0':
            baseString += trans.string('Sprites', 11, '[id]', self.spritedata[2])

        # Movement ID (Nybble 2)
        if self.type in SpritesWithMovementIDsNyb2 and self.spritedata[2] != '\0':
            baseString += trans.string('Sprites', 12, '[id]', self.spritedata[2])
        elif self.type in MushroomScrewPlatforms and self.spritedata[2] >> 4 != '\0':
            baseString += trans.string('Sprites', 12, '[id]', self.spritedata[2] >> 4)

        # Movement ID (Nybble 3)
        if self.type in SpritesWithMovementIDsNyb3 and self.spritedata[3] >> 4 != '\0':
            baseString += trans.string('Sprites', 12, '[id]', (self.spritedata[3] >> 4))

        # Movement ID (Nybble 5)
        if self.type in SpritesWithMovementIDsNyb5 and self.spritedata[5] >> 4:
            baseString += trans.string('Sprites', 12, '[id]', (self.spritedata[5] >> 4))
        elif self.type in SpritesWithMovementIDsNyb5Type2 and self.spritedata[5] != '\0':
            baseString += trans.string('Sprites', 12, '[id]', self.spritedata[5])

        # Rotation ID
        if self.type in SpritesWithRotationIDs and self.spritedata[5] != '\0':
            baseString += trans.string('Sprites', 13, '[id]', self.spritedata[5])

        # Location ID (Nybble 5)
        if self.type in SpritesWithLocationIDsNyb5 and self.spritedata[5] != '\0':
            baseString += trans.string('Sprites', 14, '[id]', self.spritedata[5])
        elif self.type in SpritesWithLocationIDsNyb5and0xF and self.spritedata[5] & 15 != '\0':
            baseString += trans.string('Sprites', 14, '[id]', self.spritedata[5] & 15)
        elif self.type in SpritesWithLocationIDsNyb4 and self.spritedata[4] != '\0':
            baseString += trans.string('Sprites', 14, '[id]', self.spritedata[4])
        elif self.type in BowserFireballArea and self.spritedata[3] != '\0':
            baseString += trans.string('Sprites', 14, '[id]', self.spritedata[3])
        elif self.type in CheepCheepArea: # nybble 8-9
            if (((self.spritedata[3] & 0xF) << 4) | ((self.spritedata[4] & 0xF0) >> 4)) != '\0':
                baseString += trans.string('Sprites', 14, '[id]', (((self.spritedata[3] & 0xF) << 4) | ((self.spritedata[4] & 0xF0) >> 4)))
        elif self.type in PoltergeistItem and (((self.spritedata[4] & 0xF) << 4) | ((self.spritedata[5] & 0xF0) >> 4)) != '\0': # nybble 10-11
            baseString += trans.string('Sprites', 14, '[id]', (((self.spritedata[4] & 0xF) << 4) | ((self.spritedata[5] & 0xF0) >> 4)))

        # Add ')' to the end
        baseString += trans.string('Sprites', 15)

        return baseString

    def __lt__(self, other):
        # Sort by objx, then objy, then sprite type
        return (self.objx * 100000 + self.objy) * 1000 + self.type < (other.objx * 100000 + other.objy) * 1000 + other.type

    def InitializeSprite(self):
        """
        Initializes sprite and creates any auxiliary objects needed
        """
        type = self.type

        if type > len(Sprites): return

        self.name = Sprites[type].name
        self.setToolTip(trans.string('Sprites', 0, '[type]', self.type, '[name]', self.name))
        self.UpdateListItem()

        imgs = gamedef.getImageClasses()
        if type in imgs:
            self.setImageObj(imgs[type])

        if setting('drawSpritesBehindL0'):
            self.setZValue(15000) # Between layer 0 and layer 1
        else:
            self.setZValue(24000) # In front of locations



    def setImageObj(self, obj):
        """
        Sets a new sprite image object for this SpriteItem
        """
        for auxObj in self.ImageObj.aux:
            if auxObj.scene() is None: continue
            auxObj.scene().removeItem(auxObj)

        if setting('drawSpritesBehindL0'):
            self.setZValue(15000) # Between layer 0 and layer 1
        self.resetTransform()

        if (self.type in gamedef.getImageClasses()) and (self.type not in SLib.SpriteImagesLoaded):
            gamedef.getImageClasses()[self.type].loadImages()
            SLib.SpriteImagesLoaded.add(self.type)
        self.ImageObj = obj(self)

        self.UpdateDynamicSizing()
        self.UpdateRects()
        self.ChangingPos = True
        self.setPos(
            int((self.objx + self.ImageObj.xOffset) * TileWidth / 16),
            int((self.objy + self.ImageObj.yOffset) * TileWidth / 16),
            )
        self.ChangingPos = False

        self.updateScene()

    def UpdateDynamicSizing(self):
        """
        Updates the sizes for dynamically sized sprites
        """
        CurrentRect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        CurrentAuxRects = []
        for auxObj in self.ImageObj.aux:
            CurrentAuxRects.append(QtCore.QRectF(
                auxObj.x() + self.x(),
                auxObj.y() + self.y(),
                auxObj.BoundingRect.width(),
                auxObj.BoundingRect.height(),
                ))

        self.ImageObj.dataChanged()
        self.UpdateRects()

        self.ChangingPos = True
        self.setPos(
            int((self.objx + self.ImageObj.xOffset) * TileWidth / 16),
            int((self.objy + self.ImageObj.yOffset) * TileWidth / 16),
            )
        self.ChangingPos = False

        if self.scene() is not None:
            self.scene().update(CurrentRect)
            self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
            for auxUpdateRect in CurrentAuxRects:
                self.scene().update(auxUpdateRect)

    def UpdateRects(self):
        """
        Creates all the rectangles for the sprite
        """
        type = self.type

        self.prepareGeometryChange()

        # Get rects
        imgRect = QtCore.QRectF(
            0, 0,
            self.ImageObj.width * TileWidth / 16,
            self.ImageObj.height * TileWidth / 16,
            )
        spriteboxRect = QtCore.QRectF(
            0, 0,
            self.ImageObj.spritebox.BoundingRect.width(),
            self.ImageObj.spritebox.BoundingRect.height(),
            )
        imgOffsetRect = imgRect.translated(
            (self.objx + self.ImageObj.xOffset) * (TileWidth / 16),
            (self.objy + self.ImageObj.yOffset) * (TileWidth / 16),
            )
        spriteboxOffsetRect = spriteboxRect.translated(
            (self.objx * (TileWidth / 16)) + self.ImageObj.spritebox.BoundingRect.topLeft().x(),
            (self.objy * (TileWidth / 16)) + self.ImageObj.spritebox.BoundingRect.topLeft().y(),
            )

        if SpriteImagesShown:
            unitedRect = imgRect.united(spriteboxRect)
            unitedOffsetRect = imgOffsetRect.united(spriteboxOffsetRect)

            # SelectionRect: Used to determine the size of the
            # "this sprite is selected" translucent white box that
            # appears when a sprite with an image is selected.
            self.SelectionRect = QtCore.QRectF(
                0, 0,
                imgRect.width() - 1,
                imgRect.height() - 1,
                )

            # LevelRect: Used by the Level Overview to determine
            # the size and position of the sprite in the level.
            # Measured in blocks.
            self.LevelRect = QtCore.QRectF(
                unitedOffsetRect.topLeft().x() / TileWidth,
                unitedOffsetRect.topLeft().y() / TileWidth,
                unitedOffsetRect.width() / TileWidth,
                unitedOffsetRect.height() / TileWidth,
                )

            # BoundingRect: The sprite can only paint within
            # this area.
            self.BoundingRect = unitedRect.translated(
                self.ImageObj.spritebox.BoundingRect.topLeft().x(),
                self.ImageObj.spritebox.BoundingRect.topLeft().y(),
                )

        else:
            self.SelectionRect = QtCore.QRectF(0, 0, TileWidth, TileWidth)

            self.LevelRect = QtCore.QRectF(
                spriteboxOffsetRect.topLeft().x() / TileWidth,
                spriteboxOffsetRect.topLeft().y() / TileWidth,
                spriteboxOffsetRect.width() / TileWidth,
                spriteboxOffsetRect.height() / TileWidth,
                )

            # BoundingRect: The sprite can only paint within
            # this area.
            self.BoundingRect = spriteboxRect.translated(
                self.ImageObj.spritebox.BoundingRect.topLeft().x(),
                self.ImageObj.spritebox.BoundingRect.topLeft().y(),
                )

    def getFullRect(self):
        """
        Returns a rectangle that contains the sprite and all
        auxiliary objects.
        """
        self.UpdateRects()

        br = self.BoundingRect.translated(
            self.x(),
            self.y(),
            )
        for aux in self.ImageObj.aux:
            br = br.united(
                aux.BoundingRect.translated(
                    aux.x() + self.x(),
                    aux.y() + self.y(),
                    )
                )

        return br

    def itemChange(self, change, value):
        """
        Makes sure positions don't go out of bounds and updates them as necessary
        """

        tileWidthMult = TileWidth / 16
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            if self.scene() is None: return value
            if self.ChangingPos: return value

            if SpriteImagesShown:
                xOffset, xOffsetAdjusted = self.ImageObj.xOffset, self.ImageObj.xOffset * tileWidthMult
                yOffset, yOffsetAdjusted = self.ImageObj.yOffset, self.ImageObj.yOffset * tileWidthMult
            else:
                xOffset, xOffsetAdjusted = 0, 0
                yOffset, yOffsetAdjusted = 0, 0

            # snap to 24x24
            newpos = value

            # snap even further if Shift isn't held
            # but -only- if OverrideSnapping is off
            if not OverrideSnapping:
                objectsSelected = any([isinstance(thing, ObjectItem) for thing in mainWindow.CurrentSelection])
                if QtWidgets.QApplication.keyboardModifiers() == Qt.AltModifier:
                    # Alt is held; don't snap
                    newpos.setX((int((newpos.x() + 0.75) / tileWidthMult) * tileWidthMult))
                    newpos.setY((int((newpos.y() + 0.75) / tileWidthMult) * tileWidthMult))
                elif not objectsSelected and self.isSelected() and len(mainWindow.CurrentSelection) > 1:
                    # Snap to 8x8, but with the dragoffsets
                    dragoffsetx, dragoffsety = int(self.dragoffsetx), int(self.dragoffsety)
                    if dragoffsetx < -(TileWidth / 2): dragoffsetx += TileWidth / 2
                    if dragoffsety < -(TileWidth / 2): dragoffsety += TileWidth / 2
                    if dragoffsetx == 0: dragoffsetx = -(TileWidth / 2)
                    if dragoffsety == 0: dragoffsety = -(TileWidth / 2)
                    referenceX = int((newpos.x() + (TileWidth / 4) + (TileWidth / 2) + dragoffsetx - xOffsetAdjusted) / (TileWidth / 2)) * (TileWidth / 2)
                    referenceY = int((newpos.y() + (TileWidth / 4) + (TileWidth / 2) + dragoffsety - yOffsetAdjusted) / (TileWidth / 2)) * (TileWidth / 2)
                    newpos.setX(referenceX - ((TileWidth / 2) + dragoffsetx) + xOffsetAdjusted)
                    newpos.setY(referenceY - ((TileWidth / 2) + dragoffsety) + yOffsetAdjusted)
                elif objectsSelected and self.isSelected():
                    # Objects are selected, too; move in sync by snapping to whole blocks
                    dragoffsetx, dragoffsety = int(self.dragoffsetx), int(self.dragoffsety)
                    if dragoffsetx == 0: dragoffsetx = -TileWidth
                    if dragoffsety == 0: dragoffsety = -TileWidth
                    referenceX = int((newpos.x() + (TileWidth / 2) + TileWidth + dragoffsetx - xOffsetAdjusted) / TileWidth) * TileWidth
                    referenceY = int((newpos.y() + (TileWidth / 2) + TileWidth + dragoffsety - yOffsetAdjusted) / TileWidth) * TileWidth
                    newpos.setX(referenceX - (TileWidth + dragoffsetx) + xOffsetAdjusted)
                    newpos.setY(referenceY - (TileWidth + dragoffsety) + yOffsetAdjusted)
                else:
                    # Snap to 8x8
                    newpos.setX(int(int((newpos.x() + (TileWidth / 4) - xOffsetAdjusted) / (TileWidth / 2)) * (TileWidth / 2) + xOffsetAdjusted))
                    newpos.setY(int(int((newpos.y() + (TileWidth / 4) - yOffsetAdjusted) / (TileWidth / 2)) * (TileWidth / 2) + yOffsetAdjusted))

            x = newpos.x()
            y = newpos.y()

            # don't let it get out of the boundaries
            if x < 0: newpos.setX(0)
            if x > 1023 * TileWidth: newpos.setX(1023 * TileWidth)
            if y < 0: newpos.setY(0)
            if y > 511 * TileWidth: newpos.setY(511 * TileWidth)

            # update the data
            x = int(newpos.x() / tileWidthMult - xOffset)
            y = int(newpos.y() / tileWidthMult - yOffset)

            if x != self.objx or y != self.objy:
                #oldrect = self.BoundingRect
                #oldrect.translate(self.objx*(TileWidth/16), self.objy*(TileWidth/16))
                updRect = QtCore.QRectF(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
                #self.scene().update(updRect.united(oldrect))
                self.scene().update(updRect)

                self.LevelRect.moveTo((x + xOffset) / 16, (y + yOffset) / 16)

                for auxObj in self.ImageObj.aux:
                    auxUpdRect = QtCore.QRectF(
                        self.x() + auxObj.x(),
                        self.y() + auxObj.y(),
                        auxObj.BoundingRect.width(),
                        auxObj.BoundingRect.height(),
                        )
                    self.scene().update(auxUpdRect)

                self.scene().update(
                    self.x() + self.ImageObj.spritebox.BoundingRect.topLeft().x(),
                    self.y() + self.ImageObj.spritebox.BoundingRect.topLeft().y(),
                    self.ImageObj.spritebox.BoundingRect.width(),
                    self.ImageObj.spritebox.BoundingRect.height(),
                    )

                oldx = self.objx
                oldy = self.objy
                self.objx = x
                self.objy = y
                if self.positionChanged is not None:
                    self.positionChanged(self, oldx, oldy, x, y)

                self.ImageObj.positionChanged()

                SetDirty()

            return newpos

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed for cloning
        """
        if event.button() == Qt.LeftButton:
            if QtWidgets.QApplication.keyboardModifiers() == Qt.ControlModifier:
                newitem = SpriteItem(self.type, self.objx, self.objy, self.spritedata)
                newitem.listitem = ListWidgetItem_SortsByOther(newitem, newitem.ListString())
                mainWindow.spriteList.addItem(newitem.listitem)
                Area.sprites.append(newitem)
                mainWindow.scene.addItem(newitem)
                mainWindow.scene.clearSelection()
                self.setSelected(True)
                newitem.UpdateListItem()
                SetDirty()
                return

        LevelEditorItem.mousePressEvent(self, event)

    def nearestZone(self, obj=False):
        """
        Calls a modified MapPositionToZoneID (if obj = True, it returns the actual ZoneItem object)
        """
        if not hasattr(Area, 'zones'): return None
        id = MapPositionToZoneID(Area.zones, self.objx, self.objy, True)
        if obj:
            for z in Area.zones:
                if z.id == id: return z
        else: return id

    def updateScene(self):
        """
        Calls self.scene().update()
        """
        # Some of the more advanced painters need to update the whole scene
        # and this is a convenient way to do it:
        # self.parent.updateScene()
        if self.scene() is not None:
            self.scene().update()

    def paint(self, painter, option=None, widget=None, overrideGlobals=False):
        """
        Paints the sprite
        """
        if setting('drawSpritesBehindL0'):
            self.setZValue(15000) # Between layer 0 and layer 1
        
        # Setup stuff
        if option is not None:
            painter.setClipRect(option.exposedRect)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Turn aux things on or off
        for aux in self.ImageObj.aux:
            aux.setVisible(SpriteImagesShown)

        # Default spritebox
        drawSpritebox = True
        spriteboxRect = QtCore.QRectF(0, 0, TileWidth, TileWidth)

        if SpriteImagesShown or overrideGlobals:
            self.ImageObj.paint(painter)

            drawSpritebox = self.ImageObj.spritebox.shown

            # Draw the selected-sprite-image overlay box
            if self.isSelected() and (not drawSpritebox or self.ImageObj.size != (16, 16)):
                painter.setPen(QtGui.QPen(theme.color('sprite_lines_s'), 1, Qt.DotLine))
                painter.drawRect(self.SelectionRect)
                painter.fillRect(self.SelectionRect, theme.color('sprite_fill_s'))

            # Determine the spritebox position
            if drawSpritebox:
                spriteboxRect = self.ImageObj.spritebox.RoundedRect

        # Draw the spritebox if applicable
        if drawSpritebox:
            if self.isSelected():
                painter.setBrush(QtGui.QBrush(theme.color('spritebox_fill_s')))
                painter.setPen(QtGui.QPen(theme.color('spritebox_lines_s'), 1 / 24 * TileWidth))
            else:
                painter.setBrush(QtGui.QBrush(theme.color('spritebox_fill')))
                painter.setPen(QtGui.QPen(theme.color('spritebox_lines'), 1 / 24 * TileWidth))
            painter.drawRect(spriteboxRect)

            painter.setFont(self.font)
            painter.drawText(spriteboxRect, Qt.AlignCenter, str(self.type))

    def scene(self):
        """
        Solves a small bug
        """
        return mainWindow.scene

    def delete(self):
        """
        Delete the sprite from the level
        """
        sprlist = mainWindow.spriteList
        mainWindow.UpdateFlag = True
        sprlist.takeItem(sprlist.row(self.listitem))
        mainWindow.UpdateFlag = False
        sprlist.selectionModel().clearSelection()
        Area.sprites.remove(self)
        #self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        self.scene().update() # The zone painters need for the whole thing to update


class EntranceItem(LevelEditorItem):
    """
    Level editor item that represents an entrance
    """
    BoundingRect = QtCore.QRectF(0, 0, TileWidth, TileWidth)
    RoundedRect = QtCore.QRectF(1 / 24 * TileWidth, 1 / 24 * TileWidth, TileWidth - 1 / 24 * TileWidth, TileWidth - 1 / 24 * TileWidth)
    EntranceImages = None

    class AuxEntranceItem(QtWidgets.QGraphicsItem):
        """
        Auxiliary item for drawing entrance things
        """
        BoundingRect = QtCore.QRectF(0, 0, TileWidth, TileWidth)
        def __init__(self, parent):
            """
            Initializes the auxiliary entrance thing
            """
            super().__init__(parent)
            self.parent = parent
            self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
            self.setFlag(QtWidgets.QGraphicsItem.ItemStacksBehindParent, True)
            self.setParentItem(parent)
            self.hover = False

        def TypeChange(self):
            """
            Handles type changes to the entrance
            """
            if self.parent.enttype == 20:
                # Jumping facing right
                self.setPos(0, -11.5 * TileWidth)
                self.BoundingRect = QtCore.QRectF(0, 0, 4.0833333 * TileWidth, 12.5 * TileWidth)
            elif self.parent.enttype == 21:
                # Vine
                self.setPos(-0.5 * TileWidth, -10 * TileWidth)
                self.BoundingRect = QtCore.QRectF(0, 0, 2 * TileWidth, 29 * TileWidth)
            elif self.parent.enttype == 24:
                # Jumping facing left
                self.setPos(-3.0833333 * TileWidth, -11.5 * TileWidth)
                self.BoundingRect = QtCore.QRectF(0, 0, 4.0833333 * TileWidth, 12.5 * TileWidth)
            else:
                self.setPos(0, 0)
                self.BoundingRect = QtCore.QRectF(0, 0, TileWidth, TileWidth)

        def paint(self, painter, option, widget):
            """
            Paints the entrance aux
            """

            painter.setClipRect(option.exposedRect)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)

            if self.parent.enttype == 20:
                # Jumping facing right

                path = QtGui.QPainterPath(QtCore.QPoint(TileWidth / 2, 11.5 * TileWidth))
                path.cubicTo(QtCore.QPoint(TileWidth * 5 / 3, -TileWidth), QtCore.QPoint(2.0833333 * TileWidth, -TileWidth), QtCore.QPoint(2.5 * TileWidth, TileWidth * 3 / 2))
                path.lineTo(QtCore.QPoint(4 * TileWidth, 12.5 * TileWidth))

                painter.setPen(SLib.OutlinePen)
                painter.drawPath(path)

            elif self.parent.enttype == 21:
                # Vine

                # Draw the top half
                painter.setOpacity(1)
                painter.drawPixmap(0, 0, SLib.ImageCache['VineTop'])
                painter.drawTiledPixmap(TileWidth // 2, TileWidth * 2, TileWidth, 7 * TileWidth, SLib.ImageCache['VineMid'])
                # Draw the bottom half
                # This is semi-transparent because you can't interact with it.
                painter.setOpacity(0.5)
                painter.drawTiledPixmap(TileWidth // 2, TileWidth * 9, TileWidth, 19 * TileWidth, SLib.ImageCache['VineMid'])
                painter.drawPixmap(TileWidth // 2, 28 * TileWidth, SLib.ImageCache['VineBtm'])

            elif self.parent.enttype == 24:
                # Jumping facing left

                path = QtGui.QPainterPath(QtCore.QPoint(3.5833333 * TileWidth, 11.5 * TileWidth))
                path.cubicTo(QtCore.QPoint(2.41666666 * TileWidth, -TileWidth), QtCore.QPoint(TileWidth / 2, -TileWidth), QtCore.QPoint(1.58333333 * TileWidth, TileWidth * 3 / 2))
                path.lineTo(QtCore.QPoint(TileWidth / 12, TileWidth * 12.5))

                painter.setPen(SLib.OutlinePen)
                painter.drawPath(path)

        def boundingRect(self):
            """
            Required by Qt
            """
            return self.BoundingRect

    def __init__(self, x, y, unk05, id, destarea, destentrance, type, unk0C, zone, unk0F, settings, unk12, unk13, unk14, unk15, unk16):
        """
        Creates an entrance with specific data
        """
        if EntranceItem.EntranceImages is None:
            ei = []
            src = QtGui.QPixmap('satorudata/entrances.png')
            for i in range(18):
                ei.append(src.copy(i * TileWidth, 0, TileWidth, TileWidth))
            EntranceItem.EntranceImages = ei

        super().__init__()

        layer = 0; path = 0; cpd = 0

        self.font = NumberFont
        self.objx = x
        self.objy = y
        self.unk05 = unk05
        self.entid = id
        self.destarea = destarea
        self.destentrance = destentrance
        self.enttype = type
        self.unk0C = unk0C
        self.entzone = zone
        self.unk0F = unk0F
        self.entsettings = settings
        self.unk12 = unk12
        self.unk13 = unk13
        self.unk14 = unk14
        self.unk15 = unk15
        self.unk16 = unk16
        self.entlayer = layer
        self.entpath = path
        self.listitem = None
        self.LevelRect = QtCore.QRectF(self.objx / 16, self.objy / 16, 1, 1)
        self.cpdirection = cpd

        self.setFlag(self.ItemIsMovable, not EntrancesFrozen)
        self.setFlag(self.ItemIsSelectable, not EntrancesFrozen)

        global DirtyOverride
        DirtyOverride += 1
        self.setPos(int(x * TileWidth / 16), int(y * TileWidth / 16))
        DirtyOverride -= 1

        self.aux = self.AuxEntranceItem(self)

        self.setZValue(27000)
        self.UpdateTooltip()
        self.TypeChange()

    def UpdateTooltip(self):
        """
        Updates the entrance object's tooltip
        """
        if self.enttype >= len(EntranceTypeNames):
            name = trans.string('Entrances', 1)
        else:
            name = EntranceTypeNames[self.enttype]

        if (self.entsettings & 0x80) != 0:
            destination = trans.string('Entrances', 2)
        else:
            if self.destarea == 0:
                destination = trans.string('Entrances', 3, '[id]', self.destentrance)
            else:
                destination = trans.string('Entrances', 4, '[id]', self.destentrance, '[area]', self.destarea)

        self.name = name
        self.destination = destination
        self.setToolTip(trans.string('Entrances', 0, '[ent]', self.entid, '[type]', name, '[dest]', destination))

    def ListString(self):
        """
        Returns a string that can be used to describe the entrance in a list
        """
        if self.enttype >= len(EntranceTypeNames):
            name = trans.string('Entrances', 1)
        else:
            name = EntranceTypeNames[self.enttype]

        if (self.entsettings & 0x80) != 0:
            return trans.string('Entrances', 5, '[id]', self.entid, '[name]', name, '[x]', self.objx, '[y]', self.objy)
        else:
            return trans.string('Entrances', 6, '[id]', self.entid, '[name]', name, '[x]', self.objx, '[y]', self.objy)

    def __lt__(self, other):
        return self.entid < other.entid

    def TypeChange(self):
        """
        Handles the entrance's type changing
        """

        # Determine the size and position of the entrance
        x, y, w, h = 0, 0, 1, 1
        if self.enttype in (3, 4):
            # Vertical pipe
            w = 2
        elif self.enttype in (5, 6):
            # Horizontal pipe
            h = 2

        # Now make the rects
        self.RoundedRect = QtCore.QRectF(x * TileWidth, y * TileWidth, w * TileWidth, h * TileWidth)
        self.BoundingRect = QtCore.QRectF(x * TileWidth, y * TileWidth, w * TileWidth, h * TileWidth)

        # Update the aux thing
        self.aux.TypeChange()

    def paint(self, painter, option, widget):
        """
        Paints the entrance
        """
        global theme

        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(theme.color('entrance_fill_s')))
            painter.setPen(QtGui.QPen(theme.color('entrance_lines_s'), 1 / 24 * TileWidth))
        else:
            painter.setBrush(QtGui.QBrush(theme.color('entrance_fill')))
            painter.setPen(QtGui.QPen(theme.color('entrance_lines'), 1 / 24 * TileWidth))

        self.TypeChange()
        painter.drawRoundedRect(self.RoundedRect, 4, 4)

        icontype = 0
        enttype = self.enttype
        if enttype == 0 or enttype == 1: icontype = 1 # normal
        if enttype == 2: icontype = 2 # door exit
        if enttype == 3: icontype = 4 # pipe up
        if enttype == 4: icontype = 5 # pipe down
        if enttype == 5: icontype = 6 # pipe left
        if enttype == 6: icontype = 7 # pipe right
        if enttype == 8: icontype = 12 # ground pound
        if enttype == 9: icontype = 13 # sliding
        #0F/15 is unknown?
        if enttype == 16: icontype = 8 # mini pipe up
        if enttype == 17: icontype = 9 # mini pipe down
        if enttype == 18: icontype = 10 # mini pipe left
        if enttype == 19: icontype = 11 # mini pipe right
        if enttype == 20: icontype = 15 # jump out facing right
        if enttype == 21: icontype = 17 # vine entrance
        if enttype == 23: icontype = 14 # boss battle entrance
        if enttype == 24: icontype = 16 # jump out facing left
        if enttype == 27: icontype = 3 # door entrance

        painter.drawPixmap(0, 0, EntranceItem.EntranceImages[icontype])

        painter.setFont(self.font)
        margin = TileWidth / 10
        painter.drawText(QtCore.QRectF(margin, margin, TileWidth / 2 - margin, TileWidth / 2 - margin), Qt.AlignCenter, str(self.entid))

    def delete(self):
        """
        Delete the entrance from the level
        """
        elist = mainWindow.entranceList
        mainWindow.UpdateFlag = True
        elist.takeItem(elist.row(self.listitem))
        mainWindow.UpdateFlag = False
        elist.selectionModel().clearSelection()
        Area.entrances.remove(self)
        self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())

    def itemChange(self, change, value):
        """
        Handle movement
        """
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            if self.scene() is None: return value

            updRect = QtCore.QRectF(
                self.x() + self.aux.x(),
                self.y() + self.aux.y(),
                self.aux.BoundingRect.width(),
                self.aux.BoundingRect.height(),
                )
            self.scene().update(updRect)

        return super().itemChange(change, value)

    def getFullRect(self):
        """
        Returns a rectangle that contains the entrance and any
        auxiliary objects.
        """

        br = self.BoundingRect.translated(
            self.x(),
            self.y(),
            )
        br = br.united(
            self.aux.BoundingRect.translated(
                self.aux.x() + self.x(),
                self.aux.y() + self.y(),
                )
            )

        return br


class PathItem(LevelEditorItem):
    """
    Level editor item that represents a path node
    """
    BoundingRect = QtCore.QRectF(0, 0, TileWidth, TileWidth)
    SelectionRect = QtCore.QRectF(0, 0, TileWidth, TileWidth)
    RoundedRect = QtCore.QRectF(0, 0, TileWidth, TileWidth)


    def __init__(self, objx, objy, pathinfo, nodeinfo, unk1, unk2, unk3, unk4): # no idea what the unknowns are, so...placeholders!
        """
        Creates a path node with specific data
        """

        global mainWindow
        super().__init__()

        self.font = NumberFont
        self.objx = objx
        self.objy = objy
        self.unk1 = unk1
        self.unk2 = unk2
        self.unk3 = unk3
        self.unk4 = unk4
        self.pathid = pathinfo['id']
        self.nodeid = pathinfo['nodes'].index(nodeinfo)
        self.pathinfo = pathinfo
        self.nodeinfo = nodeinfo
        self.listitem = None
        self.LevelRect = (QtCore.QRectF(self.objx/16, self.objy/16, TileWidth/16, TileWidth/16))
        self.setFlag(self.ItemIsMovable, not PathsFrozen)
        self.setFlag(self.ItemIsSelectable, not PathsFrozen)

        global DirtyOverride
        DirtyOverride += 1
        self.setPos(int(objx * TileWidth / 16), int(objy * TileWidth / 16))
        DirtyOverride -= 1

        self.setZValue(25002)
        self.UpdateTooltip()

        self.setVisible(PathsShown)

        # now that we're inited, set
        self.nodeinfo['graphicsitem'] = self

    def UpdateTooltip(self):
        """
        Updates the path object's tooltip
        """
        self.setToolTip(trans.string('Paths', 0, '[path]', self.pathid, '[node]', self.nodeid))

    def ListString(self):
        """
        Returns a string that can be used to describe the path in a list
        """
        return trans.string('Paths', 1, '[path]', self.pathid, '[node]', self.nodeid)

    def __lt__(self, other):
        return (self.pathid * 10000 + self.nodeid) < (other.pathid * 10000 + other.nodeid)

    def updatePos(self):
        """
        Our x/y was changed, update pathinfo
        """
        self.pathinfo['nodes'][self.nodeid]['x'] = self.objx
        self.pathinfo['nodes'][self.nodeid]['y'] = self.objy

    def updateId(self):
        """
        Path was changed, find our new nodeid
        """
        # called when 1. add node 2. delete node 3. change node order
        # hacky code but it works. considering how pathnodes are stored.
        self.nodeid = self.pathinfo['nodes'].index(self.nodeinfo)
        self.UpdateTooltip()
        self.scene().update()
        self.UpdateListItem()

        # if node doesn't exist, let Satoru implode!

    def paint(self, painter, option, widget):
        """
        Paints the path
        """
        global theme

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setClipRect(option.exposedRect)

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(theme.color('path_fill_s')))
            painter.setPen(QtGui.QPen(theme.color('path_lines_s'), 1 / 24 * TileWidth))
        else:
            painter.setBrush(QtGui.QBrush(theme.color('path_fill')))
            painter.setPen(QtGui.QPen(theme.color('path_lines'), 1 / 24 * TileWidth))
        painter.drawRoundedRect(self.RoundedRect, 4, 4)

        icontype = 0

        painter.setFont(self.font)
        margin = TileWidth / 10
        painter.drawText(QtCore.QRectF(margin, margin, TileWidth / 2 - margin, TileWidth / 2 - margin), Qt.AlignCenter, str(self.pathid))
        painter.drawText(QtCore.QRectF(margin, TileWidth / 2, TileWidth / 2 - margin, TileWidth / 2 - margin), Qt.AlignCenter, str(self.nodeid))

    def delete(self):
        """
        Delete the path from the level
        """
        global mainWindow
        plist = mainWindow.pathList
        mainWindow.UpdateFlag = True
        plist.takeItem(plist.row(self.listitem))
        mainWindow.UpdateFlag = False
        plist.selectionModel().clearSelection()
        Area.paths.remove(self)
        self.pathinfo['nodes'].remove(self.nodeinfo)

        if(len(self.pathinfo['nodes']) < 1):
            Area.pathdata.remove(self.pathinfo)
            self.scene().removeItem(self.pathinfo['peline'])

        # update other nodes' IDs
        for pathnode in self.pathinfo['nodes']:
            pathnode['graphicsitem'].updateId()

        self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())


class PathEditorLineItem(LevelEditorItem):
    """
    Level editor item to draw a line between two path nodes
    """
    BoundingRect = QtCore.QRectF(0, 0, 1, 1) # compute later

    def __init__(self, nodelist):
        """
        Creates a path line with specific data
        """

        global mainWindow
        super().__init__()

        self.objx = 0
        self.objy = 0
        self.nodelist = nodelist
        self.loops = False
        self.setFlag(self.ItemIsMovable, False)
        self.setFlag(self.ItemIsSelectable, False)
        self.computeBoundRectAndPos()
        self.setZValue(25002)
        self.UpdateTooltip()

        self.setVisible(PathsShown)

    def UpdateTooltip(self):
        """
        For compatibility, just in case
        """
        self.setToolTip('')

    def ListString(self):
        """
        Returns an empty string
        """
        return ''

    def nodePosChanged(self):
        self.computeBoundRectAndPos()
        self.scene().update()

    def computeBoundRectAndPos(self):
        xcoords = []
        ycoords = []
        for node in self.nodelist:
            xcoords.append(int(node['x']))
            ycoords.append(int(node['y']))
        self.objx = (min(xcoords) - 4)
        self.objy = (min(ycoords) - 4)

        mywidth = (8 + (max(xcoords) - self.objx)) * (TileWidth/16)
        myheight = (8 + (max(ycoords) - self.objy)) * (TileWidth/16)
        global DirtyOverride
        DirtyOverride += 1
        self.setPos(self.objx * (TileWidth/16), self.objy * (TileWidth/16))
        DirtyOverride -= 1
        self.prepareGeometryChange()
        self.BoundingRect = QtCore.QRectF(-4, -4, mywidth, myheight)



    def paint(self, painter, option, widget):
        """
        Paints the path lines
        """
        global theme

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setClipRect(option.exposedRect)

        color = theme.color('path_connector')
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtGui.QPen(color, 3 * TileWidth / 24, join = Qt.RoundJoin, cap = Qt.RoundCap))
        ppath = QtGui.QPainterPath()

        lines = []

        firstn = True

        snl = self.nodelist
        mult = TileWidth / 16
        for j, node in enumerate(snl):
            if ((j + 1) < len(snl)):
                a = QtCore.QPointF(float(snl[j]['x'] * mult) - self.x(), float(snl[j]['y'] * mult) - self.y())
                b = QtCore.QPointF(float(snl[j + 1]['x'] * mult) - self.x(), float(snl[j + 1]['y'] * mult) - self.y())
                lines.append(QtCore.QLineF(a, b))
            elif self.loops and (j + 1) == len(snl):
                a = QtCore.QPointF(float(snl[j]['x'] * mult) - self.x(), float(snl[j]['y'] * mult) - self.y())
                b = QtCore.QPointF(float(snl[0]['x'] * mult) - self.x(), float(snl[0]['y'] * mult) - self.y())
                lines.append(QtCore.QLineF(a, b))

        painter.drawLines(lines)


    def delete(self):
        """
        Delete the line from the level
        """
        self.scene().update()


class CommentItem(LevelEditorItem):
    """
    Level editor item that represents a in-level comment
    """
    BoundingRect = QtCore.QRectF(-8 * TileWidth / 24, -8 * TileWidth / 24, 48 * TileWidth / 24, 48 * TileWidth / 24)
    SelectionRect = QtCore.QRectF(-4 * TileWidth / 24, -4 * TileWidth / 24, 4 * TileWidth / 24, 4 * TileWidth / 24)
    Circle = QtCore.QRectF(0, 0, 32 * TileWidth / 24, 32 * TileWidth / 24)

    def __init__(self, x, y, text=''):
        """
        Creates a in-level comment
        """
        super().__init__()
        zval = 50000
        self.zval = zval

        self.text = text

        self.objx = x
        self.objy = y
        self.listitem = None
        self.LevelRect = (QtCore.QRectF(self.objx / 16, self.objy / 16, 2.25, 2.25))

        self.setFlag(self.ItemIsMovable, not CommentsFrozen)
        self.setFlag(self.ItemIsSelectable, not CommentsFrozen)

        global DirtyOverride
        DirtyOverride += 1
        self.setPos(int(x * TileWidth / 16), int(y * TileWidth / 16))
        DirtyOverride -= 1

        self.setZValue(zval + 1)
        self.UpdateTooltip()

        self.TextEdit = QtWidgets.QPlainTextEdit()
        self.TextEditProxy = mainWindow.scene.addWidget(self.TextEdit)
        self.TextEditProxy.setZValue(self.zval)
        self.TextEditProxy.setCursor(Qt.IBeamCursor)
        self.TextEditProxy.boundingRect = lambda self: QtCore.QRectF(0, 0, 100 * TileWidth, 100 * TileWidth)
        self.TextEdit.setVisible(False)
        self.TextEdit.setMaximumWidth(192 * TileWidth / 24)
        self.TextEdit.setMaximumHeight(128 * TileWidth / 24)
        self.TextEdit.setPlainText(self.text)
        self.TextEdit.textChanged.connect(self.handleTextChanged)
        self.reposTextEdit()

        self.setVisible(CommentsShown)


    def UpdateTooltip(self):
        """
        For compatibility, just in case
        """
        self.setToolTip(trans.string('Comments', 1, '[x]', self.objx, '[y]', self.objy))


    def ListString(self):
        """
        Returns a string that can be used to describe the comment in a list
        """
        t = self.OneLineText()
        return trans.string('Comments', 0, '[x]', self.objx, '[y]', self.objy, '[text]', t)


    def OneLineText(self):
        """
        Returns the text of this comment in a format that can be written on one line
        """
        t = str(self.text)
        if t.replace(' ', '').replace('\n', '') == '': t = trans.string('Comments', 3)
        while '\n\n' in t: t = t.replace('\n\n', '\n')
        t = t.replace('\n', trans.string('Comments', 2))

        f = None
        if self.listitem is not None: f = self.listitem.font()
        t2 = clipStr(t, 128, f)
        if t2 is not None: t = t2 + '...'

        return t


    def paint(self, painter, option, widget):
        """
        Paints the comment
        """
        global theme

        painter.setClipRect(option.exposedRect)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(theme.color('comment_fill_s')))
            p = QtGui.QPen(theme.color('comment_lines_s'))
            p.setWidth(3 * TileWidth / 24)
            painter.setPen(p)
        else:
            painter.setBrush(QtGui.QBrush(theme.color('comment_fill')))
            p = QtGui.QPen(theme.color('comment_lines'))
            p.setWidth(3 * TileWidth / 24)
            painter.setPen(p)

        painter.drawEllipse(self.Circle)
        if not self.isSelected(): painter.setOpacity(.5)
        painter.drawPixmap(4 * TileWidth / 24, 4 * TileWidth / 24, GetIcon('comments', 24).pixmap(TileWidth, TileWidth))
        painter.setOpacity(1)


        # Set the text edit visibility
        try: shouldBeVisible = (len(mainWindow.scene.selectedItems()) == 1) and self.isSelected()
        except RuntimeError: shouldBeVisible = False
        try: self.TextEdit.setVisible(shouldBeVisible)
        except RuntimeError:
            # Sometimes Qt deletes my text edit.
            # Therefore, I need to make a new one.
            self.TextEdit = QtWidgets.QPlainTextEdit()
            self.TextEditProxy = mainWindow.scene.addWidget(self.TextEdit)
            self.TextEditProxy.setZValue(self.zval)
            self.TextEditProxy.setCursor(Qt.IBeamCursor)
            self.TextEditProxy.BoundingRect = QtCore.QRectF(0, 0, 100 * TileWidth, 100 * TileWidth)
            self.TextEditProxy.boundingRect = lambda self: self.BoundingRect
            self.TextEdit.setMaximumWidth(192 * TileWidth / 24)
            self.TextEdit.setMaximumHeight(128 * TileWidth / 24)
            self.TextEdit.setPlainText(self.text)
            self.TextEdit.textChanged.connect(self.handleTextChanged)
            self.reposTextEdit()
            self.TextEdit.setVisible(shouldBeVisible)

    def handleTextChanged(self):
        """
        Handles the text being changed
        """
        self.text = str(self.TextEdit.toPlainText())
        if hasattr(self, 'textChanged'): self.textChanged(self)

    def reposTextEdit(self):
        """
        Repositions the text edit
        """
        self.TextEditProxy.setPos((self.objx * 3/2) + TileWidth, (self.objy * 3/2) + TileWidth * 2 / 3)

    def handlePosChange(self, oldx, oldy):
        """
        Handles the position changing
        """
        self.reposTextEdit()

        # Manual scene update :(
        w = 8 * TileWidth + TileWidth
        h = 16 / 3 * TileWidth + TileWidth
        oldx *= TileWidth / 16
        oldy *= TileWidth / 16
        oldRect = QtCore.QRectF(oldx, oldy, w, h)
        self.scene().update(oldRect)


    def delete(self):
        """
        Delete the comment from the level
        """
        clist = mainWindow.commentList
        mainWindow.UpdateFlag = True
        clist.takeItem(clist.row(self.listitem))
        mainWindow.UpdateFlag = False
        clist.selectionModel().clearSelection()
        p = self.TextEditProxy
        p.setSelected(False)
        mainWindow.scene.removeItem(p)
        Area.comments.remove(self)
        self.scene().update(self.x(), self.y(), self.BoundingRect.width(), self.BoundingRect.height())
        mainWindow.SaveComments()

#####################################################################
############################## WIDGETS ##############################
#####################################################################

class LevelOverviewWidget(QtWidgets.QWidget):
    """
    Widget that shows an overview of the level and can be clicked to move the view
    """
    moveIt = QtCore.pyqtSignal(int, int)

    def __init__(self):
        """
        Constructor for the level overview widget
        """
        global theme

        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding))

        self.bgbrush = QtGui.QBrush(theme.color('bg'))
        self.objbrush = QtGui.QBrush(theme.color('overview_object'))
        self.viewbrush = QtGui.QBrush(theme.color('overview_zone_fill'))
        self.view = QtCore.QRectF(0,0,0,0)
        self.spritebrush = QtGui.QBrush(theme.color('overview_sprite'))
        self.entrancebrush = QtGui.QBrush(theme.color('overview_entrance'))
        self.locationbrush = QtGui.QBrush(theme.color('overview_location_fill'))

        self.scale = 0.375
        self.maxX = 1
        self.maxY = 1
        self.CalcSize()
        self.Rescale()

        self.Xposlocator = 0
        self.Yposlocator = 0
        self.Hlocator = 50
        self.Wlocator = 80
        self.mainWindowScale = 1

    def Reset(self):
        """
        Resets the max and scale variables
        """
        self.scale = 0.375
        self.maxX = 1
        self.maxY = 1
        self.CalcSize()
        self.Rescale()

    def CalcSize(self):
        """
        Calculates all the required sizes for this scale
        """
        self.posmult = TileWidth / self.scale

    def mouseMoveEvent(self, event):
        """
        Handles mouse movement over the widget
        """
        QtWidgets.QWidget.mouseMoveEvent(self, event)

        if event.buttons() == Qt.LeftButton:
            self.moveIt.emit(event.pos().x() * self.posmult, event.pos().y() * self.posmult)

    def mousePressEvent(self, event):
        """
        Handles mouse pressing events over the widget
        """
        QtWidgets.QWidget.mousePressEvent(self, event)

        if event.button() == Qt.LeftButton:
            self.moveIt.emit(event.pos().x() * self.posmult, event.pos().y() * self.posmult)

    def paintEvent(self, event):
        """
        Paints the level overview widget
        """
        global theme

        if not hasattr(Area, 'layers'):
            # fixes race condition where this widget is painted after
            # the level is created, but before it's loaded
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        self.Rescale()
        painter.scale(self.scale, self.scale)
        painter.fillRect(0, 0, 1024, 512, self.bgbrush)

        maxX = self.maxX
        maxY = self.maxY
        dr = painter.drawRect
        fr = painter.fillRect

        maxX = 0
        maxY = 0

        b = self.viewbrush
        painter.setPen(QtGui.QPen(theme.color('overview_zone_lines'), 1))

        for zone in Area.zones:
            x = zone.objx / 16
            y = zone.objy / 16
            width = zone.width / 16
            height = zone.height / 16
            fr(x, y, width, height, b)
            dr(x, y, width, height)
            if x+width > maxX:
                maxX = x+width
            if y+height > maxY:
                maxY = y+height

        b = self.objbrush

        for layer in Area.layers:
            for obj in layer:
                fr(obj.LevelRect, b)
                if obj.objx > maxX:
                    maxX = obj.objx
                if obj.objy > maxY:
                    maxY = obj.objy


        b = self.spritebrush

        for sprite in Area.sprites:
            fr(sprite.LevelRect, b)
            if sprite.objx/16 > maxX:
                maxX = sprite.objx/16
            if sprite.objy/16 > maxY:
                maxY = sprite.objy/16


        b = self.entrancebrush

        for ent in Area.entrances:
            fr(ent.LevelRect, b)
            if ent.objx/16 > maxX:
                maxX = ent.objx/16
            if ent.objy/16 > maxY:
                maxY = ent.objy/16


        b = self.locationbrush
        painter.setPen(QtGui.QPen(theme.color('overview_location_lines'), 1))

        for location in Area.locations:
            x = location.objx / 16
            y = location.objy / 16
            width = location.width / 16
            height = location.height / 16
            fr(x, y, width, height, b)
            dr(x, y, width, height)
            if x+width > maxX:
                maxX = x+width
            if y+height > maxY:
                maxY = y+height

        self.maxX = maxX
        self.maxY = maxY

        b = self.locationbrush
        painter.setPen(QtGui.QPen(theme.color('overview_viewbox'), 1))
        painter.drawRect(self.Xposlocator/TileWidth/self.mainWindowScale, self.Yposlocator/TileWidth/self.mainWindowScale, self.Wlocator/TileWidth/self.mainWindowScale, self.Hlocator/TileWidth/self.mainWindowScale)


    def Rescale(self):
        self.Xscale = (float(self.width())/float(self.maxX+45))
        self.Yscale = (float(self.height())/float(self.maxY+25))

        if self.Xscale <= self.Yscale:
            self.scale = self.Xscale
        else:
            self.scale = self.Yscale

        if self.scale < 0.002: self.scale = 0.002

        self.CalcSize()


class ObjectPickerWidget(QtWidgets.QStackedWidget):
    """
    A widget that lets you pick from all available objects.
    """

    ObjChanged = QtCore.pyqtSignal()
    ObjReplace = QtCore.pyqtSignal()
    EmbeddedObjUpdate = QtCore.pyqtSignal(int)
    EmbeddedObjDelete = QtCore.pyqtSignal(int)

    current = (None, None) # Current tab index, current object index within that tab

    def __init__(self, parent=None, embeddedObjectDeleteRequestHandler=None):
        super().__init__(parent)

        self.mainPicker = ObjectPickerListWidget(self)
        self.megaPicker = ObjectPickerTreeWidget(self)
        self.embedPicker = ObjectPickerListWidget(self)

        self.mainPicker.ObjChanged.connect(lambda idx: self.handleObjChanged(0, idx))
        self.megaPicker.ObjChanged.connect(lambda idxs: self.handleObjChanged(1, idxs))
        self.embedPicker.ObjChanged.connect(lambda idx: self.handleObjChanged(2, idx))

        self.mainPicker.ObjReplace.connect(lambda idx: self.handleObjReplace(0, idx))
        self.megaPicker.ObjReplace.connect(lambda idxs: self.handleObjReplace(1, idxs))
        self.embedPicker.ObjReplace.connect(lambda idx: self.handleObjReplace(2, idx))
        
        self.embedPicker.ObjUpdate.connect(self.handleEmbeddedObjUpdate)
        self.embedPicker.ObjDelete.connect(self.handleEmbeddedObjDelete)

        self.embedPicker.requestDeleteObject = embeddedObjectDeleteRequestHandler

        self.mainPicker.forceNumbering = True
        self.embedPicker.forceNumbering = True
        self.embedPicker.allowImportReplace = True
        self.embedPicker.allowDelete = True

        self.mainTilesetDropdown = QtWidgets.QComboBox()
        self.mainTilesetDropdown.addItems(['Pa0_jyotyu', 'Pa0_jyotyu_chika', 'Pa0_jyotyu_yougan', 'Pa0_jyotyu_yougan2'])
        self.mainTilesetDropdown.currentIndexChanged.connect(self.handleMainDropdown)

        self.embedImport = QtWidgets.QPushButton('Import')
        self.embedImport.clicked.connect(self.handleEmbedImport)

        mainWrap = QtWidgets.QWidget()
        mainWrapL = QtWidgets.QVBoxLayout(mainWrap)
        mainWrapL.setContentsMargins(0, 0, 0, 0)
        mainWrapL.addWidget(self.mainTilesetDropdown)
        mainWrapL.addWidget(self.mainPicker)

        embedWrap = QtWidgets.QWidget()
        embedWrapL = QtWidgets.QVBoxLayout(embedWrap)
        embedWrapL.setContentsMargins(0, 0, 0, 0)
        embedWrapL.addWidget(self.embedImport)
        embedWrapL.addWidget(self.embedPicker)

        self.addWidget(mainWrap)
        self.addWidget(self.megaPicker)
        self.addWidget(embedWrap)


    def LoadFromTilesets(self):
        """
        Load everything from the currently-loaded tilesets.
        """
        self.mainPicker.Load(MainObjects)
        self.megaPicker.Load(OneTilesetObjects, OneTilesetHierarchy)
        self.embedPicker.Load(EmbeddedObjects)


    def ShowTileset(self, which):
        self.setCurrentIndex(which)


    def handleObjChanged(self, tab, idx):
        self.current = (tab, idx)
        self.ObjChanged.emit()


    def handleObjReplace(self, tab, idx):
        self.current = (tab, idx)
        self.ObjReplace.emit()


    def handleEmbeddedObjUpdate(self, idx):
        return self.EmbeddedObjUpdate.emit(idx)

    def handleEmbeddedObjDelete(self, idx):
        return self.EmbeddedObjDelete.emit(idx)


    def handleEmbedImport(self):
        """
        The user clicked the Import button, so do that.
        """
        obj = importOneTilesetObject()
        if not obj: return

        # Add it
        self.embedPicker.Add(obj)


    def handleMainDropdown(self):
        """
        The user changed the tileset in the Main tab
        """
        name = ['Pa0_jyotyu.sarc', 'Pa0_jyotyu_chika.sarc', 'Pa0_jyotyu_yougan.sarc', 'Pa0_jyotyu_yougan2.sarc'][self.mainTilesetDropdown.currentIndex()]
        
        with open(os.path.join(Pa0Path, name), 'rb') as f:
            data = f.read()

        LoadMainTileset(data, name)
        ProcessOverrides(MainObjects, name.split(".")[0])
        ProcessPa0Descriptions(MainObjects, name.split(".")[0])

        self.mainPicker.Load(MainObjects)

        mainWindow.scene.update()


    def setObject(self, idx):
        """
        Set the current selected object to object idx.
        """
        [self.mainPicker, self.megaPicker, self.embedPicker][self.currentIndex()].setObject(idx)


class ObjectPickerTreeWidget(QtWidgets.QTreeWidget):
    """
    A widget that lets you make a hierarchial structure of ObjectPickerListWidgets
    """

    ObjChanged = QtCore.pyqtSignal(str)
    ObjReplace = QtCore.pyqtSignal(str)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(1)
        self.setIndentation(10) # default is 20
        self.header().close() # http://www.qtforum.org/article/22020/qtreewidget-remove-header.html?s=f9097c1aceec33e13704f96bdb1e866bc086d418#post79716
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setSelectionMode(self.NoSelection)

        self.clear()


    def Load(self, objectsDict, objectsHierarchy):
        """
        Load objects from the dict and hierarchy provided.
        The folders will be alphabetized automatically.
        """
        self.clear()

        def handleObjectList(parent, nameList):
            item = QtWidgets.QTreeWidgetItem(parent)

            # Sort the name list (not in-place -- that would modify
            # the OneTilesetHierarchy global)
            nameList = sorted(nameList,
                key=lambda name: objectsDict[name]
                )

            # Convert that to a list of objects
            fullObjList = []
            for name in nameList:
                fullObjList.append(objectsDict[name])

            # Set up the list widget, etc
            listWidget = ObjectPickerListWidget(self, fullObjList)
            listWidget.setFrameStyle(QtWidgets.QFrame.NoFrame)
            listWidget.setMinimumHeight(390)
            listWidget.setMaximumHeight(390)
            self.setItemWidget(item, 0, listWidget)
            self.widget2Item[listWidget] = item
            self.allListWidgets.append(listWidget)
            listWidget.ObjChanged.connect(lambda idx: self.handleListWidgetObjectChangedReplaced(listWidget, idx, False))
            listWidget.ObjReplace.connect(lambda idx: self.handleListWidgetObjectChangedReplaced(listWidget, idx, True))

            self.objectListNames[listWidget] = nameList

        def handleFolder(parent, index, d):
            if index: index += '/'
            for key, value in sorted(d.items(), key=lambda keyval: keyval[0]):
                if key == '/':
                    handleObjectList(parent, value)
                else:
                    item = QtWidgets.QTreeWidgetItem(parent)
                    item.setText(0, key)
                    handleFolder(item, index + key, value)

        handleFolder(self, '', objectsHierarchy)


    def clear(self):
        super().clear()
        self.allListWidgets = []
        self.objectListNames = {}
        self.widget2Item = {}


    def setObject(self, idx):
        """
        Set the current selected object to idx
        """
        for widget, names in self.objectListNames.items():
            if idx in names: break
        else: return

        widget.setObject(names.index(idx))

        item = self.widget2Item[widget].parent()
        while item is not None:
            self.expandItem(item)
            item = item.parent()

        self.ObjChanged.emit(idx)


    def handleListWidgetObjectChangedReplaced(self, widget, idx, replace):
        """
        An object was selected in one of the list widgets.
        If replace is True, then the Alt key was held down, too.
        Unselect all selected objects in the other list widgets.
        """
        for w in self.allListWidgets:
            if w is not widget:
                w.clearSelection()
        if replace:
            self.ObjReplace.emit(self.objectListNames[widget][idx])
        else:
            self.ObjChanged.emit(self.objectListNames[widget][idx])


class ObjectPickerListWidget(QtWidgets.QListView):
    """
    Widget that shows a list of available objects
    """

    ObjChanged = QtCore.pyqtSignal(int)
    ObjReplace = QtCore.pyqtSignal(int)
    ObjUpdate = QtCore.pyqtSignal(int)
    ObjDelete = QtCore.pyqtSignal(int)

    objects = None

    allowImportReplace = False
    allowDelete = False

    # Monkey-patch this in if you want it
    requestDeleteObject = lambda num: True

    # Have this be a property so we can set it on
    # the model dynamically, too
    _forceNumbering = False
    @property
    def forceNumbering(self):
        return self._forceNumbering
    @forceNumbering.setter
    def forceNumbering(self, val):
        self._forceNumbering = val
        self.model_.forceNumbering = val


    def __init__(self, parent=None, objects=None):
        """
        Initializes the widget
        """
        super().__init__(parent)
        self.setFlow(self.LeftToRight)
        self.setLayoutMode(self.SinglePass)
        self.setMovement(self.Static)
        self.setResizeMode(self.Adjust)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setWrapping(True)

        self.model_ = self.ObjectListModel()
        self.setModel(self.model_)

        self.setItemDelegate(self.ObjectItemDelegate())

        self.clicked.connect(self.HandleObjReplace)

        if objects is not None:
            self.Load(objects)


    def Load(self, objects):
        """
        Load these objects into the widget
        """
        self.objects = objects
        self.model_.Load(objects)


    def Add(self, object):
        """
        Add this object to the widget.
        """
        self.objects.append(object)
        self.model_.Add(object)


    def contextMenuEvent(self, e):
        """
        The user right-clicked the object view widget
        """
        super().contextMenuEvent(e)

        idx = self.indexAt(e.pos())

        menu = QtWidgets.QMenu()
        menu.addAction('Export...', lambda: self.exportObject(idx.row()))
        if self.allowImportReplace:
            menu.addAction('Import Replacement...', lambda: self.importReplaceObject(idx.row()))
        if self.allowDelete:
            menu.addAction('Delete', lambda: self.deleteObject(idx.row()))
        menu.exec_(e.globalPos())


    def exportObject(self, num):
        """
        The user hit Export.
        """
        obj = self.objects[num]

        folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Export Object to This Folder')
        if not folder: return

        for fn, fd in obj.asNewFormat().items():
            with open(os.path.join(folder, fn), 'wb') as f:
                f.write(fd)


    def importReplaceObject(self, num):
        """
        The user hit Import Replacement.
        """

        obj = importOneTilesetObject()
        if not obj: return

        self.objects[num] = obj
        self.model_.Replace(obj, num)

        self.ObjUpdate.emit(num)


    def deleteObject(self, num):
        """
        The user hit Delete.
        """
        if not self.requestDeleteObject(num): return

        del self.objects[num]
        self.model_.Remove(num)

        self.ObjDelete.emit(num)


    def setObject(self, idx):
        """
        Set the currently-selected object to idx
        """
        self.selectionModel().clearSelection()
        self.selectionModel().select(self.model_.index(idx, 0), QtCore.QItemSelectionModel.Select)
        self.ObjChanged.emit(idx)


    def currentChanged(self, current, previous):
        """
        Throws a signal when the selected object changed
        """
        self.ObjChanged.emit(current.row())


    def HandleObjReplace(self, index):
        """
        Throws a signal when the selected object is used as a replacement
        """
        if QtWidgets.QApplication.keyboardModifiers() == Qt.AltModifier:
            self.ObjReplace.emit(index.row())


    class ObjectItemDelegate(QtWidgets.QAbstractItemDelegate):
        """
        Handles tileset objects and their rendering
        """

        def paint(self, painter, option, index):
            """
            Paints an object
            """
            if option.state & QtWidgets.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            p = index.model().data(index, Qt.DecorationRole)
            if p is not None:
                # p might be None due to threading issues from progressive
                # tileset loading.
                painter.drawPixmap(option.rect.x()+2, option.rect.y()+2, p)
            #painter.drawText(option.rect, str(index.row()))

        def sizeHint(self, option, index):
            """
            Returns the size for the object
            """
            m = index.model()
            return m.data(index, Qt.UserRole) or QtCore.QSize(TileWidth, TileWidth)


    class ObjectListModel(QtCore.QAbstractListModel):
        """
        Model containing all the objects in a tileset
        """

        forceNumbering = False

        def __init__(self):
            """
            Initializes the model
            """
            super().__init__()
            self.objects = [None] * 256
            self.ritems = [None] * 256
            self.itemsize = []
            self.tooltips = []

        def rowCount(self, parent=None):
            """
            Required by Qt
            """
            return len(self.objects)

        def data(self, index, role=Qt.DisplayRole):
            """
            Get what we have for a specific row
            """
            if not index.isValid(): return None
            n = index.row()
            if n < 0: return None
            if n >= len(self.objects): return None

            if role == Qt.DecorationRole and n < len(self.ritems):
                return self.ritems[n]

            if role == Qt.BackgroundRole:
                return QtGui.qApp.palette().base()

            if role == Qt.UserRole and n < len(self.itemsize):
                return self.itemsize[n]

            if role == Qt.ToolTipRole and n < len(self.tooltips):
                return self.tooltips[n]

            return None


        def Load(self, defs):
            """
            Renders all the object previews for the model
            """
            self.beginResetModel()

            self.objects = []
            self.ritems = []
            self.itemsize = []
            self.tooltips = []

            for obj in defs:
                self._add(obj)

            self.endResetModel()


        def Add(self, object):
            """
            Add this object to the model.
            """
            self.beginResetModel()
            self._add(object)
            self.endResetModel()


        def Replace(self, object, idx):
            """
            Replace the object at idx with this one.
            """
            self.beginResetModel()

            self.objects[idx] = object

            pm = self._makePreview(object)
            self.ritems[idx] = pm
            self.itemsize[idx] = pm.size() + QtCore.QSize(4, 4)

            self.tooltips[idx] = self._makeTooltip(object, idx, self.forceNumbering)

            self.endResetModel()


        def _add(self, object):
            """
            Actually adds an object to the model.
            Don't use this directly -- use Add() to get the boilerplate
            setup stuff done, too.
            If forceNumber is True, the object will forcefully be given
            a name like "Object 22", even if it already has another name.
            """
            self.objects.append(object)

            pm = self._makePreview(object)
            self.ritems.append(pm)
            self.itemsize.append(pm.size() + QtCore.QSize(4, 4))

            self.tooltips.append(self._makeTooltip(object, len(self.objects) - 1, self.forceNumbering))


        @staticmethod
        def _makePreview(obj):
            """
            Make a preview for this object.
            """

            # Constants
            FORCED_TILE_WIDTH = 32 # Objects will be resized so that each tile is this wide...
            FORCED_MAX_WH = 250    # ... unless that causes the object to be taller or wider than
                                   # this, in which case it will be shrank until it fits this.

            pm = QtGui.QPixmap.fromImage(PIL.ImageQt.ImageQt(nsmbulib.Tile.tilesToImage(obj.render(obj.width, obj.height), useRepr=True)))

            # Resize objects while imposing a maximum width and height
            st = Qt.SmoothTransformation
            w, h = pm.width() * FORCED_TILE_WIDTH / TileWidth, pm.height() * FORCED_TILE_WIDTH / TileWidth
            if w > h and w > FORCED_MAX_WH:
                pm = pm.scaledToWidth(FORCED_MAX_WH, st)
            elif h > w and h > FORCED_MAX_WH:
                pm = pm.scaledToHeight(FORCED_MAX_WH, st)
            else:
                pm = pm.scaledToWidth(w, st)

            return pm


        @staticmethod
        def _makeTooltip(obj, num, forceNumbering):
            """
            Make a tooltip for this object, with number num.
            If forceNumbering is True, the object will forcefully be given
            a name like "Object 22", even if it already has another name.
            """
            if obj.name and not forceNumbering:
                name = obj.name
            else:
                name = 'Object %d' % num

            name += ' (' + str(obj.role)

            if obj.randomizeX or obj.randomizeY:
                name += ', randomized'

            if obj.decorative:
                name += ', decorative'

            name += ')'

            if obj.description:
                name += ': \n' + obj.description

            return name


        def Remove(self, num):
            """
            Remove the num'th object.
            """
            self.beginResetModel()

            # Remove the thing
            del self.objects[num]
            del self.ritems[num]
            del self.itemsize[num]
            del self.tooltips[num]

            # Update object names for the objects with higher indices
            for idx in range(num, len(self.tooltips)):
                self.tooltips[idx] = self._makeTooltip(self.objects[idx], idx, self.forceNumbering)

            # Let Qt know we're done
            self.endResetModel()


class StampChooserWidget(QtWidgets.QListView):
    """
    Widget that shows a list of available stamps
    """
    selectionChangedSignal = QtCore.pyqtSignal()
    def __init__(self):
        """
        Initializes the widget
        """
        super().__init__()

        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setLayoutMode(QtWidgets.QListView.SinglePass)
        self.setMovement(QtWidgets.QListView.Static)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setWrapping(True)

        self.model = StampListModel()
        self.setModel(self.model)

        self.setItemDelegate(StampChooserWidget.StampItemDelegate())


    class StampItemDelegate(QtWidgets.QStyledItemDelegate):
        """
        Handles stamp rendering
        """

        def __init__(self):
            """
            Initializes the delegate
            """
            super().__init__()

        def createEditor(self, parent, option, index):
            """
            Creates a stamp name editor
            """
            return QtWidgets.QLineEdit(parent)

        def setEditorData(self, editor, index):
            """
            Sets the data for the stamp name editor from the data at index
            """
            editor.setText(index.model().data(index, Qt.UserRole + 1))

        def setModelData(self, editor, model, index):
            """
            Set the data in the model for the data at index
            """
            index.model().setData(index, editor.text())

        def paint(self, painter, option, index):
            """
            Paints a stamp
            """

            if option.state & QtWidgets.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            painter.drawPixmap(option.rect.x() + 2, option.rect.y() + 2, index.model().data(index, Qt.DecorationRole))

        def sizeHint(self, option, index):
            """
            Returns the size for the stamp
            """
            return index.model().data(index, Qt.DecorationRole).size() + QtCore.QSize(4, 4)


    def addStamp(self, stamp):
        """
        Adds a stamp
        """
        self.model.addStamp(stamp)


    def removeStamp(self, stamp):
        """
        Removes a stamp
        """
        self.model.removeStamp(stamp)


    def currentlySelectedStamp(self):
        """
        Returns the currently selected stamp
        """
        idxobj = self.currentIndex()
        if idxobj.row() == -1: return
        return self.model.items[idxobj.row()]

    def selectionChanged(self, selected, deselected):
        """
        Called when the selection changes.
        """
        val = super().selectionChanged(selected, deselected)
        self.selectionChangedSignal.emit()
        return val


class SpritePickerWidget(QtWidgets.QTreeWidget):
    """
    Widget that shows a list of available sprites
    """
    def __init__(self):
        """
        Initializes the widget
        """
        super().__init__()
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.currentItemChanged.connect(self.HandleItemChange)

        LoadSpriteData()
        LoadSpriteListData()
        LoadSpriteCategories()
        self.LoadItems()

    def LoadItems(self):
        """
        Loads tree widget items
        """
        self.clear()

        for viewname, view, nodelist in SpriteCategories:
            for n in nodelist:
                nodelist.remove(n)
            for catname, category in view:
                cnode = QtWidgets.QTreeWidgetItem()
                cnode.setText(0, catname)
                cnode.setData(0, Qt.UserRole, -1)

                isSearch = (catname == trans.string('Sprites', 16))
                if isSearch:
                    self.SearchResultsCategory = cnode
                    SearchableItems = []

                for id in category:
                    snode = QtWidgets.QTreeWidgetItem()
                    if id == 9999:
                        snode.setText(0, trans.string('Sprites', 17))
                        snode.setData(0, Qt.UserRole, -2)
                        self.NoSpritesFound = snode
                    else:
                        snode.setText(0, trans.string('Sprites', 18, '[id]', id, '[name]', Sprites[id].name))
                        snode.setData(0, Qt.UserRole, id)

                    if isSearch:
                        SearchableItems.append(snode)

                    cnode.addChild(snode)

                self.addTopLevelItem(cnode)
                cnode.setHidden(True)
                nodelist.append(cnode)

        self.ShownSearchResults = SearchableItems
        self.NoSpritesFound.setHidden(True)

        self.itemClicked.connect(self.HandleSprReplace)

        # BUGFIX: Makes sure the first view is loaded when the editor is started.
        self.SwitchView(SpriteCategories[0])


    def SwitchView(self, view):
        """
        Changes the selected sprite view
        """
        for i in range(0, self.topLevelItemCount()):
            self.topLevelItem(i).setHidden(True)

        for node in view[2]:
            node.setHidden(False)


    def HandleItemChange(self, current, previous):
        """
        Throws a signal when the selected object changed
        """
        if current is None: return
        id = current.data(0, Qt.UserRole)
        if id != -1:
            self.SpriteChanged.emit(id)


    def SetSearchString(self, searchfor):
        """
        Shows the items containing that string
        """
        check = self.SearchResultsCategory

        rawresults = self.findItems(searchfor, Qt.MatchContains | Qt.MatchRecursive)
        results = list(filter((lambda x: x.parent() == check), rawresults))

        for x in self.ShownSearchResults:
            x.setHidden(True)
        for x in results:
            x.setHidden(False)
        self.ShownSearchResults = results

        self.NoSpritesFound.setHidden((len(results) != 0))
        self.SearchResultsCategory.setExpanded(True)


    def HandleSprReplace(self, item, column):
        """
        Throws a signal when the selected sprite is used as a replacement
        """
        if QtWidgets.QApplication.keyboardModifiers() == Qt.AltModifier:
            id = item.data(0, Qt.UserRole)
            if id != -1:
                self.SpriteReplace.emit(id)

    SpriteChanged = QtCore.pyqtSignal(int)
    SpriteReplace = QtCore.pyqtSignal(int)


class SpriteEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing sprite data
    """
    DataUpdate = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create the raw editor
        font = QtGui.QFont()
        font.setPointSize(8)
        editbox = QtWidgets.QLabel(trans.string('SpriteDataEditor', 3))
        editbox.setFont(font)
        edit = QtWidgets.QLineEdit()
        edit.textEdited.connect(self.HandleRawDataEdited)
        self.raweditor = edit

        editboxlayout = QtWidgets.QHBoxLayout()
        editboxlayout.addWidget(editbox)
        editboxlayout.addWidget(edit)
        editboxlayout.setStretch(1, 1)

        # 'Editing Sprite #' label
        self.spriteLabel = QtWidgets.QLabel('-')
        self.spriteLabel.setWordWrap(True)

        self.noteButton = QtWidgets.QToolButton()
        self.noteButton.setIcon(GetIcon('note'))
        self.noteButton.setText(trans.string('SpriteDataEditor', 4))
        self.noteButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.noteButton.setAutoRaise(True)
        self.noteButton.clicked.connect(self.ShowNoteTooltip)

        self.relatedObjFilesButton = QtWidgets.QToolButton()
        self.relatedObjFilesButton.setIcon(GetIcon('data'))
        self.relatedObjFilesButton.setText(trans.string('SpriteDataEditor', 7))
        self.relatedObjFilesButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.relatedObjFilesButton.setAutoRaise(True)
        self.relatedObjFilesButton.clicked.connect(self.ShowRelatedObjFilesTooltip)

        toplayout = QtWidgets.QHBoxLayout()
        toplayout.addWidget(self.spriteLabel)
        toplayout.addStretch(1)
        toplayout.addWidget(self.relatedObjFilesButton)
        toplayout.addWidget(self.noteButton)

        subLayout = QtWidgets.QVBoxLayout()
        subLayout.setContentsMargins(0, 0, 0, 0)

        # create a layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(toplayout)
        mainLayout.addLayout(subLayout)

        layout = QtWidgets.QGridLayout()
        self.editorlayout = layout
        subLayout.addLayout(layout)
        subLayout.addLayout(editboxlayout)

        self.setLayout(mainLayout)

        self.spritetype = -1
        self.data = b'\0\0\0\0\0\0\0\0\0\0\0\0'
        self.fields = []
        self.UpdateFlag = False
        self.DefaultMode = defaultmode

        self.notes = None
        self.relatedObjFiles = None


    class PropertyDecoder(QtCore.QObject):
        """
        Base class for all the sprite data decoder/encoders
        """
        updateData = QtCore.pyqtSignal('PyQt_PyObject')

        def retrieve(self, data):
            """
            Extracts the value from the specified nybble(s)
            """
            nybble = self.nybble

            if isinstance(nybble, tuple):
                if nybble[1] == (nybble[0] + 2) and (nybble[0] | 1) == 0:
                    # optimize if it's just one byte
                    return data[nybble[0] >> 1]
                else:
                    # we have to calculate it sadly
                    # just do it by looping, shouldn't be that bad
                    value = 0
                    for n in range(nybble[0], nybble[1]):
                        value <<= 4
                        value |= (data[n >> 1] >> (0 if (n & 1) == 1 else 4)) & 15
                    return value
            else:
                # we just want one nybble
                if nybble >= (len(data) * 2): return 0
                return (data[nybble//2] >> (0 if (nybble & 1) == 1 else 4)) & 15


        def insertvalue(self, data, value):
            """
            Assigns a value to the specified nybble(s)
            """
            nybble = self.nybble
            sdata = list(data)

            if isinstance(nybble, tuple):
                if nybble[1] == (nybble[0] + 2) and (nybble[0] | 1) == 0:
                    # just one byte, this is easier
                    sdata[nybble[0] >> 1] = value & 255
                else:
                    # AAAAAAAAAAA
                    for n in reversed(range(nybble[0], nybble[1])):
                        cbyte = sdata[n >> 1]
                        if (n & 1) == 1:
                            cbyte = (cbyte & 240) | (value & 15)
                        else:
                            cbyte = ((value & 15) << 4) | (cbyte & 15)
                        sdata[n >> 1] = cbyte
                        value >>= 4
            else:
                # only overwrite one nybble
                cbyte = sdata[nybble >> 1]
                if (nybble & 1) == 1:
                    cbyte = (cbyte & 240) | (value & 15)
                else:
                    cbyte = ((value & 15) << 4) | (cbyte & 15)
                sdata[nybble >> 1] = cbyte

            return bytes(sdata)


    class CheckboxPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a checkbox
        """

        def __init__(self, title, nybble, mask, comment, layout, row):
            """
            Creates the widget
            """
            super().__init__()

            self.widget = QtWidgets.QCheckBox(title)
            if comment is not None: self.widget.setToolTip(comment)
            self.widget.clicked.connect(self.HandleClick)

            if isinstance(nybble, tuple):
                length = nybble[1] - nybble[0] + 1
            else:
                length = 1

            xormask = 0
            for i in range(length):
                xormask |= 0xF << (i * 4)

            self.nybble = nybble
            self.mask = mask
            self.xormask = xormask
            layout.addWidget(self.widget, row, 0, 1, 2)

        def update(self, data):
            """
            Updates the value shown by the widget
            """
            value = ((self.retrieve(data) & self.mask) == self.mask)
            self.widget.setChecked(value)

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            value = self.retrieve(data) & (self.mask ^ self.xormask)
            if self.widget.isChecked():
                value |= self.mask
            return self.insertvalue(data, value)

        def HandleClick(self, clicked=False):
            """
            Handles clicks on the checkbox
            """
            self.updateData.emit(self)


    class ListPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a combobox
        """

        def __init__(self, title, nybble, model, comment, layout, row):
            """
            Creates the widget
            """
            super().__init__()

            self.model = model
            self.widget = QtWidgets.QComboBox()
            self.widget.setModel(model)
            if comment is not None: self.widget.setToolTip(comment)
            self.widget.currentIndexChanged.connect(self.HandleIndexChanged)

            self.nybble = nybble
            layout.addWidget(QtWidgets.QLabel(title+':'), row, 0, Qt.AlignRight)
            layout.addWidget(self.widget, row, 1)

        def update(self, data):
            """
            Updates the value shown by the widget
            """
            value = self.retrieve(data)
            if not self.model.existingLookup[value]:
                self.widget.setCurrentIndex(-1)
                return

            i = 0
            for x in self.model.entries:
                if x[0] == value:
                    self.widget.setCurrentIndex(i)
                    break
                i += 1

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            return self.insertvalue(data, self.model.entries[self.widget.currentIndex()][0])

        def HandleIndexChanged(self, index):
            """
            Handle the current index changing in the combobox
            """
            self.updateData.emit(self)


    class ValuePropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a spinbox
        """

        def __init__(self, title, nybble, max, comment, layout, row):
            """
            Creates the widget
            """
            super().__init__()

            self.widget = QtWidgets.QSpinBox()
            self.widget.setRange(0, max - 1)
            if comment is not None: self.widget.setToolTip(comment)
            self.widget.valueChanged.connect(self.HandleValueChanged)

            self.nybble = nybble
            layout.addWidget(QtWidgets.QLabel(title+':'), row, 0, Qt.AlignRight)
            layout.addWidget(self.widget, row, 1)

        def update(self, data):
            """
            Updates the value shown by the widget
            """
            value = self.retrieve(data)
            self.widget.setValue(value)

        def assign(self, data):
            """
            Assigns the selected value to the data
            """
            return self.insertvalue(data, self.widget.value())

        def HandleValueChanged(self, value):
            """
            Handle the value changing in the spinbox
            """
            self.updateData.emit(self)


    class BitfieldPropertyDecoder(PropertyDecoder):
        """
        Class that decodes/encodes sprite data to/from a bitfield
        """

        def __init__(self, title, startbit, bitnum, comment, layout, row):
            """
            Creates the widget
            """
            super().__init__()

            self.startbit = startbit
            self.bitnum = bitnum

            self.widgets = []
            CheckboxLayout = QtWidgets.QGridLayout()
            CheckboxLayout.setContentsMargins(0, 0, 0, 0)
            for i in range(bitnum):
                c = QtWidgets.QCheckBox()
                self.widgets.append(c)
                CheckboxLayout.addWidget(c, 0, i)
                if comment is not None: c.setToolTip(comment)
                c.toggled.connect(self.HandleValueChanged)

                L = QtWidgets.QLabel(str(i + 1))
                CheckboxLayout.addWidget(L, 1, i)
                CheckboxLayout.setAlignment(L, Qt.AlignHCenter)

            w = QtWidgets.QWidget()
            w.setLayout(CheckboxLayout)

            layout.addWidget(QtWidgets.QLabel(title + ':'), row, 0, Qt.AlignRight)
            layout.addWidget(w, row, 1)

        def update(self, data):
            """
            Updates the value shown by the widget
            """
            for bitIdx in range(self.bitnum):
                checkbox = self.widgets[bitIdx]

                adjustedIdx = bitIdx + self.startbit
                byteNum = adjustedIdx // 8
                bitNum = adjustedIdx % 8
                checkbox.setChecked((data[byteNum] >> (7 - bitNum) & 1))

        def assign(self, data):
            """
            Assigns the checkbox states to the data
            """
            data = bytearray(data)

            for idx in range(self.bitnum):
                checkbox = self.widgets[idx]

                adjustedIdx = idx + self.startbit
                byteIdx = adjustedIdx // 8
                bitIdx = adjustedIdx % 8

                origByte = data[byteIdx]
                origBit = (origByte >> (7 - bitIdx)) & 1
                newBit = 1 if checkbox.isChecked() else 0

                if origBit == newBit: continue
                if origBit == 0 and newBit == 1:
                    # Turn the byte on by OR-ing it in
                    newByte = (origByte | (1 << (7 - bitIdx))) & 0xFF
                else:
                    # Turn it off by:
                    # inverting it
                    # OR-ing in the new byte
                    # inverting it back
                    newByte = ~origByte & 0xFF
                    newByte = newByte | (1 << (7 - bitIdx))
                    newByte = ~newByte & 0xFF

                data[byteIdx] = newByte

            return bytes(data)

        def HandleValueChanged(self, value):
            """
            Handle any checkbox being changed
            """
            self.updateData.emit(self)


    def setSprite(self, type, reset=False):
        """
        Change the sprite type used by the data editor
        """
        if (self.spritetype == type) and not reset: return

        self.spritetype = type
        if type != 1000:
            sprite = Sprites[type]
        else:
            sprite = None

        # remove all the existing widgets in the layout
        layout = self.editorlayout
        for row in range(2, layout.rowCount()):
            for column in range(0, layout.columnCount()):
                w = layout.itemAtPosition(row, column)
                if w is not None:
                    widget = w.widget()
                    layout.removeWidget(widget)
                    widget.setParent(None)

        if sprite is None:
            self.spriteLabel.setText(trans.string('SpriteDataEditor', 5, '[id]', type))
            self.noteButton.setVisible(False)

            # use the raw editor if nothing is there
            self.raweditor.setVisible(True)
            if len(self.fields) > 0: self.fields = []

        else:
            self.spriteLabel.setText(trans.string('SpriteDataEditor', 6, '[id]', type, '[name]', sprite.name))

            self.noteButton.setVisible(sprite.notes is not None)
            self.notes = sprite.notes

            self.relatedObjFilesButton.setVisible(sprite.relatedObjFiles is not None)
            self.relatedObjFiles = sprite.relatedObjFiles

            # create all the new fields
            fields = []
            row = 2

            for f in sprite.fields:
                if f[0] == 0:
                    nf = SpriteEditorWidget.CheckboxPropertyDecoder(f[1], f[2], f[3], f[4], layout, row)
                elif f[0] == 1:
                    nf = SpriteEditorWidget.ListPropertyDecoder(f[1], f[2], f[3], f[4], layout, row)
                elif f[0] == 2:
                    nf = SpriteEditorWidget.ValuePropertyDecoder(f[1], f[2], f[3], f[4], layout, row)
                elif f[0] == 3:
                    nf = SpriteEditorWidget.BitfieldPropertyDecoder(f[1], f[2], f[3], f[4], layout, row)

                nf.updateData.connect(self.HandleFieldUpdate)
                fields.append(nf)
                row += 1

            self.fields = fields


    def update(self):
        """
        Updates all the fields to display the appropriate info
        """
        self.UpdateFlag = True

        data = self.data
        self.raweditor.setText('%02x%02x %02x%02x %02x%02x %02x%02x %02x%02x %02x%02x' % (data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11]))
        self.raweditor.setStyleSheet('')

        # Go through all the data
        for f in self.fields:
            f.update(data)

        self.UpdateFlag = False



    def ShowNoteTooltip(self):
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), self.notes, self)



    def ShowRelatedObjFilesTooltip(self):
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), self.relatedObjFiles, self)


    def HandleFieldUpdate(self, field):
        """
        Triggered when a field's data is updated
        """
        if self.UpdateFlag: return

        data = field.assign(self.data)
        self.data = data

        self.raweditor.setText('%02x%02x %02x%02x %02x%02x %02x%02x %02x%02x %02x%02x' % (data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11]))
        self.raweditor.setStyleSheet('')

        for f in self.fields:
            if f != field: f.update(data)

        self.DataUpdate.emit(data)


    def HandleRawDataEdited(self, text):
        """
        Triggered when the raw data textbox is edited
        """

        raw = text.replace(' ', '')
        valid = False

        if len(raw) == 24:
            try:
                data = []
                for r in range(0, len(raw), 2):
                    data.append(int(raw[r:r+2], 16))
                data = bytes(data)
                valid = True
            except Exception: pass

        # if it's valid, let it go
        if valid:
            self.raweditor.setStyleSheet('')
            self.data = data

            self.UpdateFlag = True
            for f in self.fields: f.update(data)
            self.UpdateFlag = False

            self.DataUpdate.emit(data)
            self.raweditor.setStyleSheet('QLineEdit { background-color: #ffffff; }')
        else:
            self.raweditor.setStyleSheet('QLineEdit { background-color: #ffd2d2; }')


class EntranceEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing entrance properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create widgets
        self.entranceID = QtWidgets.QSpinBox()
        self.entranceID.setRange(0, 255)
        self.entranceID.setToolTip(trans.string('EntranceDataEditor', 1))
        self.entranceID.valueChanged.connect(self.HandleEntranceIDChanged)

        self.entranceType = QtWidgets.QComboBox()
        LoadEntranceNames()
        self.entranceType.addItems(EntranceTypeNames)
        self.entranceType.setToolTip(trans.string('EntranceDataEditor', 3))
        self.entranceType.activated.connect(self.HandleEntranceTypeChanged)

        self.destArea = QtWidgets.QSpinBox()
        self.destArea.setRange(0, 4)
        self.destArea.setToolTip(trans.string('EntranceDataEditor', 7))
        self.destArea.valueChanged.connect(self.HandleDestAreaChanged)

        self.destEntrance = QtWidgets.QSpinBox()
        self.destEntrance.setRange(0, 255)
        self.destEntrance.setToolTip(trans.string('EntranceDataEditor', 5))
        self.destEntrance.valueChanged.connect(self.HandleDestEntranceChanged)

        self.allowEntryCheckbox = QtWidgets.QCheckBox(trans.string('EntranceDataEditor', 8))
        self.allowEntryCheckbox.setToolTip(trans.string('EntranceDataEditor', 9))
        self.allowEntryCheckbox.clicked.connect(self.HandleAllowEntryClicked)

        self.unk05 = QtWidgets.QSpinBox()
        self.unk05.setRange(0, 255)
        self.unk05.setToolTip('Unknown 0x05')
        self.unk05.valueChanged.connect(self.HandleUnk05)
        self.unk0C = QtWidgets.QSpinBox()
        self.unk0C.setRange(0, 255)
        self.unk0C.setToolTip('Unknown 0x0C')
        self.unk0C.valueChanged.connect(self.HandleUnk0C)
        self.unk0F = QtWidgets.QSpinBox()
        self.unk0F.setRange(0, 255)
        self.unk0F.setToolTip('Unknown 0x0F')
        self.unk0F.valueChanged.connect(self.HandleUnk0F)
        self.unk12 = QtWidgets.QSpinBox()
        self.unk12.setRange(0, 255)
        self.unk12.setToolTip('Unknown 0x12')
        self.unk12.valueChanged.connect(self.HandleUnk12)
        self.unk13 = QtWidgets.QSpinBox()
        self.unk13.setRange(0, 255)
        self.unk13.setToolTip('Unknown 0x13')
        self.unk13.valueChanged.connect(self.HandleUnk13)
        self.unk14 = QtWidgets.QSpinBox()
        self.unk14.setRange(0, 255)
        self.unk14.setToolTip('Unknown 0x14')
        self.unk14.valueChanged.connect(self.HandleUnk14)
        self.unk15 = QtWidgets.QSpinBox()
        self.unk15.setRange(0, 255)
        self.unk15.setToolTip('Unknown 0x15')
        self.unk15.valueChanged.connect(self.HandleUnk15)
        self.unk16 = QtWidgets.QSpinBox()
        self.unk16.setRange(0, 255)
        self.unk16.setToolTip('Unknown 0x16')
        self.unk16.valueChanged.connect(self.HandleUnk16)


        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Entrance #' label
        self.editingLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 0, 0, 1, 4, Qt.AlignTop)

        # add labels
        layout.addWidget(QtWidgets.QLabel(trans.string('EntranceDataEditor', 2)), 1, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(trans.string('EntranceDataEditor', 0)), 3, 0, 1, 1, Qt.AlignRight)

        layout.addWidget(createHorzLine(), 2, 0, 1, 4)

        layout.addWidget(QtWidgets.QLabel(trans.string('EntranceDataEditor', 4)), 3, 2, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(trans.string('EntranceDataEditor', 6)), 4, 2, 1, 1, Qt.AlignRight)

        # add the widgets
        layout.addWidget(self.entranceType, 1, 1, 1, 3)
        layout.addWidget(self.entranceID, 3, 1, 1, 1)

        layout.addWidget(self.destEntrance, 3, 3, 1, 1)
        layout.addWidget(self.destArea, 4, 3, 1, 1)
        layout.addWidget(createHorzLine(), 5, 0, 1, 4)
        layout.addWidget(self.allowEntryCheckbox, 6, 0, 1, 2)#, Qt.AlignRight)
        layout.addWidget(createHorzLine(), 7, 0, 1, 4)

        layout.addWidget(QtWidgets.QLabel('Unknown 0x05:'), 8, 0)
        layout.addWidget(QtWidgets.QLabel('Unknown 0x0C:'), 9, 0)
        layout.addWidget(QtWidgets.QLabel('Unknown 0x0F:'), 10, 0)
        layout.addWidget(QtWidgets.QLabel('Unknown 0x12:'), 11, 0)
        layout.addWidget(QtWidgets.QLabel('Unknown 0x13:'), 12, 0)
        layout.addWidget(QtWidgets.QLabel('Unknown 0x14:'), 13, 0)
        layout.addWidget(QtWidgets.QLabel('Unknown 0x15:'), 14, 0)
        layout.addWidget(QtWidgets.QLabel('Unknown 0x16:'), 15, 0)
        layout.addWidget(self.unk05, 8, 1)
        layout.addWidget(self.unk0C, 9, 1)
        layout.addWidget(self.unk0F, 10, 1)
        layout.addWidget(self.unk12, 11, 1)
        layout.addWidget(self.unk13, 12, 1)
        layout.addWidget(self.unk14, 13, 1)
        layout.addWidget(self.unk15, 14, 1)
        layout.addWidget(self.unk16, 15, 1)

        self.ent = None
        self.UpdateFlag = False


    def setEntrance(self, ent):
        """
        Change the entrance being edited by the editor, update all fields
        """
        if self.ent == ent: return

        self.editingLabel.setText(trans.string('EntranceDataEditor', 23, '[id]', ent.entid))
        self.ent = ent
        self.UpdateFlag = True

        self.entranceID.setValue(ent.entid)
        self.entranceType.setCurrentIndex(ent.enttype)
        self.destArea.setValue(ent.destarea)
        self.destEntrance.setValue(ent.destentrance)

        self.unk05.setValue(ent.unk05)
        self.unk0C.setValue(ent.unk0C)
        self.unk0F.setValue(ent.unk0F)
        self.unk12.setValue(ent.unk12)
        self.unk13.setValue(ent.unk13)
        self.unk14.setValue(ent.unk14)
        self.unk15.setValue(ent.unk15)
        self.unk16.setValue(ent.unk16)

        self.allowEntryCheckbox.setChecked(((ent.entsettings & 0x80) == 0))

        self.UpdateFlag = False


    def HandleEntranceIDChanged(self, i):
        """
        Handler for the entrance ID changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.entid = i
        self.ent.update()
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
        self.editingLabel.setText(trans.string('EntranceDataEditor', 23, '[id]', i))


    def HandleEntranceTypeChanged(self, i):
        """
        Handler for the entrance type changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.enttype = i
        self.ent.TypeChange()
        self.ent.update()
        self.ent.UpdateTooltip()
        mainWindow.scene.update()
        self.ent.UpdateListItem()


    def HandleDestAreaChanged(self, i):
        """
        Handler for the destination area changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.destarea = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()


    def HandleDestEntranceChanged(self, i):
        """
        Handler for the destination entrance changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.destentrance = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()


    def HandleUnk05(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.unk05 = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
    def HandleUnk0C(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.unk0C = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
    def HandleUnk0F(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.unk0F = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
    def HandleUnk12(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.unk12 = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
    def HandleUnk13(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.unk13 = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
    def HandleUnk14(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.unk14 = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
    def HandleUnk15(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.unk15 = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()
    def HandleUnk16(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.ent.unk16 = i
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()


    def HandleAllowEntryClicked(self, checked):
        """
        Handle for the Allow Entry checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if not checked:
            self.ent.entsettings |= 0x80
        else:
            self.ent.entsettings &= ~0x80
        self.ent.UpdateTooltip()
        self.ent.UpdateListItem()


    def HandleUnknownFlagClicked(self, checked):
        """
        Handle for the Unknown Flag checkbox being clicked
        """
        if self.UpdateFlag: return
        SetDirty()
        if checked:
            self.ent.entsettings |= 2
        else:
            self.ent.entsettings &= ~2


    def HandleActiveLayerChanged(self, i):
        """
        Handle for the active layer changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.ent.entlayer = i


class PathNodeEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing path node properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create widgets
        #[20:52:41]  [Angel-SL] 1. (readonly) pathid 2. (readonly) nodeid 3. x 4. y 5. speed (float spinner) 6. accel (float spinner)
        #not doing [20:52:58]  [Angel-SL] and 2 buttons - 7. 'Move Up' 8. 'Move Down'
        self.speed = QtWidgets.QDoubleSpinBox()
        self.speed.setRange(min(sys.float_info), max(sys.float_info))
        self.speed.setToolTip(trans.string('PathDataEditor', 3))
        self.speed.setDecimals(int(sys.float_info.__getattribute__('dig')))
        self.speed.valueChanged.connect(self.HandleSpeedChanged)
        self.speed.setMaximumWidth(256)

        self.accel = QtWidgets.QDoubleSpinBox()
        self.accel.setRange(min(sys.float_info), max(sys.float_info))
        self.accel.setToolTip(trans.string('PathDataEditor', 5))
        self.accel.setDecimals(int(sys.float_info.__getattribute__('dig')))
        self.accel.valueChanged.connect(self.HandleAccelChanged)
        self.accel.setMaximumWidth(256)

        self.delay = QtWidgets.QSpinBox()
        self.delay.setRange(0, 65535)
        self.delay.setToolTip(trans.string('PathDataEditor', 7))
        self.delay.valueChanged.connect(self.HandleDelayChanged)
        self.delay.setMaximumWidth(256)

        self.loops = QtWidgets.QCheckBox()
        self.loops.setToolTip(trans.string('PathDataEditor', 1))
        self.loops.stateChanged.connect(self.HandleLoopsChanged)

        self.unk1 = QtWidgets.QSpinBox()
        self.unk1.setRange(-127, 127)
        self.unk1.setToolTip(trans.string('PathDataEditor', 12))
        self.unk1.valueChanged.connect(self.Handleunk1Changed)
        self.unk1.setMaximumWidth(256)

        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Path #' label
        self.editingLabel = QtWidgets.QLabel('-')
        self.editingPathLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 3, 0, 1, 2, Qt.AlignTop)
        layout.addWidget(self.editingPathLabel, 0, 0, 1, 2, Qt.AlignTop)
        # add labels
        layout.addWidget(QtWidgets.QLabel(trans.string('PathDataEditor', 0)), 1, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(trans.string('PathDataEditor', 2)), 4, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(trans.string('PathDataEditor', 4)), 5, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(trans.string('PathDataEditor', 6)), 6, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(trans.string('PathDataEditor', 11)), 7, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(createHorzLine(), 2, 0, 1, 2)

        # add the widgets
        layout.addWidget(self.loops, 1, 1)
        layout.addWidget(self.speed, 4, 1)
        layout.addWidget(self.accel, 5, 1)
        layout.addWidget(self.delay, 6, 1)
        layout.addWidget(self.unk1, 7, 1)


        self.path = None
        self.UpdateFlag = False


    def setPath(self, path):
        """
        Change the path being edited by the editor, update all fields
        """
        if self.path == path: return

        if path.pathid == 90:
            self.editingPathLabel.setText(trans.string('PathDataEditor', 13, '[id]', path.pathid))
        else:
            self.editingPathLabel.setText(trans.string('PathDataEditor', 8, '[id]', path.pathid))
        self.editingLabel.setText(trans.string('PathDataEditor', 9, '[id]', path.nodeid))
        self.path = path
        self.UpdateFlag = True

        self.speed.setValue(path.nodeinfo['speed'])
        self.accel.setValue(path.nodeinfo['accel'])
        self.delay.setValue(path.nodeinfo['delay'])
        self.loops.setChecked(path.pathinfo['loops'])

        self.UpdateFlag = False


    def HandleSpeedChanged(self, i):
        """
        Handler for the speed changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.path.nodeinfo['speed'] = i


    def HandleAccelChanged(self, i):
        """
        Handler for the accel changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.path.nodeinfo['accel'] = i


    def HandleDelayChanged(self, i):
        """
        Handler for the delay changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.path.nodeinfo['delay'] = i


    def Handleunk1Changed(self, i):
        """
        Handler for the delay changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.path.nodeinfo['unk1'] = i


    def HandleLoopsChanged(self, i):
        if self.UpdateFlag: return
        SetDirty()
        self.path.pathinfo['loops'] = (i == Qt.Checked)
        self.path.pathinfo['peline'].loops = (i == Qt.Checked)
        mainWindow.scene.update()


class ObjectDataEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing object data
    """
    brickContents = ['One Coin',
                     'Ten Coins',
                     'Fire Flower',
                     'Invincibility Star',
                     '1-UP',
                     'Vine',
                     'Mini Mushroom',
                     'Propeller Mushroom',
                     'Penguin Suit',
                     'Yoshi',
                     'Ice Flower',
                     'Acorn Mushroom',
                     ]
    questionContents = ['One Coin',
                        'Fire Flower',
                        'Invincibility Star',
                        'Continuous Star',
                        'Vine',
                        'Spring',
                        'Mini Mushroom',
                        'Propeller Mushroom',
                        'Penguin Suit',
                        'Yoshi',
                        'Ice Flower',
                        'Acorn Mushroom',
                        ]
    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # Create widgets
        self.questionCheck = QtWidgets.QCheckBox('? Block')
        self.questionCheck.stateChanged.connect(self.HandleQuestionCheckboxChanged)

        self.contentsList = QtWidgets.QComboBox()
        self.contentsList.setToolTip('Set the contents of the block')
        self.contentsList.addItems(self.brickContents)
        self.contentsList.currentIndexChanged.connect(self.HandleContentsChanged)

        L = QtWidgets.QFormLayout(self)
        L.addWidget(self.questionCheck)
        L.addRow('Contents:', self.contentsList)

        self.object = None
        self.UpdateFlag = False


    def setObject(self, object):
        """
        Change the object being edited by the editor, update all fields
        """
        # Set object
        if object is self.object:
            return
        elif object.from_ != OBJECT_FROM_MAIN or object.idx != 28:
            return

        self.UpdateFlag = True
        self.object = object
        if object.data == 0:
            object.data = 13 # obj 28 should never have a data value of 0

        # Get and set fields
        value = object.data
        isQuest = value >= 13

        self.questionCheck.setChecked(isQuest)
        self.contentsList.clear()
        self.contentsList.addItems(self.questionContents if isQuest else self.brickContents)
        self.contentsList.setCurrentIndex((value - 1) % 12)

        self.UpdateFlag = False


    def HandleContentsChanged(self, value):
        """
        Handle a contents index change
        """
        if self.UpdateFlag: return
        SetDirty()

        if self.questionCheck.isChecked():
            value += 12
        self.object.data = value + 1

        mainWindow.scene.update()


    def HandleQuestionCheckboxChanged(self, isQuest):
        """
        Handle the user checking or unchecking the "? block" checkbox
        """
        if self.UpdateFlag: return
        SetDirty()

        value = self.contentsList.currentIndex()

        self.contentsList.clear()
        self.contentsList.addItems(self.questionContents if isQuest else self.brickContents)
        self.contentsList.setCurrentIndex(value % 12)

        self.HandleContentsChanged(value % 12)


class IslandGeneratorWidget(QtWidgets.QWidget):
    """
    Widget for editing entrance properties
    """
    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create widgets
        self.wpos = QtWidgets.QSpinBox()
        self.wpos.setRange(1, 65535)
        self.wpos.setToolTip('Width (tiles)')
        self.wpos.setValue(7)

        self.hpos = QtWidgets.QSpinBox()
        self.hpos.setRange(1, 65535)
        self.hpos.setToolTip('Height (tiles)')
        self.hpos.setValue(7)

        self.tileset = QtWidgets.QSpinBox()
        self.tileset.setRange(1, 4)
        self.tileset.setToolTip('Tileset ID')
        self.tileset.setValue(2)

        self.tstl = QtWidgets.QSpinBox()
        self.tstl.setRange(0, 65536)
        self.tstl.setToolTip('Top-left Object ID')
        self.tstl.setValue(5)

        self.tstg = QtWidgets.QSpinBox()
        self.tstg.setRange(0, 65536)
        self.tstg.setToolTip('Top Ground Object ID')
        self.tstg.setValue(0)

        self.tstr = QtWidgets.QSpinBox()
        self.tstr.setRange(0, 65536)
        self.tstr.setToolTip('Top-right Object ID')
        self.tstr.setValue(6)


        self.tsml = QtWidgets.QSpinBox()
        self.tsml.setRange(0, 65536)
        self.tsml.setToolTip('Middle-left Object ID')
        self.tsml.setValue(3)

        self.tsmf = QtWidgets.QSpinBox()
        self.tsmf.setRange(0, 65536)
        self.tsmf.setToolTip('Middle Filler Object ID')
        self.tsmf.setValue(1)

        self.tsmr = QtWidgets.QSpinBox()
        self.tsmr.setRange(0, 65536)
        self.tsmr.setToolTip('Middle-right Object ID')
        self.tsmr.setValue(4)


        self.tsbl = QtWidgets.QSpinBox()
        self.tsbl.setRange(0, 65536)
        self.tsbl.setToolTip('Bottom-left Object ID')
        self.tsbl.setValue(7)

        self.tsbm = QtWidgets.QSpinBox()
        self.tsbm.setRange(0, 65536)
        self.tsbm.setToolTip('Bottom Roof Object ID')
        self.tsbm.setValue(2)

        self.tsbr = QtWidgets.QSpinBox()
        self.tsbr.setRange(0, 65536)
        self.tsbr.setToolTip('Bottom-right Object ID')
        self.tsbr.setValue(8)


        self.midix = QtWidgets.QSpinBox()
        self.midix.setRange(0, 65536)
        self.midix.setValue(0)
        self.midix.setToolTip('Top Ground, Middle Filler and Bottom Roof \'interval\'. Set 0 to disable. The amount of tiles before a new object is created.<br><br>e.g. if you wanted a 2000t long island, the middle can be seperated into 100 20t long objects instead of 1 2000t long object.')

        self.midiy = QtWidgets.QSpinBox()
        self.midiy.setRange(0, 65536)
        self.midiy.setValue(0)
        self.midiy.setToolTip('Middle Left, Middle Filler and Middle Right \'interval\'. Set 0 to disable. The amount of tiles before a new object is created.<br><br>e.g. if you wanted a 2000t tall island, the middle can be seperated into 100 20t tall objects instead of 1 2000t tall object.')


        self.layer = QtWidgets.QSpinBox()
        self.layer.setRange(0, 2)
        self.layer.setToolTip('Layer to paint the island onto')
        self.layer.setValue(1)

        self.copyButton = QtWidgets.QPushButton('Copy to Clipboard')
        self.copyButton.setToolTip('Copies the island you specified here to the clipboard. Paste it anywhere in Satoru. (Ctrl+V)')
        self.copyButton.clicked.connect(self.HandleCopy)

        self.placeButton = QtWidgets.QPushButton('Place')
        self.placeButton.setToolTip('Places the island specified here into Satoru.')
        self.placeButton.clicked.connect(self.HandlePlace)


        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        self.editingLabel = QtWidgets.QLabel('<b>Island Generator</b>')
        layout.addWidget(self.editingLabel, 0, 0, 1, 4, Qt.AlignTop)
        # add labels

        layout.addWidget(QtWidgets.QLabel('Width:'), 1, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel('Height:'), 2, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel('Layer:'), 3, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel('Tileset ID:'), 4, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel('X Interval:'), 5, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel('Y Interval:'), 6, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(createHorzLine(), 7, 0, 1, -1)

        # add the widgets
        layout.addWidget(self.wpos, 1, 1, 1, -1)
        layout.addWidget(self.hpos, 2, 1, 1, -1)
        layout.addWidget(self.layer, 3, 1, 1, -1)
        layout.addWidget(self.tileset, 4, 1, 1, -1)
        layout.addWidget(self.midix, 5, 1, 1, -1)
        layout.addWidget(self.midiy, 6, 1, 1, -1)

        layout.addWidget(self.tstl, 8, 1, 1, 1)
        layout.addWidget(self.tstg, 8, 2, 1, 1)
        layout.addWidget(self.tstr, 8, 3, 1, 1)

        layout.addWidget(self.tsml, 9, 1, 1, 1)
        layout.addWidget(self.tsmf, 9, 2, 1, 1)
        layout.addWidget(self.tsmr, 9, 3, 1, 1)

        layout.addWidget(self.tsbl, 10, 1, 1, 1)
        layout.addWidget(self.tsbm, 10, 2, 1, 1)
        layout.addWidget(self.tsbr, 10, 3, 1, 1)

        layout.addWidget(self.copyButton, 11, 0, 1, 2)
        layout.addWidget(self.placeButton, 11, 3, 1, 2)
        self.UpdateFlag = False

    def GetClipboardString(self):
        midixwas0 = False
        midiywas0 = False
        if self.midix.value() == 0:
            self.midix.setValue(self.wpos.value())
            midixwas0 = True
        if self.midiy.value() == 0:
            self.midiy.setValue(self.hpos.value())
            midiywas0 = True
        ret = ''
        convclip = ['SatoruClip']

        # Paint the top tiles

        # Top-left tip
        convclip.append('0:%d:%d:%d:0:0:1:1' % (self.tileset.value()-1, self.tstl.value(), self.layer.value()))
        # Top Ground
        remnx = self.wpos.value() - 2
        remx = 1
        while True:
            if remnx >= self.midix.value():
                convclip.append('0:%d:%d:%d:%d:0:%d:%d' % (self.tileset.value()-1, self.tstg.value(), self.layer.value(), remx, self.midix.value(), 1))
                remnx -= self.midix.value()
                remx += self.midix.value()
            else:
                convclip.append('0:%d:%d:%d:%d:0:%d:%d' % (self.tileset.value()-1, self.tstg.value(), self.layer.value(), remx, remnx, 1))
                break

        # Top-right tip
        convclip.append('0:%d:%d:%d:%d:0:1:1' % (self.tileset.value()-1, self.tstr.value(), self.layer.value(), self.wpos.value() - 1))

        # Paint the middle tiles

        remny = self.hpos.value() -2
        remy = 1

        # Middle-left edge
        while True:
            if remny >= self.midiy.value():
                convclip.append('0:%d:%d:%d:0:%d:%d:%d' % (self.tileset.value()-1, self.tsml.value(), self.layer.value(), remy ,1, self.midiy.value()))
                remny -= self.midiy.value()
                remy += self.midiy.value()
            else:
                convclip.append('0:%d:%d:%d:0:%d:%d:%d' % (self.tileset.value()-1, self.tsml.value(), self.layer.value(), remy, 1, remny))
                break



        # Middle Filler! Hard
        fullwidt = int(math_floor((self.wpos.value()-2) / self.midix.value()))

        widtremainder = int(math_floor((self.wpos.value()-2) % self.midix.value()))

        fullvert = int(math_floor((self.hpos.value()-2) / self.midiy.value()))
        vertremainder = int(math_floor((self.hpos.value()-2) % self.midiy.value()))



        for x in range(fullwidt):
            for y in range(fullvert):
                convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsmf.value(), self.layer.value(), (x*self.midix.value()) +1, (y*self.midiy.value()) +1 ,self.midix.value(), self.midiy.value()))


        # Now paint the remainders
        if vertremainder:
            remnx = self.wpos.value() - 2 - widtremainder
            remx = 1
            while True:
                if remnx >= self.midix.value():
                    convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsmf.value(), self.layer.value(), remx, self.hpos.value() - 1 - vertremainder , self.midix.value(), vertremainder))
                    remnx -= self.midix.value()
                    remx += self.midix.value()

                else:
                    convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsmf.value(), self.layer.value(), remx, self.hpos.value() - 1 - vertremainder, remnx, vertremainder))
                    break

        if widtremainder > 0:
            remny = self.hpos.value() - 2 - vertremainder
            remy = 1
            while True:
                if remny >= self.midiy.value():
                    convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsmf.value(), self.layer.value(), self.wpos.value() - 1 - widtremainder, remy , widtremainder, self.midiy.value()))
                    remny -= self.midiy.value()
                    remy += self.midiy.value()

                else:
                    convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsmf.value(), self.layer.value(), self.wpos.value() - 1 - widtremainder, remy , widtremainder, remny))
                    break

        if vertremainder and widtremainder:
            convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsmf.value(), self.layer.value(), self.wpos.value() - 1 - widtremainder, self.hpos.value() - 1 - vertremainder , widtremainder, vertremainder))


        # Middle-right edge

        remny = self.hpos.value() -2
        remy = 1
        while True:
            if remny >= self.midiy.value():
                convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsmr.value(), self.layer.value(), self.wpos.value() -1, remy ,1, self.midiy.value()))
                remny -= self.midiy.value()
                remy += self.midiy.value()
            else:
                convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsmr.value(), self.layer.value(), self.wpos.value() -1, remy, 1, remny))
                break


        # Paint the bottom tiles

        # bottom-left tip
        convclip.append('0:%d:%d:%d:0:%d:1:1' % (self.tileset.value()-1, self.tsbl.value(), self.layer.value(), self.hpos.value() -1))
        # Bottom Roof
        remnx = self.wpos.value() - 2
        remx = 1
        while True:
            if remnx >= self.midix.value():
                convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsbm.value(), self.layer.value(), remx, self.hpos.value() -1, self.midix.value(), 1))
                remnx -= self.midix.value()
                remx += self.midix.value()
            else:
                convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (self.tileset.value()-1, self.tsbm.value(), self.layer.value(), remx, self.hpos.value() -1, remnx, 1))
                break

        # Bottom-right tip
        convclip.append('0:%d:%d:%d:%d:%d:1:1' % (self.tileset.value()-1, self.tsbr.value(), self.layer.value(), self.wpos.value() - 1, self.hpos.value() -1))
        convclip.append('%')
        if midixwas0:
            self.midix.setValue(0)
        if midiywas0:
            self.midiy.setValue(0)
        return '|'.join(convclip)


    def HandleCopy(self):
        """
        Makes a copy of the island
        """
        retcb = self.GetClipboardString()
        mainWindow.actions_['paste'].setEnabled(True)
        mainWindow.clipboard = retcb
        mainWindow.systemClipboard.setText(mainWindow.clipboard)



    def HandlePlace(self):
        """
        Places the island directly into the editor
        """
        retcb = self.GetClipboardString()
        mainWindow.placeEncodedObjects(retcb)


class LocationEditorWidget(QtWidgets.QWidget):
    """
    Widget for editing location properties
    """

    def __init__(self, defaultmode=False):
        """
        Constructor
        """
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))

        # create widgets
        self.locationID = QtWidgets.QSpinBox()
        self.locationID.setToolTip(trans.string('LocationDataEditor', 1))
        self.locationID.setRange(0, 255)
        self.locationID.valueChanged.connect(self.HandleLocationIDChanged)

        self.locationX = QtWidgets.QSpinBox()
        self.locationX.setToolTip(trans.string('LocationDataEditor', 3))
        self.locationX.setRange(16, 65535)
        self.locationX.valueChanged.connect(self.HandleLocationXChanged)

        self.locationY = QtWidgets.QSpinBox()
        self.locationY.setToolTip(trans.string('LocationDataEditor', 5))
        self.locationY.setRange(16, 65535)
        self.locationY.valueChanged.connect(self.HandleLocationYChanged)

        self.locationWidth = QtWidgets.QSpinBox()
        self.locationWidth.setToolTip(trans.string('LocationDataEditor', 7))
        self.locationWidth.setRange(1, 65535)
        self.locationWidth.valueChanged.connect(self.HandleLocationWidthChanged)

        self.locationHeight = QtWidgets.QSpinBox()
        self.locationHeight.setToolTip(trans.string('LocationDataEditor', 9))
        self.locationHeight.setRange(1, 65535)
        self.locationHeight.valueChanged.connect(self.HandleLocationHeightChanged)

        self.snapButton = QtWidgets.QPushButton(trans.string('LocationDataEditor', 10))
        self.snapButton.clicked.connect(self.HandleSnapToGrid)

        # create a layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # 'Editing Location #' label
        self.editingLabel = QtWidgets.QLabel('-')
        layout.addWidget(self.editingLabel, 0, 0, 1, 4, Qt.AlignTop)

        # add labels
        layout.addWidget(QtWidgets.QLabel(trans.string('LocationDataEditor', 0)), 1, 0, 1, 1, Qt.AlignRight)

        layout.addWidget(createHorzLine(), 2, 0, 1, 4)

        layout.addWidget(QtWidgets.QLabel(trans.string('LocationDataEditor', 2)), 3, 0, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(trans.string('LocationDataEditor', 4)), 4, 0, 1, 1, Qt.AlignRight)

        layout.addWidget(QtWidgets.QLabel(trans.string('LocationDataEditor', 6)), 3, 2, 1, 1, Qt.AlignRight)
        layout.addWidget(QtWidgets.QLabel(trans.string('LocationDataEditor', 8)), 4, 2, 1, 1, Qt.AlignRight)

        # add the widgets
        layout.addWidget(self.locationID, 1, 1, 1, 1)
        layout.addWidget(self.snapButton, 1, 3, 1, 1)

        layout.addWidget(self.locationX, 3, 1, 1, 1)
        layout.addWidget(self.locationY, 4, 1, 1, 1)

        layout.addWidget(self.locationWidth, 3, 3, 1, 1)
        layout.addWidget(self.locationHeight, 4, 3, 1, 1)


        self.loc = None
        self.UpdateFlag = False


    def setLocation(self, loc):
        """
        Change the location being edited by the editor, update all fields
        """
        self.loc = loc
        self.UpdateFlag = True

        self.FixTitle()
        self.locationID.setValue(loc.id)
        self.locationX.setValue(loc.objx)
        self.locationY.setValue(loc.objy)
        self.locationWidth.setValue(loc.width)
        self.locationHeight.setValue(loc.height)

        self.UpdateFlag = False


    def FixTitle(self):
        self.editingLabel.setText(trans.string('LocationDataEditor', 11, '[id]', self.loc.id))


    def HandleLocationIDChanged(self, i):
        """
        Handler for the location ID changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.id = i
        self.loc.update()
        self.loc.UpdateTitle()
        self.FixTitle()


    def HandleLocationXChanged(self, i):
        """
        Handler for the location X-pos changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.objx = i
        self.loc.autoPosChange = True
        self.loc.setX(int(i * TileWidth / 16))
        self.loc.autoPosChange = False
        self.loc.UpdateRects()
        self.loc.update()


    def HandleLocationYChanged(self, i):
        """
        Handler for the location Y-pos changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.objy = i
        self.loc.autoPosChange = True
        self.loc.setY(int(i * TileWidth / 16))
        self.loc.autoPosChange = False
        self.loc.UpdateRects()
        self.loc.update()


    def HandleLocationWidthChanged(self, i):
        """
        Handler for the location width changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.width = i
        self.loc.UpdateRects()
        self.loc.update()


    def HandleLocationHeightChanged(self, i):
        """
        Handler for the location height changing
        """
        if self.UpdateFlag: return
        SetDirty()
        self.loc.height = i
        self.loc.UpdateRects()
        self.loc.update()


    def HandleSnapToGrid(self):
        """
        Snaps the current location to an 8x8 grid
        """
        SetDirty()

        loc = self.loc
        left = loc.objx
        top = loc.objy
        right = left+loc.width
        bottom = top+loc.height

        if left % 8 < 4:
            left -= (left % 8)
        else:
            left += 8 - (left % 8)

        if top % 8 < 4:
            top -= (top % 8)
        else:
            top += 8 - (top % 8)

        if right % 8 < 4:
            right -= (right % 8)
        else:
            right += 8 - (right % 8)

        if bottom % 8 < 4:
            bottom -= (bottom % 8)
        else:
            bottom += 8 - (bottom % 8)

        if right <= left: right += 8
        if bottom <= top: bottom += 8

        loc.objx = left
        loc.objy = top
        loc.width = right - left
        loc.height = bottom - top

        loc.setPos(int(left * TileWidth / 16), int(top * TileWidth / 16))
        loc.UpdateRects()
        loc.update()
        self.setLocation(loc) # updates the fields


class LoadingTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.unk1 = QtWidgets.QSpinBox()
        self.unk1.setRange(0, 0x255)
        self.unk1.setToolTip(trans.string('AreaDlg', 25))
        self.unk1.setValue(Area.unk1)

        self.unk2 = QtWidgets.QSpinBox()
        self.unk2.setRange(0, 255)
        self.unk2.setToolTip(trans.string('AreaDlg', 25))
        self.unk2.setValue(Area.unk2)

        self.wrap = QtWidgets.QCheckBox(trans.string('AreaDlg', 7))
        self.wrap.setToolTip(trans.string('AreaDlg', 8))
        self.wrap.setChecked((Area.wrapFlag & 1) != 0)

        self.timer = QtWidgets.QSpinBox()
        self.timer.setRange(0, 999)
        self.timer.setToolTip(trans.string('AreaDlg', 4))
        self.timer.setValue(Area.timeLimit + 100)

        self.timelimit2 = QtWidgets.QSpinBox()
        self.timelimit2.setRange(0, 999)
        self.timelimit2.setToolTip(trans.string('AreaDlg', 38))
        self.timelimit2.setValue(Area.timelimit2)

        self.timelimit3 = QtWidgets.QSpinBox()
        self.timelimit3.setRange(0, 999)
        self.timelimit3.setToolTip(trans.string('AreaDlg', 38))
        self.timelimit3.setValue(Area.timelimit3)

        self.unk3 = QtWidgets.QSpinBox()
        self.unk3.setRange(0, 999)
        self.unk3.setToolTip(trans.string('AreaDlg', 26))
        self.unk3.setValue(Area.unk3)

        self.unk4 = QtWidgets.QSpinBox()
        self.unk4.setRange(0, 999)
        self.unk4.setToolTip(trans.string('AreaDlg', 26))
        self.unk4.setValue(Area.unk4)

        self.unk5 = QtWidgets.QSpinBox()
        self.unk5.setRange(0, 999)
        self.unk5.setToolTip(trans.string('AreaDlg', 26))
        self.unk5.setValue(Area.unk5)

        self.unk6 = QtWidgets.QSpinBox()
        self.unk6.setRange(0, 999)
        self.unk6.setToolTip(trans.string('AreaDlg', 26))
        self.unk6.setValue(Area.unk6)

        self.unk7 = QtWidgets.QSpinBox()
        self.unk7.setRange(0, 999)
        self.unk7.setToolTip(trans.string('AreaDlg', 26))
        self.unk7.setValue(Area.unk7)

        settingsLayout = QtWidgets.QFormLayout()
        settingsLayout.addRow(trans.string('AreaDlg', 22), self.unk1)
        settingsLayout.addRow(trans.string('AreaDlg', 23), self.unk2)
        settingsLayout.addRow(trans.string('AreaDlg', 3), self.timer)
        settingsLayout.addRow(trans.string('AreaDlg', 36), self.timelimit2)
        settingsLayout.addRow(trans.string('AreaDlg', 37), self.timelimit3)
        settingsLayout.addRow(trans.string('AreaDlg', 24), self.unk3)
        settingsLayout.addRow(trans.string('AreaDlg', 32), self.unk4)
        settingsLayout.addRow(trans.string('AreaDlg', 33), self.unk5)
        settingsLayout.addRow(trans.string('AreaDlg', 34), self.unk6)
        settingsLayout.addRow(trans.string('AreaDlg', 35), self.unk7)
        settingsLayout.addRow(self.wrap)

        Layout = QtWidgets.QVBoxLayout()
        Layout.addLayout(settingsLayout)
        Layout.addStretch(1)
        self.setLayout(Layout)


class LevelViewWidget(QtWidgets.QGraphicsView):
    """
    QGraphicsView subclass for the level view
    """
    PositionHover = QtCore.pyqtSignal(int, int)
    FrameSize = QtCore.pyqtSignal(int, int)
    repaint = QtCore.pyqtSignal()
    dragstamp = False

    def __init__(self, scene, parent):
        """
        Constructor
        """
        super().__init__(scene, parent)

        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        #self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(119,136,153)))
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        #self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setMouseTracking(True)
        #self.setOptimizationFlags(QtWidgets.QGraphicsView.IndirectPainting)
        self.YScrollBar = QtWidgets.QScrollBar(Qt.Vertical, parent)
        self.XScrollBar = QtWidgets.QScrollBar(Qt.Horizontal, parent)
        self.setVerticalScrollBar(self.YScrollBar)
        self.setHorizontalScrollBar(self.XScrollBar)

        self.currentobj = None

        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)


    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed
        """
        if event.button() == Qt.RightButton:
            if CurrentPaintType in (0, 1, 2) and CurrentObject != -1:
                # paint an object
                clicked = mainWindow.view.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)
                clickedx = int(clicked.x() / TileWidth)
                clickedy = int(clicked.y() / TileWidth)

                ln = CurrentLayer
                layer = Area.layers[CurrentLayer]
                if len(layer) == 0:
                    z = (2 - ln) * 8192
                else:
                    z = layer[-1].zValue() + 1

                if CurrentPaintType == 0 and isinstance(CurrentObject, int) and CurrentObject >= len(MainObjects): return
                if CurrentPaintType == 1 and CurrentObject not in OneTilesetObjects: return
                if CurrentPaintType == 2 and isinstance(CurrentObject, int) and CurrentObject >= len(EmbeddedObjects): return
                obj = ObjectItem(CurrentPaintType + 1, CurrentObject, ln, clickedx, clickedy, 1, 1, z, 0)
                layer.append(obj)
                mw = mainWindow
                obj.positionChanged = mw.HandleObjPosChange
                mw.scene.addItem(obj)

                self.dragstamp = False
                self.currentobj = obj
                self.dragstartx = clickedx
                self.dragstarty = clickedy
                mw.updateTileCountLabel()
                SetDirty()

            elif CurrentPaintType == 3:
                raise NotImplementedError('Paint type 3 is no longer in use.')

            elif CurrentPaintType == 4 and CurrentSprite != -1:
                # paint a sprite
                clicked = mainWindow.view.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)

                if CurrentSprite >= 0: # fixes a bug -Treeki
                    #[18:15:36]  Angel-SL: I found a bug in Reggie
                    #[18:15:42]  Angel-SL: you can paint a 'No sprites found'
                    #[18:15:47]  Angel-SL: results in a sprite -2

                    # paint a sprite
                    clickedx = int(clicked.x() // TileWidth) * 16
                    clickedy = int(clicked.y() // TileWidth) * 16

                    data = mainWindow.defaultDataEditor.data
                    spr = SpriteItem(CurrentSprite, clickedx, clickedy, data)

                    mw = mainWindow
                    spr.positionChanged = mw.HandleSprPosChange
                    mw.scene.addItem(spr)

                    spr.listitem = ListWidgetItem_SortsByOther(spr)
                    mw.spriteList.addItem(spr.listitem)
                    Area.sprites.append(spr)

                    self.dragstamp = False
                    self.currentobj = spr
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy

                    self.scene().update()

                    spr.UpdateListItem()

                SetDirty()

            elif CurrentPaintType == 5:
                # paint an entrance
                clicked = mainWindow.view.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)
                clickedx = int((clicked.x() - 12) / TileWidth * 16)
                clickedy = int((clicked.y() - 12) / TileWidth * 16)

                getids = [False for x in range(256)]
                for ent in Area.entrances: getids[ent.entid] = True
                minimumID = getids.index(False)

                ent = EntranceItem(clickedx, clickedy, 0, minimumID, 0, 0, 0, 0, 0, 0, 0x80, 0, 0, 0, 0, 0)
                mw = mainWindow
                ent.positionChanged = mw.HandleEntPosChange
                mw.scene.addItem(ent)

                elist = mw.entranceList
                # if it's the first available ID, all the other indexes should match right?
                # so I can just use the ID to insert
                ent.listitem = ListWidgetItem_SortsByOther(ent)
                elist.insertItem(minimumID, ent.listitem)

                global PaintingEntrance, PaintingEntranceListIndex
                PaintingEntrance = ent
                PaintingEntranceListIndex = minimumID

                Area.entrances.insert(minimumID, ent)

                self.dragstamp = False
                self.currentobj = ent
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                ent.UpdateListItem()

                SetDirty()
            elif CurrentPaintType == 6:
                # paint a path node
                clicked = mainWindow.view.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)
                clickedx = int((clicked.x() - 12) / TileWidth * 16)
                clickedy = int((clicked.y() - 12) / TileWidth * 16)
                mw = mainWindow
                plist = mw.pathList
                selectedpn = None if not plist.selectedItems() else plist.selectedItems()[0]

                if selectedpn is None:
                    getids = [False for x in range(256)]
                    getids[0] = True
                    for pathdatax in Area.pathdata:
                        #if(len(pathdatax['nodes']) > 0):
                        getids[int(pathdatax['id'])] = True
                    newpathid = getids.index(False)

                    newpathdata = {'id': newpathid,
                                   'unk1': 0,
                                   'nodes': [{'x': clickedx, 'y': clickedy, 'speed': 0.5, 'accel': 0.00498, 'delay': 0}],
                                   'loops': False
                    }
                    Area.pathdata.append(newpathdata)
                    newnode = PathItem(clickedx, clickedy, newpathdata, newpathdata['nodes'][0], 0, 0, 0, 0)
                    newnode.positionChanged = mw.HandlePathPosChange

                    mw.scene.addItem(newnode)

                    peline = PathEditorLineItem(newpathdata['nodes'])
                    newpathdata['peline'] = peline
                    mw.scene.addItem(peline)

                    Area.pathdata.sort(key=lambda path: int(path['id']))

                    newnode.listitem = ListWidgetItem_SortsByOther(newnode)
                    plist.clear()
                    for fpath in Area.pathdata:
                        for fpnode in fpath['nodes']:
                            fpnode['graphicsitem'].listitem = ListWidgetItem_SortsByOther(fpnode['graphicsitem'], fpnode['graphicsitem'].ListString())
                            plist.addItem(fpnode['graphicsitem'].listitem)
                            fpnode['graphicsitem'].updateId()
                    newnode.listitem.setSelected(True)
                    Area.paths.append(newnode)

                    self.dragstamp = False
                    self.currentobj = newnode
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy

                    newnode.UpdateListItem()

                    SetDirty()
                else:
                    pathd = None
                    for pathnode in Area.paths:
                        if pathnode.listitem == selectedpn:
                            selectedpnobj = pathnode
                            pathd = pathnode.pathinfo
                            nodeid = pathnode.nodeid + 1

                    if not pathd: return # shouldn't happen

                    pathid = pathd['id']
                    newnodedata = {'x': clickedx, 'y': clickedy, 'speed': 0.5, 'accel': 0.00498, 'delay': 0}
                    pathd['nodes'].insert(nodeid, newnodedata)

                    newnode = PathItem(clickedx, clickedy, pathd, newnodedata, 0, 0, 0, 0)

                    newnode.positionChanged = mw.HandlePathPosChange
                    mw.scene.addItem(newnode)

                    newnode.listitem = ListWidgetItem_SortsByOther(newnode)
                    plist.clear()
                    for fpath in Area.pathdata:
                        for fpnode in fpath['nodes']:
                            fpnode['graphicsitem'].listitem = ListWidgetItem_SortsByOther(fpnode['graphicsitem'], fpnode['graphicsitem'].ListString())
                            plist.addItem(fpnode['graphicsitem'].listitem)
                            fpnode['graphicsitem'].updateId()

                    selectedpnobj.setSelected(False)
                    newnode.setSelected(True)
                    newnode.listitem.setSelected(True)

                    Area.paths.append(newnode)
                    pathd['peline'].nodePosChanged()
                    self.dragstamp = False
                    self.currentobj = newnode
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy

                    newnode.UpdateListItem()

                    SetDirty()

            elif CurrentPaintType == 7:
                # paint a location
                clicked = mainWindow.view.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)

                clickedx = int(clicked.x() / TileWidth * 16)
                clickedy = int(clicked.y() / TileWidth * 16)

                allID = set() # faster 'x in y' lookups for sets
                newID = 1
                for i in Area.locations:
                    allID.add(i.id)

                while newID <= 255:
                    if newID not in allID:
                        break
                    newID += 1

                global OverrideSnapping
                OverrideSnapping = True
                loc = LocationItem(clickedx, clickedy, 4, 4, newID)
                OverrideSnapping = False

                mw = mainWindow
                loc.positionChanged = mw.HandleLocPosChange
                loc.sizeChanged = mw.HandleLocSizeChange
                loc.listitem = ListWidgetItem_SortsByOther(loc)
                mw.locationList.addItem(loc.listitem)
                mw.scene.addItem(loc)

                Area.locations.append(loc)

                self.dragstamp = False
                self.currentobj = loc
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                loc.UpdateListItem()

                SetDirty()

            elif CurrentPaintType == 8:
                # paint a stamp
                clicked = mainWindow.view.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)

                clickedx = int(clicked.x() / TileWidth * 16)
                clickedy = int(clicked.y() / TileWidth * 16)

                stamp = mainWindow.stampChooser.currentlySelectedStamp()
                if stamp is not None:
                    objs = mainWindow.placeEncodedObjects(stamp.SatoruClip, False, clickedx, clickedy)

                    for obj in objs:
                        obj.dragstartx = obj.objx
                        obj.dragstarty = obj.objy
                        obj.update()

                    mainWindow.scene.update()

                    self.dragstamp = True
                    self.dragstartx = clickedx
                    self.dragstarty = clickedy
                    self.currentobj = objs

                    SetDirty()

            elif CurrentPaintType == 9:
                # paint a comment

                clicked = mainWindow.view.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)
                clickedx = int((clicked.x() - TileWidth / 2) / TileWidth * 16)
                clickedy = int((clicked.y() - TileWidth / 2) / TileWidth * 16)

                com = CommentItem(clickedx, clickedy, '')
                mw = mainWindow
                com.positionChanged = mw.HandleComPosChange
                com.textChanged = mw.HandleComTxtChange
                mw.scene.addItem(com)
                com.setVisible(CommentsShown)

                clist = mw.commentList
                com.listitem = QtWidgets.QListWidgetItem()
                clist.addItem(com.listitem)

                Area.comments.append(com)

                self.dragstamp = False
                self.currentobj = com
                self.dragstartx = clickedx
                self.dragstarty = clickedy

                mainWindow.SaveComments()

                com.UpdateListItem()

                SetDirty()
            event.accept()
        elif (event.button() == Qt.LeftButton) and (QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier):
            mw = mainWindow

            pos = mw.view.mapToScene(event.x(), event.y())
            addsel = mw.scene.items(pos)
            for i in addsel:
                if (int(i.flags()) & i.ItemIsSelectable) != 0:
                    i.setSelected(not i.isSelected())
                    break

        else:
            QtWidgets.QGraphicsView.mousePressEvent(self, event)
        mainWindow.levelOverview.update()


    def resizeEvent(self, event):
        """
        Catches resize events
        """
        self.FrameSize.emit(event.size().width(), event.size().height())
        event.accept()
        QtWidgets.QGraphicsView.resizeEvent(self, event)


    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed
        """

        pos = mainWindow.view.mapToScene(event.x(), event.y())
        if pos.x() < 0: pos.setX(0)
        if pos.y() < 0: pos.setY(0)
        self.PositionHover.emit(int(pos.x()), int(pos.y()))

        if event.buttons() == Qt.RightButton and self.currentobj is not None and not self.dragstamp:

            # possibly a small optimization
            type_obj = ObjectItem
            type_spr = SpriteItem
            type_ent = EntranceItem
            type_loc = LocationItem
            type_path = PathItem
            type_com = CommentItem

            # iterate through the objects if there's more than one
            if isinstance(self.currentobj, list) or isinstance(self.currentobj, tuple):
                objlist = self.currentobj
            else:
                objlist = (self.currentobj,)

            for obj in objlist:

                if isinstance(obj, type_obj):
                    # resize/move the current object
                    cx = obj.objx
                    cy = obj.objy
                    cwidth = obj.width
                    cheight = obj.height

                    dsx = self.dragstartx
                    dsy = self.dragstarty
                    clicked = mainWindow.view.mapToScene(event.x(), event.y())
                    if clicked.x() < 0: clicked.setX(0)
                    if clicked.y() < 0: clicked.setY(0)
                    clickx = int(clicked.x() / TileWidth)
                    clicky = int(clicked.y() / TileWidth)

                    # allow negative width/height and treat it properly :D
                    if clickx >= dsx:
                        x = dsx
                        width = clickx - dsx + 1
                    else:
                        x = clickx
                        width = dsx - clickx + 1

                    if clicky >= dsy:
                        y = dsy
                        height = clicky - dsy + 1
                    else:
                        y = clicky
                        height = dsy - clicky + 1

                    # if the position changed, set the new one
                    if cx != x or cy != y:
                        obj.objx = x
                        obj.objy = y
                        obj.setPos(x * TileWidth, y * TileWidth)

                    # if the size changed, recache it and update the area
                    if cwidth != width or cheight != height:
                        obj.width = width
                        obj.height = height
                        obj.updateObjCache()

                        oldrect = obj.BoundingRect
                        oldrect.translate(cx * TileWidth, cy * TileWidth)
                        newrect = QtCore.QRectF(obj.x(), obj.y(), obj.width * TileWidth, obj.height * TileWidth)
                        updaterect = oldrect.united(newrect)

                        obj.UpdateRects()
                        obj.scene().update(updaterect)

                elif isinstance(obj, type_loc):
                    # resize/move the current location
                    cx = obj.objx
                    cy = obj.objy
                    cwidth = obj.width
                    cheight = obj.height

                    dsx = self.dragstartx
                    dsy = self.dragstarty
                    clicked = mainWindow.view.mapToScene(event.x(), event.y())
                    if clicked.x() < 0: clicked.setX(0)
                    if clicked.y() < 0: clicked.setY(0)
                    clickx = int(clicked.x() / TileWidth * 16)
                    clicky = int(clicked.y() / TileWidth * 16)

                    # allow negative width/height and treat it properly :D
                    if clickx >= dsx:
                        x = dsx
                        width = clickx - dsx + 1
                    else:
                        x = clickx
                        width = dsx - clickx + 1

                    if clicky >= dsy:
                        y = dsy
                        height = clicky - dsy + 1
                    else:
                        y = clicky
                        height = dsy - clicky + 1

                    # if the position changed, set the new one
                    if cx != x or cy != y:
                        obj.objx = x
                        obj.objy = y

                        global OverrideSnapping
                        OverrideSnapping = True
                        obj.setPos(x * TileWidth / 16, y * TileWidth / 16)
                        OverrideSnapping = False

                    # if the size changed, recache it and update the area
                    if cwidth != width or cheight != height:
                        obj.width = width
                        obj.height = height
                        # obj.updateObjCache()

                        oldrect = obj.BoundingRect
                        oldrect.translate(cx * TileWidth / 16, cy * TileWidth / 16)
                        newrect = QtCore.QRectF(obj.x(), obj.y(), obj.width * TileWidth / 16, obj.height * TileWidth / 16)
                        updaterect = oldrect.united(newrect)

                        obj.UpdateRects()
                        obj.scene().update(updaterect)


                elif isinstance(obj, type_spr):
                    # move the created sprite
                    clicked = mainWindow.view.mapToScene(event.x(), event.y())
                    if clicked.x() < 0: clicked.setX(0)
                    if clicked.y() < 0: clicked.setY(0)
                    clickedx = int((clicked.x() - TileWidth / 2) / TileWidth * 16)
                    clickedy = int((clicked.y() - TileWidth / 2) / TileWidth * 16)

                    if obj.objx != clickedx or obj.objy != clickedy:
                        obj.objx = clickedx
                        obj.objy = clickedy
                        obj.setPos(int((clickedx+obj.ImageObj.xOffset) * TileWidth / 16), int((clickedy+obj.ImageObj.yOffset) * TileWidth / 16))

                elif isinstance(obj, type_ent) or isinstance(obj, type_path) or isinstance(obj, type_com):
                    # move the created entrance/path/comment
                    clicked = mainWindow.view.mapToScene(event.x(), event.y())
                    if clicked.x() < 0: clicked.setX(0)
                    if clicked.y() < 0: clicked.setY(0)
                    clickedx = int((clicked.x() - TileWidth / 2) / TileWidth * 16)
                    clickedy = int((clicked.y() - TileWidth / 2) / TileWidth * 16)

                    if obj.objx != clickedx or obj.objy != clickedy:
                        obj.objx = clickedx
                        obj.objy = clickedy
                        obj.setPos(int(clickedx * TileWidth / 16), int(clickedy * TileWidth / 16))
            event.accept()

        elif event.buttons() == Qt.RightButton and self.currentobj is not None and self.dragstamp:
            # The user is dragging a stamp - many objects.

            # possibly a small optimization
            type_obj = ObjectItem
            type_spr = SpriteItem

            # iterate through the objects if there's more than one
            if isinstance(self.currentobj, list) or isinstance(self.currentobj, tuple):
                objlist = self.currentobj
            else:
                objlist = (self.currentobj,)

            for obj in objlist:

                clicked = mainWindow.view.mapToScene(event.x(), event.y())
                if clicked.x() < 0: clicked.setX(0)
                if clicked.y() < 0: clicked.setY(0)

                changex = clicked.x() - (self.dragstartx * TileWidth / 16)
                changey = clicked.y() - (self.dragstarty * TileWidth / 16)
                changexobj = int(changex / TileWidth)
                changeyobj = int(changey / TileWidth)
                changexspr = changex * 2/3
                changeyspr = changey * 2/3

                if isinstance(obj, type_obj):
                    # move the current object
                    newx = int(obj.dragstartx + changexobj)
                    newy = int(obj.dragstarty + changeyobj)

                    if obj.objx != newx or obj.objy != newy:

                        obj.objx = newx
                        obj.objy = newy
                        obj.setPos(newx * TileWidth, newy * TileWidth)

                elif isinstance(obj, type_spr):
                    # move the created sprite

                    newx = int(obj.dragstartx + changexspr)
                    newy = int(obj.dragstarty + changeyspr)

                    if obj.objx != newx or obj.objy != newy:
                        obj.objx = newx
                        obj.objy = newy
                        obj.setPos(int((newx + obj.ImageObj.xOffset) * TileWidth / 16), int((newy + obj.ImageObj.yOffset) * TileWidth / 16))

            self.scene().update()

        else:
            QtWidgets.QGraphicsView.mouseMoveEvent(self, event)


    def mouseReleaseEvent(self, event):
        """
        Overrides mouse release events if needed
        """
        if event.button() == Qt.RightButton:
            self.currentobj = None
            event.accept()
        else:
            QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)


    def paintEvent(self, e):
        """
        Handles paint events and fires a signal
        """
        self.repaint.emit()
        QtWidgets.QGraphicsView.paintEvent(self, e)


    def drawForeground(self, painter, rect):
        """
        Draws a foreground grid
        """
        if GridType is None: return
        global theme

        Zoom = mainWindow.ZoomLevel
        drawLine = painter.drawLine
        GridColor = theme.color('grid')

        if GridType == 'grid': # draw a classic grid
            startx = rect.x()
            startx -= (startx % TileWidth)
            endx = startx + rect.width() + TileWidth

            starty = rect.y()
            starty -= (starty % TileWidth)
            endy = starty + rect.height() + TileWidth

            x = startx - TileWidth
            while x <= endx:
                x += TileWidth
                if x % (TileWidth * 8) == 0:
                    painter.setPen(QtGui.QPen(GridColor, 2 * TileWidth / 24, Qt.DashLine))
                    drawLine(x, starty, x, endy)
                elif x % (TileWidth * 4) == 0:
                    if Zoom < 25: continue
                    painter.setPen(QtGui.QPen(GridColor, 1 * TileWidth / 24, Qt.DashLine))
                    drawLine(x, starty, x, endy)
                else:
                    if Zoom < 50: continue
                    painter.setPen(QtGui.QPen(GridColor, 1 * TileWidth / 24, Qt.DotLine))
                    drawLine(x, starty, x, endy)

            y = starty - TileWidth
            while y <= endy:
                y += TileWidth
                if y % (TileWidth * 8) == 0:
                    painter.setPen(QtGui.QPen(GridColor, 2 * TileWidth / 24, Qt.DashLine))
                    drawLine(startx, y, endx, y)
                elif y % (TileWidth * 4) == 0 and Zoom >= 25:
                    painter.setPen(QtGui.QPen(GridColor, 1 * TileWidth / 24, Qt.DashLine))
                    drawLine(startx, y, endx, y)
                elif Zoom >= 50:
                    painter.setPen(QtGui.QPen(GridColor, 1 * TileWidth / 24, Qt.DotLine))
                    drawLine(startx, y, endx, y)

        else: # draw a checkerboard
            L = 0.2
            D = 0.1     # Change these values to change the checkerboard opacity

            Light = QtGui.QColor(GridColor)
            Dark = QtGui.QColor(GridColor)
            Light.setAlpha(Light.alpha()*L)
            Dark.setAlpha(Dark.alpha()*D)

            size = TileWidth if Zoom >= 50 else TileWidth * 8

            board = QtGui.QPixmap(8*size, 8*size)
            board.fill(QtGui.QColor(0,0,0,0))
            p = QtGui.QPainter(board)
            p.setPen(Qt.NoPen)

            p.setBrush(QtGui.QBrush(Light))
            for x, y in ((0, size), (size, 0)):
                p.drawRect(x+(4*size), y,          size, size)
                p.drawRect(x+(4*size), y+(2*size), size, size)
                p.drawRect(x+(6*size), y,          size, size)
                p.drawRect(x+(6*size), y+(2*size), size, size)

                p.drawRect(x,          y+(4*size), size, size)
                p.drawRect(x,          y+(6*size), size, size)
                p.drawRect(x+(2*size), y+(4*size), size, size)
                p.drawRect(x+(2*size), y+(6*size), size, size)
            p.setBrush(QtGui.QBrush(Dark))
            for x, y in ((0, 0), (size, size)):
                p.drawRect(x,          y,          size, size)
                p.drawRect(x,          y+(2*size), size, size)
                p.drawRect(x+(2*size), y,          size, size)
                p.drawRect(x+(2*size), y+(2*size), size, size)

                p.drawRect(x,          y+(4*size), size, size)
                p.drawRect(x,          y+(6*size), size, size)
                p.drawRect(x+(2*size), y+(4*size), size, size)
                p.drawRect(x+(2*size), y+(6*size), size, size)

                p.drawRect(x+(4*size), y,          size, size)
                p.drawRect(x+(4*size), y+(2*size), size, size)
                p.drawRect(x+(6*size), y,          size, size)
                p.drawRect(x+(6*size), y+(2*size), size, size)

                p.drawRect(x+(4*size), y+(4*size), size, size)
                p.drawRect(x+(4*size), y+(6*size), size, size)
                p.drawRect(x+(6*size), y+(4*size), size, size)
                p.drawRect(x+(6*size), y+(6*size), size, size)


            del p

            painter.drawTiledPixmap(rect, board, QtCore.QPointF(rect.x(), rect.y()))


class InfoPreviewWidget(QtWidgets.QWidget):
    """
    Widget that shows a preview of the level metadata info - available in vertical & horizontal flavors
    """
    def __init__(self, direction):
        """
        Creates and initializes the widget
        """
        super().__init__()
        self.direction = direction

        self.Label1 = QtWidgets.QLabel('')
        if self.direction == Qt.Horizontal: self.Label2 = QtWidgets.QLabel('')
        self.updateLabels()

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.Label1)
        if self.direction == Qt.Horizontal: self.mainLayout.addWidget(self.Label2)
        self.setLayout(self.mainLayout)

        if self.direction == Qt.Horizontal: self.setMinimumWidth(256)

    def updateLabels(self):
        """
        Updates the widget labels
        """
        if ('Area' not in globals()) or not hasattr(Area, 'filename'): # can't get level metadata if there's no level
            self.Label1.setText('')
            if self.direction == Qt.Horizontal: self.Label2.setText('')
            return

        a = [ # MUST be a list, not a tuple
            mainWindow.fileTitle,
            Area.Title,
            trans.string('InfoDlg', 8, '[name]', Area.Creator),
            trans.string('InfoDlg', 5) + ' ' + Area.Author,
            trans.string('InfoDlg', 6) + ' ' + Area.Group,
            trans.string('InfoDlg', 7) + ' ' + Area.Webpage,
            ]

        for b, section in enumerate(a): # cut off excessively long strings
            if self.direction == Qt.Vertical: short = clipStr(section, 128)
            else: short = clipStr(section, 184)
            if short is not None: a[b] = short + '...'

        if self.direction == Qt.Vertical:
            str1 = a[0]+'<br>'+a[1]+'<br>'+a[2]+'<br>'+a[3]+'<br>'+a[4]+'<br>'+a[5]
            self.Label1.setText(str1)
        else:
            str1 = a[0]+'<br>'+a[1]+'<br>'+a[2]
            str2 = a[3]+'<br>'+a[4]+'<br>'+a[5]
            self.Label1.setText(str1)
            self.Label2.setText(str2)

        self.update()


class ZoomWidget(QtWidgets.QWidget):
    """
    Widget that allows easy zoom level control
    """
    def __init__(self):
        """
        Creates and initializes the widget
        """
        super().__init__()
        maxwidth = 512-128
        maxheight = 20

        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.minLabel = QtWidgets.QPushButton()
        self.minusLabel = QtWidgets.QPushButton()
        self.plusLabel = QtWidgets.QPushButton()
        self.maxLabel = QtWidgets.QPushButton()

        self.slider.setMaximumHeight(maxheight)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(mainWindow.ZoomLevels)-1)
        self.slider.setTickInterval(2)
        self.slider.setTickPosition(self.slider.TicksAbove)
        self.slider.setPageStep(1)
        self.slider.setTracking(True)
        self.slider.setSliderPosition(self.findIndexOfLevel(100))
        self.slider.valueChanged.connect(self.sliderMoved)

        self.minLabel.setIcon(GetIcon('zoommin'))
        self.minusLabel.setIcon(GetIcon('zoomout'))
        self.plusLabel.setIcon(GetIcon('zoomin'))
        self.maxLabel.setIcon(GetIcon('zoommax'))
        self.minLabel.setFlat(True)
        self.minusLabel.setFlat(True)
        self.plusLabel.setFlat(True)
        self.maxLabel.setFlat(True)
        self.minLabel.clicked.connect(mainWindow.HandleZoomMin)
        self.minusLabel.clicked.connect(mainWindow.HandleZoomOut)
        self.plusLabel.clicked.connect(mainWindow.HandleZoomIn)
        self.maxLabel.clicked.connect(mainWindow.HandleZoomMax)

        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.minLabel,   0, 0)
        self.layout.addWidget(self.minusLabel, 0, 1)
        self.layout.addWidget(self.slider,     0, 2)
        self.layout.addWidget(self.plusLabel,  0, 3)
        self.layout.addWidget(self.maxLabel,   0, 4)
        self.layout.setVerticalSpacing(0)
        self.layout.setHorizontalSpacing(0)
        self.layout.setContentsMargins(0,0,4,0)

        self.setLayout(self.layout)
        self.setMinimumWidth(maxwidth)
        self.setMaximumWidth(maxwidth)
        self.setMaximumHeight(maxheight)

    def sliderMoved(self):
        """
        Handle the slider being moved
        """
        mainWindow.ZoomTo(mainWindow.ZoomLevels[self.slider.value()])

    def setZoomLevel(self, newLevel):
        """
        Moves the slider to the zoom level given
        """
        self.slider.setSliderPosition(self.findIndexOfLevel(newLevel))

    def findIndexOfLevel(self, level):
        for i, mainlevel in enumerate(mainWindow.ZoomLevels):
            if float(mainlevel) == float(level): return i


class ZoomStatusWidget(QtWidgets.QWidget):
    """
    Shows the current zoom level, in percent
    """
    def __init__(self):
        """
        Creates and initializes the widget
        """
        super().__init__()
        self.label = QtWidgets.QPushButton('100%')
        self.label.setFlat(True)
        self.label.clicked.connect(mainWindow.HandleZoomActual)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(4,0,8,0)
        self.setMaximumWidth(56)

        self.setLayout(self.layout)

    def setZoomLevel(self, zoomLevel):
        """
        Updates the widget
        """
        if float(int(zoomLevel)) == float(zoomLevel):
            self.label.setText(str(int(zoomLevel))+'%')
        else:
            self.label.setText(str(float(zoomLevel))+'%')


class ListWidgetWithToolTipSignal(QtWidgets.QListWidget):
    """
    A QtWidgets.QListWidget that includes a signal that
    is emitted when a tooltip is about to be shown. Useful
    for making tooltips that update every time you show
    them.
    """
    toolTipAboutToShow = QtCore.pyqtSignal(QtWidgets.QListWidgetItem)

    def viewportEvent(self, e):
        """
        Handles viewport events
        """
        if e.type() == e.ToolTip:
            self.toolTipAboutToShow.emit(self.itemFromIndex(self.indexAt(e.pos())))

        return super().viewportEvent(e)


class ListWidgetItem_SortsByOther(QtWidgets.QListWidgetItem):
    """
    A ListWidgetItem that defers sorting to another object.
    """
    def __init__(self, reference, text=''):
        super().__init__(text)
        self.reference = reference
    def __lt__(self, other):
        return self.reference < other.reference


#####################################################################
############################## DIALOGS ##############################
#####################################################################

class InputBox(QtWidgets.QDialog):
    Type_TextBox = 1
    Type_SpinBox = 2
    Type_HexSpinBox = 3

    def __init__(self, type=Type_TextBox):
        super().__init__()

        self.label = QtWidgets.QLabel('-')
        self.label.setWordWrap(True)

        if type == InputBox.Type_TextBox:
            self.textbox = QtWidgets.QLineEdit()
            widget = self.textbox
        elif type == InputBox.Type_SpinBox:
            self.spinbox = QtWidgets.QSpinBox()
            widget = self.spinbox
        elif type == InputBox.Type_HexSpinBox:
            self.spinbox = HexSpinBox()
            widget = self.spinbox

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(widget)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)


class AboutDialog(QtWidgets.QDialog):
    """
    Shows the About info for Satoru
    """
    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('AboutDlg', 0))
        self.setWindowIcon(GetIcon('satoru'))

        # Set the palette to the default
        # defaultPalette is a global
        self.setPalette(QtGui.QPalette(defaultPalette))

        # Open the readme file
        f = open('readme.md', 'r')
        readme = f.read()
        f.close()
        del f

        # Logo
        logo = QtGui.QPixmap('satorudata/about.png')
        logoLabel = QtWidgets.QLabel()
        logoLabel.setPixmap(logo)
        logoLabel.setContentsMargins(16, 4, 32, 4)

        # Description
        description =  '<html><head><style type=\'text/CSS\'>'
        description += 'body {font-family: Calibri}'
        description += '.main {font-size: 12px}'
        description += '</style></head><body>'
        description += '<center><h1><i>Satoru</i> Level Editor</h1><div class=\'main\'>'
        description += '<i>Satoru Level Editor</i> is an open-source global project started by Treeki in 2010 that aims to bring you the fun of designing original New Super Mario Bros. Wii&trade;-compatible levels.<br>'
        description += 'Interested? Check out <a href=\'http://rvlution.net/satoru\'>rvlution.net/satoru</a> for updates and related downloads, or <a href=\'http://rvlution.net/forums\'>rvlution.net/forums</a> to get in touch with the developers.<br>'
        description += '</div></center></body></html>'

        # Description label
        descLabel = QtWidgets.QLabel()
        descLabel.setText(description)
        descLabel.setMinimumWidth(512)
        descLabel.setWordWrap(True)

        # Readme.md viewer
        readmeView = QtWidgets.QPlainTextEdit()
        readmeView.setPlainText(readme)
        readmeView.setReadOnly(True)

        # Buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)

        # Main layout
        L = QtWidgets.QGridLayout()
        L.addWidget(logoLabel, 0, 0, 2, 1)
        L.addWidget(descLabel, 0, 1)
        L.addWidget(readmeView, 1, 1)
        L.addWidget(buttonBox, 2, 0, 1, 2)
        L.setRowStretch(1, 1)
        L.setColumnStretch(1, 1)
        self.setLayout(L)


class ObjectShiftDialog(QtWidgets.QDialog):
    """
    Lets you pick an amount to shift selected items by
    """
    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('ShftItmDlg', 0))
        self.setWindowIcon(GetIcon('move'))

        self.XOffset = QtWidgets.QSpinBox()
        self.XOffset.setRange(-16384, 16383)

        self.YOffset = QtWidgets.QSpinBox()
        self.YOffset.setRange(-8192, 8191)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        moveLayout = QtWidgets.QFormLayout()
        offsetlabel = QtWidgets.QLabel(trans.string('ShftItmDlg', 2))
        offsetlabel.setWordWrap(True)
        moveLayout.addWidget(offsetlabel)
        moveLayout.addRow(trans.string('ShftItmDlg', 3), self.XOffset)
        moveLayout.addRow(trans.string('ShftItmDlg', 4), self.YOffset)

        moveGroupBox = QtWidgets.QGroupBox(trans.string('ShftItmDlg', 1))
        moveGroupBox.setLayout(moveLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(moveGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class ObjectTilesetSwapDialog(QtWidgets.QDialog):
    """
    Lets you pick tilesets to swap objects to
    """
    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle('Swap Objects\' Tilesets')
        self.setWindowIcon(GetIcon('swap'))

        # Create widgets
        self.FromTS = QtWidgets.QSpinBox()
        self.FromTS.setRange(1, 4)

        self.ToTS = QtWidgets.QSpinBox()
        self.ToTS.setRange(1, 4)


        # Swap layouts
        swapLayout = QtWidgets.QFormLayout()

        swapLayout.addRow('From tileset:', self.FromTS)
        swapLayout.addRow('To tileset:', self.ToTS)

        self.DoExchange = QtWidgets.QCheckBox('Exchange (perform 2-way conversion)')


        # Buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)


        # Main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(swapLayout)
        mainLayout.addWidget(self.DoExchange)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class ObjectTypeSwapDialog(QtWidgets.QDialog):
    """
    Lets you pick object types to swap objects to
    """
    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle("Swap Objects' Types")
        self.setWindowIcon(GetIcon('swap'))


        # Create widgets
        self.FromType = QtWidgets.QSpinBox()
        self.FromType.setRange(0, 255)

        self.ToType = QtWidgets.QSpinBox()
        self.ToType.setRange(0, 255)

        self.FromTileset = QtWidgets.QSpinBox()
        self.FromTileset.setRange(1, 4)

        self.ToTileset = QtWidgets.QSpinBox()
        self.ToTileset.setRange(1, 4)

        self.DoExchange = QtWidgets.QCheckBox('Exchange (perform 2-way conversion)')


        # Swap layout
        swapLayout = QtWidgets.QGridLayout()

        swapLayout.addWidget(QtWidgets.QLabel('From tile type:'), 0, 0)
        swapLayout.addWidget(self.FromType, 0, 1)

        swapLayout.addWidget(QtWidgets.QLabel('From tileset:'), 1, 0)
        swapLayout.addWidget(self.FromTileset, 1, 1)

        swapLayout.addWidget(QtWidgets.QLabel('To tile type:'), 0, 2)
        swapLayout.addWidget(self.ToType, 0, 3)

        swapLayout.addWidget(QtWidgets.QLabel('To tileset:'), 1, 2)
        swapLayout.addWidget(self.ToTileset, 1, 3)


        # Buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)


        # Main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(swapLayout)
        mainLayout.addWidget(self.DoExchange)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class MetaInfoDialog(QtWidgets.QDialog):
    """
    Allows the user to enter in various meta-info to be kept in the level for display
    """
    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('InfoDlg', 0))
        self.setWindowIcon(GetIcon('info'))

        title = Area.Metadata.strData('Title')
        author = Area.Metadata.strData('Author')
        group = Area.Metadata.strData('Group')
        website = Area.Metadata.strData('Website')
        creator = Area.Metadata.strData('Creator')
        password = Area.Metadata.strData('Password')
        if title is None: title = '-'
        if author is None: author = '-'
        if group is None: group = '-'
        if website is None: website = '-'
        if creator is None: creator = '(unknown)'
        if password is None: password = ''

        self.levelName = QtWidgets.QLineEdit()
        self.levelName.setMaxLength(128)
        self.levelName.setReadOnly(True)
        self.levelName.setMinimumWidth(320)
        self.levelName.setText(title)

        self.Author = QtWidgets.QLineEdit()
        self.Author.setMaxLength(128)
        self.Author.setReadOnly(True)
        self.Author.setMinimumWidth(320)
        self.Author.setText(author)

        self.Group = QtWidgets.QLineEdit()
        self.Group.setMaxLength(128)
        self.Group.setReadOnly(True)
        self.Group.setMinimumWidth(320)
        self.Group.setText(group)

        self.Website = QtWidgets.QLineEdit()
        self.Website.setMaxLength(128)
        self.Website.setReadOnly(True)
        self.Website.setMinimumWidth(320)
        self.Website.setText(website)

        self.Password = QtWidgets.QLineEdit()
        self.Password.setMaxLength(128)
        self.Password.textChanged.connect(self.PasswordEntry)
        self.Password.setMinimumWidth(320)

        self.changepw = QtWidgets.QPushButton(trans.string('InfoDlg', 1))


        if password != '':
            self.levelName.setReadOnly(False)
            self.Author.setReadOnly(False)
            self.Group.setReadOnly(False)
            self.Website.setReadOnly(False)
            self.changepw.setDisabled(False)


        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.addButton(self.changepw, buttonBox.ActionRole)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.changepw.clicked.connect(self.ChangeButton)
        self.changepw.setDisabled(True)

        self.lockedLabel = QtWidgets.QLabel(trans.string('InfoDlg', 2))

        infoLayout = QtWidgets.QFormLayout()
        infoLayout.addWidget(self.lockedLabel)
        infoLayout.addRow(trans.string('InfoDlg', 3), self.Password)
        infoLayout.addRow(trans.string('InfoDlg', 4), self.levelName)
        infoLayout.addRow(trans.string('InfoDlg', 5), self.Author)
        infoLayout.addRow(trans.string('InfoDlg', 6), self.Group)
        infoLayout.addRow(trans.string('InfoDlg', 7), self.Website)

        self.PasswordLabel = infoLayout.labelForField(self.Password)

        levelIsLocked = password != ''
        self.lockedLabel.setVisible(levelIsLocked)
        self.PasswordLabel.setVisible(levelIsLocked)
        self.Password.setVisible(levelIsLocked)

        infoGroupBox = QtWidgets.QGroupBox(trans.string('InfoDlg', 8, '[name]', creator))
        infoGroupBox.setLayout(infoLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(infoGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.PasswordEntry('')


    def PasswordEntry(self, text):
        pswd = Area.Metadata.strData('Password')
        if pswd is None: pswd = ''
        if text == pswd:
            self.levelName.setReadOnly(False)
            self.Author.setReadOnly(False)
            self.Group.setReadOnly(False)
            self.Website.setReadOnly(False)
            self.changepw.setDisabled(False)
        else:
            self.levelName.setReadOnly(True)
            self.Author.setReadOnly(True)
            self.Group.setReadOnly(True)
            self.Website.setReadOnly(True)
            self.changepw.setDisabled(True)


    #   To all would be crackers who are smart enough to reach here:
    #
    #   Make your own levels.
    #
    #
    #
    #       - The management
    #


    def ChangeButton(self):
        """
        Allows the changing of a given password
        """

        class ChangePWDialog(QtWidgets.QDialog):
            """
            Dialog
            """
            def __init__(self):
                super().__init__()
                self.setWindowTitle(trans.string('InfoDlg', 9))
                self.setWindowIcon(GetIcon('info'))

                self.New = QtWidgets.QLineEdit()
                self.New.setMaxLength(64)
                self.New.textChanged.connect(self.PasswordMatch)
                self.New.setMinimumWidth(320)

                self.Verify = QtWidgets.QLineEdit()
                self.Verify.setMaxLength(64)
                self.Verify.textChanged.connect(self.PasswordMatch)
                self.Verify.setMinimumWidth(320)

                self.Ok = QtWidgets.QPushButton('OK')
                self.Cancel = QtWidgets.QDialogButtonBox.Cancel

                buttonBox = QtWidgets.QDialogButtonBox()
                buttonBox.addButton(self.Ok, buttonBox.AcceptRole)
                buttonBox.addButton(self.Cancel)

                buttonBox.accepted.connect(self.accept)
                buttonBox.rejected.connect(self.reject)
                self.Ok.setDisabled(True)

                infoLayout = QtWidgets.QFormLayout()
                infoLayout.addRow(trans.string('InfoDlg', 10), self.New)
                infoLayout.addRow(trans.string('InfoDlg', 11), self.Verify)

                infoGroupBox = QtWidgets.QGroupBox(trans.string('InfoDlg', 12))

                infoLabel = QtWidgets.QVBoxLayout()
                infoLabel.addWidget(QtWidgets.QLabel(trans.string('InfoDlg', 13)), 0, Qt.AlignCenter)
                infoLabel.addLayout(infoLayout)
                infoGroupBox.setLayout(infoLabel)

                mainLayout = QtWidgets.QVBoxLayout()
                mainLayout.addWidget(infoGroupBox)
                mainLayout.addWidget(buttonBox)
                self.setLayout(mainLayout)

            def PasswordMatch(self, text):
                self.Ok.setDisabled(self.New.text() != self.Verify.text() and self.New.text() != '')

        dlg = ChangePWDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.lockedLabel.setVisible(True)
            self.Password.setVisible(True)
            self.PasswordLabel.setVisible(True)
            pswd = str(dlg.Verify.text())
            Area.Metadata.setStrData('Password', pswd)
            self.Password.setText(pswd)
            SetDirty()

            self.levelName.setReadOnly(False)
            self.Author.setReadOnly(False)
            self.Group.setReadOnly(False)
            self.Website.setReadOnly(False)
            self.changepw.setDisabled(False)


class AreaOptionsDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose among various area options from tabs
    """
    def __init__(self):
        """
        Creates and initializes the tab dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('AreaDlg', 0))
        self.setWindowIcon(GetIcon('area'))

        self.tabWidget = QtWidgets.QTabWidget()
        self.LoadingTab = LoadingTab()

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.LoadingTab)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class ZonesDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose among various zones from tabs
    """
    def __init__(self):
        """
        Creates and initializes the tab dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('ZonesDlg', 0))
        self.setWindowIcon(GetIcon('zones'))

        self.tabWidget = QtWidgets.QTabWidget()

        self.zoneTabs = []
        for i, z in enumerate(Area.zones):
            ZoneTabName = trans.string('ZonesDlg', 3, '[num]', i + 1)
            tab = ZoneTab(z)
            self.zoneTabs.append(tab)
            self.tabWidget.addTab(tab, ZoneTabName)


        if self.tabWidget.count() > 5:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, str(tab + 1))


        self.NewButton = QtWidgets.QPushButton(trans.string('ZonesDlg', 4))
        self.DeleteButton = QtWidgets.QPushButton(trans.string('ZonesDlg', 5))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.addButton(self.NewButton, buttonBox.ActionRole);
        buttonBox.addButton(self.DeleteButton, buttonBox.ActionRole);

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        #self.NewButton.setEnabled(len(self.zoneTabs) < 8)
        self.NewButton.clicked.connect(self.NewZone)
        self.DeleteButton.clicked.connect(self.DeleteZone)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


    def NewZone(self):
        if len(self.zoneTabs) >= 15:
            result = QtWidgets.QMessageBox.warning(self, trans.string('ZonesDlg', 6), trans.string('ZonesDlg', 7), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No:
                return

        id = len(self.zoneTabs)
        z = ZoneItem(256, 256, 448, 224, 0, 0, id, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, id)
        ZoneTabName = trans.string('ZonesDlg', 3, '[num]', id + 1)
        tab = ZoneTab(z)
        self.zoneTabs.append(tab)
        self.tabWidget.addTab(tab, ZoneTabName)
        if self.tabWidget.count() > 5:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, str(tab + 1))

        self.NewButton.setEnabled(len(self.zoneTabs) < 8)



    def DeleteZone(self):
        curindex = self.tabWidget.currentIndex()
        tabamount = self.tabWidget.count()
        if tabamount == 0: return
        self.tabWidget.removeTab(curindex)

        for tab in range(curindex, tabamount):
            if self.tabWidget.count() < 6:
                self.tabWidget.setTabText(tab, trans.string('ZonesDlg', 3, '[num]', tab+1))
            if self.tabWidget.count() > 5:
                self.tabWidget.setTabText(tab, str(tab + 1))

        self.zoneTabs.pop(curindex)
        if self.tabWidget.count() < 6:
            for tab in range(0, self.tabWidget.count()):
                self.tabWidget.setTabText(tab, trans.string('ZonesDlg', 3, '[num]', tab+1))

        #self.NewButton.setEnabled(len(self.zoneTabs) < 8)


class ZoneTab(QtWidgets.QWidget):
    def __init__(self, z):
        super().__init__()

        self.zoneObj = z
        self.AutoChangingSize = False

        self.createDimensions(z)
        self.createVisibility(z)
        self.createBounds(z)
        self.createAudio(z)
        self.createUnks(z)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.Dimensions)
        mainLayout.addWidget(self.Visibility)
        mainLayout.addWidget(self.Bounds)
        mainLayout.addWidget(self.Audio)
        mainLayout.addWidget(self.Unks)
        self.setLayout(mainLayout)



    def createDimensions(self, z):
        self.Dimensions = QtWidgets.QGroupBox(trans.string('ZonesDlg', 8))

        self.Zone_xpos = QtWidgets.QSpinBox()
        self.Zone_xpos.setRange(16, 65535)
        self.Zone_xpos.setToolTip(trans.string('ZonesDlg', 10))
        self.Zone_xpos.setValue(z.objx)

        self.Zone_ypos = QtWidgets.QSpinBox()
        self.Zone_ypos.setRange(16, 65535)
        self.Zone_ypos.setToolTip(trans.string('ZonesDlg', 12))
        self.Zone_ypos.setValue(z.objy)

        self.Zone_width = QtWidgets.QSpinBox()
        self.Zone_width.setRange(300, 65535)
        self.Zone_width.setToolTip(trans.string('ZonesDlg', 14))
        self.Zone_width.setValue(z.width)
        self.Zone_width.valueChanged.connect(self.PresetDeselected)

        self.Zone_height = QtWidgets.QSpinBox()
        self.Zone_height.setRange(200, 65535)
        self.Zone_height.setToolTip(trans.string('ZonesDlg', 16))
        self.Zone_height.setValue(z.height)
        self.Zone_height.valueChanged.connect(self.PresetDeselected)

        # Common retail zone presets
        # 416 x 224; Zoom Level 0 (used with minigames)
        # 448 x 224; Zoom Level 0 (used with boss battles)
        # 512 x 272; Zoom Level 0 (used in many, many places)
        # 560 x 304; Zoom Level 2
        # 608 x 320; Zoom Level 2 (actually 609x320; rounded it down myself)
        # 784 x 320; Zoom Level 2 (not added to list because it's just an expansion of 608x320)
        # 704 x 384; Zoom Level 3 (used multiple times; therefore it's important)
        # 944 x 448; Zoom Level 4 (used in 9-3 zone 3)
        self.Zone_presets_values = ('0: 416x224', '0: 448x224', '0: 512x272', '2: 560x304', '2: 608x320', '3: 704x384', '4: 944x448')

        self.Zone_presets = QtWidgets.QComboBox()
        self.Zone_presets.addItems(self.Zone_presets_values)
        self.Zone_presets.setToolTip(trans.string('ZonesDlg', 18))
        self.Zone_presets.currentIndexChanged.connect(self.PresetSelected)
        self.PresetDeselected() # can serve as an initializer for self.Zone_presets


        ZonePositionLayout = QtWidgets.QFormLayout()
        ZonePositionLayout.addRow(trans.string('ZonesDlg', 9), self.Zone_xpos)
        ZonePositionLayout.addRow(trans.string('ZonesDlg', 11), self.Zone_ypos)

        ZoneSizeLayout = QtWidgets.QFormLayout()
        ZoneSizeLayout.addRow(trans.string('ZonesDlg', 13), self.Zone_width)
        ZoneSizeLayout.addRow(trans.string('ZonesDlg', 15), self.Zone_height)
        ZoneSizeLayout.addRow(trans.string('ZonesDlg', 17), self.Zone_presets)


        innerLayout = QtWidgets.QHBoxLayout()

        innerLayout.addLayout(ZonePositionLayout)
        innerLayout.addLayout(ZoneSizeLayout)
        self.Dimensions.setLayout(innerLayout)


    def createUnks(self, z):
        self.Unks = QtWidgets.QGroupBox('Misc Values')

        self.unk0B = QtWidgets.QSpinBox()
        self.unk0B.setRange(0, 255)
        self.unk0B.setToolTip('An unknown. Try to help us document it! Used as 3 in a few places, everywhere else is 0.')
        self.unk0B.setValue(z.unk1)

        self.unk0E = QtWidgets.QSpinBox()
        self.unk0E.setRange(0, 255)
        self.unk0E.setToolTip('An unknown. Try to help us document it! Used as 0, 1, 2, 3, 4, 5, 6.')
        self.unk0E.setValue(z.cammode)

        InnerLayout = QtWidgets.QFormLayout()
        InnerLayout.addRow('Unknown 0x0B:', self.unk0B)
        InnerLayout.addRow('Unknown 0x0E:', self.unk0E)
        self.Unks.setLayout(InnerLayout)

    def createVisibility(self, z):
        self.Visibility = QtWidgets.QGroupBox(trans.string('ZonesDlg', 19))

        self.Zone_modeldark = QtWidgets.QComboBox()
        self.Zone_modeldark.addItems(ZoneThemeValues)
        self.Zone_modeldark.setToolTip(trans.string('ZonesDlg', 21))
        if z.modeldark < 0: z.modeldark = 0
        if z.modeldark >= len(ZoneThemeValues): z.modeldark = len(ZoneThemeValues)
        self.Zone_modeldark.setCurrentIndex(z.modeldark)

        # self.Zone_terraindark = QtWidgets.QComboBox()
        # self.Zone_terraindark.addItems(ZoneTerrainThemeValues)
        # self.Zone_terraindark.setToolTip(trans.string('ZonesDlg', 23))
        # if z.terraindark < 0: z.terraindark = 0
        # if z.terraindark >= len(ZoneTerrainThemeValues): z.terraindark = len(ZoneTerrainThemeValues)
        # self.Zone_terraindark.setCurrentIndex(z.terraindark)


        self.Zone_vnormal = QtWidgets.QRadioButton(trans.string('ZonesDlg', 24))
        self.Zone_vnormal.setToolTip(trans.string('ZonesDlg', 25))

        self.Zone_vspotlight = QtWidgets.QRadioButton(trans.string('ZonesDlg', 26))
        self.Zone_vspotlight.setToolTip(trans.string('ZonesDlg', 27))

        self.Zone_vfulldark = QtWidgets.QRadioButton(trans.string('ZonesDlg', 28))
        self.Zone_vfulldark.setToolTip(trans.string('ZonesDlg', 29))

        self.Zone_visibility = QtWidgets.QComboBox()

        self.zv = z.visibility
        VRadioDiv = self.zv // 16

        if VRadioDiv == 0:
            self.Zone_vnormal.setChecked(True)
        elif VRadioDiv == 1:
            self.Zone_vspotlight.setChecked(True)
        elif VRadioDiv == 2:
            self.Zone_vfulldark.setChecked(True)
        elif VRadioDiv == 3:
            self.Zone_vfulldark.setChecked(True)


        self.ChangeList()
        self.Zone_vnormal.clicked.connect(self.ChangeList)
        self.Zone_vspotlight.clicked.connect(self.ChangeList)
        self.Zone_vfulldark.clicked.connect(self.ChangeList)


        self.Zone_xtrack = QtWidgets.QCheckBox()
        self.Zone_xtrack.setToolTip(trans.string('ZonesDlg', 31))
        if z.cammode in [0, 3, 6]:
            self.Zone_xtrack.setChecked(True)
        self.Zone_ytrack = QtWidgets.QCheckBox()
        self.Zone_ytrack.setToolTip(trans.string('ZonesDlg', 33))
        if z.cammode in [0, 1, 3, 4]:
            self.Zone_ytrack.setChecked(True)


        self.Zone_camerazoom = QtWidgets.QComboBox()
        self.Zone_camerazoom.setToolTip(trans.string('ZonesDlg', 35))
        newItems1 = ['-2', '-1', '0', '1', '2', '3', '4']
        self.Zone_camerazoom.addItems(newItems1)
        if z.camzoom == 8:
            self.Zone_camerazoom.setCurrentIndex(0)
        elif (z.camzoom == 9 and z.cammode in [3, 4]) or (z.camzoom in [19, 20] and z.cammode == 9):
            self.Zone_camerazoom.setCurrentIndex(1)
        elif (z.camzoom in [0, 1, 2] and z.cammode in [0, 1, 6]) or (z.camzoom in [10, 11] and z.cammode in [3, 4]) or (z.camzoom == 13 and z.cammode == 9):
            self.Zone_camerazoom.setCurrentIndex(2)
        elif z.camzoom in [5, 6, 7, 9, 10] and z.cammode in [0, 1, 6] or (z.camzoom == 12 and z.cammode == 9):
            self.Zone_camerazoom.setCurrentIndex(3)
        elif (z.camzoom in [4, 11] and z.cammode in [0, 1, 6]) or (z.camzoom in [1, 5] and z.cammode in [3, 4])  or (z.camzoom == 14 and z.cammode == 9):
            self.Zone_camerazoom.setCurrentIndex(4)
        elif (z.camzoom == 3 and z.cammode in [0, 1, 6]) or (z.camzoom == 2 and z.cammode in [3, 4]) or (z.camzoom == 15 and z.cammode == 9):
            self.Zone_camerazoom.setCurrentIndex(5)
        elif (z.camzoom == 16 and z.cammode in [0, 1, 6]) or (z.camzoom in [3, 7] and z.cammode in [3, 4]) or (z.camzoom == 16 and z.cammode == 9):
            self.Zone_camerazoom.setCurrentIndex(6)
        else:
            self.Zone_camerazoom.setCurrentIndex(2)

        self.Zone_camerabias = QtWidgets.QCheckBox()
        self.Zone_camerabias.setToolTip(trans.string('ZonesDlg', 37))
        if z.camzoom in [1, 2, 3, 4, 5, 6, 9, 10]:
            self.Zone_camerabias.setChecked(True)

        # directionmodeValues = trans.stringList('ZonesDlg', 38)
        # self.Zone_directionmode = QtWidgets.QComboBox()
        # self.Zone_directionmode.addItems(directionmodeValues)
        # self.Zone_directionmode.setToolTip(trans.string('ZonesDlg', 40))
        # if z.camtrack < 0: z.camtrack = 0
        # if z.camtrack >= 6: z.camtrack = 6
        # idx = z.camtrack/2
        # if z.camtrack == 1: idx = 1
        # self.Zone_directionmode.setCurrentIndex(idx)

        # Layouts
        ZoneZoomLayout = QtWidgets.QFormLayout()
        ZoneZoomLayout.addRow(trans.string('ZonesDlg', 34), self.Zone_camerazoom)
        ZoneZoomLayout.addRow(trans.string('ZonesDlg', 20), self.Zone_modeldark)
        # ZoneZoomLayout.addRow(trans.string('ZonesDlg', 22), self.Zone_terraindark)

        ZoneCameraLayout = QtWidgets.QFormLayout()
        ZoneCameraLayout.addRow(trans.string('ZonesDlg', 30), self.Zone_xtrack)
        ZoneCameraLayout.addRow(trans.string('ZonesDlg', 32), self.Zone_ytrack)
        ZoneCameraLayout.addRow(trans.string('ZonesDlg', 36), self.Zone_camerabias)

        ZoneVisibilityLayout = QtWidgets.QHBoxLayout()
        ZoneVisibilityLayout.addWidget(self.Zone_vnormal)
        ZoneVisibilityLayout.addWidget(self.Zone_vspotlight)
        ZoneVisibilityLayout.addWidget(self.Zone_vfulldark)

        # ZoneDirectionLayout = QtWidgets.QFormLayout()
        # ZoneDirectionLayout.addRow(trans.string('ZonesDlg', 39), self.Zone_directionmode)

        TopLayout = QtWidgets.QHBoxLayout()
        TopLayout.addLayout(ZoneCameraLayout)
        TopLayout.addLayout(ZoneZoomLayout)

        InnerLayout = QtWidgets.QVBoxLayout()
        InnerLayout.addLayout(TopLayout)
        InnerLayout.addLayout(ZoneVisibilityLayout)
        InnerLayout.addWidget(self.Zone_visibility)
        # InnerLayout.addLayout(ZoneDirectionLayout)
        self.Visibility.setLayout(InnerLayout)

    def ChangeList(self):
        VRadioMod = self.zv % 16

        if self.Zone_vnormal.isChecked():
            self.Zone_visibility.clear()
            addList = trans.stringList('ZonesDlg', 41)
            self.Zone_visibility.addItems(addList)
            self.Zone_visibility.setToolTip(trans.string('ZonesDlg', 42))
            self.Zone_visibility.setCurrentIndex(VRadioMod)
        elif self.Zone_vspotlight.isChecked():
            self.Zone_visibility.clear()
            addList = trans.stringList('ZonesDlg', 43)
            self.Zone_visibility.addItems(addList)
            self.Zone_visibility.setToolTip(trans.string('ZonesDlg', 44))
            self.Zone_visibility.setCurrentIndex(VRadioMod)
        elif self.Zone_vfulldark.isChecked():
            self.Zone_visibility.clear()
            addList = trans.stringList('ZonesDlg', 45)
            self.Zone_visibility.addItems(addList)
            self.Zone_visibility.setToolTip(trans.string('ZonesDlg', 46))
            self.Zone_visibility.setCurrentIndex(VRadioMod)


    def createBounds(self, z):
        self.Bounds = QtWidgets.QGroupBox(trans.string('ZonesDlg', 47))

        #Block3 = Area.bounding[z.block3id]

        self.Zone_yboundup = QtWidgets.QSpinBox()
        self.Zone_yboundup.setRange(-32766, 32767)
        self.Zone_yboundup.setToolTip(trans.string('ZonesDlg', 49))
        self.Zone_yboundup.setSpecialValueText('32')
        self.Zone_yboundup.setValue(z.yupperbound)

        self.Zone_ybounddown = QtWidgets.QSpinBox()
        self.Zone_ybounddown.setRange(-32766, 32767)
        self.Zone_ybounddown.setToolTip(trans.string('ZonesDlg', 51))
        self.Zone_ybounddown.setValue(z.ylowerbound)

        self.Zone_yboundup2 = QtWidgets.QSpinBox()
        self.Zone_yboundup2.setRange(-32766, 32767)
        self.Zone_yboundup2.setToolTip(trans.string('ZonesDlg', 71))
        self.Zone_yboundup2.setValue(z.yupperbound2)

        self.Zone_ybounddown2 = QtWidgets.QSpinBox()
        self.Zone_ybounddown2.setRange(-32766, 32767)
        self.Zone_ybounddown2.setToolTip(trans.string('ZonesDlg', 73))
        self.Zone_ybounddown2.setValue(z.ylowerbound2)

        self.Zone_boundflg = QtWidgets.QCheckBox()
        self.Zone_boundflg.setToolTip(trans.string('ZonesDlg', 75))
        self.Zone_boundflg.setChecked(z.unknownbnf == 0xF)


        LA = QtWidgets.QFormLayout()
        LA.addRow(trans.string('ZonesDlg', 48), self.Zone_yboundup)
        LA.addRow(trans.string('ZonesDlg', 50), self.Zone_ybounddown)
        LA.addRow(trans.string('ZonesDlg', 74), self.Zone_boundflg)
        LB = QtWidgets.QFormLayout()
        LB.addRow(trans.string('ZonesDlg', 70), self.Zone_yboundup2)
        LB.addRow(trans.string('ZonesDlg', 72), self.Zone_ybounddown2)
        LC = QtWidgets.QGridLayout()
        LC.addLayout(LA, 0, 0)
        LC.addLayout(LB, 0, 1)

        self.Bounds.setLayout(LC)


    def createAudio(self, z):
        self.Audio = QtWidgets.QGroupBox(trans.string('ZonesDlg', 52))
        self.AutoEditMusic = False

        self.Zone_music = QtWidgets.QComboBox()
        self.Zone_music.setToolTip(trans.string('ZonesDlg', 54))
        newItems = getMusic()
        for a, b in newItems:
            self.Zone_music.addItem(b, a) # text, songid
        self.Zone_music.setCurrentIndex(self.Zone_music.findData(z.music))
        self.Zone_music.currentIndexChanged.connect(self.handleMusicListSelect)

        self.Zone_musicid = QtWidgets.QSpinBox()
        self.Zone_musicid.setToolTip(trans.string('ZonesDlg', 69))
        self.Zone_musicid.setMaximum(255)
        self.Zone_musicid.setValue(z.music)
        self.Zone_musicid.valueChanged.connect(self.handleMusicIDChange)

        # self.Zone_sfx = QtWidgets.QComboBox()
        # self.Zone_sfx.setToolTip(trans.string('ZonesDlg', 56))
        # newItems3 = trans.stringList('ZonesDlg', 57)
        # self.Zone_sfx.addItems(newItems3)
        # self.Zone_sfx.setCurrentIndex(z.sfxmod / 16)

        # self.Zone_boss = QtWidgets.QCheckBox()
        # self.Zone_boss.setToolTip(trans.string('ZonesDlg', 59))
        # self.Zone_boss.setChecked(z.sfxmod % 16)


        ZoneAudioLayout = QtWidgets.QFormLayout()
        ZoneAudioLayout.addRow(trans.string('ZonesDlg', 53), self.Zone_music)
        ZoneAudioLayout.addRow(trans.string('ZonesDlg', 68), self.Zone_musicid)
        # ZoneAudioLayout.addRow(trans.string('ZonesDlg', 55), self.Zone_sfx)
        # ZoneAudioLayout.addRow(trans.string('ZonesDlg', 58), self.Zone_boss)

        self.Audio.setLayout(ZoneAudioLayout)


    def handleMusicListSelect(self):
        """
        Handles the user selecting an entry from the music list
        """
        if self.AutoEditMusic: return
        id = self.Zone_music.itemData(self.Zone_music.currentIndex())
        id = int(str(id)) # id starts out as a QString

        self.AutoEditMusic = True
        self.Zone_musicid.setValue(id)
        self.AutoEditMusic = False

    def handleMusicIDChange(self):
        """
        Handles the user selecting a custom music ID
        """
        if self.AutoEditMusic: return
        id = self.Zone_musicid.value()

        # BUG: The music entries are out of order

        self.AutoEditMusic = True
        self.Zone_music.setCurrentIndex(self.Zone_music.findData(id))
        self.AutoEditMusic = False

    def PresetSelected(self, info=None):
        """
        Handles a zone size preset being selected
        """
        if self.AutoChangingSize: return

        if self.Zone_presets.currentText() == trans.string('ZonesDlg', 60): return
        w, h = self.Zone_presets.currentText()[3:].split('x')

        self.AutoChangingSize = True
        self.Zone_width.setValue(int(w))
        self.Zone_height.setValue(int(h))
        self.AutoChangingSize = False

        if self.Zone_presets.itemText(0) == trans.string('ZonesDlg', 60): self.Zone_presets.removeItem(0)

    def PresetDeselected(self, info=None):
        """
        Handles the zone height or width boxes being changed
        """
        if self.AutoChangingSize: return

        self.AutoChangingSize = True
        w = self.Zone_width.value()
        h = self.Zone_height.value()
        check = str(w) + 'x' + str(h)

        found = None
        for preset in self.Zone_presets_values:
            if check == preset[3:]: found = preset


        if found is not None:
            self.Zone_presets.setCurrentIndex(self.Zone_presets.findText(found))
            if self.Zone_presets.itemText(0) == trans.string('ZonesDlg', 60): self.Zone_presets.removeItem(0)
        else:
            if self.Zone_presets.itemText(0) != trans.string('ZonesDlg', 60): self.Zone_presets.insertItem(0, trans.string('ZonesDlg', 60))
            self.Zone_presets.setCurrentIndex(0)
        self.AutoChangingSize = False


class BGDialog(QtWidgets.QDialog):
    """
    Dialog that lets you change the backgrounds for zones in this area
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tabWidget = QtWidgets.QTabWidget()
        self.tabs = []
        for i, z in enumerate(Area.zones):
            page = BGTab(z)
            self.tabs.append(page)
            tabWidget.addTab(page, 'Zone %d' % i)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        L = QtWidgets.QVBoxLayout(self)
        L.addWidget(tabWidget)
        L.addWidget(buttonBox)


class BGTab(QtWidgets.QWidget):
    """
    A widget that lets you edit the background of a zone
    """
    def __init__(self, zone, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = QtWidgets.QComboBox()
        self.name.setEditable(True)
        self.name.addItems(sorted(BackgroundNames.values()))
        self.name.setCurrentText(self.niceName(zone.bgName))
        self.name.setToolTip("The background for the level. <br><b>Note:</b> entries that are marked with a * need special conditions to render properly. Some models are placed at a specific location when used and will have a corrupt screen if the player is out of bounds of said location")
        self.name.currentTextChanged.connect(self.handleNameChanged)

        self.unk1 = QtWidgets.QSpinBox()
        self.unk1.setRange(0, 0xFF)
        self.unk1.setValue(zone.bgUnk1)

        self.unk2 = QtWidgets.QSpinBox()
        self.unk2.setRange(0, 0xFFFF)
        self.unk2.setValue(zone.bgUnk2)

        self.previewLabel = QtWidgets.QLabel()

        leftLayout = QtWidgets.QFormLayout()
        leftLayout.addRow('Background Name:', self.name)
        leftLayout.addRow('Unknown Value 1:', self.unk1)
        leftLayout.addRow('Unknown Value 2:', self.unk2)

        L = QtWidgets.QHBoxLayout(self)
        L.addLayout(leftLayout)
        L.addWidget(self.previewLabel)

        self.handleNameChanged() # initialize the preview label


    def niceName(self, name):
        """
        Returns the human-friendly name for the BG chosen
        """
        name = self.name.currentText() if name is None else name
        return BackgroundNames.get(name, name)


    def bgName(self):
        """
        Return the name string for the currently-selected BG
        """
        humanName = self.name.currentText()
        for ugly, nice in BackgroundNames.items():
            if humanName == nice:
                return ugly
        return humanName


    def handleNameChanged(self):
        """
        The user changed the name -- update the preview
        """
        name = self.bgName()

        path = os.path.join('satorudata', 'bg', 'dv_' + name + '.png')
        if os.path.isfile(path):
            pix = QtGui.QPixmap(path)
        else:
            pix = QtGui.QPixmap(
                os.path.join('satorudata', 'bg', 'no_preview.png'))
        self.previewLabel.setPixmap(pix)


class ScreenCapChoiceDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose which zone to take a pic of
    """
    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('ScrShtDlg', 0))
        self.setWindowIcon(GetIcon('screenshot'))

        i=0
        self.zoneCombo = QtWidgets.QComboBox()
        self.zoneCombo.addItem(trans.string('ScrShtDlg', 1))
        self.zoneCombo.addItem(trans.string('ScrShtDlg', 2))
        for z in Area.zones:
            i = i+1
            self.zoneCombo.addItem(trans.string('ScrShtDlg', 3, '[zone]', i))


        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.zoneCombo)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class AutoSavedInfoDialog(QtWidgets.QDialog):
    """
    Dialog which lets you know that an auto saved level exists
    """

    def __init__(self, filename):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('AutoSaveDlg', 0))
        self.setWindowIcon(GetIcon('save'))

        mainlayout = QtWidgets.QVBoxLayout(self)

        hlayout = QtWidgets.QHBoxLayout()

        icon = QtWidgets.QLabel()
        hlayout.addWidget(icon)

        label = QtWidgets.QLabel(trans.string('AutoSaveDlg', 1, '[path]', filename))
        label.setWordWrap(True)
        hlayout.addWidget(label)
        hlayout.setStretch(1, 1)

        buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.No | QtWidgets.QDialogButtonBox.Yes)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        mainlayout.addLayout(hlayout)
        mainlayout.addWidget(buttonbox)


class AreaChoiceDialog(QtWidgets.QDialog):
    """
    Dialog which lets you choose an area
    """

    def __init__(self, areacount):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('AreaChoiceDlg', 0))
        self.setWindowIcon(GetIcon('areas'))

        self.areaCombo = QtWidgets.QComboBox()
        for i in range(areacount):
            self.areaCombo.addItem(trans.string('AreaChoiceDlg', 1, '[num]', i+1))

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.areaCombo)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)


class PreferencesDialog(QtWidgets.QDialog):
    """
    Dialog which lets you customize Satoru
    """
    def __init__(self):
        """
        Creates and initializes the dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('PrefsDlg', 0))
        self.setWindowIcon(GetIcon('settings'))

        # Create the tab widget
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.currentChanged.connect(self.tabChanged)

        # Create other widgets
        self.infoLabel = QtWidgets.QLabel()
        self.generalTab = self.getGeneralTab()
        self.toolbarTab = self.getToolbarTab()
        self.themesTab = self.getThemesTab()
        self.tabWidget.addTab(self.generalTab, trans.string('PrefsDlg', 1))
        self.tabWidget.addTab(self.toolbarTab, trans.string('PrefsDlg', 2))
        self.tabWidget.addTab(self.themesTab, trans.string('PrefsDlg', 3))

        # Create the buttonbox
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # Create a main layout
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.infoLabel)
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        # Update it
        self.tabChanged()
        self.menuSettingChanged()

    def tabChanged(self):
        """
        Handles the current tab being changed
        """
        self.infoLabel.setText(self.tabWidget.currentWidget().info)

    def menuSettingChanged(self):
        """
        Handles the menu-style option being changed
        """
        self.tabWidget.setTabEnabled(1, self.generalTab.MenuM.isChecked())

    def getGeneralTab(self):
        """
        Returns the General Tab
        """

        class GeneralTab(QtWidgets.QWidget):
            """
            General Tab
            """
            info = trans.string('PrefsDlg', 4)

            def __init__(self, menuHandler):
                """
                Initializes the General Tab
                """
                super().__init__()

                # Add the Menu Format settings
                self.MenuR = QtWidgets.QRadioButton(trans.string('PrefsDlg', 12))
                self.MenuM = QtWidgets.QRadioButton(trans.string('PrefsDlg', 13))
                self.MenuG = QtWidgets.QButtonGroup() # huge glitches if it's not assigned to self.something
                self.MenuG.setExclusive(True)
                self.MenuG.addButton(self.MenuR)
                self.MenuG.addButton(self.MenuM)
                MenuL = QtWidgets.QVBoxLayout()
                MenuL.addWidget(self.MenuR)
                MenuL.addWidget(self.MenuM)
                self.MenuG.buttonClicked.connect(menuHandler)

                # Add the Translation Language setting
                self.Trans = QtWidgets.QComboBox()
                self.Trans.setMaximumWidth(256)

                # Disable auto pick checkbox
                self.DisableAutoPick = QtWidgets.QCheckBox()
                self.DisableAutoPick.stateChanged.connect(self.HandleDisableAutoPick)

                self.ShowSpritesBehindL0 = QtWidgets.QCheckBox()
                self.ShowSpritesBehindL0.stateChanged.connect(self.HandleSpritesBehindL0)                

                # Add the Clear Recent Files button
                ClearRecentBtn = QtWidgets.QPushButton(trans.string('PrefsDlg', 16))
                ClearRecentBtn.setMaximumWidth(ClearRecentBtn.minimumSizeHint().width())
                ClearRecentBtn.clicked.connect(self.ClearRecent)

                # Create the main layout
                L = QtWidgets.QFormLayout()
                L.addRow(trans.string('PrefsDlg', 11), MenuL)
                L.addRow(trans.string('PrefsDlg', 14), self.Trans)
                L.addRow("Disable auto-picking selected tiles", self.DisableAutoPick)
                L.addRow("Show sprites behind Layer 0 (slow!)", self.ShowSpritesBehindL0)
                L.addRow(trans.string('PrefsDlg', 15), ClearRecentBtn)

                self.setLayout(L)

                # Set the buttons
                self.Reset()

            def Reset(self):
                """
                Read the preferences and check the respective boxes
                """
                if str(setting('Menu')) == 'Ribbon': self.MenuR.setChecked(True)
                else: self.MenuM.setChecked(True)

                self.Trans.addItem('English')
                self.Trans.setItemData(0, None, Qt.UserRole)
                self.Trans.setCurrentIndex(0)
                i = 1
                for trans in os.listdir('satorudata/translations'):
                    if trans.lower() == 'english': continue

                    fp = 'satorudata/translations/' + trans + '/main.xml'
                    if not os.path.isfile(fp): continue

                    transobj = SatoruTranslation(trans)
                    name = transobj.name
                    self.Trans.addItem(name)
                    self.Trans.setItemData(i, trans, Qt.UserRole)
                    if trans == str(setting('Translation')):
                        self.Trans.setCurrentIndex(i)
                    i += 1

                if setting('DisableAutoPick') == True:
                    self.DisableAutoPick.setCheckState(Qt.Checked)

                if setting('drawSpritesBehindL0') == True:
                    self.ShowSpritesBehindL0.setCheckState(Qt.Checked)

            def ClearRecent(self):
                """
                Handle the Clear Recent Files button being clicked
                """
                ans = QtWidgets.QMessageBox.question(None, trans.string('PrefsDlg', 17), trans.string('PrefsDlg', 18), QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
                if ans != QtWidgets.QMessageBox.Yes: return
                self.RecentMenu.clearAll()

            def HandleDisableAutoPick(self, state):
                """Handles ticking the Disable auto-pick checkbox"""
                if state == Qt.Checked:
                    setSetting('DisableAutoPick', True)
                else:
                    setSetting('DisableAutoPick', False)

            def HandleSpritesBehindL0(self, state):
                """Handles ticking the Show sprites behind L0 checkbox"""
                if state == Qt.Checked:
                    setSetting('drawSpritesBehindL0', True)
                else:
                    setSetting('drawSpritesBehindL0', False)


        return GeneralTab(self.menuSettingChanged)

    def getToolbarTab(self):
        """
        Returns the Toolbar Tab
        """

        class ToolbarTab(QtWidgets.QWidget):
            """
            Toolbar Tab
            """
            info = trans.string('PrefsDlg', 5)

            def __init__(self):
                """
                Initializes the Toolbar Tab
                """
                global FileActions
                global EditActions
                global ViewActions
                global SettingsActions
                global HelpActions

                super().__init__()

                # Determine which keys are activated
                if setting('ToolbarActs') in (None, 'None', 'none', '', 0):
                    # Get the default settings
                    toggled = {}
                    for List in (FileActions, EditActions, ViewActions, SettingsActions, HelpActions):
                        for name, activated, key in List:
                            toggled[key] = activated
                else: # Get the registry settings
                    toggled = setting('ToolbarActs')
                    newToggled = {} # here, I'm replacing QStrings w/ python strings
                    for key in toggled:
                        newToggled[str(key)] = toggled[key]
                    toggled = newToggled

                # Create some data
                self.FileBoxes = []
                self.EditBoxes = []
                self.ViewBoxes = []
                self.SettingsBoxes = []
                self.HelpBoxes = []
                FL = QtWidgets.QVBoxLayout()
                EL = QtWidgets.QVBoxLayout()
                VL = QtWidgets.QVBoxLayout()
                SL = QtWidgets.QVBoxLayout()
                HL = QtWidgets.QVBoxLayout()
                FB = QtWidgets.QGroupBox(trans.string('Menubar', 0))
                EB = QtWidgets.QGroupBox(trans.string('Menubar', 1))
                VB = QtWidgets.QGroupBox(trans.string('Menubar', 2))
                SB = QtWidgets.QGroupBox(trans.string('Menubar', 3))
                HB = QtWidgets.QGroupBox(trans.string('Menubar', 4))

                # Arrange this data so it can be iterated over
                menuItems = (
                    (FileActions, self.FileBoxes, FL, FB),
                    (EditActions, self.EditBoxes, EL, EB),
                    (ViewActions, self.ViewBoxes, VL, VB),
                    (SettingsActions, self.SettingsBoxes, SL, SB),
                    (HelpActions, self.HelpBoxes, HL, HB),
                )

                # Set up the menus by iterating over the above data
                for defaults, boxes, layout, group in menuItems:
                    for L, C, I in defaults:
                        box = QtWidgets.QCheckBox(L)
                        boxes.append(box)
                        layout.addWidget(box)
                        try: box.setChecked(toggled[I])
                        except KeyError: pass
                        box.InternalName = I # to save settings later
                    group.setLayout(layout)


                # Create the always-enabled Current Area checkbox
                CurrentArea = QtWidgets.QCheckBox(trans.string('PrefsDlg', 19))
                CurrentArea.setChecked(True)
                CurrentArea.setEnabled(False)

                # Create the Reset button
                reset = QtWidgets.QPushButton(trans.string('PrefsDlg', 20))
                reset.clicked.connect(self.reset)

                # Create the main layout
                L = QtWidgets.QGridLayout()
                L.addWidget(reset,       0, 0, 1, 1)
                L.addWidget(FB,          1, 0, 3, 1)
                L.addWidget(EB,          1, 1, 3, 1)
                L.addWidget(VB,          1, 2, 3, 1)
                L.addWidget(SB,          1, 3, 1, 1)
                L.addWidget(HB,          2, 3, 1, 1)
                L.addWidget(CurrentArea, 3, 3, 1, 1)
                self.setLayout(L)

            def reset(self):
                """
                This is called when the Reset button is clicked
                """
                items = (
                    (self.FileBoxes, FileActions),
                    (self.EditBoxes, EditActions),
                    (self.ViewBoxes, ViewActions),
                    (self.SettingsBoxes, SettingsActions),
                    (self.HelpBoxes, HelpActions)
                )

                for boxes, defaults in items:
                    for box, default in zip(boxes, defaults):
                        box.setChecked(default[1])

        return ToolbarTab()

    def getThemesTab(self):
        """
        Returns the Themes Tab
        """

        class ThemesTab(QtWidgets.QWidget):
            """
            Themes Tab
            """
            info = trans.string('PrefsDlg', 6)

            def __init__(self):
                """
                Initializes the Themes Tab
                """
                super().__init__()

                # Get the current and available themes
                self.themeID = theme.themeName
                self.themes = self.getAvailableThemes()

                # Create the radiobuttons
                self.btns = []
                self.btnvals = {}
                for name, themeObj in self.themes:
                    displayname = name
                    if displayname.lower().endswith('.rt'): displayname = displayname[:-3]

                    btn = QtWidgets.QRadioButton(displayname)
                    if name == str(setting('Theme')): btn.setChecked(True)
                    btn.clicked.connect(self.UpdatePreview)

                    self.btns.append(btn)
                    self.btnvals[btn] = (name, themeObj)

                # Create the buttons group
                btnG = QtWidgets.QButtonGroup()
                btnG.setExclusive(True)
                for btn in self.btns:
                    btnG.addButton(btn)

                # Create the buttons groupbox
                L = QtWidgets.QGridLayout()
                for idx, button in enumerate(self.btns):
                    L.addWidget(btn, idx%12, int(idx/12))
                btnGB = QtWidgets.QGroupBox(trans.string('PrefsDlg', 21))
                btnGB.setLayout(L)

                # Create the preview labels and groupbox
                self.preview = QtWidgets.QLabel()
                self.description = QtWidgets.QLabel()
                L = QtWidgets.QVBoxLayout()
                L.addWidget(self.preview)
                L.addWidget(self.description)
                L.addStretch(1)
                previewGB = QtWidgets.QGroupBox(trans.string('PrefsDlg', 22))
                previewGB.setLayout(L)

                # Create the options box options
                keys = QtWidgets.QStyleFactory().keys()
                self.NonWinStyle = QtWidgets.QComboBox()
                self.NonWinStyle.setToolTip(trans.string('PrefsDlg', 24))
                self.NonWinStyle.addItems(keys)
                uistyle = setting('uiStyle')
                if uistyle is not None:
                    self.NonWinStyle.setCurrentIndex(keys.index(setting('uiStyle')))

                # Create the options groupbox
                L = QtWidgets.QVBoxLayout()
                L.addWidget(self.NonWinStyle)
                optionsGB = QtWidgets.QGroupBox(trans.string('PrefsDlg', 25))
                optionsGB.setLayout(L)

                # Create a main layout
                L = QtWidgets.QGridLayout()
                L.addWidget(btnGB, 0, 0, 2, 1)
                L.addWidget(optionsGB, 0, 1)
                L.addWidget(previewGB, 1, 1)
                L.setRowStretch(1, 1)
                self.setLayout(L)

                # Update the preview things
                self.UpdatePreview()


            def getAvailableThemes(self):
                """Searches the Themes folder and returns a list of theme filepaths.
                Automatically adds 'Classic' to the list."""
                themes = os.listdir('satorudata/themes')
                themeList = [('Classic', SatoruTheme())]
                for themeName in themes:
                    try:
                        if themeName.split('.')[-1].lower() == 'rt':
                            data = open('satorudata/themes/' + themeName, 'rb').read()
                            theme = SatoruTheme(data)
                            themeList.append((themeName, theme))
                    except Exception: pass

                return tuple(themeList)

            def UpdatePreview(self):
                """
                Updates the preview
                """
                for btn in self.btns:
                    if btn.isChecked():
                        t = self.btnvals[btn][1]
                        self.preview.setPixmap(self.drawPreview(t))
                        text = trans.string('PrefsDlg', 26, '[name]', t.themeName, '[creator]', t.creator, '[description]', t.description)
                        self.description.setText(text)

            def drawPreview(self, theme):
                """
                Returns a preview pixmap for the given theme
                """

                # Set up some things
                px = QtGui.QPixmap(350, 185)
                px.fill(theme.color('bg'))
                return px


                paint = QtGui.QPainter(px)

                UIColor = theme.color('ui')
                if UIColor is None: UIColor = toQColor(240,240,240) # close enough

                ice = QtGui.QPixmap('satorudata/sprites/ice_flow_7.png')

                font = QtGui.QFont(NumberFont) # need to make a new instance to avoid changing global settings
                font.setPointSize(6)
                paint.setFont(font)

                # Draw the spriteboxes
                paint.setPen(QtGui.QPen(theme.color('spritebox_lines'), 1))
                paint.setBrush(QtGui.QBrush(theme.color('spritebox_fill')))

                paint.drawRoundedRect(176, 64, 16, 16, 5, 5)
                paint.drawText(QtCore.QPointF(180, 75), '38')

                paint.drawRoundedRect(16, 96, 16, 16, 5, 5)
                paint.drawText(QtCore.QPointF(20, 107), '53')

                # Draw the entrance
                paint.setPen(QtGui.QPen(theme.color('entrance_lines'), 1))
                paint.setBrush(QtGui.QBrush(theme.color('entrance_fill')))

                paint.drawRoundedRect(208, 128, 16, 16, 5, 5)
                paint.drawText(QtCore.QPointF(212, 138), '0')

                # Draw the location
                paint.setPen(QtGui.QPen(theme.color('location_lines'), 1))
                paint.setBrush(QtGui.QBrush(theme.color('location_fill')))

                paint.drawRect(16, 144, 96, 32)
                paint.setPen(QtGui.QPen(theme.color('location_text'), 1))
                paint.drawText(QtCore.QPointF(20, 154), '1')

                # Draw the iceblock (can't easily draw a tileset obj)
                paint.drawPixmap(160, 144, ice.scaled(ice.width()*2/3, ice.height()*2/3))

                # Draw the zone
                paint.setPen(QtGui.QPen(theme.color('zone_lines'), 3))
                paint.setBrush(QtGui.QBrush(toQColor(0,0,0,0)))
                paint.drawRect(136, 52, 256, 120)
                paint.setPen(QtGui.QPen(theme.color('zone_corner'), 3))
                paint.setBrush(QtGui.QBrush(theme.color('zone_corner'), 3))
                paint.drawRect(135, 51, 2, 2)
                paint.drawRect(135, 171, 2, 2)
                paint.setPen(QtGui.QPen(theme.color('zone_text'), 1))
                font = QtGui.QFont(NumberFont)
                font.setPointSize(5)
                paint.setFont(font)
                paint.drawText(QtCore.QPointF(140, 62), 'Zone 1')

                # Draw the grid
                paint.setPen(QtGui.QPen(theme.color('grid'), 1, Qt.DotLine))
                gridcoords = []
                i=0
                while i < 350:
                    gridcoords.append(i)
                    i=i+16
                for i in gridcoords:
                    paint.setPen(QtGui.QPen(theme.color('grid'), 0.75, Qt.DotLine))
                    paint.drawLine(i, 0, i, 185)
                    paint.drawLine(0, i, 350, i)
                    if (i/16)%4 == 0:
                        paint.setPen(QtGui.QPen(theme.color('grid'), 1.5, Qt.DotLine))
                        paint.drawLine(i, 0, i, 185)
                        paint.drawLine(0, i, 350, i)
                    if (i/16)%8 == 0:
                        paint.setPen(QtGui.QPen(theme.color('grid'), 2.25, Qt.DotLine))
                        paint.drawLine(i, 0, i, 185)
                        paint.drawLine(0, i, 350, i)

                # Draw the UI
                paint.setBrush(QtGui.QBrush(UIColor))
                paint.setPen(toQColor(0,0,0,0))
                paint.drawRect(0, 0, 350, 24)
                paint.drawRect(300, 24, 50, 165)

                # Delete the painter and return the pixmap
                del paint
                return px


        return ThemesTab()


class UpdateDialog(QtWidgets.QDialog):
    """
    Dialog to display any available updates
    """
    def __init__(self):
        """
        Init the dialog
        """
        super().__init__()
        self.setWindowTitle(trans.string('Updates', 0))
        self.setWindowIcon(GetIcon('download'))
        self.setMinimumWidth(256)

        # Create widgets
        self.msgLabel = QtWidgets.QLabel()
        self.dldBtn = QtWidgets.QPushButton(trans.string('Updates', 4))
        self.dldBtn.clicked.connect(self.handleDldBtn)
        self.dldBtn.hide()
        self.progLabel = QtWidgets.QLabel()

        # Create the buttonbox
        buttonBox = QtWidgets.QDialogButtonBox()
        buttonBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.PerformCheck()

        # Create a main layout
        L = QtWidgets.QVBoxLayout()
        L.addWidget(self.msgLabel)
        L.addWidget(self.dldBtn)
        L.addWidget(self.progLabel)
        L.addWidget(buttonBox)
        self.setLayout(L)

    def PerformCheck(self):
        """
        Performs the update check
        """
        # Attempt to download data
        errors = False
        try: data = self.getTxt()
        except Exception: errors = True

        if not errors:
            try: releaseType = open('release.txt', 'r').read()
            except Exception: releaseType = 'unknown'
            releaseType = releaseType.replace('\n', '').replace('\r', '')

            available = SatoruVersion in data and len(data[SatoruVersion].values()) > 0

        # All right; now handle the results
        if errors:
            # Errors occurred
            self.UpdateUi('error')
        elif available:
            # Update is available
            name = list(data[SatoruVersion].keys())[0]
            infourl = data[SatoruVersion][name]['InfoUrl']
            url = data[SatoruVersion][name][releaseType]['url']
            self.UpdateUi(True, name, infourl, url)
        else:
            # No update is available
            self.UpdateUi(False)

    def getTxt(self):
        """
        Returns the parsed data in the online text file
        """
        rawdata = urllib.request.urlopen(UpdateURL)
        rawdata = rawdata.read(20000).decode('latin-1')

        tree = etree.ElementTree(etree.fromstring(rawdata))
        root = tree.getroot()

        rootData = {}
        for versionNode in root:
            if versionNode.tag.lower() != 'version': continue
            versionData = {}

            for updateNode in versionNode:
                if updateNode.tag.lower() != 'update': continue
                updateData = {}

                for releaseNode in updateNode:
                    if releaseNode.tag.lower() != 'release': continue
                    releaseData = {}
                    releaseData['url'] = releaseNode.attrib['url']

                    updateData[releaseNode.attrib['id']] = releaseData

                versionData[updateNode.attrib['name']] = updateData
                updateData['InfoUrl'] = updateNode.attrib['url']

            rootData[versionNode.attrib['id']] = versionData

        return rootData


    def UpdateUi(self, available, name='', infourl='', url=''):
        """
        Updates the UI based on updateinfo
        """
        if available == 'error':
            # Error while checking for update
            self.msgLabel.setText(trans.string('Updates', 1))
        elif not available:
            # No updates
            self.msgLabel.setText(trans.string('Updates', 2))
        else:
            # Updates!
            self.msgLabel.setText(trans.string('Updates', 3, '[name]', name, '[info]', infourl))

            self.dldBtn.show()
            self.dldBtn.url = url # hacky method


    def handleDldBtn(self):
        """
        Handles the user clicking the Download Now button
        """
        self.dldBtn.hide()
        self.progLabel.show()
        self.progLabel.setText(trans.string('Updates', 5))

        downloader = self.downloader(self.dldBtn.url)
        downloader.done.connect(self.handleDldDone)

        thread = threading.Thread(None, downloader.run)
        thread.start()

    def handleDldDone(self):
        """
        The download finished
        """
        self.progLabel.setText(trans.string('Updates', 6))

    class downloader(QtCore.QObject):
        """
        An object that downloads the update. Contains signals.
        """
        done = QtCore.pyqtSignal()
        def __init__(self, url):
            """
            Initializes it
            """
            super().__init__()
            self.url = url

        def run(self):
            """
            Runs the download
            """
            local_filename, headers = urllib.request.urlretrieve(self.url)

            if local_filename.startswith('\\'):
                local_filename = local_filename[1:]
            dest = os.path.dirname(sys.argv[0])

            zipfile.ZipFile(local_filename).extractall(dest)

            time.sleep(8)

            self.done.emit()


#####################################################################
############################### STAMP ###############################
#####################################################################

class Stamp():
    """
    Class that represents a stamp in the list
    """
    def __init__(self, SatoruClip=None, Name=''):
        """
        Initializes the stamp
        """
        self.SatoruClip = SatoruClip
        self.Name = Name
        self.Icon = self.render()

    def renderPreview(self):
        """
        Renders the stamp preview
        """
        minX, minY, maxX, maxY = 24576, 12288, 0, 0

        layers, sprites = mainWindow.getEncodedObjects(self.SatoruClip)

        # Go through the sprites and find the maxs and mins
        for spr in sprites:

            br = spr.getFullRect()

            x1 = br.topLeft().x()
            y1 = br.topLeft().y()
            x2 = x1 + br.width()
            y2 = y1 + br.height()

            if x1 < minX: minX = x1
            if x2 > maxX: maxX = x2
            if y1 < minY: minY = y1
            if y2 > maxY: maxY = y2

        # Go through the objects and find the maxs and mins
        for layer in layers:
            for obj in layer:
                x1 = (obj.objx * TileWidth)
                x2 = x1 + (obj.width * TileWidth)
                y1 = (obj.objy * TileWidth)
                y2 = y1 + (obj.height * TileWidth)

                if x1 < minX: minX = x1
                if x2 > maxX: maxX = x2
                if y1 < minY: minY = y1
                if y2 > maxY: maxY = y2

        # Calculate offset amounts (snap to TileWidthxTileWidth increments)
        offsetX = int(minX // TileWidth) * TileWidth
        offsetY = int(minY // TileWidth) * TileWidth
        drawOffsetX = offsetX - minX
        drawOffsetY = offsetY - minY

        # Go through the things again and shift them by the offset amount
        for spr in sprites:
            spr.objx -= offsetX / TileWidth / 16
            spr.objy -= offsetY / TileWidth / 16
        for layer in layers:
            for obj in layer:
                obj.objx -= offsetX // TileWidth
                obj.objy -= offsetY // TileWidth

        # Calculate the required pixmap size
        pixmapSize = (maxX - minX, maxY - minY)

        # Create the pixmap, and a painter
        pix = QtGui.QPixmap(pixmapSize[0], pixmapSize[1])
        pix.fill(Qt.transparent)
        painter = QtGui.QPainter(pix)
        painter.setRenderHint(painter.Antialiasing)

        # Paint all objects
        objw, objh = int(pixmapSize[0] // TileWidth) + 1, int(pixmapSize[1] // TileWidth) + 1
        for layer in reversed(layers):
            tmap = []
            for i in range(objh):
                tmap.append([-1] * objw)
            for obj in layer:
                startx = int(obj.objx)
                starty = int(obj.objy)

                desty = starty
                for row in obj.objdata:
                    destrow = tmap[desty]
                    destx = startx
                    for tile in row:
                        if tile > 0:
                            destrow[destx] = tile
                        destx += 1
                    desty += 1

                painter.save()
                desty = 0
                for row in tmap:
                    destx = 0
                    for tile in row:
                        if tile is None: continue
                        px = QtGui.QPixmap.fromImage(PIL.ImageQt.ImageQt(tile.image))
                        painter.drawPixmap(destx + drawOffsetX, desty + drawOffsetY, px)
                        destx += TileWidth
                    desty += TileWidth
                painter.restore()

        # Paint all sprites
        for spr in sprites:
            offx = ((spr.objx + spr.ImageObj.xOffset) * TileWidth / 16) + drawOffsetX
            offy = ((spr.objy + spr.ImageObj.yOffset) * TileWidth / 16) + drawOffsetY

            painter.save()
            painter.translate(offx, offy)

            spr.paint(painter, None, None, True)

            painter.restore()

            # Paint any auxiliary things
            for aux in spr.ImageObj.aux:
                painter.save()
                painter.translate(
                    offx + aux.x(),
                    offy + aux.y(),
                    )

                aux.paint(painter, None, None)

                painter.restore()

        # End painting
        painter.end()
        del painter

        # Scale it
        maxW, maxH = 96, 96
        w, h = pix.width(), pix.height()
        if w > h and w > maxW:
            pix = pix.scaledToWidth(maxW)
        elif h > w and h > maxH:
            pix = pix.scaledToHeight(maxH)

        # Return it
        return pix

    def render(self):
        """
        Renders the stamp icon, preview AND text
        """

        # Get the preview icon
        prevIcon = self.renderPreview()

        # Calculate the total size of the icon
        textSize = self.calculateTextSize(self.Name)
        totalWidth = max(prevIcon.width(), textSize.width())
        totalHeight = prevIcon.height() + 2 + textSize.height()

        # Make a pixmap and painter
        pix = QtGui.QPixmap(totalWidth, totalHeight)
        pix.fill(Qt.transparent)
        painter = QtGui.QPainter(pix)

        # Draw the preview
        iconWidth = prevIcon.width()
        iconXOffset = (totalWidth - prevIcon.width()) / 2
        painter.drawPixmap(iconXOffset, 0, prevIcon)

        # Draw the text
        textRect = QtCore.QRectF(0, prevIcon.height() + 2, totalWidth, textSize.height())
        painter.setFont(QtGui.QFont())
        painter.drawText(textRect, Qt.AlignTop | Qt.TextWordWrap, self.Name)

        # Return the pixmap
        return pix

    @staticmethod
    def calculateTextSize(text):
        """
        Calculates the size of text. Crops to 96 pixels wide.
        """
        fontMetrics = QtGui.QFontMetrics(QtGui.QFont())
        fontRect = fontMetrics.boundingRect(QtCore.QRect(0, 0, 96, 48), Qt.TextWordWrap, text)
        w, h = fontRect.width(), fontRect.height()
        return QtCore.QSizeF(min(w, 96), h)

    def update(self):
        """
        Updates the stamp icon
        """
        self.Icon = self.render()


class StampListModel(QtCore.QAbstractListModel):
    """
    Model containing all the stamps
    """

    def __init__(self):
        """
        Initializes the model
        """
        super().__init__()

        self.items = [] # list of Stamp objects

    def rowCount(self, parent=None):
        """
        Required by Qt
        """
        return len(self.items)

    def data(self, index, role=Qt.DisplayRole):
        """
        Get what we have for a specific row
        """
        if not index.isValid(): return None
        n = index.row()
        if n < 0: return None
        if n >= len(self.items): return None

        if role == Qt.DecorationRole:
            return self.items[n].Icon

        elif role == Qt.BackgroundRole:
            return QtGui.qApp.palette().base()

        elif role == Qt.UserRole:
            return self.items[n].Name

        elif role == Qt.StatusTipRole:
            return self.items[n].Name

        else: return None

    def setData(self, index, value, role=Qt.DisplayRole):
        """
        Set data for a specific row
        """
        if not index.isValid(): return None
        n = index.row()
        if n < 0: return None
        if n >= len(self.items): return None

        if role == Qt.UserRole:
            self.items[n].Name = value

    def addStamp(self, stamp):
        """
        Adds a stamp
        """

        # Start resetting
        self.beginResetModel()

        # Add the stamp to self.items
        self.items.append(stamp)

        # Finish resetting
        self.endResetModel()

    def removeStamp(self, stamp):
        """
        Removes a stamp
        """

        # Start resetting
        self.beginResetModel()

        # Remove the stamp from self.items
        idx = self.items.index(stamp)
        self.items.remove(stamp)

        # Finish resetting
        self.endResetModel()

#####################################################################
############################# GAME DEFS #############################
#####################################################################

class SatoruGameDefinition():
    """
    A class that defines a NSMBW hack: songs, tilesets, sprites, songs, etc.
    """

    # Gamedef File - has 2 values: name (str) and patch (bool)
    class GameDefinitionFile():
        """
        A class that defines a filepath, and some options
        """
        def __init__(self, path, patch):
            """
            Initializes the GameDefinitionFile
            """
            self.path = path
            self.patch = patch

    def __init__(self, name=None):
        """
        Initializes the SatoruGameDefinition
        """
        self.InitAsEmpty()

        # Try to init it from name if possible
        NoneTypes = (None, 'None', 0, '', True, False)
        if name in NoneTypes: return
        else:
            try: self.InitFromName(name)
            except Exception: self.InitAsEmpty() # revert


    def InitAsEmpty(self):
        """
        Sets all properties to their default values
        """
        gdf = self.GameDefinitionFile

        self.custom = False
        self.base = None # gamedef to use as a base
        self.gamepath = None
        self.name = trans.string('Gamedefs', 13) # 'New Super Mario Bros. Wii'
        self.description = trans.string('Gamedefs', 14) # 'A new Mario adventure!<br>' and the date
        self.version = '2'

        self.sprites = sprites

        self.files = {
            'entrancetypes': gdf(None, False),
            'levelnames': gdf(None, False),
            'music': gdf(None, False),
            'spritecategories': gdf(None, False),
            'spritedata': gdf(None, False),
            'spritelistdata': gdf(None, False),
            'spritenames': gdf(None, False),
            'tilesets': gdf(None, False),
            'ts1_descriptions': gdf(None, False),
            }
        self.folders = {
            'sprites': gdf(None, False),
            }

    def InitFromName(self, name):
        """
        Attempts to open/load a Game Definition from a name string
        """
        raise NotImplementedError

    def GetGamePath(self):
        """
        Returns the game path
        """
        if not self.custom: return str(setting('GamePath_NSMBU'))
        name = 'GamePath_' + self.name
        setname = setting(name)

        # Use the default if there are no settings for this yet
        if setname is None: return str(setting('GamePath_NSMBU'))
        else: return str(setname)

    def SetGamePath(self, path):
        """
        Sets the game path
        """
        if not self.custom: setSetting('GamePath_NSMBU', path)
        else:
            name = 'GamePath_' + self.name
            setSetting(name, path)

    def GetGamePaths(self):
        """
        Returns game paths of this gamedef and its bases
        """
        mainpath = str(setting('GamePath_NSMBU'))
        if not self.custom: return [mainpath,]

        name = 'GamePath_' + self.name
        stg = setting(name)
        if self.base is None:
            return [mainpath, stg]
        else:
            paths = self.base.GetGamePaths()
            paths.append(stg)
            return paths


    def GetLastLevel(self):
        """
        Returns the last loaded level
        """
        if not self.custom: return setting('LastLevelNSMBUversion')
        name = 'LastLevel_' + self.name
        stg = setting(name)

        # Use the default if there are no settings for this yet
        if stg is None: return setting('LastLevelNSMBUversion')
        else: return stg

    def SetLastLevel(self, path):
        """
        Sets the last loaded level
        """
        if path in (None, 'None', 'none', True, 'True', 'true', False, 'False', 'false', 0, 1, ''): return
        #print('Last loaded level set to ' + str(path))
        if not self.custom: setSetting('LastLevelNSMBUversion', path)
        else:
            name = 'LastLevel_' + self.name
            setSetting(name, path)


    def recursiveFiles(self, name, isPatch=False, folder=False):
        """
        Checks each base of this gamedef and returns a list of successive file paths
        """
        ListToCheckIn = self.files if not folder else self.folders

        # This can be handled 4 ways: if we do or don't have a base, and if we do or don't have a copy of the file.
        if self.base is None:
            if ListToCheckIn[name].path is None: # No base, no file

                if isPatch: return [], True
                else: return []

            else: # No base, file

                alist = []
                alist.append(ListToCheckIn[name].path)
                if isPatch: return alist, ListToCheckIn[name].patch
                else: return alist

        else:

            if isPatch: listUpToNow, wasPatch = self.base.recursiveFiles(name, True, folder)
            else: listUpToNow = self.base.recursiveFiles(name, False, folder)

            if ListToCheckIn[name].path is None: # Base, no file

                if isPatch: return listUpToNow, wasPatch
                else: return listUpToNow

            else: # Base, file

                # If it's a patch, just add it to the end of the list
                if ListToCheckIn[name].patch: listUpToNow.append(ListToCheckIn[name].path)

                # If it's not (it's free-standing), make a new list and start over
                else:
                    newlist = []
                    newlist.append(ListToCheckIn[name].path)
                    if isPatch: return newlist, False
                    else: return newlist

                # Return
                if isPatch: return listUpToNow, wasPatch
                else: return listUpToNow

    def multipleRecursiveFiles(self, *args):
        """
        Returns multiple recursive files in order of least recent to most recent as a list of tuples, one list per gamedef base
        """

        # This should be very simple
        # Each arg should be a file name
        if self.base is None: main = [] # start a new level
        else: main = self.base.multipleRecursiveFiles(*args)

        # Add the values from this level, and then return it
        result = []
        for name in args:
            try:
                file = self.files[name]
                if file.path is None: raise KeyError
                result.append(self.files[name])
            except KeyError: result.append(None)
        main.append(tuple(result))
        return main

    def file(self, name):
        """
        Returns a file by recursively checking successive gamedef bases
        """
        if name not in self.files: return

        if self.files[name].path is not None: return self.files[name].path
        else:
            if self.base is None: return
            return self.base.file(name) # it can recursively check its base, too

    def getImageClasses(self):
        """
        Gets all image classes
        """
        if not self.custom:
            return self.sprites.ImageClasses

        if self.base is not None:
            images = dict(self.base.getImageClasses())
        else:
            images = {}

        if hasattr(self.sprites, 'ImageClasses'):
            images.update(self.sprites.ImageClasses)
        return images

def GetPath(id_):
    """
    Checks the game definition and the translation and returns the appropriate path
    """
    global gamedef
    global trans

    # If there's a custom gamedef, use that
    if gamedef.custom and gamedef.file(id_) is not None: return gamedef.file(id_)
    else: return trans.path(id_)

def getMusic():
    """
    Uses the current gamedef + translation to get the music data, and returns it as a list of tuples
    """

    transsong = trans.files['music']
    gamedefsongs, isPatch = gamedef.recursiveFiles('music', True)
    if isPatch:
        paths = [transsong]
        for path in gamedefsongs: paths.append(path)
    else: paths = gamedefsongs

    songs = []
    for path in paths:
        musicfile = open(path)
        data = musicfile.read()
        musicfile.close()
        del musicfile

        # Split the data
        data = data.split('\n')
        while '' in data: data.remove('')
        for i, line in enumerate(data): data[i] = line.split(':')

        # Apply it
        for songid, name in data:
            found = False
            for song in songs:
                if song[0] == songid:
                    song[1] = name
                    found = True
            if not found:
                songs.append([songid, name])

    return sorted(songs, key=lambda song: int(song[0]))

def FindGameDef(name, skip=None):
    "Helper function to find a game def with a specific name. Skip will be skipped"""
    toSearch = [None] # Add the original game first
    for folder in os.listdir('satorudata/games'): toSearch.append(folder)

    for folder in toSearch:
        if folder == skip: continue
        def_ = SatoruGameDefinition(folder)
        if (not def_.custom) and (folder is not None): continue
        if def_.name == name: return def_

#####################################################################
########################### MAIN FUNCTION ###########################
#####################################################################

class SatoruWindow(QtWidgets.QMainWindow):
    """
    Satoru main level editor window
    """
    ZoomLevel = 100
    actions_ = {}

    def CreateAction(self, shortname, function, icon, text, statustext, shortcut, toggle=False):
        """
        Helper function to create an action
        """

        if icon is not None:
            act = QtWidgets.QAction(icon, text, self)
        else:
            act = QtWidgets.QAction(text, self)

        if shortcut is not None: act.setShortcut(shortcut)
        if statustext is not None: act.setStatusTip(statustext)
        if toggle:
            act.setCheckable(True)
        if function is not None: act.triggered.connect(function)

        self.actions_[shortname] = act

    def __init__(self):
        """
        Editor window constructor
        """
        global Initializing
        Initializing = True

        # Satoru Version number goes below here. 64 char max (32 if non-ascii).
        self.SatoruInfo = SatoruID

        self.ZoomLevels = [7.5, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 85.0, 90.0, 95.0, 100.0, 125.0, 150.0, 175.0, 200.0, 250.0, 300.0, 350.0, 400.0]

        self.AutosaveTimer = QtCore.QTimer()
        self.AutosaveTimer.timeout.connect(self.Autosave)
        self.AutosaveTimer.start(20000)

        # required variables
        self.UpdateFlag = False
        self.SelectionUpdateFlag = False
        self.selObj = None
        self.CurrentSelection = []

        self.CurrentGame = setting('CurrentGame')
        if self.CurrentGame is None: self.CurrentGame = NewSuperMarioBrosU

        # set up the window
        super().__init__(None)
        self.setWindowTitle('Satoru Level Editor')
        self.setWindowIcon(QtGui.QIcon('satorudata/icon.png'))
        self.setIconSize(QtCore.QSize(16, 16))
        self.setUnifiedTitleAndToolBarOnMac(True)

        # create the level view
        self.scene = LevelScene(0, 0, 1024*TileWidth, 512*TileWidth, self)
        self.scene.setItemIndexMethod(QtWidgets.QGraphicsScene.NoIndex)
        self.scene.selectionChanged.connect(self.ChangeSelectionHandler)

        self.view = LevelViewWidget(self.scene, self)
        self.view.centerOn(0,0) # this scrolls to the top left
        self.view.PositionHover.connect(self.PositionHovered)
        self.view.XScrollBar.valueChanged.connect(self.XScrollChange)
        self.view.YScrollBar.valueChanged.connect(self.YScrollChange)
        self.view.FrameSize.connect(self.HandleWindowSizeChange)

        # done creating the window!
        self.setCentralWidget(self.view)

        # set up the clipboard stuff
        self.clipboard = None
        self.systemClipboard = QtWidgets.QApplication.clipboard()
        self.systemClipboard.dataChanged.connect(self.TrackClipboardUpdates)

        # we might have something there already, activate Paste if so
        self.TrackClipboardUpdates()

    def __init2__(self):
        """
        Finishes initialization. (fixes bugs with some widgets calling mainWindow.something before it's fully init'ed)
        """
        # set up actions and menus
        self.SetupActionsAndMenus()

        # set up the status bar
        self.posLabel = QtWidgets.QLabel()
        self.tileCountLabel = QtWidgets.QLabel()
        self.selectionLabel = QtWidgets.QLabel()
        self.hoverLabel = QtWidgets.QLabel()
        self.statusBar().addWidget(self.posLabel)
        self.statusBar().addWidget(self.tileCountLabel)
        self.statusBar().addWidget(self.selectionLabel)
        self.statusBar().addWidget(self.hoverLabel)
        self.ZoomWidget = ZoomWidget()
        self.ZoomStatusWidget = ZoomStatusWidget()
        self.statusBar().addPermanentWidget(self.ZoomWidget)
        self.statusBar().addPermanentWidget(self.ZoomStatusWidget)

        # create the various panels
        self.SetupDocksAndPanels()

        # now get stuff ready
        curgame = self.CurrentGame

        # load first level
        if '-level' in sys.argv:
            index = sys.argv.index('-level')
            try:
                fn = sys.argv[index + 1]
                self.LoadLevel(curgame, fn, True, 1)
            except:
                self.LoadLevel(curgame, FirstLevels[curgame], False, 1)
        else:
            fn = QtWidgets.QFileDialog.getOpenFileName(self, trans.string('FileDlgs', 0), '', FileTypes)[0]
            if fn:
                self.LoadLevel(curgame, fn, True, 1)
            else:
                self.LoadLevel(curgame, FirstLevels[curgame], False, 1)

        QtCore.QTimer.singleShot(100, self.levelOverview.update)

        toggleHandlers = {
            self.HandleSpritesVisibility: SpritesShown,
            self.HandleSpriteImages: SpriteImagesShown,
            self.HandleLocationsVisibility: LocationsShown,
            self.HandleCommentsVisibility: CommentsShown,
            self.HandlePathsVisibility: PathsShown,
        }
        for handler in toggleHandlers:
            handler(toggleHandlers[handler]) # call each toggle-button handler to set each feature correctly upon startup

        # let's restore the state and geometry
        # geometry: determines the main window position
        # state: determines positions of docks
        if settings.contains('MainWindowGeometry'):
            self.restoreGeometry(setting('MainWindowGeometry'))
        if settings.contains('MainWindowState'):
            self.restoreState(setting('MainWindowState'), 0)

        # Load the most recently used gamedef
        LoadGameDef(setting('LastGameDef'), False)

        # Aaaaaand... initializing is done!
        Initializing = False

    def SetupActionsAndMenus(self):
        """
        Sets up Satoru's actions, menus and toolbars
        """

        # File
        self.CreateAction('newlevel', self.HandleNewLevel, GetIcon('new'), trans.string('MenuItems', 0), trans.string('MenuItems', 1), QtGui.QKeySequence.New)
        self.CreateAction('openfromname', self.HandleOpenFromName, GetIcon('open'), trans.string('MenuItems', 2), trans.string('MenuItems', 3), QtGui.QKeySequence.Open)
        self.CreateAction('openfromfile', self.HandleOpenFromFile, GetIcon('openfromfile'), trans.string('MenuItems', 4), trans.string('MenuItems', 5), QtGui.QKeySequence('Ctrl+Shift+O'))
        self.CreateAction('save', self.HandleSave, GetIcon('save'), trans.string('MenuItems', 8), trans.string('MenuItems', 9), QtGui.QKeySequence.Save)
        self.CreateAction('saveas', self.HandleSaveAs, GetIcon('saveas'), trans.string('MenuItems', 10), trans.string('MenuItems', 11), QtGui.QKeySequence.SaveAs)
        self.CreateAction('exportseparately', self.HandleExportSeparately, GetIcon('saveas'), trans.string('MenuItems', 136), trans.string('MenuItems', 137), QtGui.QKeySequence.SaveAs)
        self.CreateAction('metainfo', self.HandleInfo, GetIcon('info'), trans.string('MenuItems', 12), trans.string('MenuItems', 13), QtGui.QKeySequence('Ctrl+Alt+I'))
        self.CreateAction('screenshot', self.HandleScreenshot, GetIcon('screenshot'), trans.string('MenuItems', 14), trans.string('MenuItems', 15), QtGui.QKeySequence('Ctrl+Alt+S'))
        self.CreateAction('changegamepath', self.HandleChangeGamePath, GetIcon('folderpath'), trans.string('MenuItems', 16), trans.string('MenuItems', 17), QtGui.QKeySequence('Ctrl+Alt+G'))
        self.CreateAction('changeonetileset', self.HandleChangeOneTileset, GetIcon('folderpath'), trans.string('MenuItems', 134), trans.string('MenuItems', 135), QtGui.QKeySequence('Ctrl+Alt+Shift+G'))
        self.CreateAction('preferences', self.HandlePreferences, GetIcon('settings'), trans.string('MenuItems', 18), trans.string('MenuItems', 19), QtGui.QKeySequence('Ctrl+Alt+P'))
        self.CreateAction('exit', self.HandleExit, GetIcon('delete'), trans.string('MenuItems', 20), trans.string('MenuItems', 21), QtGui.QKeySequence('Ctrl+Q'))

        # Edit
        self.CreateAction('selectall', self.SelectAll, GetIcon('select'), trans.string('MenuItems', 22), trans.string('MenuItems', 23), QtGui.QKeySequence.SelectAll)
        self.CreateAction('deselect', self.Deselect, GetIcon('deselect'), trans.string('MenuItems', 24), trans.string('MenuItems', 25), QtGui.QKeySequence('Ctrl+D'))
        self.CreateAction('cut', self.Cut, GetIcon('cut'), trans.string('MenuItems', 26), trans.string('MenuItems', 27), QtGui.QKeySequence.Cut)
        self.CreateAction('copy', self.Copy, GetIcon('copy'), trans.string('MenuItems', 28), trans.string('MenuItems', 29), QtGui.QKeySequence.Copy)
        self.CreateAction('paste', self.Paste, GetIcon('paste'), trans.string('MenuItems', 30), trans.string('MenuItems', 31), QtGui.QKeySequence.Paste)
        self.CreateAction('shiftitems', self.ShiftItems, GetIcon('move'), trans.string('MenuItems', 32), trans.string('MenuItems', 33), QtGui.QKeySequence('Ctrl+Shift+S'))
        self.CreateAction('mergelocations', self.MergeLocations, GetIcon('merge'), trans.string('MenuItems', 34), trans.string('MenuItems', 35), QtGui.QKeySequence('Ctrl+Shift+E'))
        self.CreateAction('swapobjectstilesets', self.SwapObjectsTilesets, GetIcon('swap'), trans.string('MenuItems', 104), trans.string('MenuItems', 105), QtGui.QKeySequence('Ctrl+Shift+L'))
        self.CreateAction('swapobjectstypes', self.SwapObjectsTypes, GetIcon('swap'), trans.string('MenuItems', 106), trans.string('MenuItems', 107), QtGui.QKeySequence('Ctrl+Shift+Y'))
        self.CreateAction('freezeobjects', self.HandleObjectsFreeze, GetIcon('objectsfreeze'), trans.string('MenuItems', 38), trans.string('MenuItems', 39), QtGui.QKeySequence('Ctrl+Shift+1'), True)
        self.CreateAction('freezesprites', self.HandleSpritesFreeze, GetIcon('spritesfreeze'), trans.string('MenuItems', 40), trans.string('MenuItems', 41), QtGui.QKeySequence('Ctrl+Shift+2'), True)
        self.CreateAction('freezeentrances', self.HandleEntrancesFreeze, GetIcon('entrancesfreeze'), trans.string('MenuItems', 42), trans.string('MenuItems', 43), QtGui.QKeySequence('Ctrl+Shift+3'), True)
        self.CreateAction('freezelocations', self.HandleLocationsFreeze, GetIcon('locationsfreeze'), trans.string('MenuItems', 44), trans.string('MenuItems', 45), QtGui.QKeySequence('Ctrl+Shift+4'), True)
        self.CreateAction('freezepaths', self.HandlePathsFreeze, GetIcon('pathsfreeze'), trans.string('MenuItems', 46), trans.string('MenuItems', 47), QtGui.QKeySequence('Ctrl+Shift+5'), True)
        self.CreateAction('freezecomments', self.HandleCommentsFreeze, GetIcon('commentsfreeze'), trans.string('MenuItems', 114), trans.string('MenuItems', 115), QtGui.QKeySequence('Ctrl+Shift+9'), True)

        # View
        self.CreateAction('showlay0', self.HandleUpdateLayer0, GetIcon('layer0'), trans.string('MenuItems', 48), trans.string('MenuItems', 49), QtGui.QKeySequence('Ctrl+1'), True)
        self.CreateAction('showlay1', self.HandleUpdateLayer1, GetIcon('layer1'), trans.string('MenuItems', 50), trans.string('MenuItems', 51), QtGui.QKeySequence('Ctrl+2'), True)
        self.CreateAction('showlay2', self.HandleUpdateLayer2, GetIcon('layer2'), trans.string('MenuItems', 52), trans.string('MenuItems', 53), QtGui.QKeySequence('Ctrl+3'), True)
        self.CreateAction('tileanim', self.HandleTilesetAnimToggle, GetIcon('animation'), trans.string('MenuItems', 108), trans.string('MenuItems', 109), QtGui.QKeySequence('Ctrl+7'), True)
        self.CreateAction('collisions', self.HandleCollisionsToggle, GetIcon('collisions'), trans.string('MenuItems', 110), trans.string('MenuItems', 111), QtGui.QKeySequence('Ctrl+8'), True)
        self.CreateAction('depth', self.HandleDepthToggle, GetIcon('depth'), trans.string('MenuItems', 122), trans.string('MenuItems', 123), QtGui.QKeySequence('Ctrl+H'), True)
        self.CreateAction('realview', self.HandleRealViewToggle, GetIcon('realview'), trans.string('MenuItems', 118), trans.string('MenuItems', 119), QtGui.QKeySequence('Ctrl+9'), True)
        self.CreateAction('showsprites', self.HandleSpritesVisibility, GetIcon('sprites'), trans.string('MenuItems', 54), trans.string('MenuItems', 55), QtGui.QKeySequence('Ctrl+4'), True)
        self.CreateAction('showspriteimages', self.HandleSpriteImages, GetIcon('sprites'), trans.string('MenuItems', 56), trans.string('MenuItems', 57), QtGui.QKeySequence('Ctrl+6'), True)
        self.CreateAction('showlocations', self.HandleLocationsVisibility, GetIcon('locations'), trans.string('MenuItems', 58), trans.string('MenuItems', 59), QtGui.QKeySequence('Ctrl+5'), True)
        self.CreateAction('showpaths', self.HandlePathsVisibility, GetIcon('paths'), trans.string('MenuItems', 138), trans.string('MenuItems', 139), QtGui.QKeySequence('Ctrl+*'), True)
        self.CreateAction('showcomments', self.HandleCommentsVisibility, GetIcon('comments'), trans.string('MenuItems', 116), trans.string('MenuItems', 117), QtGui.QKeySequence('Ctrl+0'), True)
        self.CreateAction('fullscreen', self.HandleFullscreen, GetIcon('fullscreen'), trans.string('MenuItems', 126), trans.string('MenuItems', 127), QtGui.QKeySequence('Ctrl+U'), True)
        self.CreateAction('grid', self.HandleSwitchGrid, GetIcon('grid'), trans.string('MenuItems', 60), trans.string('MenuItems', 61), QtGui.QKeySequence('Ctrl+G'), False)
        self.CreateAction('zoommax', self.HandleZoomMax, GetIcon('zoommax'), trans.string('MenuItems', 62), trans.string('MenuItems', 63), QtGui.QKeySequence('Ctrl+PgDown'), False)
        self.CreateAction('zoomin', self.HandleZoomIn, GetIcon('zoomin'), trans.string('MenuItems', 64), trans.string('MenuItems', 65), QtGui.QKeySequence.ZoomIn, False)
        self.CreateAction('zoomactual', self.HandleZoomActual, GetIcon('zoomactual'), trans.string('MenuItems', 66), trans.string('MenuItems', 67), QtGui.QKeySequence('Ctrl+0'), False)
        self.CreateAction('zoomout', self.HandleZoomOut, GetIcon('zoomout'), trans.string('MenuItems', 68), trans.string('MenuItems', 69), QtGui.QKeySequence.ZoomOut, False)
        self.CreateAction('zoommin', self.HandleZoomMin, GetIcon('zoommin'), trans.string('MenuItems', 70), trans.string('MenuItems', 71), QtGui.QKeySequence('Ctrl+PgUp'), False)
        # Show Overview and Show Palette are added later

        # Settings
        self.CreateAction('areaoptions', self.HandleAreaOptions, GetIcon('area'), trans.string('MenuItems', 72), trans.string('MenuItems', 73), QtGui.QKeySequence('Ctrl+Alt+A'))
        self.CreateAction('zones', self.HandleZones, GetIcon('zones'), trans.string('MenuItems', 74), trans.string('MenuItems', 75), QtGui.QKeySequence('Ctrl+Alt+Z'))
        self.CreateAction('backgrounds', self.HandleBG, GetIcon('background'), trans.string('MenuItems', 76), trans.string('MenuItems', 77), QtGui.QKeySequence('Ctrl+Alt+B'))
        self.CreateAction('addarea', self.HandleAddNewArea, GetIcon('add'), trans.string('MenuItems', 78), trans.string('MenuItems', 79), QtGui.QKeySequence('Ctrl+Alt+N'))
        self.CreateAction('importarea', self.HandleImportArea, GetIcon('import'), trans.string('MenuItems', 80), trans.string('MenuItems', 81), QtGui.QKeySequence('Ctrl+Alt+O'))
        self.CreateAction('deletearea', self.HandleDeleteArea, GetIcon('delete'), trans.string('MenuItems', 82), trans.string('MenuItems', 83), QtGui.QKeySequence('Ctrl+Alt+D'))
        self.CreateAction('reloadgfx', self.ReloadTilesets, GetIcon('reload'), trans.string('MenuItems', 84), trans.string('MenuItems', 85), QtGui.QKeySequence('Ctrl+Alt+R'))
        self.CreateAction('reloaddata', self.ReloadSpriteData, GetIcon('reload'), trans.string('MenuItems', 128), trans.string('MenuItems', 129), QtGui.QKeySequence('Ctrl+Shift+R'))

        # Help
        self.CreateAction('infobox', self.AboutBox, GetIcon('satoru'), trans.string('MenuItems', 86), trans.string('MenuItems', 87), QtGui.QKeySequence('Ctrl+Shift+I'))
        self.CreateAction('helpbox', self.HelpBox, GetIcon('contents'), trans.string('MenuItems', 88), trans.string('MenuItems', 89), QtGui.QKeySequence('Ctrl+Shift+H'))
        self.CreateAction('tipbox', self.TipBox, GetIcon('tips'), trans.string('MenuItems', 90), trans.string('MenuItems', 91), QtGui.QKeySequence('Ctrl+Shift+T'))
        self.CreateAction('update', self.UpdateCheck, GetIcon('download'), trans.string('MenuItems', 120), trans.string('MenuItems', 121), QtGui.QKeySequence('Ctrl+Shift+U'))
        self.CreateAction('aboutqt', QtWidgets.qApp.aboutQt, GetIcon('qt'), trans.string('MenuItems', 92), trans.string('MenuItems', 93), QtGui.QKeySequence('Ctrl+Shift+Q'))


        # Configure them
        self.actions_['collisions'].setChecked(CollisionsShown)
        self.actions_['depth'].setChecked(DepthShown)
        self.actions_['realview'].setChecked(RealViewEnabled)

        self.actions_['showsprites'].setChecked(SpritesShown)
        self.actions_['showspriteimages'].setChecked(SpriteImagesShown)
        self.actions_['showlocations'].setChecked(LocationsShown)
        self.actions_['showcomments'].setChecked(CommentsShown)
        self.actions_['showpaths'].setChecked(PathsShown)

        self.actions_['freezeobjects'].setChecked(ObjectsFrozen)
        self.actions_['freezesprites'].setChecked(SpritesFrozen)
        self.actions_['freezeentrances'].setChecked(EntrancesFrozen)
        self.actions_['freezelocations'].setChecked(LocationsFrozen)
        self.actions_['freezepaths'].setChecked(PathsFrozen)
        self.actions_['freezecomments'].setChecked(CommentsFrozen)

        self.actions_['cut'].setEnabled(False)
        self.actions_['copy'].setEnabled(False)
        self.actions_['paste'].setEnabled(False)
        self.actions_['shiftitems'].setEnabled(False)
        self.actions_['mergelocations'].setEnabled(False)
        self.actions_['deselect'].setEnabled(False)


        ####
        menubar = QtWidgets.QMenuBar()
        self.setMenuBar(menubar)


        fmenu = menubar.addMenu(trans.string('Menubar', 0))
        fmenu.addAction(self.actions_['newlevel'])
        fmenu.addAction(self.actions_['openfromname'])
        fmenu.addAction(self.actions_['openfromfile'])
        fmenu.addSeparator()
        fmenu.addAction(self.actions_['save'])
        fmenu.addAction(self.actions_['saveas'])
        fmenu.addAction(self.actions_['exportseparately'])
        fmenu.addAction(self.actions_['metainfo'])
        fmenu.addSeparator()
        fmenu.addAction(self.actions_['screenshot'])
        fmenu.addAction(self.actions_['changegamepath'])
        fmenu.addAction(self.actions_['changeonetileset'])
        fmenu.addAction(self.actions_['preferences'])
        fmenu.addSeparator()
        fmenu.addAction(self.actions_['exit'])

        emenu = menubar.addMenu(trans.string('Menubar', 1))
        emenu.addAction(self.actions_['selectall'])
        emenu.addAction(self.actions_['deselect'])
        emenu.addSeparator()
        emenu.addAction(self.actions_['cut'])
        emenu.addAction(self.actions_['copy'])
        emenu.addAction(self.actions_['paste'])
        emenu.addSeparator()
        emenu.addAction(self.actions_['shiftitems'])
        emenu.addAction(self.actions_['mergelocations'])
        emenu.addAction(self.actions_['swapobjectstilesets'])
        emenu.addAction(self.actions_['swapobjectstypes'])
        emenu.addSeparator()
        emenu.addAction(self.actions_['freezeobjects'])
        emenu.addAction(self.actions_['freezesprites'])
        emenu.addAction(self.actions_['freezeentrances'])
        emenu.addAction(self.actions_['freezelocations'])
        emenu.addAction(self.actions_['freezepaths'])
        emenu.addAction(self.actions_['freezecomments'])

        vmenu = menubar.addMenu(trans.string('Menubar', 2))
        vmenu.addAction(self.actions_['showlay0'])
        vmenu.addAction(self.actions_['showlay1'])
        vmenu.addAction(self.actions_['showlay2'])
        vmenu.addAction(self.actions_['tileanim'])
        vmenu.addAction(self.actions_['collisions'])
        vmenu.addAction(self.actions_['depth'])
        vmenu.addAction(self.actions_['realview'])
        vmenu.addSeparator()
        vmenu.addAction(self.actions_['showsprites'])
        vmenu.addAction(self.actions_['showspriteimages'])
        vmenu.addAction(self.actions_['showlocations'])
        vmenu.addAction(self.actions_['showcomments'])
        vmenu.addAction(self.actions_['showpaths'])
        vmenu.addSeparator()
        vmenu.addAction(self.actions_['fullscreen'])
        vmenu.addAction(self.actions_['grid'])
        vmenu.addSeparator()
        vmenu.addAction(self.actions_['zoommax'])
        vmenu.addAction(self.actions_['zoomin'])
        vmenu.addAction(self.actions_['zoomactual'])
        vmenu.addAction(self.actions_['zoomout'])
        vmenu.addAction(self.actions_['zoommin'])
        vmenu.addSeparator()
        # self.levelOverviewDock.toggleViewAction() is added here later
        # so we assign it to self.vmenu
        self.vmenu = vmenu

        lmenu = menubar.addMenu(trans.string('Menubar', 3))
        lmenu.addAction(self.actions_['areaoptions'])
        lmenu.addAction(self.actions_['zones'])
        lmenu.addAction(self.actions_['backgrounds'])
        lmenu.addSeparator()
        lmenu.addAction(self.actions_['addarea'])
        lmenu.addAction(self.actions_['importarea'])
        lmenu.addAction(self.actions_['deletearea'])
        lmenu.addSeparator()
        lmenu.addAction(self.actions_['reloadgfx'])
        lmenu.addAction(self.actions_['reloaddata'])

        hmenu = menubar.addMenu(trans.string('Menubar', 4))
        hmenu.addAction(self.actions_['infobox'])
        hmenu.addAction(self.actions_['helpbox'])
        hmenu.addAction(self.actions_['tipbox'])
        hmenu.addSeparator()
        hmenu.addAction(self.actions_['update'])
        hmenu.addSeparator()
        hmenu.addAction(self.actions_['aboutqt'])

        # create a toolbar
        self.toolbar = self.addToolBar(trans.string('Menubar', 5))
        self.toolbar.setObjectName('MainToolbar')

        # Add buttons to the toolbar
        self.addToolbarButtons()

        # Add the area combo box
        self.areaComboBox = QtWidgets.QComboBox()
        self.areaComboBox.activated.connect(self.HandleSwitchArea)
        self.toolbar.addWidget(self.areaComboBox)

    def addToolbarButtons(self):
        """
        Reads from the Preferences file and adds the appropriate options to the toolbar
        """
        global FileActions
        global EditActions
        global ViewActions
        global SettingsActions
        global HelpActions

        # First, define groups. Each group is isolated by separators.
        Groups = (
            (
                'newlevel',
                'openfromname',
                'openfromfile',
                'openrecent',
                'save',
                'saveas',
                'exportseparately',
                'metainfo',
                'screenshot',
                'changegamepath',
                'changeonetileset',
                'preferences',
                'exit',
            ), (
                'selectall',
                'deselect',
            ), (
                'cut',
                'copy',
                'paste',
            ), (
                'shiftitems',
                'mergelocations',
            ), (
                'freezeobjects',
                'freezesprites',
                'freezeentrances',
                'freezelocations',
                'freezepaths',
            ), (
                'zoommax',
                'zoomin',
                'zoomactual',
                'zoomout',
                'zoommin',
            ), (
                'grid',
            ), (
                'showlay0',
                'showlay1',
                'showlay2',
            ), (
                'showsprites',
                'showspriteimages',
                'showlocations',
            ), (
                'areaoptions',
                'zones',
                'backgrounds',
            ), (
                'addarea',
                'importarea',
                'deletearea',
            ), (
                'reloadgfx',
                'reloaddata',
            ), (
                'infobox',
                'helpbox',
                'tipbox',
                'aboutqt',
            ),
        )

        # Determine which keys are activated
        if setting('ToolbarActs') in (None, 'None', 'none', '', 0):
            # Get the default settings
            toggled = {}
            for List in (FileActions, EditActions, ViewActions, SettingsActions, HelpActions):
                for name, activated, key in List:
                    toggled[key] = activated
        else: # Get the registry settings
            toggled = setting('ToolbarActs')
            newToggled = {} # here, I'm replacing QStrings w/ python strings
            for key in toggled:
                newToggled[str(key)] = toggled[key]
            toggled = newToggled

        # Add each to the toolbar if toggled[key]
        for group in Groups:
            addedButtons = False
            for key in group:
                if key in toggled and toggled[key] and key != 'save':
                    act = self.actions_[key]
                    self.toolbar.addAction(act)
                    addedButtons = True
            if addedButtons:
                self.toolbar.addSeparator()

    def SetupDocksAndPanels(self):
        """
        Sets up the dock widgets and panels
        """
        # level overview
        dock = QtWidgets.QDockWidget(trans.string('MenuItems', 94), self)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetClosable)
        #dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setObjectName('leveloverview') # needed for the state to save/restore correctly

        self.levelOverview = LevelOverviewWidget()
        self.levelOverview.moveIt.connect(self.HandleOverviewClick)
        self.levelOverviewDock = dock
        dock.setWidget(self.levelOverview)

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setVisible(True)
        act = dock.toggleViewAction()
        act.setShortcut(QtGui.QKeySequence('Ctrl+M'))
        act.setIcon(GetIcon('overview'))
        act.setStatusTip(trans.string('MenuItems', 95))
        self.vmenu.addAction(act)

        # create the sprite editor panel
        dock = QtWidgets.QDockWidget(trans.string('SpriteDataEditor', 0), self)
        dock.setVisible(False)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setObjectName('spriteeditor') #needed for the state to save/restore correctly

        self.spriteDataEditor = SpriteEditorWidget()
        self.spriteDataEditor.DataUpdate.connect(self.SpriteDataUpdated)
        dock.setWidget(self.spriteDataEditor)
        self.spriteEditorDock = dock

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)

        # create the entrance editor panel
        dock = QtWidgets.QDockWidget(trans.string('EntranceDataEditor', 24), self)
        dock.setVisible(False)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setObjectName('entranceeditor') #needed for the state to save/restore correctly

        self.entranceEditor = EntranceEditorWidget()
        dock.setWidget(self.entranceEditor)
        self.entranceEditorDock = dock

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)

        # create the path node editor panel
        dock = QtWidgets.QDockWidget(trans.string('PathDataEditor', 10), self)
        dock.setVisible(False)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setObjectName('pathnodeeditor') #needed for the state to save/restore correctly

        self.pathEditor = PathNodeEditorWidget()
        dock.setWidget(self.pathEditor)
        self.pathEditorDock = dock

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)

        # create the object editor panel
        dock = QtWidgets.QDockWidget('Modify Selected Object Properties', self)
        dock.setVisible(False)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setObjectName('objectdataeditor') #needed for the state to save/restore correctly

        self.objectEditor = ObjectDataEditorWidget(self)
        dock.setWidget(self.objectEditor)
        self.objectEditorDock = dock

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)

        # create the location editor panel
        dock = QtWidgets.QDockWidget(trans.string('LocationDataEditor', 12), self)
        dock.setVisible(False)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setObjectName('locationeditor') #needed for the state to save/restore correctly

        self.locationEditor = LocationEditorWidget()
        dock.setWidget(self.locationEditor)
        self.locationEditorDock = dock

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)

        # create the island generator panel
        dock = QtWidgets.QDockWidget(trans.string('MenuItems', 100), self)
        dock.setVisible(False)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetClosable)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setObjectName('islandgenerator') #needed for the state to save/restore correctly

        self.islandGen = IslandGeneratorWidget()
        dock.setWidget(self.islandGen)
        self.islandGenDock = dock

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)
        act = dock.toggleViewAction()
        act.setShortcut(QtGui.QKeySequence('Ctrl+I'))
        act.setIcon(GetIcon('islandgen'))
        act.setToolTip(trans.string('MenuItems', 101))
        self.vmenu.addAction(act)

        # create the palette
        dock = QtWidgets.QDockWidget(trans.string('MenuItems', 96), self)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetClosable)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setObjectName('palette') #needed for the state to save/restore correctly

        self.creationDock = dock
        act = dock.toggleViewAction()
        act.setShortcut(QtGui.QKeySequence('Ctrl+P'))
        act.setIcon(GetIcon('palette'))
        act.setStatusTip(trans.string('MenuItems', 97))
        self.vmenu.addAction(act)

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setVisible(True)


        # add tabs to it
        tabs = QtWidgets.QTabWidget()
        tabs.setIconSize(QtCore.QSize(16, 16))
        tabs.currentChanged.connect(self.CreationTabChanged)
        dock.setWidget(tabs)
        self.creationTabs = tabs

        # object choosing tabs
        tsicon = GetIcon('objects')

        self.objMetaTab = QtWidgets.QTabBar()
        self.objMetaTab.currentChanged.connect(self.ObjTabChanged)

        self.objMetaTab.addTab(tsicon, 'Main')
        self.objMetaTab.addTab(tsicon, 'OneTileset')
        self.objMetaTab.addTab(tsicon, 'Embedded')

        objMetaWidget = QtWidgets.QWidget()
        tabs.addTab(objMetaWidget, tsicon, '')
        tabs.setTabToolTip(0, trans.string('Palette', 13))

        oel = QtWidgets.QVBoxLayout(objMetaWidget)
        oel.addWidget(self.objMetaTab)

        ll = QtWidgets.QHBoxLayout()
        self.objUseLayer0 = QtWidgets.QRadioButton('0')
        self.objUseLayer0.setToolTip(trans.string('Palette', 1))
        self.objUseLayer1 = QtWidgets.QRadioButton('1')
        self.objUseLayer1.setToolTip(trans.string('Palette', 2))
        self.objUseLayer2 = QtWidgets.QRadioButton('2')
        self.objUseLayer2.setToolTip(trans.string('Palette', 3))
        ll.addWidget(QtWidgets.QLabel(trans.string('Palette', 0)))
        ll.addWidget(self.objUseLayer0)
        ll.addWidget(self.objUseLayer1)
        ll.addWidget(self.objUseLayer2)
        ll.addStretch(1)
        oel.addLayout(ll)

        lbg = QtWidgets.QButtonGroup(self)
        lbg.addButton(self.objUseLayer0, 0)
        lbg.addButton(self.objUseLayer1, 1)
        lbg.addButton(self.objUseLayer2, 2)
        lbg.buttonClicked[int].connect(self.LayerChoiceChanged)
        self.LayerButtonGroup = lbg

        self.objPicker = ObjectPickerWidget(self, self.EmbeddedObjectDeleteRequest)
        self.objPicker.ObjChanged.connect(self.ObjectChoiceChanged)
        self.objPicker.ObjReplace.connect(self.ObjectReplace)
        self.objPicker.EmbeddedObjUpdate.connect(self.EmbeddedObjectUpdate)
        self.objPicker.EmbeddedObjDelete.connect(self.EmbeddedObjectDelete)
        oel.addWidget(self.objPicker, 1)

        # sprite tab
        self.sprAllTab = QtWidgets.QTabWidget()
        self.sprAllTab.currentChanged.connect(self.SprTabChanged)
        tabs.addTab(self.sprAllTab, GetIcon('sprites'), '')
        tabs.setTabToolTip(1, trans.string('Palette', 14))

        # sprite tab: add
        self.sprPickerTab = QtWidgets.QWidget()
        self.sprAllTab.addTab(self.sprPickerTab, GetIcon('spritesadd'), trans.string('Palette', 25))

        spl = QtWidgets.QVBoxLayout(self.sprPickerTab)
        self.sprPickerLayout = spl

        svpl = QtWidgets.QHBoxLayout()
        svpl.addWidget(QtWidgets.QLabel(trans.string('Palette', 4)))

        sspl = QtWidgets.QHBoxLayout()
        sspl.addWidget(QtWidgets.QLabel(trans.string('Palette', 5)))

        LoadSpriteCategories()
        viewpicker = QtWidgets.QComboBox()
        for view in SpriteCategories:
            viewpicker.addItem(view[0])
        viewpicker.currentIndexChanged.connect(self.SelectNewSpriteView)

        self.spriteViewPicker = viewpicker
        svpl.addWidget(viewpicker, 1)

        self.spriteSearchTerm = QtWidgets.QLineEdit()
        self.spriteSearchTerm.textChanged.connect(self.NewSearchTerm)
        sspl.addWidget(self.spriteSearchTerm, 1)

        spl.addLayout(svpl)
        spl.addLayout(sspl)

        self.spriteSearchLayout = sspl
        sspl.itemAt(0).widget().setVisible(False)
        sspl.itemAt(1).widget().setVisible(False)

        self.sprPicker = SpritePickerWidget()
        self.sprPicker.SpriteChanged.connect(self.SpriteChoiceChanged)
        self.sprPicker.SpriteReplace.connect(self.SpriteReplace)
        self.sprPicker.SwitchView(SpriteCategories[0])
        spl.addWidget(self.sprPicker, 1)

        self.defaultPropButton = QtWidgets.QPushButton(trans.string('Palette', 6))
        self.defaultPropButton.setEnabled(False)
        self.defaultPropButton.clicked.connect(self.ShowDefaultProps)

        sdpl = QtWidgets.QHBoxLayout()
        sdpl.addStretch(1)
        sdpl.addWidget(self.defaultPropButton)
        sdpl.addStretch(1)
        spl.addLayout(sdpl)

        # default sprite data editor
        ddock = QtWidgets.QDockWidget(trans.string('Palette', 7), self)
        ddock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetClosable)
        ddock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        ddock.setObjectName('defaultprops') #needed for the state to save/restore correctly

        self.defaultDataEditor = SpriteEditorWidget(True)
        self.defaultDataEditor.setVisible(False)
        ddock.setWidget(self.defaultDataEditor)

        self.addDockWidget(Qt.RightDockWidgetArea, ddock)
        ddock.setVisible(False)
        ddock.setFloating(True)
        self.defaultPropDock = ddock

        # sprite tab: current
        self.sprEditorTab = QtWidgets.QWidget()
        self.sprAllTab.addTab(self.sprEditorTab, GetIcon('spritelist'), trans.string('Palette', 26))

        spel = QtWidgets.QVBoxLayout(self.sprEditorTab)
        self.sprEditorLayout = spel

        slabel = QtWidgets.QLabel(trans.string('Palette', 11))
        slabel.setWordWrap(True)
        self.spriteList = ListWidgetWithToolTipSignal()
        self.spriteList.itemActivated.connect(self.HandleSpriteSelectByList)
        self.spriteList.toolTipAboutToShow.connect(self.HandleSpriteToolTipAboutToShow)
        self.spriteList.setSortingEnabled(True)

        spel.addWidget(slabel)
        spel.addWidget(self.spriteList)

        # entrance tab
        self.entEditorTab = QtWidgets.QWidget()
        tabs.addTab(self.entEditorTab, GetIcon('entrances'), '')
        tabs.setTabToolTip(2, trans.string('Palette', 15))

        eel = QtWidgets.QVBoxLayout(self.entEditorTab)
        self.entEditorLayout = eel

        elabel = QtWidgets.QLabel(trans.string('Palette', 8))
        elabel.setWordWrap(True)
        self.entranceList = ListWidgetWithToolTipSignal()
        self.entranceList.itemActivated.connect(self.HandleEntranceSelectByList)
        self.entranceList.toolTipAboutToShow.connect(self.HandleEntranceToolTipAboutToShow)
        self.entranceList.setSortingEnabled(True)

        eel.addWidget(elabel)
        eel.addWidget(self.entranceList)

        # locations tab
        self.locEditorTab = QtWidgets.QWidget()
        tabs.addTab(self.locEditorTab, GetIcon('locations'), '')
        tabs.setTabToolTip(3, trans.string('Palette', 16))

        locL = QtWidgets.QVBoxLayout(self.locEditorTab)
        self.locEditorLayout = locL

        Llabel = QtWidgets.QLabel(trans.string('Palette', 12))
        Llabel.setWordWrap(True)
        self.locationList = ListWidgetWithToolTipSignal()
        self.locationList.itemActivated.connect(self.HandleLocationSelectByList)
        self.locationList.toolTipAboutToShow.connect(self.HandleLocationToolTipAboutToShow)
        self.locationList.setSortingEnabled(True)

        locL.addWidget(Llabel)
        locL.addWidget(self.locationList)

        # paths tab
        self.pathEditorTab = QtWidgets.QWidget()
        tabs.addTab(self.pathEditorTab, GetIcon('paths'), '')
        tabs.setTabToolTip(4, trans.string('Palette', 17))

        pathel = QtWidgets.QVBoxLayout(self.pathEditorTab)
        self.pathEditorLayout = pathel

        pathlabel = QtWidgets.QLabel(trans.string('Palette', 9))
        pathlabel.setWordWrap(True)
        deselectbtn = QtWidgets.QPushButton(trans.string('Palette', 10))
        deselectbtn.clicked.connect(self.DeselectPathSelection)
        self.pathList = ListWidgetWithToolTipSignal()
        self.pathList.itemActivated.connect(self.HandlePathSelectByList)
        self.pathList.toolTipAboutToShow.connect(self.HandlePathToolTipAboutToShow)
        self.pathList.setSortingEnabled(True)

        pathel.addWidget(pathlabel)
        pathel.addWidget(deselectbtn)
        pathel.addWidget(self.pathList)

        # events tab
        self.eventEditorTab = QtWidgets.QWidget()
        tabs.addTab(self.eventEditorTab, GetIcon('events'), '')
        tabs.setTabToolTip(6, trans.string('Palette', 18))
        tabs.setTabEnabled(6, False)

        eventel = QtWidgets.QGridLayout(self.eventEditorTab)
        self.eventEditorLayout = eventel

        eventlabel = QtWidgets.QLabel(trans.string('Palette', 20))
        eventNotesLabel = QtWidgets.QLabel(trans.string('Palette', 21))
        self.eventNotesEditor = QtWidgets.QLineEdit()
        self.eventNotesEditor.textEdited.connect(self.handleEventNotesEdit)

        self.eventChooser = QtWidgets.QTreeWidget()
        self.eventChooser.setColumnCount(2)
        self.eventChooser.setHeaderLabels((trans.string('Palette', 22), trans.string('Palette', 23)))
        self.eventChooser.itemClicked.connect(self.handleEventTabItemClick)
        self.eventChooserItems = []
        flags = Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        for id in range(32):
            itm = QtWidgets.QTreeWidgetItem()
            itm.setFlags(flags)
            itm.setCheckState(0, Qt.Unchecked)
            itm.setText(0, trans.string('Palette', 24, '[id]', str(id+1)))
            itm.setText(1, '')
            self.eventChooser.addTopLevelItem(itm)
            self.eventChooserItems.append(itm)
            if id == 0: itm.setSelected(True)

        eventel.addWidget(eventlabel, 0, 0, 1, 2)
        eventel.addWidget(eventNotesLabel, 1, 0)
        eventel.addWidget(self.eventNotesEditor, 1, 1)
        eventel.addWidget(self.eventChooser, 2, 0, 1, 2)

        # stamps tab
        self.stampTab = QtWidgets.QWidget()
        tabs.addTab(self.stampTab, GetIcon('stamp'), '')
        tabs.setTabToolTip(7, trans.string('Palette', 19))

        stampLabel = QtWidgets.QLabel(trans.string('Palette', 27))

        stampAddBtn = QtWidgets.QPushButton(trans.string('Palette', 28))
        stampAddBtn.clicked.connect(self.handleStampsAdd)
        stampAddBtn.setEnabled(False)
        self.stampAddBtn = stampAddBtn # so we can enable/disable it later
        stampRemoveBtn = QtWidgets.QPushButton(trans.string('Palette', 29))
        stampRemoveBtn.clicked.connect(self.handleStampsRemove)
        stampRemoveBtn.setEnabled(False)
        self.stampRemoveBtn = stampRemoveBtn # so we can enable/disable it later

        menu = QtWidgets.QMenu()
        menu.addAction(trans.string('Palette', 31), self.handleStampsOpen, 0) # Open Set...
        menu.addAction(trans.string('Palette', 32), self.handleStampsSave, 0) # Save Set As...
        stampToolsBtn = QtWidgets.QToolButton()
        stampToolsBtn.setText(trans.string('Palette', 30))
        stampToolsBtn.setMenu(menu)
        stampToolsBtn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        stampToolsBtn.setSizePolicy(stampAddBtn.sizePolicy())
        stampToolsBtn.setMinimumHeight(stampAddBtn.height() / 20)

        stampNameLabel = QtWidgets.QLabel(trans.string('Palette', 35))
        self.stampNameEdit = QtWidgets.QLineEdit()
        self.stampNameEdit.setEnabled(False)
        self.stampNameEdit.textChanged.connect(self.handleStampNameEdited)

        nameLayout = QtWidgets.QHBoxLayout()
        nameLayout.addWidget(stampNameLabel)
        nameLayout.addWidget(self.stampNameEdit)

        self.stampChooser = StampChooserWidget()
        self.stampChooser.selectionChangedSignal.connect(self.handleStampSelectionChanged)

        stampL = QtWidgets.QGridLayout()
        stampL.addWidget(stampLabel, 0, 0, 1, 3)
        stampL.addWidget(stampAddBtn, 1, 0)
        stampL.addWidget(stampRemoveBtn, 1, 1)
        stampL.addWidget(stampToolsBtn, 1, 2)
        stampL.addLayout(nameLayout, 2, 0, 1, 3)
        stampL.addWidget(self.stampChooser, 3, 0, 1, 3)
        self.stampTab.setLayout(stampL)

        # comments tab
        self.commentsTab = QtWidgets.QWidget()
        tabs.addTab(self.commentsTab, GetIcon('comments'), '')
        tabs.setTabToolTip(8, trans.string('Palette', 33))

        cel = QtWidgets.QVBoxLayout()
        self.commentsTab.setLayout(cel)
        self.entEditorLayout = cel

        clabel = QtWidgets.QLabel(trans.string('Palette', 34))
        clabel.setWordWrap(True)

        self.commentList = ListWidgetWithToolTipSignal()
        self.commentList.itemActivated.connect(self.HandleCommentSelectByList)
        self.commentList.toolTipAboutToShow.connect(self.HandleCommentToolTipAboutToShow)
        self.commentList.setSortingEnabled(True)

        cel.addWidget(clabel)
        cel.addWidget(self.commentList)

        # Set the current tab to the Object tab
        self.CreationTabChanged(0)

    def DeselectPathSelection(self, checked):
        """
        Deselects selected path nodes in the list
        """
        for selecteditem in self.pathList.selectedItems():
            selecteditem.setSelected(False)

    def Autosave(self):
        """
        Auto saves the level
        """
        return
        global AutoSaveDirty
        if not AutoSaveDirty: return

        name = self.getInnerSarcName()
        if "-" not in name:
            print('HEY THERE IS NO -, THIS WILL NOT WORK!')

        data = Level.save(name)
        setSetting('AutoSaveFilePath', self.fileSavePath)
        setSetting('AutoSaveFileData', QtCore.QByteArray(data))
        AutoSaveDirty = False

    def TrackClipboardUpdates(self):
        """
        Catches systemwide clipboard updates
        """
        if Initializing: return
        clip = self.systemClipboard.text()
        if clip is not None and clip != '':
            clip = str(clip).strip()

            if clip.startswith('SatoruClip|') and clip.endswith('|%'):
                self.clipboard = clip.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
                self.actions_['paste'].setEnabled(True)
            else:
                self.clipboard = None
                self.actions_['paste'].setEnabled(False)

    def XScrollChange(self, pos):
        """
        Moves the Overview current position box based on X scroll bar value
        """
        self.levelOverview.Xposlocator = pos
        self.levelOverview.update()

    def YScrollChange(self, pos):
        """
        Moves the Overview current position box based on Y scroll bar value
        """
        self.levelOverview.Yposlocator = pos
        self.levelOverview.update()

    def HandleWindowSizeChange(self, w, h):
        self.levelOverview.Hlocator = h
        self.levelOverview.Wlocator = w
        self.levelOverview.update()

    def UpdateTitle(self):
        """
        Sets the window title accordingly
        """
        self.setWindowTitle('Satoru Level Editor - %s%s' % (self.fileTitle, (' ' + trans.string('MainWindow', 0)) if Dirty else ''))

    def CheckDirty(self):
        """
        Checks if the level is unsaved and asks for a confirmation if so - if it returns True, Cancel was picked
        """
        if not Dirty: return False

        msg = QtWidgets.QMessageBox()
        msg.setText(trans.string('AutoSaveDlg', 2))
        msg.setInformativeText(trans.string('AutoSaveDlg', 3))
        msg.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
        msg.setDefaultButton(QtWidgets.QMessageBox.Save)
        ret = msg.exec_()

        if ret == QtWidgets.QMessageBox.Save:
            if not self.HandleSave():
                # save failed
                return True
            return False
        elif ret == QtWidgets.QMessageBox.Discard:
            return False
        elif ret == QtWidgets.QMessageBox.Cancel:
            return True

    def LoadEventTabFromLevel(self):
        """
        Configures the Events tab from the data in Area.defEvents
        """
        defEvents = Area.defEvents
        checked = Qt.Checked
        unchecked = Qt.Unchecked

        data = Area.Metadata.binData('EventNotes_A%d' % Area.areanum)
        eventTexts = {}
        if data is not None:
            # Iterate through the data
            idx = 0
            while idx < len(data):
                eventId = data[idx]
                idx += 1
                rawStrLen = data[idx:idx+4]
                idx += 4
                strLen = (rawStrLen[0] << 24) | (rawStrLen[1] << 16) | (rawStrLen[2] << 8) | rawStrLen[3]
                rawStr = data[idx:idx+strLen]
                idx += strLen
                newStr = ''
                for char in rawStr: newStr += chr(char)
                eventTexts[eventId] = newStr

        for id in range(32):
            item = self.eventChooserItems[id]
            value = 1 << id
            item.setCheckState(0, checked if (defEvents & value) != 0 else unchecked)
            if id in eventTexts: item.setText(1, eventTexts[id])
            else: item.setText(1, '')
            item.setSelected(False)

        self.eventChooserItems[0].setSelected(True)
        txt0 = ''
        if 0 in eventTexts: txt0 = eventTexts[0]
        self.eventNotesEditor.setText(txt0)

    def handleEventTabItemClick(self, item):
        """
        Handles an item being clicked in the Events tab
        """
        noteText = item.text(1)
        self.eventNotesEditor.setText(noteText)
        selIdx = self.eventChooserItems.index(item)
        if item.checkState(0):
            # Turn a bit on
            Area.defEvents |= 1 << selIdx
        else:
            # Turn a bit off (invert, turn on, invert)
            Area.defEvents = ~Area.defEvents
            Area.defEvents |= 1 << selIdx
            Area.defEvents = ~Area.defEvents

    def handleEventNotesEdit(self):
        """
        Handles the text within self.eventNotesEditor changing
        """
        newText = self.eventNotesEditor.text()

        # Set the text to the event chooser
        currentItem = self.eventChooser.selectedItems()[0]
        currentItem.setText(1, newText)
        selIdx = self.eventChooserItems.index(currentItem)

        # Save all the events to the metadata
        data = []
        for id in range(32):
            idtext = str(self.eventChooserItems[id].text(1))
            if idtext == '': continue

            # Add the ID
            data.append(id)

            # Add the string length
            strlen = len(idtext)
            data.append(strlen >> 24)
            data.append((strlen >> 16) & 0xFF)
            data.append((strlen >> 8) & 0xFF)
            data.append(strlen & 0xFF)

            # Add the string
            for char in idtext: data.append(ord(char))

        Area.Metadata.setBinData('EventNotes_A%d' % Area.areanum, data)
        SetDirty()

    def handleStampsAdd(self):
        """
        Handles the "Add Stamp" btn being clicked
        """
        # Create a SatoruClip
        selitems = self.scene.selectedItems()
        if len(selitems) == 0: return
        clipboard_o = []
        clipboard_s = []
        ii = isinstance
        type_obj = ObjectItem
        type_spr = SpriteItem
        for obj in selitems:
            if ii(obj, type_obj):
                clipboard_o.append(obj)
            elif ii(obj, type_spr):
                clipboard_s.append(obj)
        RegClp = self.encodeObjects(clipboard_o, clipboard_s)

        # Create a Stamp
        self.stampChooser.addStamp(Stamp(RegClp, 'New Stamp'))

    def handleStampsRemove(self):
        """
        Handles the "Remove Stamp" btn being clicked
        """
        self.stampChooser.removeStamp(self.stampChooser.currentlySelectedStamp())

    def handleStampsOpen(self):
        """
        Handles the "Open Set..." btn being clicked
        """
        filetypes = ''
        filetypes += trans.string('FileDlgs', 7) + ' (*.stamps);;' # *.stamps
        filetypes += trans.string('FileDlgs', 2) + ' (*)' # *
        fn = QtWidgets.QFileDialog.getOpenFileName(self, trans.string('FileDlgs', 6), '', filetypes)[0]
        if fn == '': return

        stamps = []

        with open(fn, 'r', encoding='utf-8') as file:
            filedata = file.read()

            if not filedata.startswith('stamps\n------\n'): return

            filesplit = filedata.split('\n')[3:]
            i = 0
            while i < len(filesplit):
                try:
                    # Get data
                    name = filesplit[i]
                    rc = filesplit[i + 1]

                    # Increment the line counter by 3, tp
                    # account for the blank line
                    i += 3

                except IndexError:
                    # Meh. Malformed stamps file.
                    i += 9999 # avoid infinite loops
                    continue

                stamps.append(Stamp(rc, name))

        for stamp in stamps: self.stampChooser.addStamp(stamp)

    def handleStampsSave(self):
        """
        Handles the "Save Set As..." btn being clicked
        """
        filetypes = ''
        filetypes += trans.string('FileDlgs', 7) + ' (*.stamps);;' # *.stamps
        filetypes += trans.string('FileDlgs', 2) + ' (*)' # *
        fn = QtWidgets.QFileDialog.getSaveFileName(self, trans.string('FileDlgs', 3), '', filetypes)[0]
        if fn == '': return

        newdata = ''
        newdata += 'stamps\n'
        newdata += '------\n'

        for stampobj in self.stampChooser.model.items:
            name = stampobj.Name
            rc = stampobj.SatoruClip
            newdata += '\n'
            newdata += stampobj.Name + '\n'
            newdata += stampobj.SatoruClip + '\n'

        with open(fn, 'w', encoding='utf-8') as f:
            f.write(newdata)

    def handleStampSelectionChanged(self):
        """
        Called when the stamp selection is changed
        """
        newStamp = self.stampChooser.currentlySelectedStamp()
        stampSelected = newStamp is not None
        self.stampRemoveBtn.setEnabled(stampSelected)
        self.stampNameEdit.setEnabled(stampSelected)

        newName = '' if not stampSelected else newStamp.Name
        self.stampNameEdit.setText(newName)

    def handleStampNameEdited(self):
        """
        Called when the user edits the name of the current stamp
        """
        stamp = self.stampChooser.currentlySelectedStamp()
        text = self.stampNameEdit.text()
        stamp.Name = text
        stamp.update()

        # Try to get it to update!!! But fail. D:
        for i in range(3):
            self.stampChooser.updateGeometries()
            self.stampChooser.update(self.stampChooser.currentIndex())
            self.stampChooser.update()
            self.stampChooser.repaint()

    def AboutBox(self):
        """
        Shows the about box
        """
        AboutDialog().exec_()

    def HandleInfo(self):
        """
        Records the Level Meta Information
        """
        if Area.areanum == 1:
            dlg = MetaInfoDialog()
            if dlg.exec_() == QtWidgets.QDialog.Accepted:
                Area.Metadata.setStrData('Title', dlg.levelName.text())
                Area.Metadata.setStrData('Author', dlg.Author.text())
                Area.Metadata.setStrData('Group', dlg.Group.text())
                Area.Metadata.setStrData('Website', dlg.Website.text())

                SetDirty()
                return
        else:
            dlg = QtWidgets.QMessageBox()
            dlg.setText(trans.string('InfoDlg', 14))
            dlg.exec_()

    def HelpBox(self):
        """
        Shows the help box
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(os.path.join(module_path(), 'satorudata', 'help', 'index.html')))

    def TipBox(self):
        """
        Satoru Tips and Commands
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(os.path.join(module_path(), 'satorudata', 'help', 'tips.html')))

    def UpdateCheck(self):
        """
        Checks for updates and displays an appropriate dialog
        """
        UpdateDialog().exec_()

    def SelectAll(self):
        """
        Select all objects in the current area
        """
        paintRect = QtGui.QPainterPath()
        paintRect.addRect(float(0), float(0), float(1024*TileWidth), float(512*TileWidth))
        self.scene.setSelectionArea(paintRect)

    def Deselect(self):
        """
        Deselect all currently selected items
        """
        items = self.scene.selectedItems()
        for obj in items:
            obj.setSelected(False)

    def Cut(self):
        """
        Cuts the selected items
        """
        return # Coming soon!
        self.SelectionUpdateFlag = True
        selitems = self.scene.selectedItems()
        self.scene.clearSelection()

        if len(selitems) > 0:
            clipboard_o = []
            clipboard_s = []
            ii = isinstance
            type_obj = ObjectItem
            type_spr = SpriteItem

            for obj in selitems:
                if ii(obj, type_obj):
                    obj.delete()
                    obj.setSelected(False)
                    self.scene.removeItem(obj)
                    clipboard_o.append(obj)
                elif ii(obj, type_spr):
                    obj.delete()
                    obj.setSelected(False)
                    self.scene.removeItem(obj)
                    clipboard_s.append(obj)

            if len(clipboard_o) > 0 or len(clipboard_s) > 0:
                SetDirty()
                self.actions_['cut'].setEnabled(False)
                self.actions_['paste'].setEnabled(True)
                self.clipboard = self.encodeObjects(clipboard_o, clipboard_s)
                self.systemClipboard.setText(self.clipboard)

        self.levelOverview.update()
        self.SelectionUpdateFlag = False
        self.ChangeSelectionHandler()

    def Copy(self):
        """
        Copies the selected items
        """
        return # Coming soon!
        selitems = self.scene.selectedItems()
        if len(selitems) > 0:
            clipboard_o = []
            clipboard_s = []
            ii = isinstance
            type_obj = ObjectItem
            type_spr = SpriteItem

            for obj in selitems:
                if ii(obj, type_obj):
                    clipboard_o.append(obj)
                elif ii(obj, type_spr):
                    clipboard_s.append(obj)

            if len(clipboard_o) > 0 or len(clipboard_s) > 0:
                self.actions_['paste'].setEnabled(True)
                self.clipboard = self.encodeObjects(clipboard_o, clipboard_s)
                self.systemClipboard.setText(self.clipboard)

    def Paste(self):
        """
        Paste the selected items
        """
        return # Coming soon!
        if self.clipboard is not None:
            self.placeEncodedObjects(self.clipboard)

    def encodeObjects(self, clipboard_o, clipboard_s):
        """
        Encode a set of objects and sprites into a string
        """
        convclip = ['SatoruClip']

        # get objects
        clipboard_o.sort(key=lambda x: x.zValue())

        for item in clipboard_o:
            convclip.append('0:%d:%d:%d:%d:%d:%d:%d' % (item.from_, item.idx, item.layer, item.objx, item.objy, item.width, item.height))

        # get sprites
        for item in clipboard_s:
            data = item.spritedata
            convclip.append('1:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d' % (item.type, item.objx, item.objy, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[9], data[10], data[11]))

        convclip.append('%')
        return '|'.join(convclip)

    def placeEncodedObjects(self, encoded, select=True, xOverride=None, yOverride=None):
        """
        Decode and place a set of objects
        """
        self.SelectionUpdateFlag = True
        self.scene.clearSelection()
        added = []

        x1 = 1024
        x2 = 0
        y1 = 512
        y2 = 0

        global OverrideSnapping
        OverrideSnapping = True

        if not (encoded.startswith('SatoruClip|') and encoded.endswith('|%')): return

        clip = encoded.split('|')[1:-1]

        if len(clip) > 300:
            result = QtWidgets.QMessageBox.warning(self, 'Satoru', trans.string('MainWindow', 1), QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No: return

        layers, sprites = self.getEncodedObjects(encoded)

        # Go through the sprites
        for spr in sprites:
            x = spr.objx / 16
            y = spr.objy / 16
            if x < x1: x1 = x
            if x > x2: x2 = x
            if y < y1: y1 = y
            if y > y2: y2 = y

            Area.sprites.append(spr)
            added.append(spr)
            self.scene.addItem(spr)

        # Go through the objects
        for layer in layers:
            for obj in layer:
                xs = obj.objx
                xe = obj.objx + obj.width - 1
                ys = obj.objy
                ye = obj.objy + obj.height - 1
                if xs < x1: x1 = xs
                if xe > x2: x2 = xe
                if ys < y1: y1 = ys
                if ye > y2: y2 = ye

                added.append(obj)
                self.scene.addItem(obj)

        layer0, layer1, layer2 = layers

        if len(layer0) > 0:
            AreaLayer = Area.layers[0]
            if len(AreaLayer) > 0:
                z = AreaLayer[-1].zValue() + 1
            else:
                z = 16384
            for obj in layer0:
                AreaLayer.append(obj)
                obj.setZValue(z)
                z += 1

        if len(layer1) > 0:
            AreaLayer = Area.layers[1]
            if len(AreaLayer) > 0:
                z = AreaLayer[-1].zValue() + 1
            else:
                z = 8192
            for obj in layer1:
                AreaLayer.append(obj)
                obj.setZValue(z)
                z += 1

        if len(layer2) > 0:
            AreaLayer = Area.layers[2]
            if len(AreaLayer) > 0:
                z = AreaLayer[-1].zValue() + 1
            else:
                z = 0
            for obj in layer2:
                AreaLayer.append(obj)
                obj.setZValue(z)
                z += 1

        # now center everything
        zoomscaler = (self.ZoomLevel / 100.0)
        width = x2 - x1 + 1
        height = y2 - y1 + 1
        viewportx = (self.view.XScrollBar.value() / zoomscaler) / TileWidth
        viewporty = (self.view.YScrollBar.value() / zoomscaler) / TileWidth
        viewportwidth = (self.view.width() / zoomscaler) / TileWidth
        viewportheight = (self.view.height() / zoomscaler) / TileWidth

        # tiles
        if xOverride is None:
            xoffset = int(0 - x1 + viewportx + ((viewportwidth / 2) - (width / 2)))
            xpixeloffset = xoffset * 16
        else:
            xoffset = int(0 - x1 + (xOverride / 16) - (width / 2))
            xpixeloffset = xoffset * 16
        if yOverride is None:
            yoffset = int(0 - y1 + viewporty + ((viewportheight / 2) - (height / 2)))
            ypixeloffset = yoffset * 16
        else:
            yoffset = int(0 - y1 + (yOverride / 16) - (height / 2))
            ypixeloffset = yoffset * 16

        for item in added:
            if isinstance(item, SpriteItem):
                item.setPos(
                    (item.objx + xpixeloffset + item.ImageObj.xOffset) * TileWidth / 16,
                    (item.objy + ypixeloffset + item.ImageObj.yOffset) * TileWidth / 16,
                    )
            elif isinstance(item, ObjectItem):
                item.setPos((item.objx + xoffset) * TileWidth, (item.objy + yoffset) * TileWidth)
            if select: item.setSelected(True)

        OverrideSnapping = False

        self.levelOverview.update()
        SetDirty()
        self.SelectionUpdateFlag = False
        self.ChangeSelectionHandler()

        return added

    def getEncodedObjects(self, encoded):
        """
        Create the objects from a SatoruClip
        """

        layers = ([], [], [])
        sprites = []

        try:
            if not (encoded.startswith('SatoruClip|') and encoded.endswith('|%')): return

            clip = encoded[11:-2].split('|')

            if len(clip) > 300:
                result = QtWidgets.QMessageBox.warning(self, 'Satoru', trans.string('MainWindow', 1), QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
                if result == QtWidgets.QMessageBox.No:
                    return

            for item in clip:
                # Check to see whether it's an object or sprite
                # and add it to the correct stack
                split = item.split(':')
                if split[0] == '0':
                    # object
                    if len(split) != 8: continue

                    tileset = int(split[1])
                    type = int(split[2])
                    layer = int(split[3])
                    objx = int(split[4])
                    objy = int(split[5])
                    width = int(split[6])
                    height = int(split[7])

                    # basic sanity checks
                    if tileset < 0 or tileset > 3: continue
                    if type < 0 or type > 255: continue
                    if layer < 0 or layer > 2: continue
                    if objx < 0 or objx > 1023: continue
                    if objy < 0 or objy > 511: continue
                    if width < 1 or width > 1023: continue
                    if height < 1 or height > 511: continue

                    newitem = ObjectItem(tileset, type, layer, objx, objy, width, height, 1, 0)

                    layers[layer].append(newitem)

                elif split[0] == '1':
                    # sprite
                    if len(split) != 11: continue

                    objx = int(split[2])
                    objy = int(split[3])
                    data = bytes(map(int, [split[4], split[5], split[6], split[7], split[8], split[9], '0', split[10], '0', '0', '0', '0', '0', '0']))

                    x = objx / 16
                    y = objy / 16

                    newitem = SpriteItem(int(split[1]), objx, objy, data)
                    sprites.append(newitem)

        except ValueError:
            # an int() probably failed somewhere
            pass

        return layers, sprites

    def ShiftItems(self):
        """
        Shifts the selected object(s)
        """
        items = self.scene.selectedItems()
        if len(items) == 0: return

        dlg = ObjectShiftDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            xoffset = dlg.XOffset.value()
            yoffset = dlg.YOffset.value()
            if xoffset == 0 and yoffset == 0: return

            type_obj = ObjectItem
            type_spr = SpriteItem
            type_ent = EntranceItem
            type_loc = LocationItem

            if ((xoffset % 16) != 0) or ((yoffset % 16) != 0):
                # warn if any objects exist
                objectsExist = False
                spritesExist = False
                for obj in items:
                    if isinstance(obj, type_obj):
                        objectsExist = True
                    elif isinstance(obj, type_spr) or isinstance(obj, type_ent):
                        spritesExist = True

                if objectsExist and spritesExist:
                    # no point in warning them if there are only objects
                    # since then, it will just silently reduce the offset and it won't be noticed
                    result = QtWidgets.QMessageBox.information(None, trans.string('ShftItmDlg', 5),  trans.string('ShftItmDlg', 6), QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
                    if result == QtWidgets.QMessageBox.No:
                        return

            xpoffset = xoffset * TileWidth / 16
            ypoffset = yoffset * TileWidth / 16

            global OverrideSnapping
            OverrideSnapping = True

            for obj in items:
                obj.setPos(obj.x() + xpoffset, obj.y() + ypoffset)

            OverrideSnapping = False

            SetDirty()

    def SwapObjectsTilesets(self):
        """
        Swaps objects' tilesets
        """
        global Area

        dlg = ObjectTilesetSwapDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            for layer in Area.layers:
                for nsmbobj in layer:
                    if nsmbobj.tileset == (dlg.FromTS.value()-1):
                        nsmbobj.SetType(dlg.ToTS.value() -1, nsmbobj.type)
                    elif nsmbobj.tileset == (dlg.ToTS.value()-1) and dlg.DoExchange.checkState() == Qt.Checked:
                        nsmbobj.SetType(dlg.FromTS.value() -1, nsmbobj.type)


            SetDirty()

    def SwapObjectsTypes(self):
        """
        Swaps objects' types
        """
        global Area

        dlg = ObjectTypeSwapDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            for layer in Area.layers:
                for nsmbobj in layer:
                    if nsmbobj.type == (dlg.FromType.value()) and nsmbobj.tileset == (dlg.FromTileset.value() - 1):
                        nsmbobj.SetType(dlg.ToTileset.value() - 1, dlg.ToType.value())
                    elif nsmbobj.type == (dlg.ToType.value()) and nsmbobj.tileset == (dlg.ToTileset.value() - 1) and dlg.DoExchange.checkState() == Qt.Checked:
                        nsmbobj.SetType(dlg.FromTileset.value() - 1, dlg.FromType.value())


            SetDirty()

    def MergeLocations(self):
        """
        Merges selected sprite locations
        """
        items = self.scene.selectedItems()
        if len(items) == 0: return

        newx = 999999
        newy = 999999
        neww = 0
        newh = 0

        type_loc = LocationItem
        for obj in items:
            if isinstance(obj, type_loc):
                if obj.objx < newx:
                    newx = obj.objx
                if obj.objy < newy:
                    newy = obj.objy
                if obj.width + obj.objx > neww:
                    neww = obj.width + obj.objx
                if obj.height + obj.objy > newh:
                    newh = obj.height + obj.objy
                obj.delete()
                obj.setSelected(False)
                self.scene.removeItem(obj)
                self.levelOverview.update()
                SetDirty()

        if newx != 999999 and newy != 999999:
            allID = set() # faster 'x in y' lookups for sets
            newID = 1
            for i in Area.locations:
                allID.add(i.id)

            while newID <= 255:
                if newID not in allID:
                    break
                newID += 1

            loc = LocationItem(newx, newy, neww - newx, newh - newy, newID)

            mw = mainWindow
            loc.positionChanged = mw.HandleObjPosChange
            mw.scene.addItem(loc)

            Area.locations.append(loc)
            loc.setSelected(True)

    def HandleAddNewArea(self):
        """
        Adds a new area to the level
        """
        if len(Level.areas) >= 4:
            QtWidgets.QMessageBox.warning(self, 'Satoru', trans.string('AreaChoiceDlg', 2))
            return

        if self.CheckDirty():
            return

        try: 
            Level.addArea()
        except: 
            return

        if not self.HandleSave():
            return

        newID = len(Level.areas)
        self.LoadLevel(None, self.fileSavePath, True, newID)

    def HandleImportArea(self):
        """
        Imports an area from another level
        """
        if len(Level.areas) >= 4:
            QtWidgets.QMessageBox.warning(self, 'Satoru', trans.string('AreaChoiceDlg', 2))
            return

        if self.CheckDirty():
            return

        fn = QtWidgets.QFileDialog.getOpenFileName(self, trans.string('FileDlgs', 0), '', FileTypes)[0]
        if fn == '': return

        with open(str(fn), 'rb') as fileobj:
            arcdata = fileobj.read()
        if LHTool.isLHCompressed(arcdata):
            arcdata = LHTool.decompressLH(arcdata)

        arc = nsmbulib.Sarc.load(arcdata)

        # get the area count
        areacount = 0

        for item, val in arc.items():
            if val is not None:
                # it's a file
                fname = item[item.rfind('/')+1:]
                if fname.startswith('course'):
                    maxarea = int(fname[6])
                    if maxarea > areacount: areacount = maxarea

        # choose one
        dlg = AreaChoiceDialog(areacount)
        if dlg.exec_() == QtWidgets.QDialog.Rejected:
            return

        area = dlg.areaCombo.currentIndex() + 1

        # get the required files
        reqcourse = 'course%d.bin' % area
        reqL0 = 'course%d_bgdatL0.bin' % area
        reqL1 = 'course%d_bgdatL1.bin' % area
        reqL2 = 'course%d_bgdatL2.bin' % area

        course = None
        L0 = None
        L1 = None
        L2 = None

        for item, val in arc.items():
            fname = item.split('/')[-1]
            if fname == reqcourse:
                course = val
            elif fname == reqL0:
                L0 = val
            elif fname == reqL1:
                L1 = val
            elif fname == reqL2:
                L2 = val

        # add them to our level
        newID = len(Level.areas) + 1

        newA = Level.addArea()
        newA.load(course, L0, L1, L2)

        if not self.HandleSave(): return
        self.LoadLevel(None, self.fileSavePath, True, newID)

    def HandleDeleteArea(self):
        """
        Deletes the current area
        """
        result = QtWidgets.QMessageBox.warning(self, 'Satoru', trans.string('DeleteArea', 0), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.No: return

        if not self.HandleSave(): return

        Level.deleteArea(Area.areanum)

        # no error checking. if it saved last time, it will probably work now

        name = self.getInnerSarcName(os.path.basename(self.fileSavePath))
        if '-' not in name:
            print('HEY THERE IS NO -, THIS WILL NOT WORK!')

        folder = os.path.dirname(self.fileSavePath)
        datas = Level.save(name, os.path.basename(self.fileSavePath), False, self.fileSavePath.lower().endswith('.szs'))
        for fn, data in datas.items():
            with open(os.path.join(folder, fn), 'wb') as f:
                f.write(data)
        self.LoadLevel(None, self.fileSavePath, True, 1)

    def HandleChangeGamePath(self, auto=False):
        """
        Change the game path used by the current game definition
        """
        if self.CheckDirty(): return

        path = None
        #while not isValidGamePath(path):
        global CurrentGame
        CurrentGame = NewSuperMarioBrosU
        path = QtWidgets.QFileDialog.getExistingDirectory(self, trans.string('ChangeGamePath', 0, '[game]', gamedef.name))
        if path == '':
            return False

        path = str(path)

        if (not isValidGamePath(path)) and (not gamedef.custom): # custom gamedefs can use incomplete folders
            QtWidgets.QMessageBox.information(self, trans.string('ChangeGamePath', 1), trans.string('ChangeGamePath', 2))
        else:
            SetGamePath(path)
            #break

        if not auto: self.LoadLevel(None, FirstLevels[CurrentGame], False, 1)
        return True

    def HandleChangeOneTileset(self):
        """
        Let the user choose a new OneTileset folder
        """
        if self.CheckDirty(): return

        newPath = getOneTilesetPath()
        if not newPath: return

        # Don't actually reload OneTileset because I'm lazy and short on time.
        QtWidgets.QMessageBox.information(self, 'OneTileset folder changed', 'The OneTileset folder was successfully changed. Please restart Satoru to reload OneTileset from the new folder.')

    def HandlePreferences(self):
        """
        Edit Satoru preferences
        """

        # Show the dialog
        dlg = PreferencesDialog()
        if dlg.exec_() == QtWidgets.QDialog.Rejected:
            return

        # Get the Menubar/Ribbon setting
        if dlg.generalTab.MenuR.isChecked():
            setSetting('Menu', 'Ribbon')
        else:
            setSetting('Menu', 'Menubar')

        # Get the translation
        name = str(dlg.generalTab.Trans.itemData(dlg.generalTab.Trans.currentIndex(), Qt.UserRole))
        setSetting('Translation', name)

        # Get the Toolbar tab settings
        boxes = (dlg.toolbarTab.FileBoxes, dlg.toolbarTab.EditBoxes, dlg.toolbarTab.ViewBoxes, dlg.toolbarTab.SettingsBoxes, dlg.toolbarTab.HelpBoxes)
        ToolbarSettings = {}
        for boxList in boxes:
            for box in boxList:
                ToolbarSettings[box.InternalName] = box.isChecked()
        setSetting('ToolbarActs', ToolbarSettings)

        # Get the theme settings
        for btn in dlg.themesTab.btns:
            if btn.isChecked():
                setSetting('Theme', dlg.themesTab.btnvals[btn][0])
                break
        setSetting('uiStyle', dlg.themesTab.NonWinStyle.currentText())

        # Warn the user that they may need to restart
        QtWidgets.QMessageBox.warning(None, trans.string('PrefsDlg', 0), trans.string('PrefsDlg', 30))

    def HandleNewLevel(self):
        """
        Create a new level
        """
        #if self.CheckDirty(): return
        #self.LoadLevel(None, None, False, 1)
        print('Not functional yet.')

    def HandleOpenFromName(self):
        """
        Open a level using the level picker
        """
        if self.CheckDirty(): return

        LoadLevelNames()
        dlg = ChooseLevelNameDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.LoadLevel(None, dlg.currentlevel, False, 1)

    def HandleOpenFromFile(self):
        """
        Open a level using the filename
        """
        if self.CheckDirty(): return

        fn = QtWidgets.QFileDialog.getOpenFileName(self, trans.string('FileDlgs', 0), '', FileTypes)[0]
        if fn == '': return
        self.LoadLevel(None, str(fn), True, 1)

    def HandleSave(self):
        """
        Save a level back to the archive
        """
        if not mainWindow.fileSavePath:
            self.HandleSaveAs()
            return

        name = self.getInnerSarcName(os.path.basename(self.fileSavePath))

        global Dirty, AutoSaveDirty

        try:
            folder = os.path.dirname(self.fileSavePath)
            levelFn = os.path.basename(self.fileSavePath)
            datas = Level.save(name, levelFn, False, levelFn.lower().endswith('.szs'))
            for fn, data in datas.items():
                with open(os.path.join(folder, fn), 'wb') as f:
                    f.write(data)
        except Exception:
            import traceback
            QtWidgets.QMessageBox.warning(None, 'Error', 'The level could not be saved:\n' + traceback.format_exc())
            return False

        Dirty = False
        AutoSaveDirty = False
        self.UpdateTitle()

        return True

    def HandleSaveAs(self, separateTilesets=False):
        """
        Save a level back to the archive, with a new filename
        """
        fn = QtWidgets.QFileDialog.getSaveFileName(self, trans.string('FileDlgs', 3), '', 'Uncompressed Level Archives (*.sarc);;' + trans.string('FileDlgs', 2) + ' (*)')[0]
        if not fn: return

        global Dirty, AutoSaveDirty
        Dirty = False
        AutoSaveDirty = False
        Dirty = False

        if not separateTilesets:
            self.fileSavePath = fn
            self.fileTitle = os.path.basename(fn)

        name = self.getInnerSarcName(os.path.basename(fn))

        try:
            folder = os.path.dirname(fn)
            datas = Level.save(name, os.path.basename(fn), separateTilesets, fn.lower().endswith('.szs'))
            for fn, data in datas.items():
                with open(os.path.join(folder, fn), 'wb') as f:
                    f.write(data)
        except Exception:
            import traceback
            QtWidgets.QMessageBox.warning(self, 'Error', 'The level could not be saved:\n' + traceback.format_exc())
            return False

        self.UpdateTitle()

        return True

    def HandleExportSeparately(self):
        """
        Export the level data and tilesets separately.
        """
        return self.HandleSaveAs(True)

    def getInnerSarcName(self, filename):

        # Skawo requested this -- assume that the level name should be the filename
        # if the filename is of the format #-#.(sarc/szs)
        filenameStart = filename.split('.')[0]
        def isint(s):
            try: int(s)
            except ValueError: return False
            return True
        if filenameStart.count('-') == 1 and all(isint(part) for part in filenameStart.split('-')):
            return filenameStart

        name = QtWidgets.QInputDialog.getText(self, 'Choose Internal Name',
            'Choose an internal filename for this level (do not add a .sarc extension) (example: 1-1):', QtWidgets.QLineEdit.Normal)[0]
        if '-' not in name:
            QtWidgets.QMessageBox.warning(self, 'Name warning',
                'The input name does not include a -, which is what retail levels use. This may crash, because it does not fit the proper format.')
        return name

    def HandleExit(self):
        """
        Exit the editor. Why would you want to do this anyway?
        """
        self.close()

    def HandleSwitchArea(self, idx):
        """
        Handle activated signals for areaComboBox
        """
        if self.CheckDirty():
            self.areaComboBox.setCurrentIndex(Area.areanum)
            return

        if Area.areanum != idx + 1:
            self.LoadLevel(None, self.fileSavePath, True, idx + 1)

    def HandleUpdateLayer0(self, checked):
        """
        Handle toggling of layer 0 being shown
        """
        global Layer0Shown

        Layer0Shown = checked

        if Area is not None:
            for obj in Area.layers[0]:
                obj.setVisible(Layer0Shown)

        self.scene.update()

    def HandleUpdateLayer1(self, checked):
        """
        Handle toggling of layer 1 being shown
        """
        global Layer1Shown

        Layer1Shown = checked

        if Area is not None:
            for obj in Area.layers[1]:
                obj.setVisible(Layer1Shown)

        self.scene.update()

    def HandleUpdateLayer2(self, checked):
        """
        Handle toggling of layer 2 being shown
        """
        global Layer2Shown

        Layer2Shown = checked

        if Area is not None:
            for obj in Area.layers[2]:
                obj.setVisible(Layer2Shown)

        self.scene.update()

    def HandleTilesetAnimToggle(self, checked):
        """
        Handle toggling of tileset animations
        """
        ...

    def HandleCollisionsToggle(self, checked):
        """
        Handle toggling of tileset collisions viewing
        """
        global CollisionsShown

        CollisionsShown = checked

        setSetting('ShowCollisions', CollisionsShown)
        self.scene.update()

    def HandleDepthToggle(self, checked):
        """
        Handle toggling of tileset depth highlighting viewing
        """
        global DepthShown

        DepthShown = checked

        setSetting('ShowDepth', DepthShown)
        self.scene.update()

    def HandleRealViewToggle(self, checked):
        """
        Handle toggling of Real View
        """
        global RealViewEnabled

        RealViewEnabled = checked
        SLib.RealViewEnabled = RealViewEnabled

        setSetting('RealViewEnabled', RealViewEnabled)
        self.scene.update()

    def HandleSpritesVisibility(self, checked):
        """
        Handle toggling of sprite visibility
        """
        global SpritesShown

        SpritesShown = checked

        if Area is not None:
            for spr in Area.sprites:
                spr.setVisible(SpritesShown)

        setSetting('ShowSprites', SpritesShown)
        self.scene.update()

    def HandleSpriteImages(self, checked):
        """
        Handle toggling of sprite images
        """
        global SpriteImagesShown

        SpriteImagesShown = checked

        setSetting('ShowSpriteImages', SpriteImagesShown)

        if Area is not None:
            for spr in Area.sprites:
                spr.UpdateRects()
                if SpriteImagesShown:
                    spr.setPos(
                        (spr.objx + spr.ImageObj.xOffset) * (TileWidth/16),
                        (spr.objy + spr.ImageObj.yOffset) * (TileWidth/16),
                        )
                else:
                    spr.setPos(
                        spr.objx * (TileWidth/16),
                        spr.objy * (TileWidth/16),
                        )

        self.scene.update()

    def HandleLocationsVisibility(self, checked):
        """
        Handle toggling of location visibility
        """
        global LocationsShown

        LocationsShown = checked

        if Area is not None:
            for loc in Area.locations:
                loc.setVisible(LocationsShown)

        setSetting('ShowLocations', LocationsShown)
        self.scene.update()

    def HandleCommentsVisibility(self, checked):
        """
        Handle toggling of comment visibility
        """
        global CommentsShown

        CommentsShown = checked

        if Area is not None:
            for com in Area.comments:
                com.setVisible(CommentsShown)

        setSetting('ShowComments', CommentsShown)
        self.scene.update()

    def HandlePathsVisibility(self, checked):
        """
        Handle toggling of path visibility
        """
        global PathsShown

        PathsShown = checked

        if Area is not None:
            for node in Area.paths:
                node.setVisible(PathsShown)
            for path in Area.pathdata:
                path['peline'].setVisible(PathsShown)

        setSetting('ShowPaths', PathsShown)
        self.scene.update()

    def HandleObjectsFreeze(self, checked):
        """
        Handle toggling of objects being frozen
        """
        global ObjectsFrozen

        ObjectsFrozen = checked
        flag1 = QtWidgets.QGraphicsItem.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.ItemIsMovable

        if Area is not None:
            for layer in Area.layers:
                for obj in layer:
                    obj.setFlag(flag1, not ObjectsFrozen)
                    obj.setFlag(flag2, not ObjectsFrozen)

        setSetting('FreezeObjects', ObjectsFrozen)
        self.scene.update()

    def HandleSpritesFreeze(self, checked):
        """
        Handle toggling of sprites being frozen
        """
        global SpritesFrozen

        SpritesFrozen = checked
        flag1 = QtWidgets.QGraphicsItem.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.ItemIsMovable

        if Area is not None:
            for spr in Area.sprites:
                spr.setFlag(flag1, not SpritesFrozen)
                spr.setFlag(flag2, not SpritesFrozen)

        setSetting('FreezeSprites', SpritesFrozen)
        self.scene.update()

    def HandleEntrancesFreeze(self, checked):
        """
        Handle toggling of entrances being frozen
        """
        global EntrancesFrozen

        EntrancesFrozen = checked
        flag1 = QtWidgets.QGraphicsItem.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.ItemIsMovable

        if Area is not None:
            for ent in Area.entrances:
                ent.setFlag(flag1, not EntrancesFrozen)
                ent.setFlag(flag2, not EntrancesFrozen)

        setSetting('FreezeEntrances', EntrancesFrozen)
        self.scene.update()

    def HandleLocationsFreeze(self, checked):
        """
        Handle toggling of locations being frozen
        """
        global LocationsFrozen

        LocationsFrozen = checked
        flag1 = QtWidgets.QGraphicsItem.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.ItemIsMovable

        if Area is not None:
            for loc in Area.locations:
                loc.setFlag(flag1, not LocationsFrozen)
                loc.setFlag(flag2, not LocationsFrozen)

        setSetting('FreezeLocations', LocationsFrozen)
        self.scene.update()

    def HandlePathsFreeze(self, checked):
        """
        Handle toggling of paths being frozen
        """
        global PathsFrozen

        PathsFrozen = checked
        flag1 = QtWidgets.QGraphicsItem.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.ItemIsMovable

        if Area is not None:
            for node in Area.paths:
                node.setFlag(flag1, not PathsFrozen)
                node.setFlag(flag2, not PathsFrozen)

        setSetting('FreezePaths', PathsFrozen)
        self.scene.update()

    def HandleCommentsFreeze(self, checked):
        """
        Handle toggling of comments being frozen
        """
        global CommentsFrozen

        CommentsFrozen = checked
        flag1 = QtWidgets.QGraphicsItem.ItemIsSelectable
        flag2 = QtWidgets.QGraphicsItem.ItemIsMovable

        if Area is not None:
            for com in Area.comments:
                com.setFlag(flag1, not CommentsFrozen)
                com.setFlag(flag2, not CommentsFrozen)

        setSetting('FreezeComments', CommentsFrozen)
        self.scene.update()

    def HandleFullscreen(self, checked):
        """
        Handle fullscreen mode
        """
        if checked:
            self.showFullScreen()
        else:
            self.showMaximized()

    def HandleSwitchGrid(self):
        """
        Handle switching of the grid view
        """
        global GridType

        if GridType is None: GridType = 'grid'
        elif GridType == 'grid': GridType = 'checker'
        else: GridType = None

        setSetting('GridType', GridType)
        self.scene.update()

    def HandleZoomIn(self):
        """
        Handle zooming in
        """
        z = self.ZoomLevel
        zi = self.ZoomLevels.index(z)
        zi += 1
        if zi < len(self.ZoomLevels):
            self.ZoomTo(self.ZoomLevels[zi])

    def HandleZoomOut(self):
        """
        Handle zooming out
        """
        z = self.ZoomLevel
        zi = self.ZoomLevels.index(z)
        zi -= 1
        if zi >= 0:
            self.ZoomTo(self.ZoomLevels[zi])

    def HandleZoomActual(self):
        """
        Handle zooming to the actual size
        """
        self.ZoomTo(100.0)

    def HandleZoomMin(self):
        """
        Handle zooming to the minimum size
        """
        self.ZoomTo(self.ZoomLevels[0])

    def HandleZoomMax(self):
        """
        Handle zooming to the maximum size
        """
        self.ZoomTo(self.ZoomLevels[len(self.ZoomLevels)-1])

    def ZoomTo(self, z):
        """
        Zoom to a specific level
        """
        zEffective = z / TileWidth * 24 # "100%" zoom level produces 24x24 level view
        tr = QtGui.QTransform()
        tr.scale(zEffective / 100.0, zEffective / 100.0)
        self.ZoomLevel = z
        self.view.setTransform(tr)
        self.levelOverview.mainWindowScale = zEffective / 100.0

        zi = self.ZoomLevels.index(z)
        self.actions_['zoommax'].setEnabled(zi < len(self.ZoomLevels) - 1)
        self.actions_['zoomin'] .setEnabled(zi < len(self.ZoomLevels) - 1)
        self.actions_['zoomactual'].setEnabled(z != 100.0)
        self.actions_['zoomout'].setEnabled(zi > 0)
        self.actions_['zoommin'].setEnabled(zi > 0)

        self.ZoomWidget.setZoomLevel(z)
        self.ZoomStatusWidget.setZoomLevel(z)

        # Update the zone grabber rects, to resize for the new zoom level
        for z in Area.zones:
            z.UpdateRects()

        self.scene.update()

    def HandleOverviewClick(self, x, y):
        """
        Handle position changes from the level overview
        """
        self.view.centerOn(x, y)
        self.levelOverview.update()

    def SaveComments(self):
        """
        Saves the comments data back to self.Metadata
        """
        b = []
        for com in Area.comments:
            xpos, ypos, tlen = com.objx, com.objy, len(com.text)
            b.append(xpos >> 24)
            b.append((xpos >> 16) & 0xFF)
            b.append((xpos >> 8) & 0xFF)
            b.append(xpos & 0xFF)
            b.append(ypos >> 24)
            b.append((ypos >> 16) & 0xFF)
            b.append((ypos >> 8) & 0xFF)
            b.append(ypos & 0xFF)
            b.append(tlen >> 24)
            b.append((tlen >> 16) & 0xFF)
            b.append((tlen >> 8) & 0xFF)
            b.append(tlen & 0xFF)
            for char in com.text: b.append(ord(char))
        Area.Metadata.setBinData('InLevelComments_A%d' % Area.areanum, b)

    def closeEvent(self, event):
        """
        Handler for the main window close event
        """

        if self.CheckDirty():
            event.ignore()
        else:
            # save our state
            self.spriteEditorDock.setVisible(False)
            self.entranceEditorDock.setVisible(False)
            self.pathEditorDock.setVisible(False)
            self.objectEditorDock.setVisible(False)
            self.locationEditorDock.setVisible(False)
            self.defaultPropDock.setVisible(False)

            # state: determines positions of docks
            # geometry: determines the main window position
            setSetting('MainWindowState', self.saveState(0))
            setSetting('MainWindowGeometry', self.saveGeometry())

            if hasattr(self, 'HelpBoxInstance'):
                self.HelpBoxInstance.close()

            if hasattr(self, 'TipsBoxInstance'):
                self.TipsBoxInstance.close()

            gamedef.SetLastLevel(str(mainWindow.fileSavePath))

            setSetting('AutoSaveFilePath', 'none')
            setSetting('AutoSaveFileData', 'x')

            event.accept()

    def LoadLevel(self, game, name, isFullPath, areaNum):
        """
        Load a level from any game into the editor
        """
        global levName; levName=name.replace('\\', '/').split('/')[-1]

        game = NewSuperMarioBrosU

        # Get the file path, if possible
        if name is not None:
            checknames = []
            if isFullPath:
                checknames = [name,]
            else:
                for ext in FileExtensions[game]:
                    checknames.append(os.path.join(gamedef.GetGamePath(), name + ext))

            found = False
            for checkname in checknames:
                if os.path.isfile(checkname):
                    found = True
                    break
            if not found:
                QtWidgets.QMessageBox.warning(self, 'Satoru', trans.string('Err_CantFindLevel', 0, '[name]', checkname), QtWidgets.QMessageBox.Ok)
                return False
            if not IsNSMBULevel(checkname):
                QtWidgets.QMessageBox.warning(self, 'Satoru', trans.string('Err_InvalidLevel', 0), QtWidgets.QMessageBox.Ok)
                return False

        name = checkname

        if not (name.endswith('.szs') or name.endswith('.sarc')): return False # keep it from crashing by loading things it shouldn't

        # Get the data
        global RestoredFromAutoSave
        if not RestoredFromAutoSave:

            # Check if there is a file by this name
            if not os.path.isfile(name):
                QtWidgets.QMessageBox.warning(None, trans.string('Err_MissingLevel', 0), trans.string('Err_MissingLevel', 1, '[file]', name))
                return False

            # Set the filepath variables
            self.fileSavePath = name
            self.fileTitle = os.path.basename(self.fileSavePath)

            # Open the file
            with open(self.fileSavePath, 'rb') as fileobj:
                levelData = fileobj.read()

        else:
            # Auto-saved level. Check if there's a path associated with it:

            if AutoSavePath == 'None':
                self.fileSavePath = None
                self.fileTitle = trans.string('WindowTitle', 0)
            else:
                self.fileSavePath = AutoSavePath
                self.fileTitle = os.path.basename(name)

            # Get the level data
            levelData = AutoSaveData
            SetDirty(noautosave=True)

            # Turn off the autosave flag
            RestoredFromAutoSave = False

        # Turn the dirty flag off, and keep it that way
        global Dirty, DirtyOverride
        Dirty = False
        DirtyOverride += 1

        # Decompress it (Yaz0)
        if levelData.startswith(b'Yaz0'):
            print('Beginning Yaz0 decompression...')
            levelData = nsmbulib.Yaz0.decompress(levelData)
            print('Decompression finished.')
        else:
            print('Yaz0 decompression skipped.')

        arc = nsmbulib.Sarc.load(levelData)

        possibilities = []
        possibilities.append(os.path.basename(name))
        if 'levelname' in arc:
            possibilities.append(arc['levelname'].decode('utf-8'))
        possibilities.append(possibilities[0].split()[-1]) # for formats like "NSMBU 1-1.szs"
        possibilities.append(possibilities[0].split()[0]) # for formats like "1-1 test.szs"
        possibilities.append(possibilities[0].split('.')[0])
        possibilities.append(possibilities[0].split('_')[0])
        for fn in possibilities:
            if fn in arc:
                levelFileData = arc[fn]
                break
        else:
            print("Could not identify the level's internal filename :/")
            return False

        # Sort the szs data
        global szsData
        szsData = {}
        for name, data in arc.items():
            szsData[name] = data

        levelData = levelFileData

        # Here's how progress is tracked. (After the major refactor, it may be a bit messed up now.)
        # - 0: Loading level data
        # [Area.__init__ is entered here]
        # - 1: Loading tilesets [1/2/3/4 allocated for each tileset]
        # - 5: Loading layers
        # [Control is returned to LoadLevel_NSMBU]
        # - 6: Loading objects
        # - 7: Preparing editor

        # First, clear out the existing level.
        self.scene.clearSelection()
        self.CurrentSelection = []
        self.scene.clear()

        # Clear out all level-thing lists
        for thingList in (self.spriteList, self.entranceList, self.locationList, self.pathList, self.commentList):
            thingList.clear()
            thingList.selectionModel().setCurrentIndex(QtCore.QModelIndex(), QtCore.QItemSelectionModel.Clear)

        # Reset these here, because if they are set after
        # creating the objects, they use the old values.
        global CurrentLayer, Layer0Shown, Layer1Shown, Layer2Shown
        CurrentLayer = 1
        Layer0Shown = True
        Layer1Shown = True
        Layer2Shown = True

        # Prevent things from snapping when they're created
        global OverrideSnapping
        OverrideSnapping = True

        # Update progress
        try:
            app.splashScreen.setProgress(trans.string('Splash', 2), 0)
        except:
            pass

        self.LoadLevel_NSMBU(levelData, areaNum)

        # Refresh object layouts
        self.objPicker.LoadFromTilesets()
        for layer in Area.layers:
            for obj in layer:
                obj.updateObjCache()
        self.scene.update()

        # Set the level overview settings
        mainWindow.levelOverview.maxX = 100
        mainWindow.levelOverview.maxY = 40

        # Fill up the area list
        self.areaComboBox.clear()
        for i in range(1, len(Level.areas) + 1):
            self.areaComboBox.addItem(trans.string('AreaCombobox', 0, '[num]', i))
        self.areaComboBox.setCurrentIndex(areaNum - 1)

        self.levelOverview.update()

        # Scroll to the initial entrance
        startEntID = Area.startEntrance
        startEnt = None
        for ent in Area.entrances:
            if ent.entid == startEntID: startEnt = ent

        self.view.centerOn(0, 0)
        if startEnt is not None: self.view.centerOn(startEnt.objx * (TileWidth/16), startEnt.objy * (TileWidth/16))
        self.ZoomTo(100.0)

        # Reset some editor things
        self.actions_['showlay0'].setChecked(True)
        self.actions_['showlay1'].setChecked(True)
        self.actions_['showlay2'].setChecked(True)
        self.actions_['addarea'].setEnabled(len(Level.areas) < 4)
        self.actions_['importarea'].setEnabled(len(Level.areas) < 4)
        self.actions_['deletearea'].setEnabled(len(Level.areas) > 1)

        # Turn snapping back on
        OverrideSnapping = False

        # Turn the dirty flag off
        DirtyOverride -= 1
        self.UpdateTitle()

        # Update UI things
        self.scene.update()

        self.levelOverview.Reset()
        self.levelOverview.update()
        QtCore.QTimer.singleShot(20, self.levelOverview.update)
        self.updateTileCountLabel()

        # Set the Current Game setting
        self.CurrentGame = game
        setSetting('CurrentGame', self.CurrentGame)

        # If we got this far, everything worked! Return True.
        return True

    def LoadLevel_NSMBU(self, levelData, areaNum):
        """
        Performs all level-loading tasks specific to New Super Mario Bros. U levels.
        Do not call this directly - use LoadLevel(NewSuperMarioBrosU, ...) instead!
        """

        # Create the new level object
        global Level
        Level = Level_NSMBU()

        # Load it
        if not Level.load(levelData, areaNum):
            raise Exception

        # Prepare the object picker
        try: # Crashes when changing Areas
            app.splashScreen.setProgress(trans.string('Splash', 4), 7)
        except:
            pass

        self.objUseLayer1.setChecked(True)

        self.objPicker.LoadFromTilesets()
        self.objMetaTab.setCurrentIndex(0)

        # Add all things to scene
        try: # Crashes when changing Areas
            app.splashScreen.setProgress(trans.string('Splash', 5), 8)
        except:
            pass

        # Load events
        self.LoadEventTabFromLevel()

        # Add all things to the scene
        pcEvent = self.HandleObjPosChange
        for layer in reversed(Area.layers):
            for obj in layer:
                obj.positionChanged = pcEvent
                self.scene.addItem(obj)

        pcEvent = self.HandleSprPosChange
        for spr in Area.sprites:
            spr.positionChanged = pcEvent
            spr.listitem = ListWidgetItem_SortsByOther(spr)
            self.spriteList.addItem(spr.listitem)
            self.scene.addItem(spr)
            spr.UpdateListItem()

        pcEvent = self.HandleEntPosChange
        for ent in Area.entrances:
            ent.positionChanged = pcEvent
            ent.listitem = ListWidgetItem_SortsByOther(ent)
            ent.listitem.entid = ent.entid
            self.entranceList.addItem(ent.listitem)
            self.scene.addItem(ent)
            ent.UpdateListItem()

        for zone in Area.zones:
            self.scene.addItem(zone)

        pcEvent = self.HandleLocPosChange
        scEvent = self.HandleLocSizeChange
        for location in Area.locations:
            location.positionChanged = pcEvent
            location.sizeChanged = scEvent
            location.listitem = ListWidgetItem_SortsByOther(location)
            self.locationList.addItem(location.listitem)
            self.scene.addItem(location)
            location.UpdateListItem()

        for path in Area.paths:
            path.positionChanged = self.HandlePathPosChange
            path.listitem = ListWidgetItem_SortsByOther(path)
            self.pathList.addItem(path.listitem)
            self.scene.addItem(path)
            path.UpdateListItem()

        for path in Area.pathdata:
            peline = PathEditorLineItem(path['nodes'])
            path['peline'] = peline
            self.scene.addItem(peline)
            peline.loops = path['loops']

        for path in Area.paths:
            path.UpdateListItem()

        for com in Area.comments:
            com.positionChanged = self.HandleComPosChange
            com.textChanged = self.HandleComTxtChange
            com.listitem = QtWidgets.QListWidgetItem()
            self.commentList.addItem(com.listitem)
            self.scene.addItem(com)
            com.UpdateListItem()

    def ReloadTilesets(self, soft=False):
        """
        Reloads OneTileset. If soft is True, they will not be reloaded if the filepaths have not changed.
        """
        if soft:
            print("Soft reloading has not been implemented.")
        else:
            LoadOneTileset()

    def ReloadSpriteData(self):
        global Sprites
        Sprites = None
        LoadSpriteData()
        for sprite in Area.sprites:
            sprite.InitializeSprite()
        self.scene.update()

    def ChangeSelectionHandler(self):
        """
        Update the visible panels whenever the selection changes
        """
        if self.SelectionUpdateFlag: return

        try:
            selitems = self.scene.selectedItems()
        except RuntimeError:
            # must catch this error: if you close the app while something is selected,
            # you get a RuntimeError about the 'underlying C++ object being deleted'
            return

        # do this to avoid flicker
        showSpritePanel = False
        showEntrancePanel = False
        showLocationPanel = False
        showPathPanel = False
        showObjPanel = False
        updateModeInfo = False

        # clear our variables
        self.selObj = None
        self.selObjs = None

        self.spriteList.setCurrentItem(None)
        self.entranceList.setCurrentItem(None)
        self.locationList.setCurrentItem(None)
        self.pathList.setCurrentItem(None)
        self.commentList.setCurrentItem(None)

        # possibly a small optimization
        func_ii = isinstance
        type_obj = ObjectItem
        type_spr = SpriteItem
        type_ent = EntranceItem
        type_loc = LocationItem
        type_path = PathItem
        type_com = CommentItem

        if len(selitems) == 0:
            # nothing is selected
            self.actions_['cut'].setEnabled(False)
            self.actions_['copy'].setEnabled(False)
            self.actions_['shiftitems'].setEnabled(False)
            self.actions_['mergelocations'].setEnabled(False)

        elif len(selitems) == 1:
            # only one item, check the type
            self.actions_['cut'].setEnabled(True)
            self.actions_['copy'].setEnabled(True)
            self.actions_['shiftitems'].setEnabled(True)
            self.actions_['mergelocations'].setEnabled(False)

            item = selitems[0]
            self.selObj = item
            if func_ii(item, type_spr):
                showSpritePanel = True
                updateModeInfo = True
            elif func_ii(item, type_ent):
                self.creationTabs.setCurrentIndex(2)
                self.UpdateFlag = True
                self.entranceList.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                showEntrancePanel = True
                updateModeInfo = True
            elif func_ii(item, type_loc):
                self.creationTabs.setCurrentIndex(3)
                self.UpdateFlag = True
                self.locationList.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                showLocationPanel = True
                updateModeInfo = True
            elif func_ii(item, type_path):
                self.creationTabs.setCurrentIndex(4)
                self.UpdateFlag = True
                self.pathList.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                showPathPanel = True
                updateModeInfo = True
            elif func_ii(item, type_obj):
                self.creationTabs.setCurrentIndex(0)
                self.objMetaTab.setCurrentIndex(item.from_ - 1)
                self.objPicker.ShowTileset(item.from_ - 1)
                if not setting('DisableAutoPick'):
                    # Do the auto-picking
                    self.objPicker.setObject(item.idx)
                    self.objPicker.handleObjChanged(item.from_ - 1, item.idx)
                    self.objPicker.current = (item.from_ - 1, item.idx)

                    if item.from_ - 1 == 0:
                        newview = self.objPicker.mainPicker.ObjChanged.emit(item.idx)
                    elif item.from_ - 1 == 1:
                        newview = self.objPicker.megaPicker.ObjChanged.emit(item.idx)
                    elif item.from_ - 1 == 2:
                        newview = self.objPicker.embedPicker.ObjChanged.emit(item.idx)
                                        
                    global CurrentObject, CurrentPaintType
                    CurrentObject = item.idx
                    CurrentPaintType = item.from_ - 1
                
                self.UpdateFlag = False
                if item.from_ == OBJECT_FROM_MAIN and item.idx == 28: # Only relevant if it's a ? block
                    showObjPanel = True
                    updateModeInfo = True
            elif func_ii(item, type_com):
                self.creationTabs.setCurrentIndex(8)
                self.UpdateFlag = True
                self.commentList.setCurrentItem(item.listitem)
                self.UpdateFlag = False
                updateModeInfo = True

        else:
            updateModeInfo = True

            # more than one item
            self.actions_['cut'].setEnabled(True)
            self.actions_['copy'].setEnabled(True)
            self.actions_['shiftitems'].setEnabled(True)



        # turn on the Stamp Add btn if applicable
        self.stampAddBtn.setEnabled(len(selitems) > 0)


        # count the # of each type, for the statusbar label
        spr = 0
        ent = 0
        obj = 0
        loc = 0
        path = 0
        com = 0
        for item in selitems:
            if func_ii(item, type_spr): spr += 1
            elif func_ii(item, type_ent): ent += 1
            elif func_ii(item, type_obj): obj += 1
            elif func_ii(item, type_loc): loc += 1
            elif func_ii(item, type_path): path += 1
            elif func_ii(item, type_com): com += 1

        if loc > 2:
            self.actions_['mergelocations'].setEnabled(True)

        # write the statusbar label text
        text = ''
        if len(selitems) > 0:
            singleitem = len(selitems) == 1
            if singleitem:
                if obj: text = trans.string('Statusbar', 0)  # 1 object selected
                elif spr: text = trans.string('Statusbar', 1)  # 1 sprite selected
                elif ent: text = trans.string('Statusbar', 2)  # 1 entrance selected
                elif loc: text = trans.string('Statusbar', 3)  # 1 location selected
                elif path: text = trans.string('Statusbar', 4)  # 1 path node selected
                else: text = trans.string('Statusbar', 29) # 1 comment selected
            else: # multiple things selected; see if they're all the same type
                if not any((spr, ent, loc, path, com)):
                    text = trans.string('Statusbar', 5, '[x]', obj) # x objects selected
                elif not any((obj, ent, loc, path, com)):
                    text = trans.string('Statusbar', 6, '[x]', spr) # x sprites selected
                elif not any((obj, spr, loc, path, com)):
                    text = trans.string('Statusbar', 7, '[x]', ent) # x entrances selected
                elif not any((obj, spr, ent, path, com)):
                    text = trans.string('Statusbar', 8, '[x]', loc) # x locations selected
                elif not any((obj, spr, ent, loc, com)):
                    text = trans.string('Statusbar', 9, '[x]', path) # x path nodes selected
                elif not any((obj, spr, ent, loc, path)):
                    text = trans.string('Statusbar', 30, '[x]', com) # x comments selected
                else: # different types
                    text = trans.string('Statusbar', 10, '[x]', len(selitems)) # x items selected
                    types = (
                        (obj, 12, 13), # variable, translation string ID if var == 1, translation string ID if var > 1
                        (spr, 14, 15),
                        (ent, 16, 17),
                        (loc, 18, 19),
                        (path, 20, 21),
                        (com, 31, 32),
                        )
                    first = True
                    for var, singleCode, multiCode in types:
                        if var > 0:
                            if not first: text += trans.string('Statusbar', 11)
                            first = False
                            text += trans.string('Statusbar', (singleCode if var == 1 else multiCode), '[x]', var)
                            # above: '[x]', var) can't hurt if var == 1

                    text += trans.string('Statusbar', 22) # ')'
        self.selectionLabel.setText(text)

        self.CurrentSelection = selitems

        for thing in selitems:
            # This helps sync non-objects with objects while dragging
            if not isinstance(thing, ObjectItem):
                thing.dragoffsetx = (((thing.objx // 16) * 16) - thing.objx) * TileWidth / 16
                thing.dragoffsety = (((thing.objy // 16) * 16) - thing.objy) * TileWidth / 16

        self.spriteEditorDock.setVisible(showSpritePanel)
        self.entranceEditorDock.setVisible(showEntrancePanel)
        self.objectEditorDock.setVisible(showObjPanel)
        self.locationEditorDock.setVisible(showLocationPanel)
        self.pathEditorDock.setVisible(showPathPanel)

        if len(self.CurrentSelection) > 0:
            self.actions_['deselect'].setEnabled(True)
        else:
            self.actions_['deselect'].setEnabled(False)

        if updateModeInfo: self.UpdateModeInfo()

    def HandleObjPosChange(self, obj, oldx, oldy, x, y):
        """
        Handle the object being dragged
        """
        if obj == self.selObj:
            if oldx == x and oldy == y: return
            SetDirty()
        self.levelOverview.update()

    def CreationTabChanged(self, nt):
        """
        Handles the selected palette tab changing
        """
        idx = self.creationTabs.currentIndex()
        CPT = -1
        if idx == 0: # objects
            CPT = self.objMetaTab.currentIndex()
            # 0: OBJECT_FROM_MAIN
            # 1: OBJECT_FROM_MEGA
            # 2: OBJECT_FROM_EMBED
        elif idx == 1: # sprites
            CPT = 4
            if self.sprAllTab.currentIndex() == 1: CPT = -1
        elif idx == 2: CPT = 5 # entrances
        elif idx == 3: CPT = 7 # locations
        elif idx == 4: CPT = 6 # paths
        elif idx == 6: CPT = -1 # events
        elif idx == 7: CPT = 8 # stamp pad
        elif idx == 8: CPT = 9 # comment

        global CurrentPaintType
        CurrentPaintType = CPT

    def ObjTabChanged(self, newTab):
        """
        Handles the selected slot tab in the object palette changing
        """
        if not hasattr(self, 'objPicker'): return

        if newTab >= 0 and newTab <= 2:
            self.objPicker.ShowTileset(newTab)

        if newTab == 0:
            picker = self.objPicker.mainPicker
        elif newTab == 1:
            picker = self.objPicker.megaPicker
        elif newTab == 2:
            picker = self.objPicker.embedPicker
        self.defaultPropDock.setVisible(False)
        global CurrentPaintType, CurrentObject
        CurrentPaintType = newTab
        try:
            CurrentObject = picker
        except:
            CurrentObject = 0

    def SprTabChanged(self, nt):
        """
        Handles the selected tab in the sprite palette changing
        """
        if nt == 0: cpt = 4
        else: cpt = -1
        global CurrentPaintType
        CurrentPaintType = cpt

    def LayerChoiceChanged(self, nl):
        """
        Handles the selected layer changing
        """
        global CurrentLayer
        CurrentLayer = nl

        # should we replace?
        if QtWidgets.QApplication.keyboardModifiers() == Qt.AltModifier:
            items = self.scene.selectedItems()
            type_obj = ObjectItem
            tileset = CurrentPaintType
            area = Area
            change = []

            if nl == 0:
                newLayer = area.layers[0]
            elif nl == 1:
                newLayer = area.layers[1]
            else:
                newLayer = area.layers[2]

            for x in items:
                if isinstance(x, type_obj) and x.layer != nl:
                    change.append(x)

            if len(change) > 0:
                change.sort(key=lambda x: x.zValue())

                if len(newLayer) == 0:
                    z = (2 - nl) * 8192
                else:
                    z = newLayer[-1].zValue() + 1

                if nl == 0:
                    newVisibility = Layer0Shown
                elif nl == 1:
                    newVisibility = Layer1Shown
                else:
                    newVisibility = Layer2Shown

                for item in change:
                    area.RemoveFromLayer(item)
                    item.layer = nl
                    newLayer.append(item)
                    item.setZValue(z)
                    item.setVisible(newVisibility)
                    item.update()
                    item.UpdateTooltip()
                    z += 1

            self.scene.update()
            SetDirty()

    def ObjectChoiceChanged(self):
        """
        Handles a new object being chosen
        """
        global CurrentObject
        CurrentObject = self.objPicker.current[1]

    def ObjectReplace(self):
        """
        Handles a new object being chosen to replace the selected objects
        """
        idx = self.objPicker.current[1]

        items = self.scene.selectedItems()
        type_obj = ObjectItem
        from_ = {0: OBJECT_FROM_MAIN, 1: OBJECT_FROM_MEGA, 2: OBJECT_FROM_EMBED}[CurrentPaintType]
        changed = False

        for x in items:
            if isinstance(x, type_obj) and (x.from_ != from_ or x.idx != idx):
                x.SetType(from_, idx)
                x.update()
                changed = True

        if changed:
            SetDirty()

    def EmbeddedObjectUpdate(self, idx):
        """
        Handles embedded object # idx being updated
        """
        for layer in Area.layers:
            for obj in layer:
                if obj.from_ == OBJECT_FROM_EMBED and obj.idx == idx:
                    obj.updateObjCache()
                    obj.update()

        self.updateTileCountLabel(force=True)
        SetDirty()

    def EmbeddedObjectDeleteRequest(self, idx):
        """
        The user would like to delete embedded object
        idx. Let them know if that can be done.
        Return True if you can go ahead and delete it;
        False otherwise.
        """
        matchingObjs = []
        for layer in Area.layers:
            for obj in layer:
                if obj.from_ == OBJECT_FROM_EMBED and obj.idx == idx:
                    matchingObjs.append(obj)

        if matchingObjs:
            where = [('(%d, %d)' % (obj.objx, obj.objy)) for obj in matchingObjs]
            dlgTxt = "You can't delete this object because there are instances of it at the following coordinates:\n"
            dlgTxt += ', '.join(where)
            dlgTxt += '\nPlease remove or replace them before deleting this object.'

            QtWidgets.QMessageBox.critical(self, 'Cannot Delete', dlgTxt)
            return False

        return True

    def EmbeddedObjectDelete(self, idx):
        """
        Handles embedded object # idx being deleted
        """
        for layer in Area.layers:
            for obj in layer:
                if obj.from_ == OBJECT_FROM_EMBED and obj.idx > idx:
                    obj.SetType(obj.from_, obj.idx - 1)
                    obj.update()

        self.updateTileCountLabel()
        SetDirty()

    def SpriteChoiceChanged(self, type):
        """
        Handles a new sprite being chosen
        """
        global CurrentSprite
        CurrentSprite = type
        if type != 1000 and type >= 0:
            self.defaultDataEditor.setSprite(type)
            self.defaultDataEditor.data = b'\0\0\0\0\0\0\0\0\0\0\0\0'
            self.defaultDataEditor.update()
            self.defaultPropButton.setEnabled(True)
        else:
            self.defaultPropButton.setEnabled(False)
            self.defaultPropDock.setVisible(False)
            self.defaultDataEditor.update()

    def SpriteReplace(self, type):
        """
        Handles a new sprite type being chosen to replace the selected sprites
        """
        items = self.scene.selectedItems()
        type_spr = SpriteItem
        changed = False

        for x in items:
            if isinstance(x, type_spr):
                x.spritedata = self.defaultDataEditor.data # change this first or else images get messed up
                x.SetType(type)
                x.update()
                changed = True

        if changed:
            SetDirty()

        self.ChangeSelectionHandler()

    def SelectNewSpriteView(self, type):
        """
        Handles a new sprite view being chosen
        """
        cat = SpriteCategories[type]
        self.sprPicker.SwitchView(cat)

        isSearch = (type == len(SpriteCategories) - 1)
        layout = self.spriteSearchLayout
        layout.itemAt(0).widget().setVisible(isSearch)
        layout.itemAt(1).widget().setVisible(isSearch)

    def NewSearchTerm(self, text):
        """
        Handles a new sprite search term being entered
        """
        self.sprPicker.SetSearchString(text)

    def ShowDefaultProps(self):
        """
        Handles the Show Default Properties button being clicked
        """
        self.defaultPropDock.setVisible(True)

    def HandleSprPosChange(self, obj, oldx, oldy, x, y):
        """
        Handle the sprite being dragged
        """
        if obj == self.selObj:
            if oldx == x and oldy == y: return
            obj.UpdateListItem()
            SetDirty()

    def SpriteDataUpdated(self, data):
        """
        Handle the current sprite's data being updated
        """
        if self.spriteEditorDock.isVisible():
            obj = self.selObj
            obj.spritedata = data
            obj.UpdateListItem()
            SetDirty()

            obj.UpdateDynamicSizing()

    def HandleEntPosChange(self, obj, oldx, oldy, x, y):
        """
        Handle the entrance being dragged
        """
        if oldx == x and oldy == y: return
        obj.UpdateListItem()
        if obj == self.selObj:
            SetDirty()

    def HandlePathPosChange(self, obj, oldx, oldy, x, y):
        """
        Handle the path being dragged
        """
        if oldx == x and oldy == y: return
        obj.updatePos()
        obj.pathinfo['peline'].nodePosChanged()
        obj.UpdateListItem()
        if obj == self.selObj:
            SetDirty()

    def HandleComPosChange(self, obj, oldx, oldy, x, y):
        """
        Handle the comment being dragged
        """
        if oldx == x and oldy == y: return
        obj.UpdateTooltip()
        obj.handlePosChange(oldx, oldy)
        obj.UpdateListItem()
        if obj == self.selObj:
            self.SaveComments()
            SetDirty()

    def HandleComTxtChange(self, obj):
        """
        Handle the comment's text being changed
        """
        obj.UpdateListItem()
        obj.UpdateTooltip()
        self.SaveComments()
        SetDirty()

    def HandleEntranceSelectByList(self, item):
        """
        Handle an entrance being selected from the list
        """
        if self.UpdateFlag: return

        # can't really think of any other way to do this
        #item = self.entranceList.item(row)
        ent = None
        for check in Area.entrances:
            if check.listitem == item:
                ent = check
                break
        if ent is None: return

        ent.ensureVisible(QtCore.QRectF(), 192, 192)
        self.scene.clearSelection()
        ent.setSelected(True)

    def HandleEntranceToolTipAboutToShow(self, item):
        """
        Handle an entrance being hovered in the list
        """
        ent = None
        for check in Area.entrances:
            if check.listitem == item:
                ent = check
                break
        if ent is None: return

        ent.UpdateListItem(True)

    def HandleLocationSelectByList(self, item):
        """
        Handle a location being selected from the list
        """
        if self.UpdateFlag: return

        # can't really think of any other way to do this
        #item = self.locationList.item(row)
        loc = None
        for check in Area.locations:
            if check.listitem == item:
                loc = check
                break
        if loc is None: return

        loc.ensureVisible(QtCore.QRectF(), 192, 192)
        self.scene.clearSelection()
        loc.setSelected(True)

    def HandleLocationToolTipAboutToShow(self, item):
        """
        Handle a location being hovered in the list
        """
        loc = None
        for check in Area.locations:
            if check.listitem == item:
                loc = check
                break
        if loc is None: return

        loc.UpdateListItem(True)

    def HandleSpriteSelectByList(self, item):
        """
        Handle a sprite being selected from the list
        """
        if self.UpdateFlag: return

        # can't really think of any other way to do this
        #item = self.spriteList.item(row)
        spr = None
        for check in Area.sprites:
            if check.listitem == item:
                spr = check
                break
        if spr is None: return

        spr.ensureVisible(QtCore.QRectF(), 192, 192)
        self.scene.clearSelection()
        spr.setSelected(True)

    def HandleSpriteToolTipAboutToShow(self, item):
        """
        Handle a sprite being hovered in the list
        """
        spr = None
        for check in Area.sprites:
            if check.listitem == item:
                spr = check
                break
        if spr is None: return

        spr.UpdateListItem(True)

    def HandlePathSelectByList(self, item):
        """
        Handle a path node being selected
        """
        #if self.UpdateFlag: return

        #can't really think of any other way to do this
        #item = self.pathlist.item(row)
        path = None
        for check in Area.paths:
           if check.listitem == item:
                path = check
                break
        if path is None: return

        path.ensureVisible(QtCore.QRectF(), 192, 192)
        self.scene.clearSelection()
        path.setSelected(True)

    def HandlePathToolTipAboutToShow(self, item):
        """
        Handle a path node being hovered in the list
        """
        path = None
        for check in Area.paths:
           if check.listitem == item:
                path = check
                break
        if path is None: return

        path.UpdateListItem(True)

    def HandleCommentSelectByList(self, item):
        """
        Handle a comment being selected
        """
        comment = None
        for check in Area.comments:
           if check.listitem == item:
                comment = check
                break
        if comment is None: return

        comment.ensureVisible(QtCore.QRectF(), 192, 192)
        self.scene.clearSelection()
        comment.setSelected(True)

    def HandleCommentToolTipAboutToShow(self, item):
        """
        Handle a comment being hovered in the list
        """
        comment = None
        for check in Area.comments:
           if check.listitem == item:
                comment = check
                break
        if comment is None: return

        comment.UpdateListItem(True)

    def HandleLocPosChange(self, loc, oldx, oldy, x, y):
        """
        Handle the location being dragged
        """
        if loc == self.selObj:
            if oldx == x and oldy == y: return
            self.locationEditor.setLocation(loc)
            SetDirty()
        loc.UpdateListItem()
        self.levelOverview.update()

    def HandleLocSizeChange(self, loc, width, height):
        """
        Handle the location being resized
        """
        if loc == self.selObj:
            self.locationEditor.setLocation(loc)
            SetDirty()
        loc.UpdateListItem()
        self.levelOverview.update()

    def UpdateModeInfo(self):
        """
        Change the info in the currently visible panel
        """
        self.UpdateFlag = True

        if self.spriteEditorDock.isVisible():
            obj = self.selObj
            self.spriteDataEditor.setSprite(obj.type)
            self.spriteDataEditor.data = obj.spritedata
            self.spriteDataEditor.update()
        elif self.entranceEditorDock.isVisible():
            self.entranceEditor.setEntrance(self.selObj)
        elif self.pathEditorDock.isVisible():
            self.pathEditor.setPath(self.selObj)
        elif self.locationEditorDock.isVisible():
            self.locationEditor.setLocation(self.selObj)
        elif self.objectEditorDock.isVisible():
            self.objectEditor.setObject(self.selObj)

        self.UpdateFlag = False

    def PositionHovered(self, x, y):
        """
        Handle a position being hovered in the view
        """
        info = ''
        hovereditems = self.scene.items(QtCore.QPointF(x, y))
        hovered = None
        type_zone = ZoneItem
        type_peline = PathEditorLineItem
        for item in hovereditems:
            hover = item.hover if hasattr(item, 'hover') else True
            if (not isinstance(item, type_zone)) and (not isinstance(item, type_peline)) and hover:
                hovered = item
                break

        if hovered is not None:
            if isinstance(hovered, ObjectItem): # Object
                extraStrId = {OBJECT_FROM_MAIN: 40, OBJECT_FROM_MEGA: 41, OBJECT_FROM_EMBED: 42}[hovered.from_]
                extra = trans.string('Statusbar', extraStrId, '[id]', hovered.idx)
                if hovered.data != 0:
                    extra += trans.string('Statusbar', 43, '[val]', hovered.data)
                info = trans.string('Statusbar', 23, '[width]', hovered.width, '[height]', hovered.height, '[xpos]', hovered.objx, '[ypos]', hovered.objy, '[layer]', hovered.layer, '[info]', extra)
            elif isinstance(hovered, SpriteItem): # Sprite
                info = trans.string('Statusbar', 24, '[name]', hovered.name, '[xpos]', hovered.objx, '[ypos]', hovered.objy)
            elif isinstance(hovered, SLib.AuxiliaryItem): # Sprite (auxiliary thing) (treat it like the actual sprite)
                info = trans.string('Statusbar', 24, '[name]', hovered.parentItem().name, '[xpos]', hovered.parentItem().objx, '[ypos]', hovered.parentItem().objy)
            elif isinstance(hovered, EntranceItem): # Entrance
                info = trans.string('Statusbar', 25, '[name]', hovered.name, '[xpos]', hovered.objx, '[ypos]', hovered.objy, '[dest]', hovered.destination)
            elif isinstance(hovered, LocationItem): # Location
                info = trans.string('Statusbar', 26, '[id]', int(hovered.id), '[xpos]', int(hovered.objx), '[ypos]', int(hovered.objy), '[width]', int(hovered.width), '[height]', int(hovered.height))
            elif isinstance(hovered, PathItem): # Path
                info = trans.string('Statusbar', 27, '[path]', hovered.pathid, '[node]', hovered.nodeid, '[xpos]', hovered.objx, '[ypos]', hovered.objy)
            elif isinstance(hovered, CommentItem): # Comment
                info = trans.string('Statusbar', 33, '[xpos]', hovered.objx, '[ypos]', hovered.objy, '[text]', hovered.OneLineText())

        self.posLabel.setText(trans.string('Statusbar', 28, '[objx]', int(x/TileWidth), '[objy]', int(y/TileWidth), '[sprx]', int(x/TileWidth*16), '[spry]', int(y/TileWidth*16)))
        self.hoverLabel.setText(info)

    def updateTileCountLabel(self, *, force=False):
        """
        Update the tile-count label
        """

        # Get all of the OneTileset objects used in the level
        oneTsetObjNames = set()
        for layer in Area.layers:
            for obj in layer:
                if obj.from_ == OBJECT_FROM_MEGA:
                    oneTsetObjNames.add(obj.idx)
        oneTsetObjs = []
        for i, name in enumerate(oneTsetObjNames):
            oneTsetObjs.append(OneTilesetObjects[name])

        # Don't count tiles if nothing has changed
        allObjs = EmbeddedObjects + oneTsetObjs
        if not force:
            # This nested if statement will prevent it from crashing if force and not hasattr()
            if hasattr(self, 'allObjCount') and len(allObjs) == self.allObjCount: return
        self.allObjCount = len(allObjs)

        # Count tiles and set up the label text
        tileCount = nsmbulib.Tileset.tileCount(allObjs)
        labelText = str(tileCount) + '/768 tiles (' + str(tileCount / 768 * 100)[:5] + '%)'
        if tileCount > 768:
            labelText = '<span style="color:red;font-weight:bold;">' + labelText + '</span>'
        self.tileCountLabel.setText(labelText)

    def keyPressEvent(self, event):
        """
        Handles key press events for the main window if needed
        """
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            sel = self.scene.selectedItems()
            self.SelectionUpdateFlag = True
            if len(sel) > 0:
                for obj in sel:
                    obj.delete()
                    obj.setSelected(False)
                    self.scene.removeItem(obj)
                    self.levelOverview.update()
                SetDirty()
                event.accept()
                self.SelectionUpdateFlag = False
                self.ChangeSelectionHandler()
                return
        self.levelOverview.update()

        QtWidgets.QMainWindow.keyPressEvent(self, event)

    def HandleAreaOptions(self):
        """
        Pops up the options for Area Dialog
        """
        dlg = AreaOptionsDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            SetDirty()
            Area.timeLimit = dlg.LoadingTab.timer.value() - 100
            Area.unk1 = dlg.LoadingTab.unk1.value()
            Area.unk2 = dlg.LoadingTab.unk2.value()
            Area.unk3 = dlg.LoadingTab.unk3.value()
            Area.unk4 = dlg.LoadingTab.unk4.value()
            Area.unk5 = dlg.LoadingTab.unk5.value()
            Area.unk6 = dlg.LoadingTab.unk6.value()
            Area.unk7 = dlg.LoadingTab.unk7.value()
            Area.timelimit2 = dlg.LoadingTab.timelimit2.value()
            Area.timelimit3 = dlg.LoadingTab.timelimit3.value()

            if dlg.LoadingTab.wrap.isChecked():
                Area.wrapFlag |= 1
            else:
                Area.wrapFlag &= ~1

    def HandleZones(self):
        """
        Pops up the options for Zone dialog
        """
        dlg = ZonesDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            SetDirty()
            i = 0

            # resync the zones
            items = self.scene.items()
            func_ii = isinstance
            type_zone = ZoneItem

            for item in items:
                if func_ii(item, type_zone):
                    self.scene.removeItem(item)

            Area.zones = []

            for tab in dlg.zoneTabs:
                z = tab.zoneObj
                z.id = i
                z.UpdateTitle()
                Area.zones.append(z)
                self.scene.addItem(z)

                if tab.Zone_xpos.value() < 16:
                    z.objx = 16
                elif tab.Zone_xpos.value() > 24560:
                    z.objx = 24560
                else:
                    z.objx = tab.Zone_xpos.value()

                if tab.Zone_ypos.value() < 16:
                    z.objy = 16
                elif tab.Zone_ypos.value() > 12272:
                    z.objy = 12272
                else:
                    z.objy = tab.Zone_ypos.value()

                if (tab.Zone_width.value() + tab.Zone_xpos.value()) > 24560:
                    z.width = 24560 - tab.Zone_xpos.value()
                else:
                    z.width = tab.Zone_width.value()

                if (tab.Zone_height.value() + tab.Zone_ypos.value()) > 12272:
                    z.height = 12272 - tab.Zone_ypos.value()
                else:
                    z.height = tab.Zone_height.value()

                z.prepareGeometryChange()
                z.UpdateRects()
                z.setPos(z.objx*(TileWidth/16), z.objy*(TileWidth/16))

                z.modeldark = tab.Zone_modeldark.currentIndex()
                # z.terraindark = tab.Zone_terraindark.currentIndex()

                if tab.Zone_xtrack.isChecked():
                    if tab.Zone_ytrack.isChecked():
                        if tab.Zone_camerabias.isChecked():
                            #Xtrack, YTrack, Bias
                            if tab.Zone_camerazoom.currentIndex() == 0:
                                z.cammode = 0
                                z.camzoom = 8
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 62))
                            elif tab.Zone_camerazoom.currentIndex() == 1:
                                z.cammode = 3
                                z.camzoom = 9
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 63))
                            elif tab.Zone_camerazoom.currentIndex() == 2:
                                z.cammode = 0
                                z.camzoom = 1
                            elif tab.Zone_camerazoom.currentIndex() == 3:
                                z.cammode = 0
                                z.camzoom = 6
                            elif tab.Zone_camerazoom.currentIndex() == 4:
                                z.cammode = 0
                                z.camzoom = 4
                            elif tab.Zone_camerazoom.currentIndex() == 5:
                                z.cammode = 0
                                z.camzoom = 3
                            elif tab.Zone_camerazoom.currentIndex() == 6:
                                z.cammode = 3
                                z.camzoom = 3
                        else:
                            #Xtrack, YTrack, No Bias
                            if tab.Zone_camerazoom.currentIndex() == 0:
                                z.cammode = 0
                                z.camzoom = 8
                            elif tab.Zone_camerazoom.currentIndex() == 1:
                                z.cammode = 3
                                z.camzoom = 9
                            elif tab.Zone_camerazoom.currentIndex() == 2:
                                z.cammode = 0
                                z.camzoom = 0
                            elif tab.Zone_camerazoom.currentIndex() == 3:
                                z.cammode = 0
                                z.camzoom = 7
                            elif tab.Zone_camerazoom.currentIndex() == 4:
                                z.cammode = 0
                                z.camzoom = 11
                            elif tab.Zone_camerazoom.currentIndex() == 5:
                                z.cammode = 3
                                z.camzoom = 2
                            elif tab.Zone_camerazoom.currentIndex() == 6:
                                z.cammode = 3
                                z.camzoom = 7
                    else:
                        if tab.Zone_camerabias.isChecked():
                            #Xtrack, No YTrack, Bias
                            z.cammode = 6
                            if tab.Zone_camerazoom.currentIndex() == 0:
                                z.camzoom = 8
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 62))
                            elif tab.Zone_camerazoom.currentIndex() == 1:
                                z.camzoom = 1
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 63))
                            elif tab.Zone_camerazoom.currentIndex() == 2:
                                z.camzoom = 2
                            elif tab.Zone_camerazoom.currentIndex() == 3:
                                z.camzoom = 6
                            elif tab.Zone_camerazoom.currentIndex() == 4:
                                z.camzoom = 4
                            elif tab.Zone_camerazoom.currentIndex() == 5:
                                z.camzoom = 3
                            elif tab.Zone_camerazoom.currentIndex() == 6:
                                z.camzoom = 16
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 65))
                        else:
                            #Xtrack, No YTrack, No Bias
                            z.cammode = 6
                            if tab.Zone_camerazoom.currentIndex() == 0:
                                z.camzoom = 8
                            elif tab.Zone_camerazoom.currentIndex() == 1:
                                z.camzoom = 0
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 64))
                            elif tab.Zone_camerazoom.currentIndex() == 2:
                                z.camzoom = 0
                            elif tab.Zone_camerazoom.currentIndex() == 3:
                                z.camzoom = 7
                            elif tab.Zone_camerazoom.currentIndex() == 4:
                                z.camzoom = 11
                            elif tab.Zone_camerazoom.currentIndex() == 5:
                                z.camzoom = 3
                            elif tab.Zone_camerazoom.currentIndex() == 6:
                                z.camzoom = 16
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 65))
                else:
                    if tab.Zone_ytrack.isChecked():
                        if tab.Zone_camerabias.isChecked():
                            #No Xtrack, YTrack, Bias
                            if tab.Zone_camerazoom.currentIndex() == 0:
                                z.cammode = 1
                                z.camzoom = 8
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 62))
                            elif tab.Zone_camerazoom.currentIndex() == 1:
                                z.cammode = 4
                                z.camzoom = 9
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 63))
                            elif tab.Zone_camerazoom.currentIndex() == 2:
                                z.cammode = 1
                                z.camzoom = 1
                            elif tab.Zone_camerazoom.currentIndex() == 3:
                                z.cammode = 1
                                z.camzoom = 10
                            elif tab.Zone_camerazoom.currentIndex() == 4:
                                z.cammode = 1
                                z.camzoom = 4
                            elif tab.Zone_camerazoom.currentIndex() == 5:
                                z.cammode = 1
                                z.camzoom = 3
                            elif tab.Zone_camerazoom.currentIndex() == 6:
                                z.cammode = 4
                                z.camzoom = 3
                        else:
                            #No Xtrack, YTrack, No Bias
                            if tab.Zone_camerazoom.currentIndex() == 0:
                                z.cammode = 4
                                z.camzoom = 8
                            elif tab.Zone_camerazoom.currentIndex() == 1:
                                z.cammode = 4
                                z.camzoom = 9
                            elif tab.Zone_camerazoom.currentIndex() == 2:
                                z.cammode = 1
                                z.camzoom = 0
                            elif tab.Zone_camerazoom.currentIndex() == 3:
                                z.cammode = 1
                                z.camzoom = 7
                            elif tab.Zone_camerazoom.currentIndex() == 4:
                                z.cammode = 1
                                z.camzoom = 11
                            elif tab.Zone_camerazoom.currentIndex() == 5:
                                z.cammode = 4
                                z.camzoom = 2
                            elif tab.Zone_camerazoom.currentIndex() == 6:
                                z.cammode = 4
                                z.camzoom = 7
                    else:
                        if tab.Zone_camerabias.isChecked():
                            #No Xtrack, No YTrack, Bias (glitchy)
                            if tab.Zone_camerazoom.currentIndex() == 0:
                                z.cammode = 9
                                z.camzoom = 8
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 66))
                            elif tab.Zone_camerazoom.currentIndex() == 1:
                                z.cammode = 9
                                z.camzoom = 20
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 66))
                            elif tab.Zone_camerazoom.currentIndex() == 2:
                                z.cammode = 9
                                z.camzoom = 13
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 66))
                            elif tab.Zone_camerazoom.currentIndex() == 3:
                                z.cammode = 9
                                z.camzoom = 12
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 66))
                            elif tab.Zone_camerazoom.currentIndex() == 4:
                                z.cammode = 9
                                z.camzoom = 14
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 66))
                            elif tab.Zone_camerazoom.currentIndex() == 5:
                                z.cammode = 9
                                z.camzoom = 15
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 66))
                            elif tab.Zone_camerazoom.currentIndex() == 6:
                                z.cammode = 9
                                z.camzoom = 16
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 66))
                        else:
                            #No Xtrack, No YTrack, No Bias (glitchy)
                            if tab.Zone_camerazoom.currentIndex() == 0:
                                z.cammode = 9
                                z.camzoom = 8
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 67))
                            elif tab.Zone_camerazoom.currentIndex() == 1:
                                z.cammode = 9
                                z.camzoom = 19
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 67))
                            elif tab.Zone_camerazoom.currentIndex() == 2:
                                z.cammode = 9
                                z.camzoom = 13
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 67))
                            elif tab.Zone_camerazoom.currentIndex() == 3:
                                z.cammode = 9
                                z.camzoom = 12
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 67))
                            elif tab.Zone_camerazoom.currentIndex() == 4:
                                z.cammode = 9
                                z.camzoom = 14
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 67))
                            elif tab.Zone_camerazoom.currentIndex() == 5:
                                z.cammode = 9
                                z.camzoom = 15
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 67))
                            elif tab.Zone_camerazoom.currentIndex() == 6:
                                z.cammode = 9
                                z.camzoom = 16
                                QtWidgets.QMessageBox.warning(None, trans.string('ZonesDlg', 61), trans.string('ZonesDlg', 67))


                if tab.Zone_vnormal.isChecked():
                    z.visibility = 0
                    z.visibility = z.visibility + tab.Zone_visibility.currentIndex()
                if tab.Zone_vspotlight.isChecked():
                    z.visibility = 16
                    z.visibility = z.visibility + tab.Zone_visibility.currentIndex()
                if tab.Zone_vfulldark.isChecked():
                    z.visibility = 32
                    z.visibility = z.visibility + tab.Zone_visibility.currentIndex()

                # val = tab.Zone_directionmode.currentIndex()*2
                # if val == 2: val = 1
                # z.camtrack = val

                z.yupperbound = tab.Zone_yboundup.value()
                z.ylowerbound = tab.Zone_ybounddown.value()
                z.yupperbound2 = tab.Zone_yboundup2.value()
                z.ylowerbound2 = tab.Zone_ybounddown2.value()
                z.unknownbnf = 0xF if tab.Zone_boundflg.isChecked() else 0

                z.music = tab.Zone_musicid.value()

                z.unk1 = tab.unk0B.value()
                z.cammode = tab.unk0E.value()

                i = i + 1
        self.levelOverview.update()

    # Handles setting the backgrounds
    def HandleBG(self):
        """
        Pops up the Background settings Dialog
        """
        dlg = BGDialog()
        if dlg.exec_() != dlg.Accepted: return

        for i, (z, tab) in enumerate(zip(Area.zones, dlg.tabs)):
            z.bgUnk1 = tab.unk1.value()
            z.bgName = tab.bgName()
            z.bgUnk2 = tab.unk2.value()

        SetDirty()

    def HandleScreenshot(self):
        """
        Takes a screenshot of the entire level and saves it
        """

        dlg = ScreenCapChoiceDialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            fn = QtWidgets.QFileDialog.getSaveFileName(mainWindow, trans.string('FileDlgs', 3), '/untitled.png', trans.string('FileDlgs', 4) + ' (*.png)')[0]
            if fn == '': return
            fn = str(fn)

            if dlg.zoneCombo.currentIndex() == 0:
                ScreenshotImage = QtGui.QImage(mainWindow.view.width(), mainWindow.view.height(), QtGui.QImage.Format_ARGB32)
                ScreenshotImage.fill(Qt.transparent)

                RenderPainter = QtGui.QPainter(ScreenshotImage)
                mainWindow.view.render(RenderPainter, QtCore.QRectF(0, 0, mainWindow.view.width(), mainWindow.view.height()), QtCore.QRect(QtCore.QPoint(0, 0), QtCore.QSize(mainWindow.view.width(), mainWindow.view.height())))
                RenderPainter.end()
            elif dlg.zoneCombo.currentIndex() == 1:
                maxX = maxY = 0
                minX = minY = 0x0ddba11
                for z in Area.zones:
                    if maxX < ((z.objx*(TileWidth/16)) + (z.width*(TileWidth/16))):
                        maxX = ((z.objx*(TileWidth/16)) + (z.width*(TileWidth/16)))
                    if maxY < ((z.objy*(TileWidth/16)) + (z.height*(TileWidth/16))):
                        maxY = ((z.objy*(TileWidth/16)) + (z.height*(TileWidth/16)))
                    if minX > z.objx*(TileWidth/16):
                        minX = z.objx*(TileWidth/16)
                    if minY > z.objy*(TileWidth/16):
                        minY = z.objy*(TileWidth/16)
                maxX = (1024*TileWidth if 1024*TileWidth < maxX+40 else maxX+40)
                maxY = (512*TileWidth if 512*TileWidth < maxY+40 else maxY+40)
                minX = (0 if 40 > minX else minX-40)
                minY = (40 if 40 > minY else minY-40)

                ScreenshotImage = QtGui.QImage(int(maxX - minX), int(maxY - minY), QtGui.QImage.Format_ARGB32)
                ScreenshotImage.fill(Qt.transparent)

                RenderPainter = QtGui.QPainter(ScreenshotImage)
                mainWindow.scene.render(RenderPainter, QtCore.QRectF(0, 0, int(maxX - minX), int(maxY - minY)), QtCore.QRectF(int(minX), int(minY), int(maxX - minX), int(maxY - minY)))
                RenderPainter.end()


            else:
                i = dlg.zoneCombo.currentIndex() - 2
                ScreenshotImage = QtGui.QImage(Area.zones[i].width*TileWidth/16, Area.zones[i].height*TileWidth/16, QtGui.QImage.Format_ARGB32)
                ScreenshotImage.fill(Qt.transparent)

                RenderPainter = QtGui.QPainter(ScreenshotImage)
                mainWindow.scene.render(RenderPainter, QtCore.QRectF(0, 0, Area.zones[i].width*TileWidth/16, Area.zones[i].height*TileWidth/16), QtCore.QRectF(int(Area.zones[i].objx)*TileWidth/16, int(Area.zones[i].objy)*TileWidth/16, Area.zones[i].width*TileWidth/16, Area.zones[i].height*TileWidth/16))
                RenderPainter.end()

            ScreenshotImage.save(fn, 'PNG', 50)

def main():
    """
    Main startup function for Satoru
    """

    global app, mainWindow, settings, SatoruVersion

    # create an application
    app = QtWidgets.QApplication(sys.argv)

    # load the settings
    settings = QtCore.QSettings('Satoru', SatoruVersion)

    global Pa0Path
    if setting('Pa0Path'):
        Pa0Path = setting('Pa0Path')
    else:
        Pa0Path = getPa0Path()

    # load the translation (needs to happen first)
    LoadTranslation()

    # load the style
    GetDefaultStyle()

    # go to the script path
    path = module_path()
    if path is not None:
        os.chdir(module_path())

    # check if required files are missing
    if FilesAreMissing():
        sys.exit(1)

    # load required stuff
    global Sprites
    global SpriteListData
    Sprites = None
    SpriteListData = None
    LoadGameDef()
    LoadTheme()
    LoadActionsLists()
    LoadConstantLists()
    SetAppStyle()
    LoadObjDescriptions()
    LoadSpriteData()
    LoadSpriteListData()
    LoadEntranceNames()
    LoadBackgroundNames()
    LoadNumberFont()
    LoadOverrides()
    LoadOneTileset()
    SLib.OutlineColor = theme.color('smi')
    SLib.main()

    # Set the default window icon (used for random popups and stuff)
    app.setWindowIcon(GetIcon('satoru'))
    app.setApplicationDisplayName('Satoru')

    # Load the splashscreen
    app.splashScreen = SatoruSplashScreen()
    app.splashScreen.setProgressLimit(9)
    app.splashScreen.show()

    global EnableAlpha, GridType, CollisionsShown, DepthShown, RealViewEnabled
    global ObjectsFrozen, SpritesFrozen, EntrancesFrozen, LocationsFrozen, PathsFrozen, CommentsFrozen
    global SpritesShown, SpriteImagesShown, LocationsShown, CommentsShown, PathsShown

    gt = setting('GridType')
    if gt == 'checker': GridType = 'checker'
    elif gt == 'grid': GridType = 'grid'
    else: GridType = None
    CollisionsShown = setting('ShowCollisions', False)
    DepthShown = setting('ShowDepth', False)
    RealViewEnabled = setting('RealViewEnabled', False)
    ObjectsFrozen = setting('FreezeObjects', False)
    SpritesFrozen = setting('FreezeSprites', False)
    EntrancesFrozen = setting('FreezeEntrances', False)
    LocationsFrozen = setting('FreezeLocations', False)
    PathsFrozen = setting('FreezePaths', False)
    CommentsFrozen = setting('FreezeComments', False)
    SpritesShown = setting('ShowSprites', True)
    SpriteImagesShown = setting('ShowSpriteImages', True)
    LocationsShown = setting('ShowLocations', True)
    CommentsShown = setting('ShowComments', True)
    PathsShown = setting('ShowPaths', True)
    SLib.RealViewEnabled = RealViewEnabled

    # choose a folder for the game
    # let the user pick a folder without restarting the editor if they fail
    while not isValidGamePath():
        path = QtWidgets.QFileDialog.getExistingDirectory(None, trans.string('ChangeGamePath', 0, '[game]', gamedef.name))
        if path == '':
            sys.exit(0)

        SetGamePath(path)
        if not isValidGamePath():
            QtWidgets.QMessageBox.information(None, trans.string('ChangeGamePath', 1),  trans.string('ChangeGamePath', 3))
        else:
            setSetting('GamePath_NSMBU', path)
            break

    # create and show the main window
    mainWindow = SatoruWindow()
    mainWindow.__init2__() # fixes bugs
    mainWindow.show()
    app.splashScreen.hide()
    del app.splashScreen
    exitcodesys = app.exec_()
    app.deleteLater()
    sys.exit(exitcodesys)

if '-generatestringsxml' in sys.argv:
    generateStringsXML = True
    ...

if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Save error log to a file
        import traceback
        with open('last_error.txt', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())
        raise
