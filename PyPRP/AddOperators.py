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

# Adds all sort of stuff to Blenders "Add" menu.


from random import *
import bpy, mathutils, bmesh, os, time
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty
from math import sqrt


from prp_AddBook import *
from prp_AddSV import *




def register():
    bpy.utils.register_class(PyPRPAgeinfoAdd)
    bpy.utils.register_class(PyPRPSpPtAdd)
    bpy.utils.register_class(PyPRPRegionAdd)
    bpy.utils.register_class(PyPRPFootstepAdd)
    bpy.utils.register_class(PyPRPPanicLinkAdd)
    
    bpy.utils.register_class(PyPRPSoftVolPlaneAdd)
    bpy.utils.register_class(PyPRPSoftVolCubeAdd)
    
    bpy.utils.register_class(INFO_MT_pyprp_add)
    bpy.utils.register_class(INFO_MT_pyprp_sv_add)
    
    bpy.utils.register_class(makeAllPhysical)
    
    bpy.types.INFO_MT_add.append(menu_func)

def unregister():
    bpy.utils.unregister_class(PyPRPAgeinfoAdd)
    bpy.utils.unregister_class(PyPRPSpPtAdd)
    bpy.utils.unregister_class(PyPRPRegionAdd)
    bpy.utils.unregister_class(PyPRPFootstepAdd)
    bpy.utils.unregister_class(PyPRPPanicLinkAdd)
    
    bpy.utils.unregister_class(PyPRPSoftVolPlaneAdd)
    bpy.utils.unregister_class(PyPRPSoftVolCubeAdd)
    
    bpy.utils.unregister_class(INFO_MT_pyprp_add)
    bpy.utils.unregister_class(INFO_MT_pyprp_sv_add)
    
    bpy.utils.unregister_class(makeAllPhysical)
    
    bpy.types.INFO_MT_add.remove(menu_func)


class PyPRPAgeinfoAdd(bpy.types.Operator):
    bl_idname = "pyprp.add_ageinfo"
    bl_label = "Add Bookinfo text files"

    def execute(self, context):
        new_book()
        return{'FINISHED'}


class PyPRPSpPtAdd(bpy.types.Operator):
    bl_idname = "pyprp.add_sppt"
    bl_label = "Add new spawn point"

    def execute(self, context):
        new_point()
        return{'FINISHED'}


class PyPRPRegionAdd(bpy.types.Operator):
    bl_idname = "pyprp.add_region"
    bl_label = "Add new spawn point"

    def execute(self, context):
        new_region()
        return{'FINISHED'}


class PyPRPFootstepAdd(bpy.types.Operator):
    bl_idname = "pyprp.add_footstep"
    bl_label = "Add new footstep sound region"

    def execute(self, context):
        new_footstepregion()
        return{'FINISHED'}


class PyPRPPanicLinkAdd(bpy.types.Operator):
    bl_idname = "pyprp.add_paniclink"
    bl_label = "Add new panic-link region"

    def execute(self, context):
        new_paniclnkregion()
        return{'FINISHED'}


class PyPRPSoftVolPlaneAdd(bpy.types.Operator):
    bl_idname = "pyprp.add_svplane"
    bl_label = "Add new soft volume plane"

    def execute(self, context):
        new_softvolumeplane()
        return{'FINISHED'}


class PyPRPSoftVolCubeAdd(bpy.types.Operator):
    bl_idname = "pyprp.add_svcube"
    bl_label = "Add new soft volume cube"

    def execute(self, context):
        new_softvolumecube()
        return{'FINISHED'}


class makeAllPhysical(bpy.types.Operator):
    bl_idname = "pyprp.allphys"
    bl_label = "special!"

    def execute(self, context):
        bpy.context.area.type="PROPERTIES"
        for object in bpy.context.scene.objects:
            if object.type != "MESH": continue
            bpy.context.scene.objects.active = object
            bpy.ops.rigidbody.object_add()
        return{'FINISHED'}


class INFO_MT_pyprp_add(bpy.types.Menu):
    """Creates a fancy menu"""
    bl_idname = "INFO_MT_pyprp_add"
    bl_label = "PyPRP"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("pyprp.add_ageinfo", text="Age infos (previously \"book\")")
        layout.operator("pyprp.add_sppt", text="Link-in point")
        layout.operator("pyprp.add_region", text="Detector region")
        layout.operator("pyprp.add_footstep", text="Footstep sound region")
        layout.operator("pyprp.add_paniclink", text="Panic-link region")
        layout.operator("pyprp.allphys", text="Make all physical")


class INFO_MT_pyprp_sv_add(bpy.types.Menu):
    """Creates a fancy menu"""
    bl_idname = "INFO_MT_pyprp_sv_add"
    bl_label = "PyPRP soft volumes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("pyprp.add_svplane", text="Soft volume plane")
        layout.operator("pyprp.add_svcube", text="Soft volume cube")



def menu_func(self, context):
    """Adds a fancy menu to the 3D view"""
    self.layout.menu("INFO_MT_pyprp_add", icon="PLUGIN")
    self.layout.menu("INFO_MT_pyprp_sv_add", icon="PLUGIN")

