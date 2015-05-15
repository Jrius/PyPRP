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

# Add an export option to Blender's menu
# (only option right now is all as full age, the remaining ones will have to be added)

import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty

from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper,
                                 axis_conversion)

from PyPRP.prp_Export import open_file


class PyPRPExport(bpy.types.Operator):
    bl_idname = "export.pyprp"
    bl_label = "PyPRP Export"
    
    filepath = StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        filePath = bpy.path.ensure_ext(self.filepath, ".age")
        
        #### EXPORT ####
        
        open_file(self.filepath, "e_age")
        
        #### DONE EXPORT ####
        
        
        
        return {'FINISHED'}

    def invoke(self, context, event):
        print("Be Invoked !")
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".age")
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {'RUNNING_MODAL'}



def menu_func_export(self, context):
    self.layout.operator(PyPRPExport.bl_idname, text="PyPRP Age (.age)") # more to come


def register():
    bpy.utils.register_class(PyPRPExport)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(PyPRPExport)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
