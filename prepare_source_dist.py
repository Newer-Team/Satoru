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


# prepare_source_dist.py
# Prepares the source distribution of Satoru!

# Use the values below to configure the release:
PackageName = 'satoru_nsmbu_041_alpha_src'


################################################################
################################################################

# Imports
import os.path, os, shutil

dir_ = 'distrib/' + PackageName

print('[[ Preparing Source Distribution for Satoru ]]')
print('>> Destination directory: %s' % dir_)

if os.path.isdir(dir_): shutil.rmtree(dir_)
os.makedirs(dir_)

folders = (
    ('satorudata', dir_ + '/satorudata'),
    ('satoruextras', dir_ + '/satoruextras'),
    )
files = (

    # alphabetical
    ('prepare_source_dist.py', dir_),
    ('satoru.py', dir_),
    ('sprites.py', dir_),
    ('strings.py', dir_),
    ('windows_build.py', dir_),

    ('license.txt', dir_),
    ('readme.txt', dir_),
    )
errors = []
for folder, folderdir in folders:
    try: shutil.copytree(folder, folderdir)
    except: errors.append(folder)
for file, filedir in files:
    try: shutil.copy(file, filedir)
    except: errors.append(file)

if len(errors) > 0:
    print('>> The following files and/or folders failed to copy:')
    for e in errors: print('    ' + e)
print('>> All done!')
