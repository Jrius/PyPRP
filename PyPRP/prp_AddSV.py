#!BPY
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
#Name: 'PyPRP Soft Volumes'
#Blender: 243
#Group: 'Add'
#Submenu: 'Add a Soft Volume Plane' i_svplane
#Submenu: 'Add a Soft Volume Cube' i_svcube
#Tooltip: 'GoW PyPRP Softvolumes'
#"""

import time, sys, os
from bpy import *
from os.path import *
from prp_Functions import *
from prp_ResManager import *


def new_softvolumeplane():
    alcCreateSoftVolumePlane()
    bpy.context.scene.update()

def new_softvolumecube():
    alcCreateSoftVolumeCube()
    bpy.context.scene.update()
