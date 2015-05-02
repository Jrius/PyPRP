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

bl_info = {
    'name': 'PyPRP exporter',
    'author': 'PyPRP team',
    'version': (0, 0, 1),
    'blender': (2, 7, 1),
    'location': 'File > Export > PyPRP',
    'description': 'PyPRP version 1 for Blender 2.71',
    'category': 'Import-Export'
}




import bpy

# this is a dirty dirty hack from PyPRP2
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import ExportOperator, AddOperators

def register():
    ExportOperator.register()
    AddOperators.register()

def unregister():
    ExportOperator.unregister()
    AddOperators.unregister()

if __name__ == "__main__":
    register()

