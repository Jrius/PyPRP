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

from bpy import *
import hashlib, random, binascii, io, copy, PIL.Image, math, struct, io, os, os.path, pickle, mathutils
from prp_AbsClasses import *
from prp_MatClasses import *
from prp_DrawClasses import *
from prp_SwimClasses import *
from prp_CamClasses import *
from prp_Types import *
from prp_DXTConv import *
from prp_HexDump import *
from prp_GeomClasses import *
from prp_Functions import *
from prp_ConvexHull import *
from prp_VolumeIsect import *
from prp_AlcScript import *
import prp_AnimClasses

import prp_Config, prp_HexDump
def stripIllegalChars(name):
    name=name.replace("*","_")
    name=name.replace("?","_")
    name=name.replace("\\","_")
    name=name.replace("/","_")
    name=name.replace("<","_")
    name=name.replace(">","_")
    name=name.replace(":","_")
    name=name.replace("\"","_")
    name=name.replace("|","_")
    name=name.replace("#","_")
    name=name.strip()
    return name

class plSceneNode(hsKeyedObject):                           #Type 0x00
    def __init__(self,parent,name="unnamed",type=0x0000):               #Members
        hsKeyedObject.__init__(self,parent,name,type)            #Base
        self.SceneObjects=hsTArray([0x01],self.getVersion())                  #plSceneObjects (vector)
        if self.getVersion()==6:
            ##myst5 types
            self.OtherObjects=hsTArray([0xCD,0x6B,0x80,0x8E,0x0110],6)
        else:
            ##Uru types
            self.OtherObjects=hsTArray([0x7A,0x98,0xA8,0xB5,0xE4,0xE8,0xE9,0xEA,0xED,0xF1,0x0109,0x010A,0x0129,0x012A,0x012B],5)


    def changePageRaw(self,sid,did,stype,dtype):
        self.SceneObjects.changePageRaw(sid,did,stype,dtype)
        self.OtherObjects.changePageRaw(sid,did,stype,dtype)


    def read(self,stream):
        hsKeyedObject.read(self,stream)
        self.SceneObjects.ReadVector(stream)
        self.OtherObjects.ReadVector(stream)
       # size, = struct.unpack("I",stream.read(4))
       # for i in range(size):
       #     o = UruObjectRef(self.getVersion())
       #     o.read(stream)
       #     #print o
       #     if not o.Key.object_type in self.data1allow:
       #         raise RuntimeError("Type %04X is not a plSceneObject [0x0000]" % o.Key.object_type)
       #     self.data1.append(o)
       # size, = struct.unpack("I",stream.read(4))
       # for i in range(size):
       #     o = UruObjectRef(self.getVersion())
       #     o.read(stream)
       #     if not o.Key.object_type in self.data2allow:
       #         raise RuntimeError("Type %04X is not in allow list 2" % o.Key.object_type)
       #     self.data2.append(o)
       # assert(self.verify())


    def write(self,stream):
        hsKeyedObject.write(self,stream)
        self.SceneObjects.WriteVector(stream)
        self.OtherObjects.WriteVector(stream)
       # stream.write(struct.pack("I",len(self.data1)))
       # for o in self.data1:
       #     #o.update(self.Key)
       #     o.write(stream)
       # stream.write(struct.pack("I",len(self.data2)))
       # for o in self.data2:
       #     #o.update(self.Key)
       #     o.write(stream)


    def _Find(page,name):
        return page.find(0x0000,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0000,name,1)
    FindCreate = staticmethod(_FindCreate)

    def import_all(self,scene):
        root = self.getRoot()


        reflist1 = []
        # 1st pass - objects containing lights...
        for ref in self.SceneObjects.vector:
            o=root.findref(ref)

            LightInfo = False

            for r in  o.data.data1.vector:
                if r.Key.object_type in [0x55,0x56,0x57]:
                    LightInfo = True

            if LightInfo:
                o.data.import_all(scene)
            else:
                reflist1.append(ref)

        # 2nd pass - other objects
        for ref in reflist1:
            o=root.findref(ref)
            o.data.import_all(scene)

        bpy.context.scene.update()


class plSceneObject(plSynchedObject):                       #Type 0x01
    def __init__(self,parent,name="unnamed",type=0x0001):               #Members
        plSynchedObject.__init__(self,parent,name,type)
        self.draw=UruObjectRef()                            #Span Info
        self.simulation=UruObjectRef()                      #Animation Info
        self.coordinate=UruObjectRef()                      #Region Info
        self.audio=UruObjectRef()                           #Sound Info
        self.scene=UruObjectRef()                           #SceneNode to which this object belong
        if self.getVersion()==6:
            #myst5 types
            self.data1=hsTArray([0x0C,0x50,0x51,0x52,0x5A,0x5B,0x76,0xB5,0xB6],6)
            self.data2=hsTArray([0x08,0x1B,0x21,0x23,0x2A,0x2C,0x3B,0x3C,0x3E,0x56,0x57,0x5F,0x60,0x62,0x6A,0x6C,0x6D,0x6E,0x7D,0x83,0x87,0x88,0x8A,0x91,0x92,0x94,0x97,0x98,0x9C,0x9E,0xA5,0xAC,0xB4,0xC1,0xD0,0xD4,0xD8,0xE0,0xF1,0x0106,0x010E,0x0113,0x0114],6)
        else:
            #uru types
            self.data1=hsTArray([0x0C,0x55,0x56,0x57,0x67,0x6A,0x88,0xD5,0xD6,0xE2,0xEC,0xF6,0x0116,0x011E,0x0133,0x0134,0x0136],5)
            self.data2=hsTArray([0x08,0x2A,0x2B,0x2D,0x3D,0x40,0x62,0x6C,0x6D,0x6F,0x71,0x76,0x77,0x79,0x7A,0x7B,0x7C,0x8F,0x95,0x9B,0xA1,0xA2,0xA4,0xA9,0xAA,0xAB,0xAC,0xAE,0xAF,0xB1,0xB2,0xB9,0xBA,0xBB,0xBD,0xC0,0xC1,0xC4,0xCB,0xCF,0xD4,0xE5,0xE7,0xEE,0xF3,0xF5,0xFB,0xFC,0xFF,0x0107,0x0108,0x010C,0x010D,0x0119,0x0122,0x012C,0x012E,0x012F,0x0131],5)

    def changePageRaw(self,sid,did,stype,dtype):
        plSynchedObject.changePageRaw(self,sid,did,stype,dtype)
        self.draw.changePageRaw(sid,did,stype,dtype)
        self.simulation.changePageRaw(sid,did,stype,dtype)
        self.coordinate.changePageRaw(sid,did,stype,dtype)
        self.audio.changePageRaw(sid,did,stype,dtype)
        for i in self.data1.vector:
            i.changePageRaw(sid,did,stype,dtype)
        for i in self.data2.vector:
            i.changePageRaw(sid,did,stype,dtype)
        self.scene.changePageRaw(sid,did,stype,dtype)


    def read(self,stream):
        plSynchedObject.read(self,stream)
        self.draw.setVersion(self.getVersion())
        self.simulation.setVersion(self.getVersion())
        self.coordinate.setVersion(self.getVersion())
        self.audio.setVersion(self.getVersion())
        self.scene.setVersion(self.getVersion())
        self.draw.read(stream)
        self.simulation.read(stream)
        self.coordinate.read(stream)
        self.audio.read(stream)
        self.data1.ReadVector(stream)
        self.data2.ReadVector(stream)
        self.scene.read(stream)


    def write(self,stream):
        plSynchedObject.write(self,stream)
        self.draw.write(stream)
        self.simulation.write(stream)
        self.coordinate.write(stream)
        self.audio.write(stream)
        self.data1.WriteVector(stream)
        self.data2.WriteVector(stream)
        self.scene.write(stream)

    def _Find(page,name):
        return page.find(0x0001,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0001,name,1)
    FindCreate = staticmethod(_FindCreate)

    def addGeneric(self,plobj):
        self.data1.append(plobj.data.getRef())

    def addModifier(self,plobj):
        self.data2.append(plobj.data.getRef())

        
    def checkSynchFlags(self):
        """Last-minute pass over the SDL flags to make sure everything is sane for online environments
           Here's the rub:
               - If the flags have already been set, do nothing.
               - If there is a Dynamic HKPhysical, see PFM (looks like a Cyanic hack).
               - If there is a Responder attached, we exclude the Responder state
               - If there is a PythonFileMod attached, we exclude everything a PFM might touch:
                   - AGMaster
                   - Layer
                   - Responder
                   - Sound
                   - XRegion
               - Otherwise, exclude everything!
        """

        def excludePyStates(self):
            self.fSynchFlags |= plSynchedObject.Flags["kExcludePersistentState"]
            self.fSDLExcludeList.append("AGMaster")
            self.fSDLExcludeList.append("Layer")
            if "Responder" not in self.fSDLExcludeList:
                self.fSDLExcludeList.append("Responder")
            self.fSDLExcludeList.append("Sound")
            self.fSDLExcludeList.append("XRegion")

        if self.fSDLExcludeList or self.fSynchFlags & plSynchedObject.Flags["kExcludeAllPersistentState"]:
            # already set by user, bye-bye
            return

        if not self.simulation.isNull():
            sim = plSimulationInterface.Find(self.getRoot(), self.simulation.Key.name)
            phys = plHKPhysical.Find(self.getRoot(), sim.data.fPhysical.Key.name)
            if phys.data.gColType & plHKPhysical.Collision["cStorePosition"]:
                excludePyStates(self)
                # we can't get any better than this.
                return


        for mod in self.data2.vector:
            # PythonFileMod?
            if mod.Key.object_type == 0x00A2:
                excludePyStates(self)
                # we're not going to exclude any more than this, so let's just go away...
                return

            # Responder Modifier?
            elif mod.Key.object_type == 0x007C:
                self.fSynchFlags |= plSynchedObject.Flags["kExcludePersistentState"]
                self.fSDLExcludeList.append("Responder")
                # don't break out--we might hit the more exclusive PFM

        # If we haven't excluded anything at all (above), then exclude everything!
        self.fSynchFlags |= plSynchedObject.Flags["kExcludeAllPersistentState"]

    def export_object(self, obj, objscript):
        plSynchedObject.export_obj(self, obj, objscript)
        # check for animations
        laipo = None
        if obj.type == "LAMP":
            laipo = obj.data.animation_data
        if obj.animation_data or laipo:
            # this will specify animation names and markers
            animParams = FindInDict(objscript, "animations", [])
            agmm = plAGMasterMod.FindCreate(self.getRoot(), obj.name)
            if(len(animParams) == 0):
                # if there is no script for the animation, make a single animation with all frames
                anim = prp_AnimClasses.plATCAnim.FindCreate(self.getRoot(), obj.name)
                anim.data.export_obj(obj)
                agmm.data.fPrivateAnims.append(anim.data.getRef())
            for animation in animParams:
                # if there are animations defined in alcscript, export each separately
                if(FindInDict(animation, "type", None) == "ageglobalanim"):
                    anim = prp_AnimClasses.plAgeGlobalAnim.FindCreate(self.getRoot(), FindInDict(animation, "name", "unnamed"))
                else:
                    anim = prp_AnimClasses.plATCAnim.FindCreate(self.getRoot(), FindInDict(animation, "name", "unnamed"))
                anim.data.export_obj(obj, animation)
                agmm.data.fPrivateAnims.append(anim.data.getRef())
            agmod = plAGModifier.FindCreate(self.getRoot(), obj.name)
            agmod.data.fChannelName = obj.name
            self.data2.append(agmod.data.getRef())
            self.data2.append(agmm.data.getRef())

    def import_all(self,scene):
        #assert(self.draw.checktype(0x0016)) #or self.draw.checktype(0x00D2))
        root = self.getRoot()

        # Current BlenderObject types:
        #  'Armature', 'Camera', 'Curve', 'Lamp', 'Lattice', 'Mball', 'Mesh', 'Surf' or 'Empty'

        # Used by us:
        #  'Camera', 'Lamp', 'Mesh', 'Empty'

        # Determine object type

        CameraMod = False
        LightInfo = False
        SpawnMod = False

        for ref in  self.data1.vector:
            if ref.Key.object_type in [0x55,0x56,0x57,0xD5,0xD6]:
                LightInfo = True

        for mod in self.data2.vector:
            if mod.Key.object_type in [0x9B,]: #CameraModifier
                CameraMod = True


        for mod in self.data2.vector:
            if mod.Key.object_type in [0x3D,]: #SpawnModifier
                SpawnMod = True

        # Create Main Object for this item
        if not self.draw.isNull(): # if it has drawables, it's a mesh
            print("\n[Visual Object %s]"%(str(self.Key.name)))

            obj = bpy.data.objects.new('Mesh',str(self.Key.name))
            scene.objects.link(obj)
            mesh = Mesh.New(str(self.Key.name))
            obj.link(mesh)
            obj.layers=[1,]

            # Import possible draw interfaces
            plDrawInterface.Import(self,root,obj)
            plCoordinateInterface.Import(self,root,obj)
            plSimulationInterface.Import(self,root,obj)

            # Import Interfaces
            for i_ref in self.data1.vector:
                if i_ref.Key.object_type in []:
                    intf=root.findref(i_ref)
                    if not intf is None:
                        intf.data.import_obj(obj)

            # Import Modifiers
            for m_ref in self.data2.vector:
                if m_ref.Key.object_type in []:
                    mod=root.findref(m_ref)
                    if not mod is None:
                        mod.data.import_obj(obj)


        elif not self.simulation.isNull(): # if it has simulation, but no drawable, it's a collider mesh
            print("\n[Phyical Object %s]"%(str(self.Key.name)))
            obj = bpy.data.objects.new('Mesh',str(self.Key.name))
            scene.objects.link(obj)
            mesh = Mesh.New(str(self.Key.name))
            obj.link(mesh)
            obj.layers=[2,]

            plCoordinateInterface.Import(self,root,obj)
            plSimulationInterface.Import(self,root,obj)

            # Import Interfaces
            for i_ref in self.data1.vector:
                if i_ref.Key.object_type in []:
                    intf=root.findref(i_ref)
                    if not intf is None:
                        intf.data.import_obj(obj)

            # Import Modifiers
            for m_ref in self.data2.vector:
                if m_ref.Key.object_type in [0x00FC,]:
                    mod=root.findref(m_ref)
                    if not mod is None:
                        mod.data.import_obj(obj)


        elif LightInfo:
            print("\n[Lamp %s]"%(str(self.Key.name)))
            obj = bpy.data.objects.new('Lamp',str(self.Key.name))
            scene.objects.link(obj)
            obj.layers=[1,]

            plLightInfo.Import(self,root,obj)
            plCoordinateInterface.Import(self,root,obj)

        elif CameraMod:
            print("\n[Camera %s]"%(str(self.Key.name)))
            obj = bpy.data.objects.new('Camera',str(self.Key.name))
            scene.objects.link(obj)
            obj.layers=[4,]

            plCameraModifier1.Import(self,root,obj)
            plCoordinateInterface.Import(self,root,obj)

        else: # if all else fails, it's an Empty
            print("\n[Empty Object %s]"%(str(self.Key.name)))
            obj = bpy.data.objects.new('Empty',str(self.Key.name))
            scene.link(obj)
            plCoordinateInterface.Import(self,root,obj)
            obj.layers=[2,] # Empty's go to layer

            # Import Modifiers
            for m_ref in self.data2.vector:
                if m_ref.Key.object_type in [0x003D,]:
                    mod=root.findref(m_ref)
                    if not mod is None:
                        mod.data.import_obj(obj)

        # Add page_num property
        if self.getPageNum() != 0: # but only if it's not page 0
            obj.addProperty("page_num",str(self.getPageNum()))

    def deldefaultproperty(self,obj,propertyname,defaultvalue):
        try:
            p=obj[propertyname]
            if(p == defaultvalue):
                obj[p] = None
        except (AttributeError, RuntimeError, KeyError):
            print("Error removing %s property" % propertyname)

class plCoordinateInterface(plObjInterface):
    plCoordinateProperties = \
    { \
        "kDisable"                  : 0, \
        "kCanEverDelayTransform"    : 1, \
        "kDelayedTransformEval"     : 2, \
        "kNumProps"                 : 3  \
    }

    def __init__(self,parent,name="unnamed",type=0x0015):
        plObjInterface.__init__(self,parent,name,type)
        #format
        self.fLocalToParent=hsMatrix44()
        self.fParentToLocal=hsMatrix44()
        self.fLocalToWorld=hsMatrix44()
        self.fWorldToLocal=hsMatrix44()
        self.fChildren=hsTArray([0x01],self.getVersion(),True)

    def changePageRaw(self,sid,did,stype,dtype):
        plObjInterface.changePageRaw(self,sid,did,stype,dtype)
        self.fChildren.changePageRaw(sid,did,stype,dtype)


    def read(self,stream):
        plObjInterface.read(self,stream)
        assert(self.parentref.Key.object_type==0x01)
        self.fLocalToParent.read(stream)
        self.fParentToLocal.read(stream)
        self.fLocalToWorld.read(stream)
        self.fWorldToLocal.read(stream)
        self.fChildren.ReadVector(stream)


    def write(self,stream):

        if len(self.BitFlags) == 0:
            #initialize bit vector to contain one value: 0
            self.BitFlags.append(0)
        plObjInterface.write(self,stream)
        self.fLocalToParent.write(stream)
        self.fParentToLocal.write(stream)
        self.fLocalToWorld.write(stream)
        self.fWorldToLocal.write(stream)
        self.fChildren.WriteVector(stream)

    def _Find(page,name):
        return page.find(0x0015,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0015,name,1)
    FindCreate = staticmethod(_FindCreate)

    def export_obj(self,obj,objlist=[]):
        print(" [Coordinate Interface %s]"%(str(self.Key.name)))
        m=getMatrix(obj)
        #m.transpose()
        self.fLocalToWorld.set(m)
        self.fLocalToParent.set(m)
        m.invert()
        self.fWorldToLocal.set(m)
        self.fParentToLocal.set(m)

        parent = obj.parent
        if not parent is None:
            # only set the parent matrices when it's parent has a coordinate interface as well...
            if needsCoordinateInterface(parent):

                parentmtx= obj.matrix_basis
                #parentmtx.transpose()
                self.fLocalToParent.set(parentmtx)

                parentmtx.invert()
                self.fParentToLocal.set(parentmtx)

                alctype = getTextPropertyOrDefault(obj,"type","object")
                if isKickable(obj):
                    self.BitFlags.SetBit(plCoordinateInterface.plCoordinateProperties["kCanEverDelayTransform"])
                    self.BitFlags.SetBit(plCoordinateInterface.plCoordinateProperties["kDelayedTransformEval"])
                    self.fLocalToParent.identity()
                    self.fParentToLocal.identity()

        ## Need to add code to detect children....
        for obj2 in objlist:
            parent = obj2.parent
            if parent == obj:
                if needsCoordinateInterface(obj2):
                    # it is dynamic, add it, otherwise just ignore it
                    name2 = obj2.name
                    scnobj2 = plSceneObject.FindCreate(self.getRoot(),name2)
                    self.fChildren.append(scnobj2.data.getRef())

    def set_matrices(self,localtoworld,localtoparent=None):
        l2w = mathutils.Matrix(localtoworld)
        w2l = mathutils.Matrix(localtoworld)
        w2l.invert()

        if(localtoparent):
            l2p = mathutils.Matrix(localtoparent)
            p2l = mathutils.Matrix(localtoparent)
            p2l.invert()
        else:
            l2p = mathutils.Matrix(l2w)
            p2l = mathutils.Matrix(w2l)

        #l2p.transpose()
        #p2l.transpose()
        #l2w.transpose()
        #w2l.transpose()

        self.fLocalToParent.set(l2p)
        self.fParentToLocal.set(p2l)
        self.fLocalToWorld.set(l2w)
        self.fWorldToLocal.set(w2l)

    def import_obj(self,obj):
        print(" [Coordinate Interface %s]"%(str(self.Key.name)))
        l2w = self.fLocalToWorld.get()
        #l2w.transpose()
        obj.setMatrix(l2w)

    # Static Method used to separate things from the resmanagers export code
    def _Export(page,obj,scnobj,name=None,isdynamic=1,objlist=[]):
        if name is None:
            name = obj.name

        if isdynamic==1:
            #set the coordinate interface
            coori=page.prp.findref(scnobj.data.coordinate)
            if coori==None:
                coori=plCoordinateInterface.FindCreate(page.prp,name)
            coori.data.parentref=scnobj.data.getRef()
            coori.data.export_obj(obj,objlist)
            scnobj.data.coordinate=coori.data.getRef()

    Export = staticmethod(_Export)

    def _Import(scnobj,prp,obj):
        if not scnobj.coordinate.isNull() and scnobj.coordinate.Key.object_type == 0x0015:
            coordinate = prp.findref(scnobj.coordinate)
            coordinate.data.import_obj(obj)

    Import = staticmethod(_Import)


class plSimulationInterface(plObjInterface):
    plSimulationProperties = \
    { \
        "kDisable"              :  0, \
        "kWeightless"           :  1, \
        "kPinned"               :  2, \
        "kWarp"                 :  3, \
        "kUpright"              :  4, \
        "kPassive"              :  5, \
        "kRotationForces"       :  6, \
        "kCameraAvoidObject"    :  7, \
        "kPhysAnim"             :  8, \
        "kStartInactive"        :  9, \
        "kNoSynchronize"        : 10, \
        "kSuppressed"           : 11, \
        "kNoOwnershipChange"    : 12, \
        "kAvAnimPushable"       : 13, \
        "kNumProps"             : 14 \
    }

    def __init__(self,parent,name="unnamed",type=0x001C):
        plObjInterface.__init__(self,parent,name,type)
        #format
        self.fProps= hsBitVector()
        self.fPhysical=UruObjectRef(self.getVersion()) #plPhysical


    def changePageRaw(self,sid,did,stype,dtype):
        plObjInterface.changePageRaw(self,sid,did,stype,dtype)
        self.fPhysical.changePageRaw(sid,did,stype,dtype)


    def read(self,stream):
        plObjInterface.read(self,stream)
        self.fProps.read(stream)
        stream.Read32()

        self.fPhysical.read(stream)
        self.fPhysical.verify(self.Key)
        assert(self.fPhysical.Key.object_type==0x3F)


    def write(self,stream):
        plObjInterface.write(self,stream)
        self.fProps.write(stream)
        stream.Write32(0)
        self.fPhysical.write(stream)

    def _Find(page,name):
        return page.find(0x001C,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x001C,name,1)
    FindCreate = staticmethod(_FindCreate)

    def import_obj(self,obj,scnobj):
        print(" [SimulationInterface %s]"%(str(self.Key.name)))
        root=self.getRoot()
        phys=root.findref(self.fPhysical)
        phys.data.import_obj(obj,scnobj)

    def export_obj(self,obj):
       pass

    def _Import(scnobj,prp,obj):
        if not scnobj.simulation.isNull():
            simi = prp.findref(scnobj.simulation)
            simi.data.import_obj(obj,scnobj)

    Import = staticmethod(_Import)

    # Export function here is to alleviate complexity of the resmanager's export code

    def _Export(page,obj,scnobj,name,SceneNodeRef,isdynamic=0):
        # if there are bounds to export...
        alctype = getTextPropertyOrDefault(obj,"type","object")
        if obj.rigid_body or alctype == "region":
            #set the simulation interface

            # see if the simulation is already there....
            simiref=scnobj.data.simulation
            simi=page.prp.findref(simiref)
            if simi==None:
                # if not, make it
                simi=page.prp.find(0x1C,name,1)
            scnobj.data.simulation=simi.data.getRef()

            # Set the SimulationInterface's Parent ref
            simi.data.parentref=scnobj.data.getRef()

            # Find the Physical object
            physical=page.prp.findref(simi.data.fPhysical)
            if physical==None:
                # Or make it if it isn't there yet
                physical=page.prp.find(0x3F,name,1)
            simi.data.fPhysical=physical.data.getRef()

            # Set the physical's scene node ref

            physical.data.fScene=SceneNodeRef
            physical.data.fSceneObject=scnobj.data.getRef()
            physical.data.export_obj(obj,scnobj,isdynamic)                

            # Check if this is parented to an object without bounds
            parent = obj.parent
            if parent != None and (parent.rigid_body == None) and alctype == "collider" and physical.data.fSubWorld.isNull() and isdynamic:
                parentScnObj = plSceneObject.Find(page,parent.name)
                parentScnObj.data.simulation=simi.data.getRef()
                scnobj.data.simulation=UruObjectRef()
                simi.data.parentref=parentScnObj.data.getRef()
                physical.data.fSceneObject=parentScnObj.data.getRef()

    Export = staticmethod(_Export)


class plPhysical(plSynchedObject):
    plLOSDB = \
    { \
        "kLOSDBNone"            :    0x0, \
        "kLOSDBUIBlockers"      :    0x1, \
        "kLOSDBUIItems"         :    0x2, \
        "kLOSDBCameraBlockers"  :    0x4, \
        "kLOSDBCustom"          :    0x8, \
        "kLOSDBLocalAvatar"     :   0x10, \
        "kLOSDBShootableItems"  :   0x20, \
        "kLOSDBAvatarWalkable"  :   0x40, \
        "kLOSDBSwimRegion"      :   0x80, \
        "kLOSDBMax"             :  0x100, \
        "kLOSDBForce16"         : 0xFFFF \
    }

    Group = \
    { \
        "kGroupStatic"          : 0x0, \
        "kGroupAvatarBlocker"   : 0x1, \
        "kGroupDynamicBlocker"  : 0x2, \
        "kGroupAvatar"          : 0x3, \
        "kGroupDynamic"         : 0x4, \
        "kGroupDetector"        : 0x5, \
        "kGroupLOSOnly"         : 0x6, \
        "kGroupMax"             : 0x7, \
    }

    Bounds = \
    { \
        "kBoxBounds"            :  0x1, \
        "kSphereBounds"         :  0x2, \
        "kHullBounds"           :  0x3, \
        "kProxyBounds"          :  0x4, \
        "kExplicitBounds"       :  0x5, \
        "kNumBounds"            :  0x6, \
        "kBoundsMax"            : 0xFF \
    }



class HKBounds:
    def __init__(self,type=0x00):
        self.fType = type

    def read(self,stream):
        pass

    def write(self,stream):
        pass

    def SizeTransform_obj(self,obj):
        m=getMatrix(obj)
        self.SizeTransform_mtx(m)

    def SizeTransform_mtx(self,m): #Blender.MathUtils.Matrix input
        s = m.to_scale()
        # build up basic scale matrix transformation from this
        m = [[s.x, 0.0, 0.0, 0.0], \
             [0.0, s.y, 0.0, 0.0], \
             [0.0, 0.0, s.z, 0,0], \
             [0.0, 0.0, 0.0, 1.0]]

        matrix = hsMatrix44()
        matrix.set(m)
        self.Transform(matrix)

    def Transform(self,matrix): # virtual function
        pass


class SphereBounds(HKBounds):
    def __init__(self,type=plPhysical.Bounds["kSphereBounds"]):
        HKBounds.__init__(self,type)
        self.fOffset = Vertex()
        self.fRadius = 1.0
        pass

    def read(self,stream):
        HKBounds.read(self,stream)
        self.fOffset.read(stream)
        self.fRadius = stream.ReadFloat()

    def write(self,stream):
        HKBounds.write(self,stream)
        self.fOffset.write(stream)
        stream.WriteFloat(self.fRadius)
        pass

    def export_obj(self,obj):
        mesh = obj.data
        rem = 0
        # if the object has modifiers and no vertex groups (as in plDrawInterface.export_obj), apply the modifiers
        if len(obj.modifiers) > 0 and len(obj.vertex_groups) == 0:
            mesh = obj.to_mesh(bpy.context.scene, True, "RENDER", True)
            rem = 1
        print("  SphereBounds export")
        print("   Sphere based on %d vertices"%len(mesh.vertices))
        self.vertexs=[]
        self.faces=[]
        #DONE
        verts=[]
        #transform to world for static objects
        matrix=hsMatrix44()
        m=getMatrix(obj)
        #m.transpose()
        matrix.set(m)
        meshverts = mesh.vertices
        for vert in meshverts:
            v=[vert.co[0],vert.co[1],vert.co[2]]
            verts.append(v)
        max=0
        for i in verts:
            for e in verts:
                d=distance(i,e)
                if d>max:
                    max=d
        self.d=max/2
        
        if rem:
            bpy.data.meshes.remove(mesh)

    def export_raw(self,vertices,faces=None):
        max=0
        print("computing distance...")
        for i in vertices:
            for e in vertices:
                d=distance(i,e)
                if d>max:
                    max=d
        self.d=max/2



class HullBounds(HKBounds):

    def __init__(self,type=plPhysical.Bounds["kHullBounds"]):
        HKBounds.__init__(self,type)
        self.fVertices = []
        self.fFaces = []
        pass

    def read(self,stream):
        HKBounds.read(self,stream)

        self.fVertices = [] # reset vertex list
        count = stream.Read32()
        for i in range(count):
            x = stream.ReadFloat()
            y = stream.ReadFloat()
            z = stream.ReadFloat()
            vertex = [x,y,z]
            self.fVertices.append(vertex)

    def write(self,stream):
        HKBounds.write(self,stream)
        stream.Write32(len(self.fVertices))
        for vertex in self.fVertices:
            stream.WriteFloat(vertex[0])
            stream.WriteFloat(vertex[1])
            stream.WriteFloat(vertex[2])

    def export_obj(self,obj):
        print("  HullBounds export")
        mesh = obj.data
        rem = 0
        # if the object has modifiers and no vertex groups (as in plDrawInterface.export_obj), apply the modifiers
        if len(obj.modifiers) > 0 and len(obj.vertex_groups) == 0:
            mesh = obj.to_mesh(bpy.context.scene, True, "RENDER", True)
            rem = 1
        print("   Exporting %d vertices"%len(mesh.vertices))
        self.fVertices=[]

        meshverts = mesh.vertices
        for vert in meshverts:
            v=[vert.co[0],vert.co[1],vert.co[2]]
            self.fVertices.append(v)
        
        if rem:
            bpy.data.meshes.remove(mesh)

    def export_raw(self,vertices,faces=None):
        print("  HullBounds raw export")
        self.fVertices=[]
        for vert in vertices:
            v=[vert[0],vert[1],vert[2]]
            self.fVertices.append(v)


    def Transform(self,matrix): # needs hsMatrix44 input
        tverts=[]
        for vi in self.fVertices:
            v=Vertex(vi[0],vi[1],vi[2])
            v.transform(matrix)
            va=[v.x,v.y,v.z]
            tverts.append(va)

        self.fVertices=tverts

    def Transform_obj(self,obj):
        matrix=hsMatrix44()
        m=getMatrix(obj)
        #m.transpose()
        matrix.set(m)

        self.Transform(matrix)

class ProxyBounds(HullBounds):
    def __init__(self,type=plPhysical.Bounds["kProxyBounds"]):
        HullBounds.__init__(self,type)
        self.fFaces = []

    def read(self,stream):
        HullBounds.read(self,stream)

        self.fFaces = [] # reset face list
        count = stream.Read32()
        for i in range(count):
            a = stream.Read16()
            b = stream.Read16()
            c = stream.Read16()
            face = [a,b,c]
            self.fFaces.append(face)

    def write(self,stream):
        HullBounds.write(self,stream)

        stream.Write32(len(self.fFaces))
        for face in self.fFaces:
            for v_idx in face:
                stream.Write16(v_idx)

    def export_obj(self,obj):
        mesh = obj.to_mesh(bpy.context.scene, True, "RENDER", True)
        # triangulate the newly created mesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        del bm
        # if the object has modifiers and no vertex groups (as in plDrawInterface.export_obj), apply the modifiers
        if len(obj.modifiers) > 0 and len(obj.vertex_groups) != 0:
            raise RuntimeError("Your object has both modifiers and vertex groups, which are incompatible in PyPRP.")
        print("  ProxyBounds export")
        print("   Exporting %d vertices"%len(mesh.vertices))
        print("   Exporting %d faces"%len(mesh.polygons))

        self.fVertices=[]
        self.fFaces=[]
        meshvertices = mesh.vertices
        for vert in meshvertices:
            v=[vert.co[0],vert.co[1],vert.co[2]]
            self.fVertices.append(v)
        for face in mesh.polygons:
            n=len(face.vertices)
            if n<3:
                # wtf ?
                continue
            elif n==3:
                tface=[]
                for i in range(3):
                    tface.append(face.vertices[i])
                self.fFaces.append(tface)
            else:
                l1 = face.vertices[0]
                l2 = face.vertices[1]
                for i in range(n-2):
                    l3 = face.vertices[i+2]
                    self.fFaces.append((l1,l2,l3))
                    l2 = l3
                    l1 = l2
        bpy.data.meshes.remove(mesh)

    def export_raw(self,vertices,faces=[]):
        self.fVertices=[]
        self.fFaces=[]
        for vert in vertices:
            v=[vert[0],vert[1],vert[2]]
            self.fVertices.append(v)

        for face in faces:
            n=len(face)
            if n<3:
                continue
            elif n==3:
                tface=[]
                for i in range(3):
                    tface.append(face[i])
                self.fFaces.append(tface)
            elif n==4:
                tface=[]
                for i in range(3):
                    tface.append(face[i])
                self.fFaces.append(tface)
                tface=[]
                for i in (0,2,3):
                    tface.append(face[i])
                self.fFaces.append(tface)
            else:
                raise RuntimeError


class BoxBounds(ProxyBounds):
    def __init__(self,type=plPhysical.Bounds["kBoxBounds"]):
        ProxyBounds.__init__(self,type)

    def read(self,stream):
        ProxyBounds.read(self,stream)

    def write(self,stream):
        ProxyBounds.write(self,stream)

    def export_obj(self,obj):
        print("  BoxBounds export")
        # first get worldspace bounding box
        verts=obj.bound_box

        # get WorldToLocal matrix...
        matrix=hsMatrix44()
        m=getMatrix(obj)
        m.invert()
        #m.transpose()
        matrix.set(m)

        #transform coordinates to local
        tverts=[]
        for vi in verts:
            v=Vertex(vi[0],vi[1],vi[2])
            v.transform(matrix)
            va=[v.x,v.y,v.z]
            tverts.append(va)
        verts=tverts
        #
        try:
            c=alcConvexHull(verts)
            self.fVertices=c.vertexs
            self.fFaces=c.faces
        except:
            raise RuntimeException("Error Generating physical bounding box for object " + str(obj.name) + " please select another bounding method")

    def export_raw(self,vertices,faces=None):
        boundsmin=None # maximum vertex
        boundsmax=None # minimum vertex

        # store each vertex
        for vertex in vertices:
            # Determine if the vertex needs to be made
            if boundsmin is None or boundsmax is None:
                boundsmin = Vertex(vert.x,vert.y,vert.z)
                boundsmax = Vertex(vert.x,vert.y,vert.z)
            else:
                if vert.x < boundsmin.x:
                    boundsmin.x = vert.x
                if vert.y < boundsmin.y:
                    boundsmin.y = vert.y
                if vert.z < boundsmin.z:
                    boundsmin.z = vert.z
                if vert.x > boundsmax.x:
                    boundsmax.x = vert.x
                if vert.y > boundsmax.y:
                    boundsmax.y = vert.y
                if vert.z > boundsmax.z:
                    boundsmax.z = vert.z
        box = []
        box.append([boundsmin.x,boundsmin.y,boundsmin.z])
        box.append([boundsmin.x,boundsmin.y,boundsmax.z])
        box.append([boundsmin.x,boundsmax.y,boundsmin.z])
        box.append([boundsmin.x,boundsmax.y,boundsmax.z])
        box.append([boundsmax.x,boundsmin.y,boundsmin.z])
        box.append([boundsmax.x,boundsmin.y,boundsmax.z])
        box.append([boundsmax.x,boundsmax.y,boundsmin.z])
        box.append([boundsmax.x,boundsmax.y,boundsmax.z])

        c=alcConvexHull(box)
        self.vertexs=c.vertexs
        self.faces=c.faces



class ExplicitBounds(ProxyBounds): # essentially a basic copy of proxybounds
    def __init__(self,type=plPhysical.Bounds["kExplicitBounds"]):
        ProxyBounds.__init__(self,type)

    def read(self,stream):
        ProxyBounds.read(self,stream)

    def write(self,stream):
        ProxyBounds.write(self,stream)


class plHKPhysical(plPhysical):
    ## Conjectured constants following:

    # Constants in these Dictionaries start with 'c' instead of 'k', to inticate that
    # they are not known flags, but conjectured settings.

    # cNone             object is not used for avatar or other object collision (can be used for camera collision)
    # cStorePosition    object responds to avatar and location is remembered after exit
    # cResetPosition    object responds to avatar and location is reset after exit.
    # cDetector         is for detector regions and clickables, indicating game logic of some kinf

    # cIgnoreAvatars    do not respond to objects of same type

    # flags for gColType (was 'type')
    Collision = \
    { \
        "cNone"             : 0x00000000,\
        "cIgnoreAvatars"    : 0x00020000,\
        "cStorePosition"    : 0x01000000,\
        "cResetPosition"    : 0x02000000,\
        "cDetector"         : 0x04000000,\
    }


    # flags for gFlagsDetect (was 'flags1')

    # cDetectVolume         is used in swim detection regions
    # cDetectBoundaries     is used in generic detection regions that need to do things on entry and exit
    FlagsDetect = \
    { \
        "cDetectNone"       : 0x00000000,\
        "cDetectVolume"     : 0x00020000,\
        "cDetectBoundaries" : 0x08000000\
    }

    # flags for gFlagsRespond (was 'flags2')
    FlagsRespond = \
    { \
        "cRespNone"         : 0x00000000,\
        "cRespClickable"    : 0x00020000,\
        "cRespInitial"      : 0x02000000\
    }

    ## end conjectured flags

    # Used for exporting (blender hull types):

    HullTypes = {"BOX" : 0, "SPHERE" : 1, "CYLINDER" : 2, "CONE" : 3, "TRIANGLEMESH" : 4, "CONVEXHULL" : 5}

    def __init__(self,parent,name="unnamed",type=0x003F):
        plSynchedObject.__init__(self,parent,name,type)

        ## Havok structure?
        self.fPosition=Vertex() #position
        self.fOrientation=hsQuat() #orientation
        self.fMass=0.0   #mass (if 0, position is ignored as well as any related coordinate interface)
        self.fRC=0.5    #refriction coefficient
        self.fEL=0.0     #elasticity
        self.fBounds = ProxyBounds()

        ## Fairly unkown parts

        # Fields in this part are starting with "g" instead of the default "f".
        # this is to indicate that they are not known fields, but conjectured names and bitfields

        self.gShort1=0
        # 0x00 almost always
        # 0x02 TreeDummy02 (sphere02)

        self.gColType=plHKPhysical.Collision["cResetPosition"]

        self.gFlagsDetect=plHKPhysical.FlagsDetect["cDetectNone"]
        self.gFlagsRespond=plHKPhysical.FlagsRespond["cRespInitial"]

        self.gBool1=0
        self.gBool2=0


        ## Uru structure
        self.fSceneObject=UruObjectRef()
        self.fProps = hsBitVector()
        self.fScene=UruObjectRef()
        self.fLOSDB=plHKPhysical.plLOSDB["kLOSDBNone"]
        self.fSubWorld=UruObjectRef()
        self.fSndGroup=UruObjectRef()
        self.blendobj = None


    def changePageRaw(self,sid,did,stype,dtype):
        plSynchedObject.changePageRaw(self,sid,did,stype,dtype)
        self.sceneobject.changePageRaw(sid,did,stype,dtype)
        self.scene.changePageRaw(sid,did,stype,dtype)
        self.subworld.changePageRaw(sid,did,stype,dtype)
        self.sndgroup.changePageRaw(sid,did,stype,dtype)


    def read(self,stream):
        plSynchedObject.read(self,stream)

        self.fPosition.read(stream)
        self.fOrientation.read(stream)

        self.fMass = stream.ReadFloat()
        self.fRC = stream.ReadFloat()
        self.fEL = stream.ReadFloat()
        bounds = stream.Read32()

        self.gColType  = stream.Read32()

        self.gFlagsDetect = stream.Read32()
        self.gFlagsRespond = stream.Read32()
        self.gBool1 = stream.ReadBool()
        self.gBool2 = stream.ReadBool()

        if bounds == plPhysical.Bounds["kBoxBounds"]:
            self.fBounds = BoxBounds()
        elif bounds == plPhysical.Bounds["kSphereBounds"]:
            self.fBounds = SphereBounds()
        elif bounds == plPhysical.Bounds["kHullBounds"]:
            self.fBounds = HullBounds()
        elif bounds == plPhysical.Bounds["kProxyBounds"]:
            self.fBounds = ProxyBounds()
        else:
            self.fBounds = ExplicitBounds()

        self.fBounds.read(stream) # HKBounds Subclass specifically set above


        self.fSceneObject.read(stream)
        self.fProps.read(stream) # bitvector
        self.fScene.read(stream)
        self.fLOSDB = stream.Read32()
        self.fSubWorld.read(stream)
        self.fSndGroup.read(stream)


    def write(self,stream):
        plSynchedObject.write(self,stream)

        self.fPosition.write(stream)

        self.fOrientation.write(stream)

        stream.WriteFloat(self.fMass)
        stream.WriteFloat(self.fRC)
        stream.WriteFloat(self.fEL)

        stream.Write32(self.fBounds.fType) # retrieve from HKBounds Subclass

        stream.Write32(self.gColType)

        stream.Write32(self.gFlagsDetect)
        stream.Write32(self.gFlagsRespond)
        stream.WriteBool(self.gBool1)
        stream.WriteBool(self.gBool2)

        self.fBounds.write(stream) # HKBounds Subclass

        self.fSceneObject.write(stream)
        self.fProps.write(stream)
        self.fScene.write(stream)
        stream.Write32(self.fLOSDB)
        self.fSubWorld.write(stream)
        self.fSndGroup.write(stream)

    def _Find(page,name):
        return page.find(0x003F,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x003F,name,1)
    FindCreate = staticmethod(_FindCreate)

    def export_obj(self,obj,scnobj,isdynamic=0):
        print(" [Physical]")

        # determine the hull type
        if obj.rigid_body:
            if obj.rigid_body.collision_shape == "BOX":
                self.fBounds = BoxBounds()
            elif obj.rigid_body.collision_shape == "SPHERE":
                self.fBounds = SphereBounds()
            elif obj.rigid_body.collision_shape == "CYLINDER":
                self.fBounds = HullBounds()
            elif obj.rigid_body.collision_shape == "CONE":
                self.fBounds = HullBounds()
            elif obj.rigid_body.collision_shape == "MESH":
                self.fBounds = ProxyBounds()
            elif obj.rigid_body.collision_shape == "CONVEX_HULL":
                self.fBounds = HullBounds()
            else:
                self.fBounds = HullBounds()
        else:
            # this should never happen, because objects without bounds set
            # should not be given a physical prp object
            # Failsafe will put it to HullBounds
            self.fBounds = HullBounds()

        # export the hull
        self.fBounds.export_obj(obj)

        # retrieve alcscript for this object
        objscript = AlcScript.objects.Find(obj.name)

        #now lets add a SndGroup if we need to
        isSndGroup = FindInDict(objscript,'physical.sndgroup',0)
        if isSndGroup:
            plPhysicalSndGroup.Export(self.getRoot(), obj, scnobj, obj.name)
            sndGroupObj = plPhysicalSndGroup.Find(self.getRoot(),obj.name)
            self.fSndGroup = sndGroupObj.data.getRef()
        #subworld-refs are processed
        Subref = FindInDict(objscript,'physical.subworld',None)
        if Subref:
            refparser = ScriptRefParser(self.getRoot(),str(self.Key.name), 0x00E2, [0x00E2,]) #plHKSubworld
            SubWorldObj = refparser.MixedRef_FindCreate(Subref)
            subworld = SubWorldObj.data.getRef()
            self.fSubWorld = subworld
            print("Adding Subworld Ref [%s] to Physical" % Subref)

        ## First determine if we should encode this as a region
        ## This should happen here, rather than in the resource manager, to avoid
        ## code congestion
        try:
            prptype = objscript['type']
        except:
            prptype = "object"
        prptype = getTextPropertyOrDefault(obj,"type",prptype)

        if prptype == "region":
            print("  Setting Region-Specific settings....")


            regiontype = FindInDict(objscript,'region.type',"logic")
            regiontype = FindInDict(objscript,'regiontype',regiontype)
            regiontype = getTextPropertyOrDefault(obj,"regiontype",regiontype)

            if regiontype == "swimdetect":
                # set the Collision Type to Detector
                self.gColType = plHKPhysical.Collision["cNone"]

                # set mass to 0.0, for swimregions
                self.fMass = 0.0
                self.fRC = 0.0
                self.fEL = 0.0

                self.gFlagsDetect  = plHKPhysical.FlagsDetect["cDetectVolume"]
                self.gFlagsRespond = plHKPhysical.FlagsRespond["cRespNone"]

                #self.fLOSDB=plHKPhysical.plLOSDB["kLOSDBSwimRegion"] #8D in AhnShpere1

            elif regiontype == "swim":
                # set the Collision Type to None
                self.gColType = plHKPhysical.Collision["cNone"]

                # set mass to 0.0, for swimregions
                self.fMass = 0.0
                self.fRC = 0.0
                self.fEL = 0.0

                self.gFlagsDetect  = plHKPhysical.FlagsDetect["cDetectNone"]
                self.gFlagsRespond = plHKPhysical.FlagsRespond["cRespNone"]

                self.fLOSDB=plHKPhysical.plLOSDB["kLOSDBSwimRegion"]

            elif regiontype == "subworld":
                # set the Collision Type to Detector
                self.gColType = plHKPhysical.Collision["cDetector"]

                # set mass to 1.0, as is default for regions
                self.fMass = 1.0
                self.fRC = 0.0
                self.fEL = 0.0

                self.gFlagsDetect  = plHKPhysical.FlagsDetect["cDetectBoundaries"]
                self.gFlagsRespond = plHKPhysical.FlagsRespond["cRespNone"]

                self.fProps[plSimulationInterface.plSimulationProperties["kPinned"]] = 1

            else:
                # set the Collision Type to Detector
                self.gColType = plHKPhysical.Collision["cDetector"]

                # set mass to 1.0, as is default for regions
                self.fMass = 1.0
                self.fRC = 0.0
                self.fEL = 0.0

                self.gFlagsDetect  = plHKPhysical.FlagsDetect["cDetectBoundaries"]
                self.gFlagsRespond = plHKPhysical.FlagsRespond["cRespNone"]

                self.fProps[plSimulationInterface.plSimulationProperties["kPinned"]] = 1


        else:
            # if not a region

            # retrieve mass from Blender rigid body settings if available
            if needsCoordinateInterface(obj):
                if isKickable(obj):
                    self.fMass = obj.rigid_body.mass
                else:
                    self.fMass = 1.0
            else:
                self.fMass = 0.0

            if self.fMass <= 0.0:
                print("  No Mass")
            else:
                print("  Mass",obj.rigid_body.mass)

            # retrieve friction from logic property
            self.fRC = obj.rigid_body.friction

            if not isKickable(obj): # is collider, then we must make sure the avatar doesn't slide on the object's surface.
                self.fLOSDB |= plPhysical.plLOSDB["kLOSDBAvatarWalkable"]

            # retrieve elasticity from alcscript
            self.fEL = obj.rigid_body.restitution

            self.gFlagsDetect = plHKPhysical.FlagsDetect["cDetectNone"]
            self.gFlagsRespond = plHKPhysical.FlagsRespond["cRespInitial"]

            coltype = getTextPropertyOrDefault(obj,"physlogic",None)
            coltype = FindInDict(objscript,"physical.physlogic",coltype)

            if coltype is None or coltype not in ["none","storepos","resetpos","detect"]:
                # Default decoding neccesary
                # if the object has logicmodifiers script, consider it a detector
                if FindInDict(objscript,"logic.modifiers",None) != None:
                    print("  Autotetecting object to logical receiver - setting settings accordingly")

                    self.gFlagsRespond = plHKPhysical.FlagsRespond["cRespClickable"]
                    self.gColType = plHKPhysical.Collision["cDetector"]
                    self.fProps[plSimulationInterface.plSimulationProperties["kWarp"]] = 1
                    self.fLOSDB = plHKPhysical.plLOSDB["kLOSDBUIItems"]

                else:
                    # basic setting: if it is an explicit dynamic object and has mass, it's position get's stored
                    if isKickable(obj):
                        self.gColType = plHKPhysical.Collision["cStorePosition"]
                    else:
                        self.gColType = plHKPhysical.Collision["cResetPosition"]
            else:
                if coltype == "storepos":
                    self.gColType = plHKPhysical.Collision["cStorePosition"]
                    self.gFlagsRespond = 0x03800000
                elif coltype == "resetpos":
                    self.gColType = plHKPhysical.Collision["cResetPosition"]
                    self.gFlagsRespond = 0x03800000
                elif coltype == "detect":
                    self.gColType = plHKPhysical.Collision["cDetector"]

                    self.gFlagsRespond = plHKPhysical.FlagsRespond["cRespClickable"]
                    self.gColType = plHKPhysical.Collision["cDetector"]
                    self.fProps[plSimulationInterface.plSimulationProperties["kWarp"]] = 1
                    self.fLOSDB = plHKPhysical.plLOSDB["kLOSDBUIItems"]
                else: # if coltype == "none":
                    self.gColType = plHKPhysical.Collision["cNone"]

            clickHack = getTextPropertyOrDefault(obj,"clickable",False)
            clickHack = FindInDict(objscript,"physical.clickable",clickHack)
            if clickHack:
                self.fLOSDB = plHKPhysical.plLOSDB["kLOSDBUIItems"]

            if (str(FindInDict(objscript,"physical.pinned","false")).lower() == "true" or (not isKickable(obj) and needsCoordinateInterface(obj))):
                print("  Pinning object")
                self.fProps[plSimulationInterface.plSimulationProperties["kPinned"]] = 1

            # and make objects Camera Blockers By default - or let them through if physical.camerapassthrough is set to true
            if str(FindInDict(objscript,"physical.campassthrough","false")).lower() != "true":
                print("  Camera blocking enabled")
                self.fLOSDB |= plPhysical.plLOSDB["kLOSDBCameraBlockers"]
            else:
                print("  Camera blocking disabled")

        #set position and other attribs
        if (self.fMass == 0.0 and  isdynamic == 0):
            print("  Object is Static")
            #transform to world for static objects
            self.fBounds.Transform_obj(obj) # do this with transformation data from object
        else:
            print("  Object is Dynamic")
            # set position
            x,y,z = obj.location
            self.Position=Vertex(x,y,z)

            # set orientation
            m = getMatrix(obj)
            quat = m.to_quaternion()
            quat.normalize()
            self.fOrientation = hsQuat()
            self.fOrientation.setQuat(quat)

            # transform the object, size only.
            self.fBounds.SizeTransform_obj(obj)


    def export_raw(self,L2Wmatrix,vertex_list,face_list,col_type,isdynamic,mass=1.0):
        # set the objects properties to a default region

        if col_type == plPhysical.Bounds["kBoxBounds"]:
            self.fBounds = BoxBounds()
        elif col_type == plPhysical.Bounds["kSphereBounds"]:
            self.fBounds = SphereBounds()
        elif col_type == plPhysical.Bounds["kHullBounds"]:
            self.fBounds = HullBounds()
        elif col_type == plPhysical.Bounds["kProxyBounds"]:
            self.fBounds = ProxyBounds()
        elif col_type == plPhysical.Bounds["kExplicitBounds"]:
            self.fBounds = ExplicitBounds()
        else:
            self.fBounds = HullBounds()

        # export the hull
        self.fBounds.export_raw(vertex_list,face_list)


        # set default settings....
        self.fMass = mass
        self.fRC = 0.0
        self.fEL = 0.0

        # export_raw is ususally only used for regions
        self.gFlagsDetect = plHKPhysical.FlagsDetect["cDetectBoundaries"]
        self.gFlagsRespond = plHKPhysical.FlagsRespond["cRespNone"]

        self.gColType = plHKPhysical.Collision["cDetector"]

        self.fProps[plSimulationInterface.plSimulationProperties["kPinned"]] = 1
        self.fLOSDB = 0

        #set position and other attribs
        if (self.fMass == 0.0 and  isdynamic == 0):
            #transform to world for static objects
            self.fBounds.Transform_obj(obj) # do this with transformation data from object
        else:
            # set position
            x,y,z = L2Wmatrix.translation
            self.Position=Vertex(x,y,z)

            # set orientation
            quat = L2Wmatrix.to_quaternion()
            quat.normalize()
            self.fOrientation = hsQuat()
            self.fOrientation.setQuat(quat)

            # transform the object, size only.
            self.fBounds.SizeTransform_mtx(L2Wmatrix)

            
class plHKSubWorld(plSynchedObject):
    def __init__(self,parent=None,name="unnamed",type=0x00E2):
        plSynchedObject.__init__(self,parent,name,type)
        self.fSceneRef = UruObjectRef()
        self.fSubworldOffset = Vertex()
        self.fSomeOddData = 0xC200B23A ##Flags?
        
    def _Find(page,name):
        return page.find(0x00E2,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x00E2,name,1)
    FindCreate = staticmethod(_FindCreate)

    def export_obj(self, obj, scnobj):
        plSynchedObject.export_obj(self, obj, AlcScript.objects.Find(obj.name))
        # sceneObj = prp_ObjClasses.plSceneObject.FindCreate(self.getRoot(),obj.name)
        self.fSceneRef = scnobj.data.getRef()
        
    def _Export(page, obj, scnobj, name):
        HKSubWorld = plHKSubWorld.FindCreate(page, name)
        HKSubWorld.data.export_obj(obj, scnobj)
        # attach to sceneobject
        print("Appending subworld [%s] to sceneobject [%s]" % (HKSubWorld.data.Key.name, scnobj.data.Key.name))
        scnobj.data.data1.append(HKSubWorld.data.getRef())
    Export = staticmethod(_Export)
        
    def read(self, s):
        plSynchedObject.read(self, s)
        self.fSceneRef.read(s)
        self.fSubworldOffset.read(s)
        self.fSomeOddData = s.Read32()
        
    def write(self, s):
        plSynchedObject.write(self,s)
        self.fSceneRef.write(s)
        self.fSubworldOffset.write(s)
        s.Write32(self.fSomeOddData)

class plOccluder(plObjInterface):
    def __init__(self, parent=None, name="unnamed", type=0x0067): # [0x0067]
        plObjInterface.__init__(self, parent, name, type)
        self.fWorldBounds = hsBounds3Ext()
        self.fPriority = float()
        self.fPolyList = [] #plCullPoly()
        self.fSceneNode = UruObjectRef(self.getVersion())
        self.fVisRegions = [] #UruObjectRef()
        
    def _Find(page,name):
        return page.find(0x0067,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0067,name,1)
    FindCreate = staticmethod(_FindCreate)
    
    def _Export(page, obj, scnobj, name, sceneNode):
        Occluder = plOccluder.FindCreate(page, name)
        Occluder.data.export_obj(obj, scnobj)
        Occluder.data.fSceneNode = sceneNode
        Occluder.data.parentref = scnobj.data.getRef()
        # attach to sceneobject
        print("Appending occluder [%s] to sceneobject [%s]" % (Occluder.data.Key.name, scnobj.data.Key.name))
        scnobj.data.data1.append(Occluder.data.getRef())
    Export = staticmethod(_Export)
    
    def read(self, stream):
        plObjInterface.read(self, stream)
        self.fWorldBounds.read(stream)
        stream.WriteFloat(self.fPriority)
        for i in range(stream.ReadShort()):
            newPoly = plCullPoly()
            newPoly.read(stream)
            self.fPolyList.append(newPoly)
        self.fSceneNode.read(stream)
        for i in range(stream.ReadShort()):
            newVisRegion = UruObjectRef(self.getVersion())
            newVisRegion.read(stream)
            self.fVisRegions.append(newVisRegion)
    
    def write(self, stream):
        plObjInterface.write(self, stream)
        self.fWorldBounds.write(stream)
        stream.WriteFloat(self.fPriority)
        stream.WriteShort(len(self.fPolyList))
        for poly in self.fPolyList:
            poly.write(stream)
        # uhm, this is The scene node
        self.fSceneNode.write(stream)
        stream.WriteShort(len(self.fVisRegions))
        for visRegion in self.fVisRegions:
            visRegion.write(stream)
            
    def export_obj(self, obj, scnobj):
        tmatrix = getMatrix(obj)
        #tmatrix.transpose()
        meshvertices = obj.data.vertices
        for face in obj.data.polygons:
            if (len(face.vertices) > 0):
                # reversed uru space
                #Nor = tmatrix.rotationPart().invert().transpose() * mathutils.Vector(face.no) * -1
                rotationPart = tmatrix.copy()
                rotationPart.translation = Vector((0,0,0))
                Nor = rotationPart.inverted() * mathutils.Vector(face.normal) * -1
                Nor.normalize()
                # transform verts into world space (transposed for uru's reversed space)
                Verts = []
                for v in face.vertices:
                    vertVec = tmatrix * mathutils.Vector(meshvertices[v].co.x, meshvertices[v].co.y, meshvertices[v].co.z)
                    Verts.append(vertVec)
                    # this is mightiliy annoying, why can't these use subscripting? :P
                    if(self.fWorldBounds.min.x > vertVec.x):
                        self.fWorldBounds.min.x = vertVec.x
                    if(self.fWorldBounds.min.y > vertVec.y):
                        self.fWorldBounds.min.y = vertVec.y
                    if(self.fWorldBounds.min.z > vertVec.z):
                        self.fWorldBounds.min.z = vertVec.z
                    if(self.fWorldBounds.max.x < vertVec.x):
                        self.fWorldBounds.max.x = vertVec.x
                    if(self.fWorldBounds.max.y < vertVec.y):
                        self.fWorldBounds.max.y = vertVec.y
                    if(self.fWorldBounds.max.z < vertVec.z):
                        self.fWorldBounds.max.z = vertVec.z
                newPoly = plCullPoly()
                newPoly.export_face(Verts, Nor)
                self.fPolyList.append(newPoly)

class plPhysicalSndGroup(hsKeyedObject):
    fSoundGroup = \
    { \
        "kNone"   : 0x00, \
        "kMetal"  : 0x01, \
        "kGrass"  : 0x02, \
        "kWood"   : 0x03, \
        "kStone"  : 0x04 \
    }
    def __init__(self,parent,name="unnamed",type=0x0127):
        hsKeyedObject.__init__(self,parent,name,type)
        self.fGroup = 0x00 #unsigned
        self.fCurrSlideSnd = 0
        self.fImpactSounds = hsTArray([],self.getVersion())
        self.fSlideSounds = hsTArray([],self.getVersion())

    def _Find(page,name):
        return page.find(0x0127,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0127,name,1)
    FindCreate = staticmethod(_FindCreate)

    def _Export(page, obj, scnobj, name):
        PhysicalSndGroup = plPhysicalSndGroup.FindCreate(page, name)
        PhysicalSndGroup.data.export_obj(obj)
    Export = staticmethod(_Export)

    def export_obj(self, obj):
        objscript = AlcScript.objects.Find(obj.name)
        refparser = ScriptRefParser(self.getRoot(),str(self.Key.name), 0x0079, [0x0079,])

        ##Enter a land of insanity
        PhysImpactSnd = FindInDict(objscript,'physical.impact','')
        if PhysImpactSnd:
            self.fImpactSounds.append(UruObjectRef(self.getVersion()))
            self.fImpactSounds.append(UruObjectRef(self.getVersion()))
            self.fImpactSounds.append(UruObjectRef(self.getVersion()))
            self.fImpactSounds.append(UruObjectRef(self.getVersion()))
            PhysImpactSndObj = refparser.MixedRef_FindCreate(PhysImpactSnd)
            self.fImpactSounds.append(PhysImpactSndObj.data.getRef())

        PhysSlideSnd = FindInDict(objscript,'physical.slide','')
        if PhysSlideSnd:            
            self.fSlideSounds.append(UruObjectRef(self.getVersion()))
            self.fSlideSounds.append(UruObjectRef(self.getVersion()))
            self.fSlideSounds.append(UruObjectRef(self.getVersion()))
            self.fSlideSounds.append(UruObjectRef(self.getVersion()))
            PhysSlideSndObj = refparser.MixedRef_FindCreate(PhysSlideSnd)
            self.fSlideSounds.append(PhysSlideSndObj.data.getRef())
        ##Exit a land of insanity

        SndGroupFlags = FindInDict(objscript,'physical.sndgroup','')
        if SndGroupFlags == 'metal':
            self.fGroup |= self.fSoundGroup['kMetal']
        elif SndGroupFlags == 'grass':
            self.fGroup |= self.fSoundGroup['kGrass']
        elif SndGroupFlags == 'wood':
            self.fGroup |= self.fSoundGroup['kWood']
        elif SndGroupFlags == 'stone':
            self.fGroup |= self.fSoundGroup['kStone']
        else:
            self.fGroup = int(SndGroupFlags)
    def read(self, stream):
        hsKeyedObject.read(self, stream)
        stream.ReadInt(self.fGroup)
        self.fImpactSounds.read(stream)
        self.fSlideSounds.read(stream)

    def write(self, stream):
        hsKeyedObject.write(self, stream)
        stream.WriteInt(self.fGroup)
        self.fImpactSounds.write(stream)
        self.fSlideSounds.write(stream)

class plMaintainersMarkerModifier(plMultiModifier):

    Calibration = \
    { \
        "kBroken"       :  0, \
        "kRepaired"     :  1, \
        "kCalibrated"   :  2  \
    }

    ScriptCalibration = \
    { \
        "broken"        :  0, \
        "repaired"      :  1, \
        "calibrated"    :  2  \
    }

    def __init__(self,parent,name="unnamed",type=0x010D):
        plMultiModifier.__init__(self,parent,name,type)
        #format
        self.fCalibrated = 2

    def _Find(page,name):
        return page.find(0x010D,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x010D,name,1)
    FindCreate = staticmethod(_FindCreate)

    def read(self,stream):
        plMultiModifier.read(self,stream)
        self.fCalibrated = stream.Read32()

    def write(self,stream):
        plMultiModifier.write(self,stream)
        stream.Write32(self.fCalibrated)

    def export_obj(self,obj):
        objscript = AlcScript.objects.Find(obj.name)
        self.fCalibrated = int(plMaintainersMarkerModifier.ScriptCalibration[FindInDict(objscript, "calibration", 0)])
    
    def _Export(page,obj,scnobj,name):
        mmm = plMaintainersMarkerModifier.FindCreate(page, name)
        mmm.data.export_obj(obj)
        scnobj.data.addModifier(mmm)
    Export = staticmethod(_Export)
