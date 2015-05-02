#
#    Copyright (C) 2008  Guild of Writers PyPRP Project Team
#    See the file AUTHORS for more info about the team
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#    Please see the file LICENSE for the full license.

# This script is now called by ExportOperator.py

#"""
#Name: 'PyPRP'
#Blender: 243
#Group: 'Add'
#Submenu: 'Create a New Book' i_book
#Submenu: 'Create a New SpawnPoint' i_swpoint
#Submenu: 'Add a (Generic) Logic Region' i_region
#Submenu: 'Add a Footstep Sound Region' i_footstepregion
#Submenu: 'Add a Panic Link Region' i_paniclnkregion
#Tooltip: 'GoW PyPRP'
#"""

import prp_Config
prp_Config.startup()

import time, sys, os
from os.path import *
from bpy import *
from prp_ResManager import *
from prp_AlcScript import *
from prp_Functions import *

import math
from math import *

def new_book():
	txt=alcFindBlenderTextNofail("Book")
	txt.clear()
	txt.write("""age:
	sequenceprefix: 100
	daylength: 24.0
	maxcapacity: 10
	starttime: 0
	lingertime: 180

	pages:
		- index: 0
		  name: mainRoom

config:
	agesdlhook: true
	""")
	txt=alcFindBlenderTextNofail("init")
	txt.clear()
	txt.write("""# --Fog settings--

# Visibility distance
Graphics.Renderer.SetYon 10000

# Fog depth (distance to start, distance to end, overall density)
Graphics.Renderer.Fog.SetDefLinear 100 10000 1

# Alternative (exponential) fog (distance to end, overall density)
# Graphics.Renderer.Fog.SetDefExp2 100000 20

# Fog color (red, green, blue - in range 0-1 )
# color when nothing is displayed
Graphics.Renderer.Fog.SetDefColor .5 .6 .9
# color to tint objects
Graphics.Renderer.SetClearColor .5 .6 .9
""")
	txt=alcFindBlenderTextNofail("AlcScript")
	txt.clear()
	txt.write("""# insert AlcScript code here""")

def new_point():
    alcCreateLinkInPoint()
    bpy.context.scene.update()

def new_region():
    alcCreateRegion()
    bpy.context.scene.update()

def new_footstepregion():
    alcCreateFootstepRegion()
    bpy.context.scene.update()

def new_paniclnkregion():
    alcCreatePanicLnkRegion()
    bpy.context.scene.update()

