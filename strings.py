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


# strings.py
# Strings for labels, tooltips, and more


################################################################
################################################################

class SatoruTranslation():
    """
    A translation of all visible Satoru strings
    """
    def __init__(self, name):
        """
        Creates a Satoru translation
        """
        self.InitAsEnglish()

        # Try to load it from an XML
        try:
            self.InitFromXML(name)
        except Exception:
            self.InitAsEnglish()


    def InitAsEnglish(self):
        """
        Initializes the SatoruTranslation as the English translation
        """
        self.name = 'English'
        self.version = 1.0
        self.translator = 'Treeki, Tempus'

        self.files = {
            'entrancetypes': 'satorudata/entrancetypes.txt',
            'levelnames': 'satorudata/levelnames.xml',
            'music': 'satorudata/music.txt',
            'spritecategories': 'satorudata/spritecategories.xml',
            'spritedata': 'satorudata/spritedata.xml',
            'tilesets': 'satorudata/tilesets.xml',
            'ts1_descriptions': 'satorudata/ts1_descriptions.txt',
            }

        self.strings = {
            'AboutDlg': {
                0: 'About Satoru',
                },
            'AreaChoiceDlg': {
                0: 'Choose an Area',
                1: 'Area [num]',
                2: 'You have reached the maximum amount of areas in this level.[br]Due to the game\'s limitations, Satoru only allows you to add up to 4 areas to a level.',
                },
            'AreaCombobox': {
                0: 'Area [num]',
                },
            'AreaDlg': {
                0: 'Area Options',
                1: 'Tilesets',
                2: 'Settings',
                3: 'Timer:',
                4: '[b]Timer:[/b][br]Sets the time limit, in "Mario seconds," for the level.[br][b]Midway Timer Info:[/b] The midway timer is calculated by subtracting 200 from this value. Because the game will use the timer setting from whatever area the midpoint is located in, it\'s possible to pick your own time limit if you put the midpoint in any area other than Area 1. Just set the time limit value for that area to the midpoint time you want + 200.',
                5: 'Entrance ID:',
                6: '[b]Entrance ID:[/b][br]Sets the entrance ID to load into when loading from the World Map',
                7: 'Wrap across Edges',
                8: '[b]Wrap across Edges:[/b][br]Makes the stage edges wrap[br]Warning: This option may cause the game to crash or behave weirdly. Wrapping only works correctly where the area is set up in the right way; see Coin Battle 1 for an example.',
                9: None, # REMOVED: 'Event [id]'
                10: None, # REMOVED: 'Default Events'
                11: 'Standard Suite',
                12: 'Stage Suite',
                13: 'Background Suite',
                14: 'Interactive Suite',
                15: 'None',
                16: '[CUSTOM]',
                17: '[CUSTOM] [name]',
                18: 'Custom filename... [name]',
                19: '[name] ([file])',
                20: 'Enter a Filename',
                21: 'Enter the name of a custom tileset file to use. It must be placed in the game\'s Stage\\Texture or Unit folder in order for Satoru to recognize it. Do not add the \'.arc\' or \'.sarc\' extension at the end of the filename.',
                22: 'Unknown Value 1:',
                23: 'Unknown Value 2:',
                24: 'Unknown Value 3:', # Currently unused
                25: '[b]Unknown Value 1:[/b] We haven\'t managed to figure out what this does, or if it does anything.',
                26: '[b]Unknown Value 2:[/b] We haven\'t managed to figure out what this does, or if it does anything.',
                27: '[b]Unknown Value 3:[/b] We haven\'t managed to figure out what this does, or if it does anything.', # Currently unused
                28: 'Name',
                29: 'File',
                30: '(None)',
                31: 'Tileset (Pa[slot]):',
                32: 'Unknown Value 4:',
                33: 'Unknown Value 5:',
                34: 'Unknown Value 6:',
                35: 'Unknown Value 7:',
                36: 'Time Limit 2:',
                37: 'Time Limit 3:',
                38: '[b]Time Limit 2 & 3:[/b]This time limit is chosen by the nybble 12 on sprite 25, Midway Point Flag. See sprite for details.',
                },
            'AutoSaveDlg': {
                0: 'Auto-saved backup found',
                1: 'Satoru has found some level data which wasn\'t saved - possibly due to a crash within the editor or by your computer. Do you want to restore this level?[br][br]If you pick No, the autosaved level data will be deleted and will no longer be accessible.[br][br]Original file path: [path]',
                2: 'The level has unsaved changes in it.',
                3: 'Do you want to save them?',
                },
            'BGDlg': {
                0: 'Backgrounds',
                1: (
                    'None',
                    '0.125x',
                    '0.25x',
                    '0.375x',
                    '0.5x',
                    '0.625x',
                    '0.75x',
                    '0.875x',
                    '1x',
                    'None',
                    '1.25x',
                    '1.5x',
                    '2x',
                    '4x',
                    ),
                2: 'Zone [num]',
                3: 'Scenery',
                4: 'Backdrop',
                5: 'Position:',
                6: 'X:',
                7: '[b]Position (X):[/b][br]Sets the horizontal offset of your background',
                8: 'Y:',
                9: '[b]Position (Y):[/b][br]Sets the vertical offset of your background',
                10: 'Scroll Rate:',
                11: '[b]Scroll Rate (X):[/b][br]Changes the rate that the background moves in[br]relation to Mario when he moves horizontally.[br]Values higher than 1x may be glitchy!',
                12: '[b]Scroll Rate (Y):[/b][br]Changes the rate that the background moves in[br]relation to Mario when he moves vertically.[br]Values higher than 1x may be glitchy!',
                13: 'Zoom:',
                14: '[b]Zoom:[/b][br]Sets the zoom level of the background image',
                15: (
                    '100%',
                    '125%',
                    '150%',
                    '200%',
                    ),
                16: 'Preview',
                17: '[name] ([hex])',
                18: '(Custom)',
                19: 'Background Types:',
                20: 'Alignment Mode: This combination of backgrounds will result in "[mode]"',
                21: (
                    'Normal',
                    'Unknown 1',
                    'Unknown 2',
                    'Unknown 3',
                    'Unknown 4',
                    'Align to Screen',
                    'Unknown 5',
                    'Unknown 6',
                    ),
                },
            'ChangeGamePath': {
                0: 'Choose the Course folder from [game]',
                1: 'Error',
                2: 'This folder doesn\'t have all of the files from the extracted NSMBU course_res_pack folder.',
                3: 'This folder doesn\'t seem to have the required files. In order to use Satoru, you need the Stage folder from the game, including the Texture folder and the level files contained within it.',
                },
            'Comments': {
                0: '[x], [y]: [text]',
                1: '[b]Comment[/b][br]at [x], [y]',
                2: ' - ',
                3: '(empty)',
                4: '...',
                },
            'DeleteArea': {
                0: 'Are you [b]sure[/b] you want to delete this area?[br][br]The level will automatically save afterwards - there is no way[br]you can undo the deletion or get it back afterwards!',
                },
            'EntranceDataEditor': {
                0: 'ID:',
                1: '[b]ID:[/b][br]Must be different from all other IDs',
                2: 'Type:',
                3: '[b]Type:[/b][br]Sets how the entrance behaves',
                4: 'Dest. ID:',
                5: '[b]Dest. ID:[/b][br]If this entrance leads nowhere or the destination is in this area, set this to 0.',
                6: 'Dest. Area:',
                7: '[b]Dest. Area:[/b][br]If this entrance leads nowhere, set this to 0.',
                8: 'Enterable',
                9: '[b]Enterable:[/b][br]If this box is checked on a pipe or door entrance, Mario will be able to enter the pipe/door. If it\'s not checked, he won\'t be able to enter it. Behaviour on other types of entrances is unknown/undefined.',
                10: 'Unknown Flag',
                11: '[b]Unknown Flag:[/b][br]This box is checked on a few entrances in the game, but we haven\'t managed to figure out what it does (or if it does anything).',
                12: 'Connected Pipe',
                13: '[b]Connected Pipe:[/b][br]This box allows you to enable an unused/broken feature in the game. It allows the pipe to function like the pipes in SMB3 where Mario simply goes through the pipe. However, it doesn\'t work correctly.',
                14: 'Connected Pipe Reverse',
                15: '[b]Connected Pipe:[/b][br]This box allows you to enable an unused/broken feature in the game. It allows the pipe to function like the pipes in SMB3 where Mario simply goes through the pipe. However, it doesn\'t work correctly.',
                16: 'Path ID:',
                17: '[b]Path ID:[/b][br]Use this option to set the path number that the connected pipe will follow.',
                18: 'Links to Forward Pipe',
                19: '[b]Links to Forward Pipe:[/b][br]If this option is set on a pipe, the destination entrance/area values will be ignored - Mario will pass through the pipe and then reappear several tiles ahead, coming out of a forward-facing pipe.',
                20: 'Layer:',
                21: ('Layer 1', 'Layer 2', 'Layer 0'),
                22: '[b]Layer:[/b][br]Allows you to change the collision layer which this entrance is active on. This option is very glitchy and not used in the default levels - for almost all normal cases, you will want to use layer 1.',
                23: '[b]Entrance [id]:[/b]',
                24: 'Modify Selected Entrance Properties',
                25: 'CP Exit Direction:',
                26: '[b]CP Exit Direction:[/b][br]Set the direction the player will exit out of a connected pipe.',
                27: (
                    'Up',
                    'Down',
                    'Left',
                    'Right',
                    ),
                28: '([id]) [name]',
                },
            'Entrances': {
                0: '[b]Entrance [ent]:[/b][br]Type: [type][br][i][dest][/i]',
                1: 'Unknown',
                2: '(cannot be entered)',
                3: '(arrives at entrance [id] in this area)',
                4: '(arrives at entrance [id] in area [area])',
                5: '[id]: [name] (cannot be entered) at [x], [y]',
                6: '[id]: [name] (enterable) at [x], [y]'
                },
            'Err_BrokenSpriteData': {
                0: 'Warning',
                1: 'The sprite data file didn\'t load correctly. The following sprites have incorrect and/or broken data in them, and may not be editable correctly in the editor: [sprites]',
                2: 'Errors',
                },
            'Err_CantFindLevel': {
                0: 'Could not find file:[br][name]',
                },
            'Err_CorruptedTileset': {
                0: 'Error',
                1: 'An error occurred while trying to load [file].arc. Check your Unit folder to make sure it is complete and not corrupted. The editor may run in a broken state or crash after this.',
                },
            'Err_CorruptedTilesetData': {
                0: 'Error',
                1: 'Cannot find the required texture within the tileset file [file].arc, so it will not be loaded. Keep in mind that the tileset file cannot be renamed without changing the names of the texture/object files within the archive as well!',
                },
            'Err_InvalidLevel': {
                0: 'This file doesn\'t seem to be a valid level.',
                },
            'Err_MissingFiles': {
                0: 'Error',
                1: 'Sorry, you seem to be missing the required data files for Satoru to work. Please redownload your copy of the editor.',
                2: 'Sorry, you seem to be missing some of the required data files for Satoru to work. Please redownload your copy of the editor. These are the files you are missing: [files]',
                },
            'Err_MissingLevel': {
                0: 'Error',
                1: 'Cannot find the required level file [file].arc. Check your Stage folder and make sure it exists.',
                },
            'Err_MissingTileset': {
                0: 'Error',
                1: 'Cannot find the required tileset file [file].arc. Check your Stage folder and make sure it exists.',
                },
            'Err_Save': {
                0: 'Error',
                1: 'Error while Satoru was trying to save the level:[br](#[err1]) [err2][br][br](Your work has not been saved! Try saving it under a different filename or in a different folder.)',
                },
            'FileDlgs': {
                0: 'Choose a level archive',
                1: 'NSMBU Level Archives',
                2: 'All Files',
                3: 'Choose a new filename',
                4: 'Portable Network Graphics',
                5: 'Compressed Level Archives',
                6: 'Choose a stamp archive',
                7: 'Stamps File',
                },
            'Gamedefs': {
                0: 'This game has custom sprite images',
                1: 'Loading patch...',
                2: 'New Game Patch',
                3: 'It appears that this is your first time using the game patch for [game]. Please select its Stage folder so custom tilesets and levels can be loaded.',
                4: 'Aborted Game Path Selection',
                5: 'Since you did not select the stage folder for [game], stages and tilesets will not load correctly. You can try again by choosing Change Game Path while the [game] patch is loaded.',
                6: 'New Game Patch',
                7: 'You can change the game path for [game] at any time by choosing Change Game Path while the [game] patch is loaded.',
                8: 'Loading sprite data...',
                9: 'Loading background names...',
                10: 'Reloading tilesets...',
                11: 'Loading sprite image data...',
                12: 'Applying sprite image data...',
                13: 'New Super Mario Bros. U',
                14: '(insert catchphrase here)[br]Published by Nintendo in August 2012.',
                15: '[i]No description[/i]',
                16: 'Loading entrance names...',
                17: 'Error',
                18: 'An error occurred while attempting to load this game patch. It will now be unloaded. Here\'s the specific error:[br][error]',
                },
            'InfoDlg': {
                0: 'Level Information',
                1: 'Add/Change Password',
                2: 'This level\'s information is locked.[br]Please enter the password below in order to modify it.',
                3: 'Password:',
                4: 'Title:',
                5: 'Author:',
                6: 'Group:',
                7: 'Website:',
                8: 'Created with [name]',
                9: 'Change Password',
                10: 'New Password:',
                11: 'Verify Password:',
                12: 'Level Information',
                13: 'Password may be composed of any ASCII character,[br]and up to 64 characters long.[br]',
                14: 'Sorry![br][br]You can only view or edit Level Information in Area 1.',
                },
            'LocationDataEditor': {
                0: 'ID:',
                1: '[b]ID:[/b][br]Must be different from all other IDs',
                2: 'X Pos:',
                3: '[b]X Pos:[/b][br]Specifies the X position of the location',
                4: 'Y Pos:',
                5: '[b]Y Pos:[/b][br]Specifies the Y position of the location',
                6: 'Width:',
                7: '[b]Width:[/b][br]Specifies the width of the location',
                8: 'Height:',
                9: '[b]Height:[/b][br]Specifies the height of the location',
                10: 'Snap to Grid',
                11: '[b]Location [id]:[/b]',
                12: 'Modify Selected Location Properties',
                },
            'Locations': {
                0: '[id]',
                1: '', # REMOVED: 'Paint New Location'
                2: '[id]: [width]x[height] at [x], [y]',
                },
            'MainWindow': {
                0: '[unsaved]',
                1: 'You\'re trying to paste over 300 items at once.[br]This may take a while (depending on your computer speed), are you sure you want to continue?',
                },
            'Menubar': {
                0: '&File',
                1: '&Edit',
                2: '&View',
                3: '&Settings',
                4: '&Help',
                5: 'Editor Toolbar',
                },
            'MenuItems': {
                0: 'New Level',
                1: 'Create a new, blank level',
                2: 'Open Level by Name...',
                3: 'Open a level based on its in-game world/number',
                4: 'Open Level by File...',
                5: 'Open a level based on its filename',
                6: 'Recent Files',
                7: 'Open a level from a list of recently opened levels',
                8: 'Save Level',
                9: 'Save the level back to the original file',
                10: 'Save Level As...',
                11: 'Save the level to a new file',
                12: 'Level Information...',
                13: "Add title and author information to the level's metadata",
                14: 'Level Screenshot...',
                15: 'Take a full size screenshot of your level for you to share',
                16: 'Change Game Path...',
                17: 'Set a different folder to load the game files from',
                18: 'Satoru Preferences...',
                19: 'Change important Satoru settings',
                20: 'Exit Satoru',
                21: 'Exit the editor',
                22: 'Select All',
                23: 'Select all items in this area',
                24: 'Deselect',
                25: 'Deselect all currently selected items',
                26: 'Cut',
                27: 'Cut out the current selection to the clipboard',
                28: 'Copy',
                29: 'Copy the current selection to the clipboard',
                30: 'Paste',
                31: 'Paste items from the clipboard',
                32: 'Shift Items...',
                33: 'Move all selected items by an offset',
                34: 'Merge Locations',
                35: 'Merge selected locations into a single large location',
                36: 'Level Diagnostics Tool...',
                37: 'Find and fix problems with the level',
                38: 'Freeze\\nObjects',
                39: 'Make objects non-selectable',
                40: 'Freeze\\nSprites',
                41: 'Make sprites non-selectable',
                42: 'Freeze Entrances',
                43: 'Make entrances non-selectable',
                44: 'Freeze\\nLocations',
                45: 'Make locations non-selectable',
                46: 'Freeze Paths',
                47: 'Make paths non-selectable',
                48: 'Layer 0',
                49: 'Toggle viewing of object layer 0',
                50: 'Layer 1',
                51: 'Toggle viewing of object layer 1',
                52: 'Layer 2',
                53: 'Toggle viewing of object layer 2',
                54: 'Show Sprites',
                55: 'Toggle viewing of sprites',
                56: 'Show Sprite Images',
                57: 'Toggle viewing of sprite images',
                58: 'Show Locations',
                59: 'Toggle viewing of locations',
                60: 'Switch\\nGrid',
                61: 'Cycle through available grid views',
                62: 'Zoom to Maximum',
                63: 'Zoom in all the way',
                64: 'Zoom In',
                65: 'Zoom into the main level view',
                66: 'Zoom 100%',
                67: 'Show the level at the default zoom',
                68: 'Zoom Out',
                69: 'Zoom out of the main level view',
                70: 'Zoom to Minimum',
                71: 'Zoom out all the way',
                72: 'Area\\nSettings...',
                73: 'Control tileset swapping, stage timer, entrance on load, and stage wrap',
                74: 'Zone\\nSettings...',
                75: 'Zone creation, deletion, and preference editing',
                76: 'Backgrounds...',
                77: 'Apply backgrounds to individual zones in the current area',
                78: 'Add New Area',
                79: 'Add a new area (sublevel) to this level',
                80: 'Import Area from Level...',
                81: 'Import an area (sublevel) from another level file',
                82: 'Delete Current Area...',
                83: 'Delete the area (sublevel) currently open from the level',
                84: 'Reload Tilesets',
                85: 'Reload the tileset data files, including any changes made since the level was loaded',
                86: 'About Satoru',
                87: 'Info about the program, and the team behind it',
                88: 'Help Contents...',
                89: 'Help documentation for the needy newbie',
                90: 'Satoru Tips...',
                91: 'Tips and controls for beginners and power users',
                92: 'About PyQt...',
                93: 'About the Qt library Satoru is based on',
                94: 'Level Overview',
                95: 'Show or hide the Level Overview window',
                96: 'Palette',
                97: 'Show or hide the Palette window',
                98: 'Change Game',
                99: 'Change the currently loaded Satoru game patch',
                100: 'Island Generator',
                101: 'Show or hide the Island Generator window',
                102: None, # REMOVED: 'Stamp Pad'
                103: None, # REMOVED: 'Show or hide the Stamp Pad window'
                104: 'Swap Objects\' Tileset',
                105: 'Swaps the tileset of objects using a certain tileset',
                106: 'Swap Objects\' Type',
                107: 'Swaps the type of objects of a certain type',
                108: 'Tileset Animations',
                109: 'Play tileset animations if they exist (may cause a slowdown)',
                110: 'Tileset Collisions',
                111: 'View tileset collisions for existing objects',
                112: 'Open Level...',
                113: None, # This keeps the even-odd pattern going, since 112 uses description 3
                114: 'Freeze Comments',
                115: 'Make comments non-selectable',
                116: 'Show Comments',
                117: 'Toggle viewing of comments',
                118: 'Real View',
                119: 'Show special effects present in the level',
                120: 'Check for Updates...',
                121: 'Check if any updates for Satoru are available to download',
                122: 'Highlight 3D Effects',
                123: 'Toggle viewing of 3D depth effect highlighting (NSMB2 only)',
                124: 'Freeze\\nProgress Paths',
                125: 'Make progress paths non-selectable',
                126: 'Show Fullscreen',
                127: 'Display the main window with all available screen space',
                128: 'Reload Spritedata',
                129: 'Reload the spritedata without restarting the editor',
                130: 'Compress NSMBU level with Fake Yaz0',
                131: 'Compress',
                132: 'Compress NSLU level with Fake Yaz0',
                133: 'Compress',
                134: 'Change OneTileset Path...',
                135: 'Change the folder OneTileset is loaded from',
                136: 'Export Level and Tilesets Separately As...',
                137: 'Export raw level data and tilesets separately',
                138: 'Show Paths',
                139: 'Toggle viewing of paths',
                },
            'Objects': {
                0: '[b][type][/b][br][width]x[height] on layer [layer]',
                1: 'Object [id]',
                3: '[b]Object [id]:[/b][br][desc]',
                4: 'Main object [id]:',
                5: 'OneTileset object "[id]":',
                6: 'Embedded object [id]:',
                },
            'OpenFromNameDlg': {
                0: 'Choose Level',
                },
            'Palette': {
                0: 'Paint on Layer:',
                1: '[b]Layer 0:[/b][br]This layer is mostly used for hidden caves, but can also be used to overlay tiles to create effects. The flashlight effect will occur if Mario walks behind a tile on layer 0 and the zone has it enabled.[br]This layer is not supported in New Super Mario Bros. U.[br][b]Note:[/b] To switch objects on other layers to this layer, select them and then click this button while holding down the [i]Alt[/i] key.',
                2: '[b]Layer 1:[/b][br]All or most of your normal level objects should be placed on this layer. This is the only layer where tile interactions (solids, slopes, etc) will work.[br][b]Note:[/b] To switch objects on other layers to this layer, select them and then click this button while holding down the [i]Alt[/i] key.',
                3: '[b]Layer 2:[/b][br]Background/wall tiles (such as those in the hidden caves) should be placed on this layer. Tiles on layer 2 have no effect on collisions.[br][b]Note:[/b] To switch objects on other layers to this layer, select them and then click this button while holding down the [i]Alt[/i] key.',
                4: 'View:',
                5: 'Search:',
                6: 'Set Default Properties',
                7: 'Default Properties',
                8: 'Entrances currently in this area:[br](Double-click one to jump to it instantly)',
                9: 'Path nodes currently in this area:[br](Double-click one to jump to it instantly)[br]To delete a path, remove all its nodes one by one.[br]To add new paths, hit the button below and right click.',
                10: 'Deselect (then right click for new path)',
                11: 'Sprites currently in this area:[br](Double-click one to jump to it instantly)',
                12: 'Locations currently in this area:[br](Double-click one to jump to it instantly)',
                13: 'Objects',
                14: 'Sprites',
                15: 'Entrances',
                16: 'Locations',
                17: 'Paths',
                18: 'Events',
                19: 'Stamps',
                20: 'Event states upon level launch:[br](Click on one to add a note)',
                21: 'Note:',
                22: 'State',
                23: 'Notes',
                24: 'Event [id]',
                25: 'Add',
                26: 'Current',
                27: 'Available stamps:',
                28: 'Add',
                29: 'Remove',
                30: 'Tools',
                31: 'Open Set...',
                32: 'Save Set As...',
                33: 'Comments',
                34: 'Comments currently in this area:[br](Double-click one to jump to it instantly)',
                35: 'Name:',
                36: 'Progress Paths',
                37: 'Progress Path nodes currently in this area:[br](Double-click one to jump to it instantly)[br]To delete a progress path, remove all its nodes one by one.[br]To add new progress paths, hit the button below and right click.',
                38: 'Deselect (then right click for new progress path)',
                },
            'PathDataEditor': {
                0: 'Loops:',
                1: '[b]Loops:[/b][br]Anything following this path will wait for any delay set at the last node and then proceed back in a straight line to the first node, and continue.',
                2: 'Speed:',
                3: '[b]Speed:[/b][br]Unknown unit. Mess around and report your findings!',
                4: 'Accel:',
                5: '[b]Accel:[/b][br]Unknown unit. Mess around and report your findings!',
                6: 'Delay:',
                7: '[b]Delay:[/b][br]Amount of time to stop here (at this node) before continuing to next node. Unit is 1/60 of a second (60 for 1 second)',
                8: '[b]Path [id][/b]',
                9: '[b]Node [id][/b]',
                10: 'Modify Selected Path Node Properties',
                11: 'Unknown 0x01:',
                12: '[b]Unknown 0x01:[/b][br]No idea what this is',
                13: '[b]Path [id] (Nabbit Path)[/b]',
                },
            'Paths': {
                0: '[b]Path [path][/b][br]Node [node]',
                1: 'Path [path], Node [node]',
                },
            'PrefsDlg': {
                0: 'Satoru Preferences',
                1: 'General',
                2: 'Toolbar',
                3: 'Themes',
                4: '[b]Satoru Preferences[/b][br]Customize Satoru by changing these settings.[br]Use the tabs below to view even more settings.[br]Satoru must be restarted before certain changes can take effect.',
                5: '[b]Toolbar Preferences[/b][br]Choose menu items you would like to appear on the toolbar.[br]Satoru must be restarted before the toolbar can be updated.[br]',
                6: '[b]Satoru Themes[/b][br]Pick a theme below to change application colors and icons.[br]You can download more themes at [a href="rvlution.net"]rvlution.net[/a].[br]Satoru must be restarted before the theme can be changed.',
                7: 'Show the splash screen:',
                8: 'If TPLLib cannot use a fast backend (recommended)',
                9: 'Always',
                10: 'Never',
                11: 'Menu format:',
                12: 'Use the ribbon',
                13: 'Use the menubar',
                14: 'Language:',
                15: 'Recent Files data:',
                16: 'Clear All',
                17: 'Clear All Recent Files Data',
                18: 'Are you sure you want to delete all recent files data? This [b]cannot[/b] be undone!',
                19: 'Current Area',
                20: 'Reset',
                21: 'Available Themes',
                22: 'Preview',
                23: 'Use Nonstandard Window Style',
                24: '[b]Use Nonstandard Window Style[/b][br]If this is checkable, the selected theme specifies a[br]window style other than the default. In most cases, you[br]should leave this checked. Uncheck this if you dislike[br]the style this theme uses.',
                25: 'Options',
                26: '[b][name][/b][br]By [creator][br][description]',
                27: 'Tilesets:',
                28: 'Use Default Tileset Picker (recommended)',
                29: 'Use Old Tileset Picker',
                30: 'You may need to restart Satoru for changes to take effect.',
                },
            'Ribbon': {
                0: '&Home',
                1: '&Actions',
                2: '&View',
                3: '&Game',
                4: None, # REMOVED: 'H&elp'
                5: 'Clipboard',
                6: 'Freeze',
                7: 'Level Information',
                8: 'Area',
                9: 'Selection',
                10: 'Items',
                11: 'Level Settings',
                12: 'Areas',
                13: 'Tilesets',
                14: 'Layers',
                15: 'Visibility',
                16: 'Zoom',
                17: 'Docks',
                18: 'Satoru',
                19: 'Libraries',
                20: '([shortcut]) [description]',
                21: ', ',
                22: '(None) [description]',
                23: '&File',
                },
            'ScrShtDlg': {
                0: 'Choose a Screenshot source',
                1: 'Current Screen',
                2: 'All Zones',
                3: 'Zone [zone]',
                },
            'ShftItmDlg': {
                0: 'Shift Items',
                1: 'Move objects by:',
                2: 'Enter an offset in pixels - each block is 16 pixels wide/high. Note that normal objects can only be placed on 16x16 boundaries, so if the offset you enter isn\'t a multiple of 16, they won\'t be moved correctly.',
                3: 'X:',
                4: 'Y:',
                5: 'Warning',
                6: 'You are trying to move object(s) by an offset which isn\'t a multiple of 16. It will work, but the objects will not be able to move exactly the same amount as the sprites. Are you sure you want to do this?',
                },
            'Splash': {
                0: '[current] (Stage [stage])',
                1: 'Loading layers...',
                2: 'Loading level data...',
                3: 'Loading tilesets...',
                4: 'Loading objects...',
                5: 'Preparing editor...',
                },
            'SpriteDataEditor': {
                0: 'Modify Selected Sprite Properties',
                1: '[b][name][/b]: [note]',
                2: '[b]Sprite Notes:[/b] [notes]',
                3: 'Modify Raw Data:',
                4: 'Notes',
                5: '[b]Unidentified/Unknown Sprite ([id])[/b]',
                6: '[b]Sprite [id]:[br][name][/b]',
                7: 'Object Files',
                8: '[b]This sprite uses:[/b][br][list]',
                },
            'Sprites': {
                0: '[b]Sprite [type]:[/b][br][name]',
                1: '[name] (at [x], [y]',
                2: ', triggered by event [event]',
                3: ', triggered by events [event1]+[event2]+[event3]+[event4]',
                4: ', triggered by event [event1], [event2], [event3], or [event4]',
                5: ', activates event [event]',
                6: ', activates events [event1] - [event2]',
                7: ', activates event [event1], [event2], [event3], or [event4]',
                8: ', Star Coin [num]',
                9: ', Star Coin 1',
                10: ', Coin/Set ID [id]',
                11: ', Movement/Coin ID [id]',
                12: ', Movement ID [id]',
                13: ', Rotation ID [id]',
                14: ', Location ID [id]',
                15: ')',
                16: 'Search Results',
                17: 'No sprites found',
                18: '[id]: [name]',
                19: 'Search',
                },
            'Statusbar': {
                0: '- 1 object selected',
                1: '- 1 sprite selected',
                2: '- 1 entrance selected',
                3: '- 1 location selected',
                4: '- 1 path node selected',
                5: '- [x] objects selected',
                6: '- [x] sprites selected',
                7: '- [x] entrances selected',
                8: '- [x] locations selected',
                9: '- [x] path nodes selected',
                10: '- [x] items selected (',
                11: ', ',
                12: '1 object',
                13: '[x] objects',
                14: '1 sprite',
                15: '[x] sprites',
                16: '1 entrance',
                17: '[x] entrances',
                18: '1 location',
                19: '[x] locations',
                20: '1 path node',
                21: '[x] path nodes',
                22: ')',
                23: '- Object under mouse: size [width]x[height] at ([xpos], [ypos]) on layer [layer]; [info]',
                24: '- Sprite under mouse: [name] at [xpos], [ypos]',
                25: '- Entrance under mouse: [name] at [xpos], [ypos] [dest]',
                26: '- Location under mouse: Location ID [id] at [xpos], [ypos]; width [width], height [height]',
                27: '- Path node under mouse: Path [path], Node [node] at [xpos], [ypos]',
                28: '([objx], [objy]) - ([sprx], [spry])',
                29: '- 1 comment selected',
                30: '- [x] comments selected',
                31: '1 comment',
                32: '[x] comments',
                33: '- Comment under mouse: [xpos], [ypos]; "[text]"',
                34: '- 1 progress path node selected',
                35: '- [x] progress path nodes selected',
                36: '1 progress path node',
                37: '[x] progress path nodes',
                38: '- Progress Path node under mouse: Progress Path [path], Node [node] at [xpos], [ypos]',
                39: '- Progress Path node under mouse: Progress Path [path]A, Node [node] at [xpos], [ypos]',
                40: 'main object [id]',
                41: 'OneTileset object "[id]"',
                42: 'embedded level object [id]',
                43: '; contents value of [val]',
                },
            'Themes': {
                0: 'Classic',
                1: 'Treeki, Tempus',
                2: 'The default Satoru theme.',
                3: '[i](unknown)[/i]',
                4: '[i]No description[/i]',
                },
            'Updates': {
                0: 'Check for Updates',
                1: 'Error while checking for updates.',
                2: 'No updates are available.',
                3: 'An update is available: [name][br][info]',
                4: 'Download Now',
                5: 'Please wait, the update is downloading...',
                6: 'Restart to finalize update!',
                },
            'WindowTitle': {
                0: 'Untitled',
                },
            'ZonesDlg': {
                0: 'Zones',
                1: (
                    'Overworld',
                    'Underground',
                    'Underwater',
                    'Lava/Volcano (reddish)',
                    'Desert',
                    'Beach*',
                    'Forest*',
                    'Snow Overworld*',
                    'Sky/Bonus*',
                    'Mountains*',
                    'Tower',
                    'Castle',
                    'Ghost House',
                    'River Cave',
                    'Ghost House Exit',
                    'Underwater Cave',
                    'Desert Cave',
                    'Icy Cave*',
                    'Lava/Volcano',
                    'Final Battle',
                    'World 8 Castle',
                    'World 8 Doomship*',
                    'Lit Tower',
                    ),
                2: (
                    'Normal/Overworld',
                    'Underground',
                    'Underwater',
                    'Lava/Volcano',
                    ),
                3: 'Zone [num]',
                4: 'New',
                5: 'Delete',
                6: 'Warning',
                7: 'You are trying to add more than 15 zones to a level - keep in mind that without the proper fix to the game, this will cause your level to [b]crash[/b] or have other strange issues![br][br]Are you sure you want to do this?',
                8: 'Dimensions',
                9: 'X position:',
                10: '[b]X position:[/b][br]Sets the X Position of the upper left corner',
                11: 'Y position:',
                12: '[b]Y position:[/b][br]Sets the Y Position of the upper left corner',
                13: 'X size:',
                14: '[b]X size:[/b][br]Sets the width of the zone',
                15: 'Y size:',
                16: '[b]Y size:[/b][br]Sets the height of the zone',
                17: 'Preset:',
                18: '[b]Preset:[/b][br]Snaps the zone to common sizes.[br]The number before each entry specifies which zoom level works best with each size.',
                19: 'Rendering and Camera',
                20: 'Zone Theme:',
                21: '[b]Zone Theme:[/b][br]Changes the way models and parts of the background are rendered (for blurring, darkness, lava effects, and so on). Themes with * next to them are used in the game, but look the same as the overworld theme.',
                22: 'Terrain Lighting:',
                23: '[b]Terrain Lighting:[/b][br]Changes the way the terrain is rendered. It also affects the parts of the background which the normal theme doesn\'t change.',
                24: 'Normal',
                25: '[b]Visibility - Normal:[/b][br]Sets the visibility mode to normal.',
                26: 'Layer 0 Spotlight',
                27: '[b]Visibility - Layer 0 Spotlight:[/b][br]Sets the visibility mode to spotlight. In Spotlight mode,[br]moving behind layer 0 objects enables a spotlight that[br]follows Mario around.',
                28: 'Full Darkness',
                29: '[b]Visibility - Full Darkness:[/b][br]Sets the visibility mode to full darkness. In full dark mode,[br]the screen is completely black and visibility is only provided[br]by the available spotlight effect. Stars and some sprites[br]can enhance the default visibility.',
                30: 'X Tracking:',
                31: '[b]X Tracking:[/b][br]Allows the camera to track Mario across the X dimension.[br]Turning off this option centers the screen horizontally in the view, producing a stationary camera mode.',
                32: 'Y Tracking:',
                33: '[b]Y Tracking:[/b][br]Allows the camera to track Mario across the Y dimension.[br]Turning off this option centers the screen vertically in the view, producing very vertically limited stages.',
                34: 'Zoom Level:',
                35: '[b]Zoom Level:[/b][br]Changes the camera zoom functionality[br] - Negative values: Zoom In[br] - Positive values: Zoom Out[br][br]Zoom Level 4 is rather glitchy',
                36: 'Bias:',
                37: '[b]Bias:[/b][br]Sets the screen bias to the left edge on load, preventing initial scrollback.[br]Useful for pathed levels.[br]Note: Not all zoom/mode combinations support bias',
                38: (
                    'Left to Right',
                    'Right to Left',
                    'Top to Bottom',
                    'Bottom to Top',
                    ),
                39: 'Camera Tracking:',
                40: '[b]Camera Tracking:[/b][br]This setting makes changes to camera tracking during multiplayer mode.[br]If the camera doesn\'t move, choose Left to Right.[br]If you\'re unsure, choose Left to Right.',
                41: (
                    'Hidden',
                    'On Top',
                    ),
                42: '[b]Visibility:[/b][br]Hidden - Mario is hidden when moving behind objects on Layer 0[br]On Top - Mario is displayed above Layer 0 at all times.[br][br]Note: Entities behind layer 0 other than Mario are never visible',
                43: (
                    'Small',
                    'Large',
                    'Full Screen',
                    ),
                44: '[b]Visibility:[/b][br]Small - A small, centered spotlight affords visibility through layer 0.[br]Large - A large, centered spotlight affords visibility through layer 0[br]Full Screen - the entire screen is revealed whenever Mario walks behind layer 0',
                45: ('Large Foglight',
                     'Lightbeam',
                     'Large Focus Light',
                     'Small Foglight',
                     'Small Focus Light',
                     'Absolute Black',
                     ),
                46: '[b]Visibility:[/b][br]Large Foglight - A large, organic lightsource surrounds Mario[br]Lightbeam - Mario is able to aim a conical lightbeam through use of the Wiimote[br]Large Focus Light - A large spotlight which changes size based upon player movement[br]Small Foglight - A small, organic lightsource surrounds Mario[br]Small Focuslight - A small spotlight which changes size based on player movement[br]Absolute Black - Visibility is provided only by fireballs, stars, and certain sprites',
                47: 'Bounds',
                48: 'Upper Bounds:',
                49: '[b]Upper Bounds:[/b][br] - Positive Values: Easier to scroll upwards (110 is centered)[br] - Negative Values: Harder to scroll upwards (30 is the top edge of the screen)[br][br]Values higher than 240 can cause instant death upon screen scrolling',
                50: 'Lower Bounds:',
                51: '[b]Lower Bounds:[/b][br] - Positive Values: Harder to scroll downwards (65 is the bottom edge of the screen)[br] - Negative Values: Easier to scroll downwards (95 is centered)[br][br]Values higher than 100 will prevent the scene from scrolling until Mario is offscreen',
                52: 'Audio',
                53: 'Background Music:',
                54: '[b]Background Music:[/b][br]Changes the background music',
                55: 'Sound Modulation:',
                56: '[b]Sound Modulation:[/b][br]Changes the sound effect modulation',
                57: (
                    'Normal',
                    'Wall Echo',
                    'Room Echo',
                    'Double Echo',
                    'Cave Echo',
                    'Underwater Echo',
                    'Triple Echo',
                    'High Pitch Echo',
                    'Tinny Echo',
                    'Flat',
                    'Dull',
                    'Hollow Echo',
                    'Rich',
                    'Triple Underwater',
                    'Ring Echo',
                    ),
                58: 'Boss Flag:',
                59: '[b]Boss Flag:[/b][br]Set for bosses to allow proper music switching by sprites',
                60: '(None)',
                61: 'Error',
                62: 'Zoom level -2 does not support bias modes.',
                63: 'Zoom level -1 does not support bias modes.',
                64: 'Zoom level -1 is not supported with these Tracking modes. Set to Zoom level 0.',
                65: 'Zoom mode 4 can be glitchy with these settings.',
                66: 'No tracking mode is consistently glitchy and does not support bias.',
                67: 'No tracking mode is consistently glitchy.',
                68: 'Background Music ID:',
                69: '[b]Background Music ID:[/b][br]This advanced option allows custom music tracks to be loaded if the proper ASM hacks are in place.',
                70: 'Upper Bounds 2:',
                71: '[b]Upper Bounds 2:[/b][br]Unknown differences from the main upper bounds.',
                72: 'Lower Bounds 2:',
                73: '[b]Lower Bounds 2:[/b][br]Unknown differences from the main lower bounds.',
                74: 'Unknown Flag',
                75: '[b]Unknown Flag:[/b][br]Unknown purpose. Seems to be always checked.',
                76: 'some unknown thing',
                },
            'Zones': {
                0: 'Zone [num]',
                },
            }


    def InitFromXML(self, name):
        """
        Parses the translation XML
        """
        if name in ('', None, 'None'): return
        name = str(name)
        MaxVer = 1.0

        # Parse the file (errors are handled by __init__())
        path = 'Satorudata/translations/' + name + '/main.xml'
        tree = etree.parse(path)
        root = tree.getroot()

        # Add attributes
        # Name
        if 'name' not in root.attrib: raise Exception
        self.name = root.attrib['name']
        # Version
        if 'version' not in root.attrib: raise Exception
        self.version = float(root.attrib['version'])
        if self.version > MaxVer: raise Exception
        # Translator
        if 'translator' not in root.attrib: raise Exception
        self.translator = root.attrib['translator']

        # Parse the nodes
        files = {}
        strings = False
        addpath = 'Satorudata/translations/' + name + '/'
        for node in root:
            if node.tag.lower() == 'file':
                # It's a file node
                name = node.attrib['name']
                path = addpath + node.attrib['path']
                files[name] = path
            elif node.tag.lower() == 'strings':
                # It's a strings node
                strings = addpath + node.attrib['path']

        # Get rid of the XML stuff
        del tree, root

        # Overwrite self.files with files
        for index in files: self.files[index] = files[index]



        # Check for a strings node
        if not strings: raise Exception

        # Parse the strings
        tree = etree.parse(strings)
        root = tree.getroot()

        # Parse the nodes
        strings = {}
        for section in root:
            # Get a section
            if section.tag.lower() != 'section': continue
            id = section.attrib['id']
            sectionStrings = {}

            # Get the strings/stringlists in this section
            for string in section:
                if not hasattr(string, 'attrib'): continue
                strValue = None
                if string.tag.lower() == 'string':
                    # String node; this is easy
                    strValue = string[0]
                elif string.tag.lower() == 'stringlist':
                    # Not as easy, but not hard
                    strValue = []
                    for entry in string:
                        if entry.tag.lower() == 'entry':
                            strValue.append(entry[0])
                    strValue = tuple(strValue)

                # Add this string to sectionStrings
                idB = int(string.attrib['id'])
                if strValue is not None: sectionStrings[idB] = strValue

            # Add it to strings
            strings[id] = sectionStrings

        # Overwrite self.strings with strings
        for index in strings:
            if index not in self.strings: self.strings[index] = {}
            for index2 in strings[index]:
                self.strings[index][index2] = strings[index][index2]


    def string(*args):
        """
        Usage: string(section, numcode, replacementDummy, replacement, replacementDummy2, replacement2, etc.)
        """
        self = args[0]

        # If there are errors when the string is found, return an error report instead
        try: return self.string_(args[1:])
        except Exception as e:
            text = '\nSatoruTranslation.string() ERROR: ' + str(args[1]) + '; ' + str(args[2]) + '; ' + repr(e) + '\n'
            # do 3 things with the text - print it, save it to SatoruErrors.txt, return it
            print(text)
            if not os.path.isfile('SatoruErrors.txt'):
                f = open('SatoruErrors.txt', 'w')
            else:
                f = open('SatoruErrors.txt', 'a')
            f.write(text)
            f.close(); del f
            return text

    def string_(*args):
        """
        Gets a string from the translation and returns it
        """
        # Get self and remove it from args
        self = args[0]
        args = args[1]

        # Get the string
        astring = self.strings[args[0]][args[1]]

        # Perform any replacements
        i = 2
        while i < len(args):

            # Get the old string
            old = str(args[i])

            # Get the new string
            new = str(args[i+1])

            # Replace
            astring = astring.replace(old, new)
            i += 2

        # Do some automatic replacements
        replace = {
            '[br]': '<br>',
            '[b]': '<b>',
            '[/b]': '</b>',
            '[i]': '<i>',
            '[/i]': '</i>',
            '[a': '<a',
            '"]': '">', # workaround
            '[/a]': '</a>',
            '\\n': '\n',
            '//n': '\n',
            }
        for old in replace:
            astring = astring.replace(old, replace[old])

        # Return it
        return astring

    def stringList(self, section, numcode):
        """
        Returns a list of strings
        """
        try: return self.strings[section][numcode]
        except Exception: return ('SatoruTranslation.stringList() ERROR:', section, numcode)

    def path(self, key):
        """
        Returns the path to the file indicated by key
        """
        try: return self.files[key]
        except Exception:
            # (print, save, return) an error message
            text = 'SatoruTranslation.path() ERROR: ' + key
            print(text)
            F = open('SatoruErrors.txt', 'w')
            F.write(text)
            F.close()
            raise SystemExit

    def generateXML(self):
        """
        Generates a strings.xml and places it in the folder of Satoru.py
        """

        # Sort self.strings
        sortedstrings = sorted(
            (
                [
                    key,
                    sorted(
                        self.strings[key].items(),
                        key=lambda entry: entry[0]),
                    ]
                for key in self.strings
                ),
            key=lambda entry: entry[0])

        # Create an XML
        root = etree.Element('strings')
        for sectionname, section in sortedstrings:
            sectionElem = etree.Element('section', {'id': sectionname})
            root.append(sectionElem)
            for stringid, string in section:
                if isinstance(string, tuple) or isinstance(string, list):
                    stringlistElem = etree.Element('stringlist', {'id': str(stringid)})
                    sectionElem.append(stringlistElem)
                    for entryname in string:
                        entryElem = etree.Element('entry')
                        entryElem.text = entryname
                        stringlistElem.append(entryElem)
                else:
                    stringElem = etree.Element('string', {'id': str(stringid)})
                    stringElem.text = string
                    sectionElem.append(stringElem)

        tree = etree.ElementTree(root)
        tree.write('strings.xml', encoding='utf-8')
