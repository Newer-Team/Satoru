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


# sprites.py
# Contains code to render NSMBU sprite images
# not even close to done...


################################################################
################################################################

# Imports

from PyQt5 import QtCore, QtGui
Qt = QtCore.Qt
from PIL.ImageQt import ImageQt

import spritelib as SLib
ImageCache = SLib.ImageCache

################################################################
################################################################

# GETTING SPRITEDATA:
# You can get the spritedata that is set on a sprite to alter
# the image that is shown. To do this, add a datachanged method,
# with the parameter self. In this method, you can access the
# spritedata through self.parent.spritedata[n], which returns
# the (n+1)th byte of the spritedata. To find the n for nybble
# x, use this formula:
# n = (x/2) - 1
#
# If the nybble you want is the upper 4 bits of n (x is odd),
# you can get the value of x like this:
# val_x = n >> 4

class SpriteImage_Block(SLib.SpriteImage):
    def __init__(self, parent, scale=1.5):
        super().__init__(parent, scale)
        self.spritebox.shown = False
        self.contentsOverride = None

        self.tilenum = 28
        self.tileheight = 1
        self.tilewidth = 1
        self.yOffset = 0
        self.xOffset = 0
        self.invisiblock = False

    def dataChanged(self):
        super().dataChanged()

        if self.contentsOverride is not None:
            self.image = ImageCache['Items'][self.contentsOverride]
        else:
            self.contents = self.parent.spritedata[9] & 0xF
            self.acorn = (self.parent.spritedata[6] >> 4) & 1

            if self.acorn:
                self.image = ImageCache['Items'][15]
            elif self.contents != 0:
                self.image = ImageCache['Items'][self.contents-1]
            else:
                self.image = None

    def paint(self, painter):
        super().paint(painter)

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if self.tilenum < len(SLib.Tiles):
            if self.invisiblock:
                painter.drawPixmap(0, 0, ImageCache['InvisiBlock'])
            else:
                qimage = QtGui.QImage(ImageQt(next(SLib.Tiles[self.tilenum].allTiles).image))
                qpixmap = QtGui.QPixmap.fromImage(qimage)
                painter.drawPixmap(self.yOffset, self.xOffset, self.tilewidth*60, self.tileheight*60, qpixmap)
        if self.image is not None:
            painter.drawPixmap(0, 0, self.image)

class SpriteImage_Pipe(SLib.SpriteImage):
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.spritebox.shown = self.mini = self.big = self.typeinfluence = False
        self.hasTop = True
        self.direction = 'U'
        self.colours = ("Green", "Red", "Yellow", "Blue")
        self.topY = self.topX = self.colour = self.extraLength = self.x = self.y = 0
        self.width = self.height = 32
        self.pipeHeight = self.pipeWidth = 120
        self.parent.setZValue(24999)

    @staticmethod
    def loadImages():
        if 'PipeTopGreen' not in ImageCache:
            for colour in ("Green", "Red", "Yellow", "Blue"):
                ImageCache['PipeTop%s' % colour] = SLib.GetImg('pipe_%s_top.png' % colour.lower())
                ImageCache['PipeMiddleV%s' % colour] = SLib.GetImg('pipe_%s_middleV.png' % colour.lower())
                ImageCache['PipeMiddleH%s' % colour] = SLib.GetImg('pipe_%s_middleH.png' % colour.lower())
                ImageCache['PipeBottom%s' % colour] = SLib.GetImg('pipe_%s_bottom.png' % colour.lower())
                ImageCache['PipeLeft%s' % colour] = SLib.GetImg('pipe_%s_left.png' % colour.lower())
                ImageCache['PipeRight%s' % colour] = SLib.GetImg('pipe_%s_right.png' % colour.lower())

                # BIG
                ImageCache['PipeBigTop%s' % colour] = ImageCache['PipeRight%s' % colour].scaled(240,240,QtCore.Qt.KeepAspectRatio)
                ImageCache['PipeBigMiddleV%s' % colour] = ImageCache['PipeRight%s' % colour].scaled(60,240)
                ImageCache['PipeBigMiddleH%s' % colour] = ImageCache['PipeRight%s' % colour].scaled(60,240)
                ImageCache['PipeBigBottom%s' % colour] = ImageCache['PipeBottom%s' % colour].scaled(240,240,QtCore.Qt.KeepAspectRatio)
                ImageCache['PipeBigLeft%s' % colour] = ImageCache['PipeLeft%s' % colour].scaled(240,240,QtCore.Qt.KeepAspectRatio)
                ImageCache['PipeBigRight%s' % colour] = ImageCache['PipeRight%s' % colour].scaled(240,240,QtCore.Qt.KeepAspectRatio)

                # MINI
                if colour == "Green":
                    ImageCache['MiniPipeTop%s' % colour] = SLib.GetImg('pipe_mini_%s_top.png' % colour.lower())
                    ImageCache['MiniPipeMiddleV%s' % colour] = SLib.GetImg('pipe_mini_%s_middleV.png' % colour.lower())
                    ImageCache['MiniPipeMiddleH%s' % colour] = SLib.GetImg('pipe_mini_%s_middleH.png' % colour.lower())
                    ImageCache['MiniPipeBottom%s' % colour] = SLib.GetImg('pipe_mini_%s_bottom.png' % colour.lower())
                    ImageCache['MiniPipeLeft%s' % colour] = SLib.GetImg('pipe_mini_%s_left.png' % colour.lower())
                    ImageCache['MiniPipeRight%s' % colour] = SLib.GetImg('pipe_mini_%s_right.png' % colour.lower())

    def dataChanged(self):
        super().dataChanged()
        rawlength = (self.parent.spritedata[5] & 0x0F) + 1
        if not self.mini:
            rawtop = (self.parent.spritedata[2] >> 4) & 3
            rawcolour = (self.parent.spritedata[5] >> 4) & 3

            if self.typeinfluence and rawtop == 0:
                rawtype = self.parent.spritedata[3] & 3
            else:
                rawtype = 0

            if rawtop < 2:
                pipeLength = rawlength + rawtype + self.extraLength + 1
            else:
                pipeLength = rawlength + rawtype + self.extraLength

            self.hasTop = (rawtop != 3)
            self.big = (rawtype == 3)
            self.colour = self.colours[rawcolour]
        else:
            pipeLength = rawlength
            self.colour = "Green"

        if self.direction in 'LR': # horizontal
            self.pipeWidth = pipeLength * 60
            self.width = (self.pipeWidth/3.75)
            if self.big:
                self.middle = ImageCache['PipeBigMiddleH%s' % self.colour]
                self.height = 64
                self.pipeHeight = 240
            elif not self.mini:
                self.middle = ImageCache['PipeMiddleH%s' % self.colour]
            else:
                self.middle = ImageCache['MiniPipeMiddleH%s' % self.colour]
                self.height = 16
                self.pipeHeight = 60

            if self.direction == 'R': # faces right
                if self.big:
                    self.top = ImageCache['PipeBigRight%s' % self.colour]
                elif not self.mini:
                    self.top = ImageCache['PipeRight%s' % self.colour]
                else:
                    self.top = ImageCache['MiniPipeRight%s' % self.colour]
                self.topX = self.pipeWidth - 60
            else: # faces left
                if self.big:
                    self.top = ImageCache['PipeBigLeft%s' % self.colour]
                elif not self.mini:
                    self.top = ImageCache['PipeLeft%s' % self.colour]
                else:
                    self.top = ImageCache['MiniPipeLeft%s' % self.colour]
                self.xOffset = 16 - self.width

        if self.direction in 'UD': # vertical
            self.pipeHeight = pipeLength * 60
            self.height = (self.pipeHeight/3.75)
            if self.big:
                self.middle = ImageCache['PipeBigMiddleV%s' % self.colour]
                self.width = 64
                self.pipeWidth = 240
            elif not self.mini:
                self.middle = ImageCache['PipeMiddleV%s' % self.colour]
            else:
                self.middle = ImageCache['MiniPipeMiddleV%s' % self.colour]
                self.width = 16
                self.pipeWidth = 60

            if self.direction == 'D': # faces down
                if self.big:
                    self.top = ImageCache['PipeBigBottom%s' % self.colour]
                elif not self.mini:
                    self.top = ImageCache['PipeBottom%s' % self.colour]
                else:
                    self.top = ImageCache['MiniPipeBottom%s' % self.colour]
                self.topY = self.pipeHeight - 60
            else: # faces up
                if self.big:
                    self.top = ImageCache['PipeBigTop%s' % self.colour]
                elif not self.mini:
                    self.top = ImageCache['PipeTop%s' % self.colour]
                else:
                    self.top = ImageCache['MiniPipeTop%s' % self.colour]
                self.yOffset = 16 - (self.pipeHeight/3.75)

    def paint(self, painter):
        super().paint(painter)
        painter.drawTiledPixmap(self.x, self.y, self.pipeWidth, self.pipeHeight, self.middle)
        if self.hasTop:
            painter.drawPixmap(self.topX, self.topY, self.top)

class SpriteImage_Goomba(SLib.SpriteImage_Static): # 0
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Goomba'],
            (-1.07, -2.67),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Goomba', 'goomba.png')

class SpriteImage_Paragoomba(SLib.SpriteImage_Static): # 1
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Paragoomba'],
            (-0.25, -10.5),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Paragoomba', 'paragoomba.png')

class SpriteImage_PipePiranhaUp(SLib.SpriteImage_Static): # 2
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['PipePiranhaUp'],
            (2.67, -29.6),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('PipePiranhaUp', 'pipe_piranha_up.png')

class SpriteImage_PipePiranhaDown(SLib.SpriteImage_Static): # 3
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['PipePiranhaDown'],
            (2.67, 16),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('PipePiranhaDown', 'pipe_piranha_down.png')

class SpriteImage_PipePiranhaLeft(SLib.SpriteImage_Static): # 4
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['PipePiranhaLeft'],
            (-29.6, 2.67),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('PipePiranhaLeft', 'pipe_piranha_left.png')

class SpriteImage_PipePiranhaRight(SLib.SpriteImage_Static): # 5
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['PipePiranhaRight'],
            (32, 4.8),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('PipePiranhaRight', 'pipe_piranha_right.png')

class SpriteImage_KoopaTroopa(SLib.SpriteImage_StaticMultiple): # 19
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['KoopaG'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('KoopaG', 'koopa_green.png')
        SLib.loadIfNotInImageCache('KoopaR', 'koopa_red.png')
        SLib.loadIfNotInImageCache('KoopaSG', 'koopa_shell_green.png')
        SLib.loadIfNotInImageCache('KoopaSR', 'koopa_shell_red.png')

    def dataChanged(self):
        shellcolour = self.parent.spritedata[5] & 1
        inshell = self.parent.spritedata[5] & 0x10

        if inshell == 0:
            self.xOffset = -3.20
            self.yOffset = -12.54
        else:
            self.xOffset = -0.8
            self.yOffset = 0.8

        if shellcolour == 0:
            if inshell == 0:
                self.image = ImageCache['KoopaG']
            else:
                self.image = ImageCache['KoopaSG']
        else:
            if inshell == 0:
                self.image = ImageCache['KoopaR']
            else:
                self.image = ImageCache['KoopaSR']

        super().dataChanged()

class SpriteImage_ParaKoopa(SLib.SpriteImage_StaticMultiple): # 20
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['ParaKoopaG'],
            (-3.73, -13.87),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('ParaKoopaG', 'parakoopa_green.png')
        SLib.loadIfNotInImageCache('ParaKoopaR', 'parakoopa_red.png')

    def dataChanged(self):
        shellcolour = self.parent.spritedata[5] & 1

        if shellcolour == 0:
            self.image = ImageCache['ParaKoopaG']
        else:
            self.image = ImageCache['ParaKoopaR']

        super().dataChanged()

class SpriteImage_BuzzyBeetle(SLib.SpriteImage_Static): # 22
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BuzzyBeetle'],
            (-0.53, 0.53),
            )

    @staticmethod
    def loadImages():
        if 'BuzzyBeetle' not in ImageCache:
            image = SLib.GetImg('buzzy_beetle.png', True)
            ImageCache['BuzzyBeetle'] = QtGui.QPixmap.fromImage(image)
            ImageCache['BuzzyBeetle_R'] = QtGui.QPixmap.fromImage(image.mirrored(1, 0))

    def dataChanged(self):
        direction = self.parent.spritedata[4] & 0x0F

        if direction == 1:
            self.image = ImageCache['BuzzyBeetle_R']
        else:
            self.image = ImageCache['BuzzyBeetle']

        super().dataChanged()

class SpriteImage_ArrowSignboard(SLib.SpriteImage_StaticMultiple): # 32
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['ArrowSign0'],
            (-7,-14),
            )

    @staticmethod
    def loadImages():
        for i in range(0,8):
            for j in ('', 's'):
                SLib.loadIfNotInImageCache('ArrowSign{0}{1}'.format(i, j), 'sign{0}{1}.png'.format(i, j))

    def dataChanged(self):
        direction = self.parent.spritedata[5] & 0xF
        if direction > 7: direction -= 8
        appear_raw = self.parent.spritedata[3] >> 4
        appear = ''
        if appear_raw == 1:
            appear = 's'

        self.image = ImageCache['ArrowSign{0}{1}'.format(direction, appear)]

        super().dataChanged()

class SpriteImage_Spiny(SLib.SpriteImage_StaticMultiple): # 23
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )

        self.yOffset = -1

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Spiny', 'spiny_norm.png')
        SLib.loadIfNotInImageCache('SpinyBall', 'spiny_ball.png')
        SLib.loadIfNotInImageCache('SpinyShell', 'spiny_shell.png')
        SLib.loadIfNotInImageCache('SpinyShellU', 'spiny_shell_u.png')

    def dataChanged(self):

        spawntype = self.parent.spritedata[5]

        if spawntype == 0:
            self.image = ImageCache['Spiny']
        elif spawntype == 1:
            self.image = ImageCache['SpinyBall']
        elif spawntype == 2:
            self.image = ImageCache['SpinyShell']
        elif spawntype == 3:
            self.image = ImageCache['SpinyShellU']
        else:
            self.image = ImageCache['Spiny']

        super().dataChanged()

class SpriteImage_MidwayFlag(SLib.SpriteImage_StaticMultiple): # 25
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['MidwayFlag'],
            (1.07, -37),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('MidwayFlag', 'midway_flag.png')

class SpriteImage_RedRing(SLib.SpriteImage_Static): # 44
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['RedRing'],
            )

        self.yOffset = -14
        self.xOffset = -7

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('RedRing', 'red_ring.png')

class SpriteImage_StarCoin(SLib.SpriteImage_Static): # 45
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['StarCoin'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('StarCoin', 'starcoin.png')

class SpriteImage_GreenCoin(SLib.SpriteImage_Static): # 50
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['GreenCoin'],
            )

        self.xOffset = -7
        self.yOffset = -2

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('GreenCoin', 'green_coins.png')

class SpriteImage_YoshiFruit(SLib.SpriteImage_Static): # 45
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['YoshiFruit'],
            (0, 0.27),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('YoshiFruit', 'yoshi_fruit.png')

class SpriteImage_QBlock(SpriteImage_Block): # 59
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )
        self.tilenum = 28

class SpriteImage_BrickBlock(SpriteImage_Block): # 60
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )
        self.tilenum = 15

class SpriteImage_InvisiBlock(SpriteImage_Block): # 61
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )
        self.invisiblock = True

class SpriteImage_StalkingPiranha(SLib.SpriteImage_StaticMultiple): # 63
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['StalkingPiranha'],
            )

        self.yOffset = -17
        #self.xOffset = -10

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('StalkingPiranha', 'stalking_piranha.png')

class SpriteImage_Coin(SLib.SpriteImage_Static): # 65
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Coin'],
            )
        self.parent.setZValue(20000)

class SpriteImage_Swooper(SLib.SpriteImage_Static): # 67
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Swooper'],
            (1.6, 0),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Swooper', 'swooper.png')

class SpriteImage_HuckitCrab(SLib.SpriteImage_StaticMultiple): # 74
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['HuckitCrab'],
            )

        self.yOffset = -4.5 # close enough, it can't be a whole number
        self.xOffset = -10

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('HuckitCrab', 'huckit_crab.png')

class SpriteImage_MovingCoin(SLib.SpriteImage_Static): # 87
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Coin'],
            )
        self.parent.setZValue(20000)

class SpriteImage_BouncyCloud(SLib.SpriteImage_StaticMultiple): # 94
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BouncyCloud'],
            )

        # Add the track
        self.aux.append(SLib.AuxiliaryTrackObject(parent, 120, 120, SLib.AuxiliaryTrackObject.Horizontal))

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BouncyCloud', 'bouncy_cloud.png')
        SLib.loadIfNotInImageCache('BouncyCloudB', 'bouncy_cloud_big.png')

    def dataChanged(self):
        direction = self.parent.spritedata[0] & 0x3
        distance  = self.parent.spritedata[7] >> 4
        isBig     = self.parent.spritedata[8] & 0xF

        self.xOffset = -1.6

        if isBig == 1:
            self.image = ImageCache['BouncyCloudB']
            self.yOffset = -3.47
        else:
            self.image = ImageCache['BouncyCloud']
            self.yOffset = -2.67

        if direction == 0:
            # Right
            self.aux[0].direction = self.aux[0].Horizontal
            self.aux[0].setSize(distance * 120, 120)
        elif direction == 1:
            # Left
            self.aux[0].direction = self.aux[0].Horizontal
            self.aux[0].setSize(distance * 120, 120)
        elif direction == 2:
            # Up
            self.aux[0].direction = self.aux[0].Vertical
            self.aux[0].setSize(120, distance * 120)
        elif direction == 3:
            # Down
            self.aux[0].direction = self.aux[0].Vertical
            self.aux[0].setSize(120, distance * 120)

        super().dataChanged()

class SpriteImage_Lamp(SLib.SpriteImage_StaticMultiple): # 96
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['LampU'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('LampU', 'lamp_underground.png')
        SLib.loadIfNotInImageCache('LampG', 'lamp_ghosthouse.png')

    def dataChanged(self):
        style = self.parent.spritedata[5] & 0x0F

        if style % 2 == 0:
            self.image = ImageCache['LampU']
            self.xOffset = -40
            self.yOffset = -38.13
        else:
            self.image = ImageCache['LampG']
            self.xOffset = -31.2
            self.yOffset = -29.6

        super().dataChanged()

class SpriteImage_CheepCheep(SLib.SpriteImage_Static): # 101
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['CheepCheep'],
            (-0.53, -2.13),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('CheepCheep', 'cheep_cheep.png')

class SpriteImage_QuestionSwitch(SLib.SpriteImage_Static): # 104
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['QSwitch'],
            )

    @staticmethod
    def loadImages():
        if 'QSwitch' not in ImageCache:
            # we need to cache 2 things, the regular switch, and the upside down one
            image = SLib.GetImg('q_switch.png', True)
            # now we set up a transform to turn the switch upside down
            transform180 = QtGui.QTransform()
            transform180.rotate(180)
            # now we store it
            ImageCache['QSwitch'] = QtGui.QPixmap.fromImage(image)
            ImageCache['QSwitchU'] = QtGui.QPixmap.fromImage(image.transformed(transform180))

    def dataChanged(self):
        isflipped = self.parent.spritedata[5] & 1

        if isflipped == 0:
            self.image = ImageCache['QSwitch']
        else:
            self.image = ImageCache['QSwitchU']

        super().dataChanged()

class SpriteImage_PSwitch(SLib.SpriteImage_Static): # 105
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['PSwitch'],
            )

    @staticmethod
    def loadImages():
        if 'PSwitch' not in ImageCache:
            # we need to cache 2 things, the regular switch, and the upside down one
            image = SLib.GetImg('p_switch.png', True)
            # now we set up a transform to turn the switch upside down
            transform180 = QtGui.QTransform()
            transform180.rotate(180)
            # now we store it
            ImageCache['PSwitch'] = QtGui.QPixmap.fromImage(image)
            ImageCache['PSwitchU'] = QtGui.QPixmap.fromImage(image.transformed(transform180))

    def dataChanged(self):
        isflipped = self.parent.spritedata[5] & 1

        if isflipped == 0:
            self.image = ImageCache['PSwitch']
        else:
            self.image = ImageCache['PSwitchU']

        super().dataChanged()

class SpriteImage_DoorGhostHouse(SLib.SpriteImage_StaticMultiple): # 108
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['DoorGhostHouse'],
            (-3.47, 2.13)
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('DoorGhostHouse', 'door_ghosthouse.png')

class SpriteImage_SpecialExitController(SLib.SpriteImage): # 115
    def __init__(self, parent):
        super().__init__(
            parent, 
            3.75
            )
        self.aux.append(SLib.AuxiliaryRectOutline(parent, 0, 0))

    def dataChanged(self):
        super().dataChanged()

        width  = self.parent.spritedata[4] & 0xF 
        height = self.parent.spritedata[5] >> 4 

        self.aux[0].setSize((width + 1) * 60, (height + 1) * 60)

class SpriteImage_SpinyCheepCheep(SLib.SpriteImage_Static): # 120
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['SpinyCheepCheep'],
            (-0.53, 3.2),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('SpinyCheepCheep', 'spiny_cheep_cheep.png')

class SpriteImage_SandPillar(SLib.SpriteImage_Static): # 123
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['SandPillar'],
            )

        self.yOffset = -143
        self.xOffset = -18

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('SandPillar', 'sand_pillar.png')

class SpriteImage_Thwomp(SLib.SpriteImage_Static): # 135
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Thwomp'],
            (-5.6, -2.13),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Thwomp', 'thwomp.png')

class SpriteImage_DryBones(SLib.SpriteImage_StaticMultiple): # 137
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['DryBones'],
            )

        self.yOffset = -12
        self.xOffset = -7

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('DryBones', 'dry_bones.png')

class SpriteImage_BigDryBones(SLib.SpriteImage_StaticMultiple): # 138
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BigDryBones'],
            )

        self.yOffset = -21
        self.xOffset = -7

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BigDryBones', 'big_dry_bones.png')

class SpriteImage_PipeUp(SpriteImage_Pipe): # 139
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.direction = 'U'
        self.typeinfluence = True

class SpriteImage_PipeDown(SpriteImage_Pipe): # 140
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.direction = 'D'
        self.typeinfluence = True

class SpriteImage_PipeLeft(SpriteImage_Pipe): # 141
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.direction = 'L'
        self.typeinfluence = True

class SpriteImage_PipeRight(SpriteImage_Pipe): # 142
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.direction = 'R'
        self.typeinfluence = True

class SpriteImage_BubbleYoshi(SLib.SpriteImage_Static): # 143, 243
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BubbleYoshi'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BubbleYoshi', 'babyyoshibubble.png')

class SpriteImage_POWBlock(SLib.SpriteImage_Static): # 152
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['POWBlock'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('POWBlock', 'block_pow.png')

class SpriteImage_CoinOutline(SLib.SpriteImage_StaticMultiple): # 158
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75, # native res (3.75*16=60)
            ImageCache['CoinOutlineMultiplayer'],
            )
        self.parent.setZValue(20000)

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('CoinOutline', 'coin_outline.png')
        SLib.loadIfNotInImageCache('CoinOutlineMultiplayer', 'coin_outline_multiplayer.png')

    def dataChanged(self):
        multi = (self.parent.spritedata[2] >> 4) & 1
        self.image = ImageCache['CoinOutline' + ('Multiplayer' if multi else '')]
        super().dataChanged()

class SpriteImage_BobOmb(SLib.SpriteImage_Static): # 164
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BobOmb'],
            (-3.73, -6.4),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BobOmb', 'bob-omb.png')

class SpriteImage_Parabomb(SLib.SpriteImage_StaticMultiple): # 170
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Parabomb'],
            )

        self.yOffset = -16

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Parabomb', 'parabomb.png')

class SpriteImage_Mechakoopa(SLib.SpriteImage_StaticMultiple): # 175
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Mechakoopa'],
            )

        self.yOffset = -10
        self.xOffset = -6

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Mechakoopa', 'mechakoopa.png')

class SpriteImage_AirshipCannon(SLib.SpriteImage_StaticMultiple): # 176
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['CannonL']
            )

        self.yOffset = -7

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('CannonL', 'Cannon_L.png')
        SLib.loadIfNotInImageCache('CannonR', 'Cannon_R.png')

    def dataChanged(self):

        direction = self.parent.spritedata[5]

        if direction == 0:
            self.image = ImageCache['CannonL']
        elif direction == 1:
            self.image = ImageCache['CannonR']
        else:
            self.image = ImageCache['CannonL']

        super().dataChanged()

class SpriteImage_Spike(SLib.SpriteImage_Static): # 180
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Spike'],
            (-5.87, -13.87),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Spike', 'spike.png')

class SpriteImage_FallingIcicle(SLib.SpriteImage_StaticMultiple): # 183
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('FallingIcicle1x1', 'falling_icicle_1x1.png')
        SLib.loadIfNotInImageCache('FallingIcicle1x2', 'falling_icicle_1x2.png')

    def dataChanged(self):

        size = self.parent.spritedata[5]

        if size == 0:
            self.image = ImageCache['FallingIcicle1x1']
        elif size == 1:
            self.image = ImageCache['FallingIcicle1x2']
        else:
            self.image = ImageCache['FallingIcicle1x1']

        super().dataChanged()

class SpriteImage_GiantIcicle(SLib.SpriteImage_Static): # 184
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['GiantIcicle'],
            )

        self.xOffset = -24

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('GiantIcicle', 'giant_icicle.png')

class SpriteImage_RouletteBlock(SLib.SpriteImage_StaticMultiple): # 195
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['RouletteBlock'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('RouletteBlock', 'block_roulette.png')

class SpriteImage_Springboard(SLib.SpriteImage_Static): # 215
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Springboard'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Springboard', 'springboard.png')

class SpriteImage_Boo(SLib.SpriteImage_Static): # 219
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Boo'],
            (-8.53, -12.53),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Boo', 'boo.png')

class SpriteImage_BalloonYoshi(SLib.SpriteImage_Static): # 224
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BalloonYoshi'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BalloonYoshi', 'balloonbabyyoshi.png')

class SpriteImage_Foo(SLib.SpriteImage_StaticMultiple): # 229
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Foo'],
            (-3.73, -8),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Foo', 'foo.png')

class SpriteImage_BigGlowBlock(SLib.SpriteImage_Static): # 232
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BigGlowBlock'],
            (-16, -16),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BigGlowBlock', 'glowblock_big.png')

class SpriteImage_Bolt(SLib.SpriteImage_StaticMultiple): # 238
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )

        self.yOffset = 3

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BoltMetal', 'bolt_metal.png')
        SLib.loadIfNotInImageCache('BoltStone', 'bolt_stone.png')

    def dataChanged(self):
        stone = self.parent.spritedata[4] & 1

        if stone == 1:
            self.image = ImageCache['BoltStone']
        else:
            self.image = ImageCache['BoltMetal']

        super().dataChanged()

class SpriteImage_TileGod(SLib.SpriteImage): # 237
    def __init__(self, parent):
        super().__init__(parent, 3.75)
        self.aux.append(SLib.AuxiliaryRectOutline(parent, 0, 0))

    def dataChanged(self):
        super().dataChanged()

        width = self.parent.spritedata[8] & 0xF
        height = self.parent.spritedata[9] & 0xF
        if width == 0: width = 1
        if height == 0: height = 1
        self.aux[0].setSize(width * 60, height * 60)

class SpriteImage_PricklyGoomba(SLib.SpriteImage_StaticMultiple): # 247
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['PricklyGoomba'],
            )

        self.yOffset = -13
        #self.xOffset = -6

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('PricklyGoomba', 'prickly_goomba.png')

class SpriteImage_Wiggler(SLib.SpriteImage_StaticMultiple): # 249
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Wiggler'],
            )

        self.yOffset = -17
        #self.xOffset = -6

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Wiggler', 'wiggler.png')

class SpriteImage_MicroGoomba(SLib.SpriteImage_Static): # 255
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['MicroGoomba'],
            (3.2, 7.47),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('MicroGoomba', 'micro_goomba.png')

class SpriteImage_Muncher(SLib.SpriteImage_StaticMultiple): # 259
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('MuncherReg', 'muncher.png')
        SLib.loadIfNotInImageCache('MuncherFr', 'muncher_frozen.png')

    def dataChanged(self):
        isfrozen = self.parent.spritedata[5] & 1

        if isfrozen == 0:
            self.image = ImageCache['MuncherReg']
        else:
            self.image = ImageCache['MuncherFr']

        super().dataChanged()

class SpriteImage_Parabeetle(SLib.SpriteImage_Static): # 261
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Parabeetle'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Parabeetle', 'parabeetle.png')

class SpriteImage_BubbleCoin(SLib.SpriteImage_Static): # 281
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BubbleCoin'],
            (-2.13, -2.67),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BubbleCoin', 'coin_bubble.png')

class SpriteImage_NoteBlock(SLib.SpriteImage_Static): # 295
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['NoteBlock'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('NoteBlock', 'noteblock.png')

class SpriteImage_Clampy(SLib.SpriteImage_Static): # 298
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Clampy'],
            (-28.53, -53.6),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Clampy', 'clampy.png')

class SpriteImage_Thwimp(SLib.SpriteImage_Static): # 303
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Thwimp'],
            (-2.4, -3.2),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Thwimp', 'thwimp.png')

class SpriteImage_Blooper(SLib.SpriteImage_StaticMultiple): # 313
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Blooper'],
            )

        self.xOffset = -2.93
        self.yOffset = -10.13

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Blooper', 'blooper.png')
        SLib.loadIfNotInImageCache('BlooperR', 'blooper_right.png')
        SLib.loadIfNotInImageCache('BlooperL', 'blooper_left.png')

    def dataChanged(self):
        direction = (self.parent.spritedata[2] & 0xF0) >> 4

        if direction == 2:
            self.image = ImageCache['BlooperR']
            self.xOffset = -1.86
            self.yOffset = -8.8
        elif direction == 3:
            self.image = ImageCache['BlooperL']
            self.xOffset = -2.67
            self.yOffset = -8.8
        else:
            self.image = ImageCache['Blooper']
            self.xOffset = -2.93
            self.yOffset = -10.13

        super().dataChanged()

class SpriteImage_Broozer(SLib.SpriteImage_Static): # 320
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Broozer'],
            )

        self.xOffset = -20
        self.yOffset = -20

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Broozer', 'broozer.png')

class SpriteImage_Barrel(SLib.SpriteImage_Static): # 323
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Barrel'],
            )

        self.xOffset = -7
        self.yOffset = -2

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Barrel', 'barrel.png')

class SpriteImage_RotationControlledCoin(SLib.SpriteImage_Static): # 325
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Coin'],
            )
        self.parent.setZValue(20000)

class SpriteImage_MovementControlledCoin(SLib.SpriteImage_Static): # 326
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Coin'],
            )
        self.parent.setZValue(20000)

class SpriteImage_BoltControlledCoin(SLib.SpriteImage_Static): # 328
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Coin'],
            )
        self.parent.setZValue(20000)

class SpriteImage_Cooligan(SLib.SpriteImage_StaticMultiple): # 334
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )

        self.xOffset = -7
        self.yOffset = -2

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('CooliganL', 'cooligan_l.png')
        SLib.loadIfNotInImageCache('CooliganR', 'cooligan_r.png')

    def dataChanged(self):

        direction = self.parent.spritedata[5]

        if direction == 0:
            self.image = ImageCache['CooliganL']
        elif direction == 1:
            self.image = ImageCache['CooliganR']
        elif direction == 2:
            self.image = ImageCache['CooliganL']
        else:
            self.image = ImageCache['CooliganL']

        super().dataChanged()

class SpriteImage_Bramball(SLib.SpriteImage_Static): # 336
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Bramball'],
            )

        self.xOffset = -30
        self.yOffset = -46

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Bramball', 'bramball.png')

class SpriteImage_WoodenBox(SLib.SpriteImage_StaticMultiple): # 338
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Reg2x2', 'reg_box_2x2.png')
        SLib.loadIfNotInImageCache('Reg4x2', 'reg_box_4x2.png')
        SLib.loadIfNotInImageCache('Reg2x4', 'reg_box_2x4.png')
        SLib.loadIfNotInImageCache('Reg4x4', 'reg_box_4x4.png')
        SLib.loadIfNotInImageCache('Inv2x2', 'inv_box_2x2.png')
        SLib.loadIfNotInImageCache('Inv4x2', 'inv_box_4x2.png')
        SLib.loadIfNotInImageCache('Inv2x4', 'inv_box_2x4.png')
        SLib.loadIfNotInImageCache('Inv4x4', 'inv_box_4x4.png')

    def dataChanged(self):

        boxcolor = self.parent.spritedata[4]
        boxsize = self.parent.spritedata[5] >> 4

        if boxsize == 0 and boxcolor == 0:
            self.image = ImageCache['Reg2x2']
        elif boxsize == 1 and boxcolor == 0:
            self.image = ImageCache['Reg2x4']
        elif boxsize == 2 and boxcolor == 0:
            self.image = ImageCache['Reg4x2']
        elif boxsize == 3 and boxcolor == 0:
            self.image = ImageCache['Reg4x4']
        elif boxsize == 0 and boxcolor == 1 or boxcolor == 2:
            self.image = ImageCache['Inv2x2']
        elif boxsize == 1 and boxcolor == 1 or boxcolor == 2:
            self.image = ImageCache['Inv2x4']
        elif boxsize == 2 and boxcolor == 1 or boxcolor == 2:
            self.image = ImageCache['Inv4x2']
        elif boxsize == 3 and boxcolor == 1 or boxcolor == 2:
            self.image = ImageCache['Inv4x4']
        else:
            self.image = ImageCache['Reg2x2'] # let's not make some nonsense out of this

        super().dataChanged()

class SpriteImage_SuperGuide(SLib.SpriteImage_Static): # 348
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['SuperGuide'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('SuperGuide', 'guide_block.png')

class SpriteImage_GoldenYoshi(SLib.SpriteImage_Static): # 365
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['GoldenYoshi'],
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('GoldenYoshi', 'babyyoshiglowing.png')

class SpriteImage_TorpedoLauncher(SLib.SpriteImage_StaticMultiple): # 378
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['TorpedoLauncher'],
            )

        self.xOffset = -22

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('TorpedoLauncher', 'torpedo_launcher.png')

class SpriteImage_GreenRing(SLib.SpriteImage_Static): # 402
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['GreenRing'],
            )

        self.yOffset = -14
        self.xOffset = -7

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('GreenRing', 'green_ring.png')

class SpriteImage_PipeUpEnterable(SpriteImage_Pipe): # 404
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.direction = 'U'
        self.extraHeight = 1

class SpriteImage_BumpPlatform(SLib.SpriteImage): # 407
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )
        self.spritebox.shown = False

    @staticmethod
    def loadImages():
        ImageCache['BumpPlatformL'] = SLib.GetImg('bump_platform_l.png')
        ImageCache['BumpPlatformM'] = SLib.GetImg('bump_platform_m.png')
        ImageCache['BumpPlatformR'] = SLib.GetImg('bump_platform_r.png')

    def dataChanged(self):
        super().dataChanged()

        self.width = ((self.parent.spritedata[8] & 0xF) + 1) << 4

    def paint(self, painter):
        super().paint(painter)

        if self.width > 32:
            painter.drawTiledPixmap(60, 0, ((self.width * 3.75)-120), 60, ImageCache['BumpPlatformM'])

        if self.width == 24:
            painter.drawPixmap(0, 0, ImageCache['BumpPlatformR'])
            painter.drawPixmap(8, 0, ImageCache['BumpPlatformL'])
        else:
            # normal rendering
            painter.drawPixmap((self.width - 16) * 3.75, 0, ImageCache['BumpPlatformR'])
            painter.drawPixmap(0, 0, ImageCache['BumpPlatformL'])

class SpriteImage_BigBrickBlock(SLib.SpriteImage_Static): # 422
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BigBrick'],
            )

        self.yOffset = 16

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BigBrick', 'big_brickblock.png')

class SpriteImage_Fliprus(SLib.SpriteImage_StaticMultiple): # 441
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )

        self.yOffset = -16
        self.xOffset = -6

    @staticmethod
    def loadImages():
        if "FliprusL" not in ImageCache:
            fliprus = SLib.GetImg('fliprus.png', True)
            ImageCache['FliprusL'] = QtGui.QPixmap.fromImage(fliprus)
            ImageCache['FliprusR'] = QtGui.QPixmap.fromImage(fliprus.mirrored(True, False))

    def dataChanged(self):
        direction = self.parent.spritedata[4]

        if direction == 0:
            self.image = ImageCache['FliprusL']
        elif direction == 1:
            self.image = ImageCache['FliprusR']
        elif direction == 2:
            self.image = ImageCache['FliprusL']
        else:
            self.image = ImageCache['FliprusL']

        super().dataChanged()

class SpriteImage_BonyBeetle(SLib.SpriteImage_Static): # 443
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BonyBeetle'],
            (0, 0.8)
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BonyBeetle', 'bony_beetle.png')

class SpriteImage_FliprusSnowball(SLib.SpriteImage_StaticMultiple): # 446
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Snowball'],
            )

        self.yOffset = -10

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Snowball', 'snowball.png')

class SpriteImage_BigGoomba(SLib.SpriteImage_StaticMultiple): # 472
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BigGoomba'],
            )

        self.yOffset = -20

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BigGoomba', 'big_goomba.png')

class SpriteImage_BigQBlock(SLib.SpriteImage_Static): # 475
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BigQBlock'],
            )

        self.yOffset = 16

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BigQBlock', 'big_qblock.png')

class SpriteImage_BigKoopaTroopa(SLib.SpriteImage_StaticMultiple): # 476
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )

        self.yOffset = -32

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BigKoopaG', 'big_koopa_green.png')
        SLib.loadIfNotInImageCache('BigKoopaR', 'big_koopa_red.png')

    def dataChanged(self):

        color = self.parent.spritedata[5] & 1

        if color == 0:
            self.image = ImageCache['BigKoopaG']
        elif color == 1:
            self.image = ImageCache['BigKoopaR']
        else:
            self.image = ImageCache['BigKoopaG']

        super().dataChanged()

class SpriteImage_WaddleWing(SLib.SpriteImage_StaticMultiple): # 481
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )

        self.yOffset = -9
        self.xOffset = -9

    @staticmethod
    def loadImages():
        if 'WaddleWingL' not in ImageCache:
            waddlewing = SLib.GetImg('waddlewing.png', True)

            ImageCache['WaddlewingL'] = QtGui.QPixmap.fromImage(waddlewing)
            ImageCache['WaddlewingR'] = QtGui.QPixmap.fromImage(waddlewing.mirrored(True, False))

    def dataChanged(self):
        rawdir = self.parent.spritedata[5]

        if rawdir == 2:
            self.image = ImageCache['WaddlewingR']
        else:
            self.image = ImageCache['WaddlewingL']

        super().dataChanged()

class SpriteImage_BoltControlledMovingCoin(SLib.SpriteImage_Static): # 496
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Coin'],
            )
        self.parent.setZValue(20000)

class SpriteImage_MovingGrassPlatform(SLib.SpriteImage): # 499
    def __init__(self, parent):
        super().__init__(parent, 3.75)
        self.aux.append(SLib.AuxiliaryRectOutline(parent, 0, 0))
        self.parent.setZValue(24999)

    def dataChanged(self):
        super().dataChanged()

        width = (self.parent.spritedata[8] & 0xF) + 1
        height = (self.parent.spritedata[9] & 0xF) + 1
        if width == 1 and height == 1:
            self.aux[0].setSize(0,0)
            return
        self.aux[0].setSize(width * 60, height * 60)

class SpriteImage_Grrrol(SLib.SpriteImage_StaticMultiple): # 504
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['GrrrolSmall'],
            )

        self.yOffset = -12

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('GrrrolSmall', 'grrrol_small.png')

class SpriteImage_PipeJoint(SLib.SpriteImage_Static): # 513
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['PipeJoint'])

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('PipeJoint', 'pipe_joint.png')

class SpriteImage_PipeJointSmall(SLib.SpriteImage_Static): # 514
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['PipeJointSmall'])

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('PipeJointSmall', 'pipe_joint_mini.png')

class SpriteImage_MiniPipeRight(SpriteImage_Pipe): # 516
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.mini = True
        self.direction = 'R'

class SpriteImage_MiniPipeLeft(SpriteImage_Pipe): # 517
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.mini = True
        self.direction = 'L'

class SpriteImage_MiniPipeUp(SpriteImage_Pipe): # 518
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.mini = True
        self.direction = 'U'

class SpriteImage_MiniPipeDown(SpriteImage_Pipe): # 519
    def __init__(self, parent, scale=3.75):
        super().__init__(parent, scale)
        self.mini = True
        self.direction = 'D'

class SpriteImage_RockyWrench(SLib.SpriteImage_Static): # 536
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['RockyWrench'],
            (-3.47, -19.2),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('RockyWrench', 'rocky_wrench.png')

class SpriteImage_MushroomPlatform(SLib.SpriteImage): # 542
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            )
        self.spritebox.shown = False

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('SkinnyOrangeL', 'orange_mushroom_skinny_l.png')
        SLib.loadIfNotInImageCache('SkinnyOrangeM', 'orange_mushroom_skinny_m.png')
        SLib.loadIfNotInImageCache('SkinnyOrangeR', 'orange_mushroom_skinny_r.png')
        SLib.loadIfNotInImageCache('SkinnyGreenL', 'green_mushroom_skinny_l.png')
        SLib.loadIfNotInImageCache('SkinnyGreenM', 'green_mushroom_skinny_m.png')
        SLib.loadIfNotInImageCache('SkinnyGreenR', 'green_mushroom_skinny_r.png')
        SLib.loadIfNotInImageCache('ThickBlueL', 'blue_mushroom_thick_l.png')
        SLib.loadIfNotInImageCache('ThickBlueM', 'blue_mushroom_thick_m.png')
        SLib.loadIfNotInImageCache('ThickBlueR', 'blue_mushroom_thick_r.png')
        SLib.loadIfNotInImageCache('ThickRedL', 'red_mushroom_thick_l.png')
        SLib.loadIfNotInImageCache('ThickRedM', 'red_mushroom_thick_m.png')
        SLib.loadIfNotInImageCache('ThickRedR', 'red_mushroom_thick_r.png')


    def dataChanged(self):
        super().dataChanged()

        # self.platformwidth is the platform width in blocks,
        # self.width is the platform width in px
        self.color = self.parent.spritedata[4] & 1
        self.girth = (self.parent.spritedata[5] >> 4) & 1

        oddwidth = ((self.parent.spritedata[8] & 1) == 1)
        if oddwidth:
            self.platformwidth = (self.parent.spritedata[8] & 0xF) * 2 - 1
        else:
            self.platformwidth = (self.parent.spritedata[8] & 0xF) * 2

        self.width = self.platformwidth * 16

        if self.girth == 1:
            self.height = 30

        self.xOffset = -0.5 * self.width

    def paint(self, painter):
        super().paint(painter)

        # more than 2 blocks, so paint the bodies
        if self.platformwidth > 2:

            # Thick mushrooms have different colors
            if self.girth == 0:

                # 60 is the width of 1 tile
                if self.color == 0:
                    painter.drawTiledPixmap(60, 0, ((self.platformwidth - 2) * 60), 60, ImageCache['SkinnyOrangeM'])
                elif self.color == 1:
                    painter.drawTiledPixmap(60, 0, ((self.platformwidth - 2) * 60), 60, ImageCache['SkinnyGreenM'])
            
            elif self.girth == 1:
                
                # Thick mushrooms have thicker edges, so take those into account
                if self.color == 0:
                    painter.drawTiledPixmap(120, 0, ((self.platformwidth - 4) * 60), 120, ImageCache['ThickRedM'])
                elif self.color == 1:
                    painter.drawTiledPixmap(120, 0, ((self.platformwidth - 4) * 60), 120, ImageCache['ThickBlueM'])

        # paint the edges
        
        # Thick mushrooms have different colors
        if self.girth == 0:

            if self.color == 0:
                painter.drawPixmap(((self.platformwidth - 1) * 60), 0, ImageCache['SkinnyOrangeR'])
                painter.drawPixmap(0, 0, ImageCache['SkinnyOrangeL'])
            elif self.color == 1:
                painter.drawPixmap(((self.platformwidth - 1) * 60), 0, ImageCache['SkinnyGreenR'])
                painter.drawPixmap(0, 0, ImageCache['SkinnyGreenL'])

        elif self.girth == 1:

            if self.color == 0:
                painter.drawPixmap(((self.platformwidth - 2) * 60), 0, ImageCache['ThickRedR'])
                painter.drawPixmap(0, 0, ImageCache['ThickRedL'])
            elif self.color == 1:
                painter.drawPixmap(((self.platformwidth - 2) * 60), 0, ImageCache['ThickBlueR'])
                painter.drawPixmap(0, 0, ImageCache['ThickBlueL'])

class SpriteImage_StoneSpike(SLib.SpriteImage_Static): # 579
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['StoneSpike'],
            (-6.67, -13.87),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('StoneSpike', 'stone_spike.png')

class SpriteImage_DeepCheep(SLib.SpriteImage_Static): # 588
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['DeepCheep'],
            (-0.53, -2.13),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('DeepCheep', 'deep_cheep.png')

class SpriteImage_SumoBro(SLib.SpriteImage_Static): # 593
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['SumoBro'],
            (-18.13, -20.8),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('SumoBro', 'sumo_bro.png')

class SpriteImage_Goombrat(SLib.SpriteImage_Static): # 595
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['Goombrat'],
            (-1.6, -2.67),
            )

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('Goombrat', 'goombrat.png')

class SpriteImage_BlueRing(SLib.SpriteImage_Static): # 662
    def __init__(self, parent):
        super().__init__(
            parent,
            3.75,
            ImageCache['BlueRing'],
            )

        self.yOffset = -14
        self.xOffset = -7

    @staticmethod
    def loadImages():
        SLib.loadIfNotInImageCache('BlueRing', 'blue_ring.png')

################################################################
################## SPRITE CLASSES ##############################
################################################################

ImageClasses = {
    0: SpriteImage_Goomba,
    1: SpriteImage_Paragoomba,
    2: SpriteImage_PipePiranhaUp,
    3: SpriteImage_PipePiranhaDown,
    4: SpriteImage_PipePiranhaLeft,
    5: SpriteImage_PipePiranhaRight,
    19: SpriteImage_KoopaTroopa,
    20: SpriteImage_ParaKoopa,
    22: SpriteImage_BuzzyBeetle,
    #23: SpriteImage_Spiny,
    25: SpriteImage_MidwayFlag,
    #32: SpriteImage_ArrowSignboard,
    #44: SpriteImage_RedRing,
    45: SpriteImage_StarCoin,
    50: SpriteImage_GreenCoin,
    54: SpriteImage_YoshiFruit,
    59: SpriteImage_QBlock,
    60: SpriteImage_BrickBlock,
    61: SpriteImage_InvisiBlock,
    63: SpriteImage_StalkingPiranha,
    65: SpriteImage_Coin,
    66: SpriteImage_Coin,
    67: SpriteImage_Swooper,
    74: SpriteImage_HuckitCrab,
    87: SpriteImage_MovingCoin,
    94: SpriteImage_BouncyCloud,
    96: SpriteImage_Lamp,
    101: SpriteImage_CheepCheep,
    104: SpriteImage_QuestionSwitch,
    105: SpriteImage_PSwitch,
    108: SpriteImage_DoorGhostHouse,
    115: SpriteImage_SpecialExitController,
    120: SpriteImage_SpinyCheepCheep,
    123: SpriteImage_SandPillar,
    135: SpriteImage_Thwomp,
    137: SpriteImage_DryBones,
    138: SpriteImage_BigDryBones,
    139: SpriteImage_PipeUp,
    140: SpriteImage_PipeDown,
    141: SpriteImage_PipeLeft,
    142: SpriteImage_PipeRight,
    143: SpriteImage_BubbleYoshi,
    152: SpriteImage_POWBlock,
    158: SpriteImage_CoinOutline,
    164: SpriteImage_BobOmb,
    170: SpriteImage_Parabomb,
    175: SpriteImage_Mechakoopa,
    176: SpriteImage_AirshipCannon,
    180: SpriteImage_Spike,
    183: SpriteImage_FallingIcicle,
    184: SpriteImage_GiantIcicle,
    195: SpriteImage_RouletteBlock,
    200: SpriteImage_MushroomPlatform,
    215: SpriteImage_Springboard,
    218: SpriteImage_Boo,
    224: SpriteImage_BalloonYoshi,
    229: SpriteImage_Foo,
    232: SpriteImage_BigGlowBlock,
    237: SpriteImage_TileGod,
    238: SpriteImage_Bolt,
    243: SpriteImage_BubbleYoshi,
    247: SpriteImage_PricklyGoomba,
    249: SpriteImage_Wiggler,
    255: SpriteImage_MicroGoomba,
    259: SpriteImage_Muncher,
    261: SpriteImage_Parabeetle,
    281: SpriteImage_BubbleCoin,
    295: SpriteImage_NoteBlock,
    298: SpriteImage_Clampy,
    303: SpriteImage_Thwimp,
    313: SpriteImage_Blooper,
    320: SpriteImage_Broozer,
    323: SpriteImage_Barrel,
    325: SpriteImage_RotationControlledCoin,
    326: SpriteImage_MovementControlledCoin,
    328: SpriteImage_BoltControlledCoin,
    334: SpriteImage_Cooligan,
    336: SpriteImage_Bramball,
    338: SpriteImage_WoodenBox,
    348: SpriteImage_SuperGuide,
    365: SpriteImage_GoldenYoshi,
    378: SpriteImage_TorpedoLauncher,
    402: SpriteImage_GreenRing,
    404: SpriteImage_PipeUpEnterable,
    407: SpriteImage_BumpPlatform,
    422: SpriteImage_BigBrickBlock,
    441: SpriteImage_Fliprus,
    443: SpriteImage_BonyBeetle,
    446: SpriteImage_FliprusSnowball,
    472: SpriteImage_BigGoomba,
    475: SpriteImage_BigQBlock,
    476: SpriteImage_BigKoopaTroopa,
    481: SpriteImage_WaddleWing,
    496: SpriteImage_BoltControlledMovingCoin,
    499: SpriteImage_MovingGrassPlatform,
    504: SpriteImage_Grrrol,
    511: SpriteImage_PipeDown,
    513: SpriteImage_PipeJoint,
    514: SpriteImage_PipeJointSmall,
    516: SpriteImage_MiniPipeRight,
    517: SpriteImage_MiniPipeLeft,
    518: SpriteImage_MiniPipeUp,
    519: SpriteImage_MiniPipeDown,
    542: SpriteImage_MushroomPlatform,
    536: SpriteImage_RockyWrench,
    579: SpriteImage_StoneSpike,
    588: SpriteImage_DeepCheep,
    593: SpriteImage_SumoBro,
    595: SpriteImage_Goombrat,
    662: SpriteImage_BlueRing,
    673: SpriteImage_TileGod
}
