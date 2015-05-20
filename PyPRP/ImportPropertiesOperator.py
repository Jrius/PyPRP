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

# Add option to import object custom properties to Blender.
# Properties are in the YAML format

import bpy
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty

from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper,
                                 axis_conversion)

from PyPRP.prp_AlcScript import AlcScript


class PyPRPImportCustomProperties(bpy.types.Operator):
    bl_idname = "import.pyprp_customproperties"
    bl_label = "Import custom properties"
    
    filepath = StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        filePath = bpy.path.ensure_ext(self.filepath, ".txt")
        
        # open the file
        f=open(filePath, "r")
        content = f.read()
        f.close()

        # parse it
        alc = AlcScript(content.replace("\t", "    "))
        rootscript = alc.GetRootScript()
        for objname in rootscript:
            try:
                obj = bpy.data.objects[objname]
            except:
                print("WARNING ! Object %s not found !" % objname)
                continue
            allprops = rootscript[objname]
            for prop in allprops:
                # don't parse special properties
                if not prop.startswith("special_") and not prop in ("rc", "el"):
                    print("%s: adding property %s with value %s" % (objname, prop, allprops[prop]))
                    obj[prop] = allprops[prop] # set obj property
            
            #print(allprops)
            
            if allprops["special_actor"]:
                print("%s: object is an actor" % objname)
                obj.show_axis = True
            if allprops["special_collisions"]:
                print("%s: object has collisions" % objname)
                if not obj.rigid_body:
                    bpy.context.scene.objects.active = obj
                    bpy.ops.rigidbody.object_add()
                obj.rigid_body.enabled = False
                if allprops["special_collisionstype"] in ("box", "sphere", "cylinder", "cone"):
                    obj.rigid_body.collision_shape = allprops["special_collisionstype"].upper()
                elif allprops["special_collisionstype"] == "triangle":
                    obj.rigid_body.collision_shape = "MESH"
                elif allprops["special_collisionstype"] == "hull":
                    obj.rigid_body.collision_shape = "CONVEX_HULL"
            if allprops["special_dynamic"]:
                print("%s: object is dynamic" % objname)
                if not obj.rigid_body:
                    bpy.context.scene.objects.active = obj
                    bpy.ops.rigidbody.object_add()
                obj.rigid_body.enabled = True
                obj.rigid_body.type = "ACTIVE"
            if obj.rigid_body:
                if "rc" in allprops:
                    print("%s: object has friction" % objname)
                    obj.rigid_body.friction = allprops["rc"]
                if "el" in allprops:
                    print("%s: object has elasticity" % objname)
                    obj.rigid_body.restitution = allprops["el"]
        
        return {'FINISHED'}

    def invoke(self, context, event):
        print("Be Invoked !")
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".txt")
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func_import(self, context):
    self.layout.operator(PyPRPImportCustomProperties.bl_idname, text="Custom properties (.txt)")


def register():
    bpy.utils.register_class(PyPRPImportCustomProperties)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(PyPRPImportCustomProperties)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
