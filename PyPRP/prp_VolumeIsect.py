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



import struct, mathutils
from prp_GeomClasses import *
from prp_Types import *
from prp_Stream import *
from prp_Functions import *

#
# Eventually, the following plVolumeIsect classes should be implemented here:
#
#[02F0] plVolumeIsect
#[02F1] plSphereIsect
#[02F2] plConeIsect
#[02F3] plCylinderIsect
#[02F4] plParallelIsect
#[02F5] plConvexIsect
#[02F6] plComplexIsect
#[02F7] plUnionIsect
#[02F8] plIntersectionIsect

class PrpVolumeIsect:
    def __init__(self,type=None,version=None):
        if type == None:
            self.vitype = 0xFFFF
        else:
            self.vitype = type
        if version == None:
            self.version = 5
        else:
            self.version = version
        self.data = None
        self.Key = plKey(self.version)
        if self.version == 5:
            #UruTypes
            if self.vitype == 0x02F0:
                self.data = plVolumeIsect(self)
            elif self.vitype == 0x02F5:
                self.data = plConvexIsect(self)
            else:
                print("Unsupported volume i-sect type %04X" % self.vitype)
        elif self.version == 6:
            #Myst 5 types
            raise RuntimeError("Unsupported Myst 5 volume i-sect type %04X" % self.type)


    def read(self,buf):
        self.data.read(buf)


    def write(self,buf):
        self.data.write(buf)


    def getVersion(self):
        return self.version


    def update(self,Key):
        self.Key.update(Key)


    def changePageRaw(self,sid,did,stype,dtype):
        self.Key.changePageRaw(sid,did,stype,dtype)
        if self.data != None:
            self.data.changePageRaw(sid,did,stype,dtype)


class plVolumeIsect:
    def __init__(self,parent=None):
        if parent == None:
            self.vitype = 0xFFFF
        else:
            self.vitype = parent.vitype
        self.parent = parent


    def read(self, buf):
        pass


    def write(self, buf):
        pass

    def export_object(self, obj):
        pass

    def changePageRaw(self,sid,did,stype,dtype):
        pass


class plConvexPlane:
    def __init__(self):
        self.Normal = mathutils.Vector((1,0,0))
        self.Point = mathutils.Vector((0,0,0))
        self.Distance = 0
        self.ScaledNormal = mathutils.Vector((1,0,0))
        self.ScaledDist = 0

    def read(self,buf):
        self.Normal = buf.ReadVector()
        self.Point = buf.ReadVector()
        self.Distance = buf.ReadFloat()
        self.ScaledNormal = buf.ReadVector()
        self.ScaledDist = buf.ReadFloat()

    def write(self,buf):
        buf.WriteVector(self.Normal)
        buf.WriteVector(self.Point)
        buf.WriteFloat(self.Distance)
        buf.WriteVector(self.ScaledNormal)
        buf.WriteFloat(self.ScaledDist)


    def addFaceToMesh(self,meshObj):
        # Invert the normal - Uru space is backwards
        self.Normal *= -1
        # Determine the axis that is closest to the normal, and choose
        # another axis
        xAxis = mathutils.Vector((1,0,0))
        yAxis = mathutils.Vector((0,1,0))
        zAxis = mathutils.Vector((0,0,1))
        vNormal = self.Normal
        xDot = abs(xAxis.dot(vNormal))
        yDot = abs(yAxis.dot(vNormal))
        zDot = abs(zAxis.dot(vNormal))
        vOther = None
        if (xDot > yDot):
            vOther = yAxis
        else:
            vOther = xAxis

        # Form one vector in the plane
        planeAxis1 = vNormal.cross(vOther).normalize()

        # Form a second vector in the plane
        planeAxis2 = planeAxis1.cross(vNormal).normalize()

        # Determine four points in the plane, and add them to
        # the face
        point = self.Point
        v0 = point-planeAxis1-planeAxis2
        v1 = point+planeAxis2-planeAxis1
        v2 = point-planeAxis2+planeAxis1
        v3 = point+planeAxis2+planeAxis1
        meshObj.verts.extend([v0,v1,v2,v3])
        startIndex = len(meshObj.verts)-4
        meshObj.faces.extend([startIndex,startIndex+1,startIndex+3,startIndex+2])


class plConvexIsect(plVolumeIsect):
    def __init__(self,parent=None):
        plVolumeIsect.__init__(self,parent)
        self.vPlanes = []

    def read(self,buf):
        plVolumeIsect.read(self,buf)
        count = buf.Read16()
        for i in range(count):
            plane = plConvexPlane()
            plane.read(buf)
            self.vPlanes.append(plane)

    def write(self,buf):
        plVolumeIsect.write(self,buf)
        buf.Write16(len(self.vPlanes))
        for plane in self.vPlanes:
            plane.write(buf)

    def createObject(self,name,page=0):
        sobj = None
        try:
            sobj = bpy.data.meshes[name]
        except:
            if sobj == None and len(self.vPlanes) > 0:
                print("Creating soft volume scene object %s using %d planes" % (name,len(self.vPlanes)))
                obj = bpy.data.meshes.new(name)
                for plane in self.vPlanes:
                    plane.addFaceToMesh(obj)

                scene = bpy.context.scene
                sobj = scene.objects.new(obj,name)
                sobj.select = False
                sobj.name = name
                sobj.layers = [6,]
                sobj.drawType = 2
                sobj.addProperty("type","svconvex")
                if (page != 0):
                    sobj.addProperty("page_num",str(page))


    def export_object(self, obj):
        tmatrix = getMatrix(obj)
        #tmatrix.transpose()
        for face in obj.data.polygons:
            if (len(face.vertices) > 0):
                # reversed uru space
                #Nor = tmatrix.rotationPart().invert().transpose() * mathutils.Vector(face.no) * -1
                Nor = tmatrix.to_3x3().inverted() * mathutils.Vector(face.normal) * -1
                Nor.normalize()
                # transform verts into world space (transposed for uru's reversed space)
                Pos = tmatrix * obj.data.vertices[face.vertices[0]].co # 1 vertex is enough to position the plane
                self.AddPlane(Nor, Pos)

    def AddPlane(self, Nor, Pos):
        for curPlane in self.vPlanes:
            if curPlane.Normal.dot(Nor) >= 0.9999:
                dist = Nor.dot(Pos)
                if dist > curPlane.Distance:
                    curPlane.Distance = dist
                    curPlane.Point = Pos
                return
        plane = plConvexPlane()
        plane.Normal = Nor
        plane.Point = Pos
        plane.Distance = Nor.dot(Pos)
        plane.ScaledNormal = plane.Normal
        plane.ScaledDist = plane.Distance
        self.vPlanes.append(plane)


class alcSoftVolumeParser:
    def __init__(self,prp):
        self.simpleSVs = []
        self.prp = prp

    def addSoftVolume(self, softVolume):
        self.simpleSVs.append(softVolume.data.getRef())

    def getSoftVolume(self, ref):
        if ref in self.simpleSVs:
            return self.simpleSVs[ref]
        return None

    def parseProperty(self, propString, rootName):
        # TODO: remove the whitespace
        newPropString = str("")
        for i in range(len(propString)):
            theChar = propString[i]
            if theChar != ' ':
                newPropString += theChar
        print("Parsing the softvolume property %s" % propString)
        # invoke the recursive method
        self.index = 0
        return self._parseProperty(newPropString, rootName)

    def isStringProperty(self, propString):
        firstChar = propString[0]
        if firstChar == '(':
            raise RuntimeError("Unexpected '(' found in softvolume property '%s'" % propString)
        #secondChar = propString[1]
        if ((firstChar == 'U') or (firstChar == 'I') or (firstChar == '!')):# and (secondChar == '('):
            return True
        return False

    def _parseProperty(self, propString, rootName):
        isSimple = False
        if len(propString) < 3:
            isSimple = True
        else:
            firstChar = propString[0]
            if firstChar == '(':
                raise RuntimeError("Unexpected '(' found in softvolume property '%s' of %s - please correct it" %(propString,rootName))
            secondChar = propString[1]
            if secondChar != '(':
                isSimple = True
            else:
                isUnion = False
                isIntersection = False
                isInverse = False
                if firstChar == 'U':
                    isUnion = True
                elif firstChar == 'I':
                    isIntersection = True
                elif firstChar == '!':
                    isInverse = True
                else:
                    raise RuntimeError("Illegal character '%s' found before the ( in softvolume property of %s; must be either 'U', 'I' or '!'" %(firstChar,rootName))
                svRefs = []
                newIndex = 2
                reachedParen = False
                while newIndex < len(propString):
                    newPropString = propString[newIndex:]
                    self.index = 0
                    svRefs.append(self._parseProperty(newPropString,rootName))
                    newIndex += self.index + 1
                    if self.index < len(newPropString):
                        if newPropString[self.index] == ')':
                            reachedParen = True
                            break
                self.index = newIndex
                if not reachedParen:
                    raise RuntimeError("Error: missing a ')' in softvolume property '%s' of %s" %(propString,rootName))
                complexSV = None
                if isUnion == True:
                    #tempname = alcUniqueName(rootName + "Union",0,0,'union')
                    #complexSV = self.prp.find(0x008A,tempname,1)
                    complexSV = self.prp.find(0x008A,rootName,1)
                elif isIntersection == True:
                    #tempname = alcUniqueName(rootName + "Isect",0,0,'isect')
                    #complexSV = self.prp.find(0x008B,tempname,1)
                    complexSV = self.prp.find(0x008B,rootName,1)
                elif isInverse == True:
                    #tempname = alcUniqueName(rootName + "Invert",0,0,'invert')
                    #complexSV = self.prp.find(0x008C,tempname,1)
                    complexSV = self.prp.find(0x008C,rootName,1)
                if complexSV == None:
                    raise RuntimeError("Error: could not create a complex soft volume for %s" % rootName)
                for svRef in svRefs:
                    complexSV.data.vSV7C.append(svRef)
                return complexSV.data.getRef()
        if isSimple:
            simpleSVName = str("")
            for self.index in range(len(propString)):
                theChar = propString[self.index]
                if not theChar in [',',')']:
                    simpleSVName += theChar
                else:
                    break;
            simpleSV = None
            for sv in self.simpleSVs:
                if (str(sv.Key.name) == simpleSVName):
                    print("Found softvolume %s" % sv.Key.name)
                    simpleSV = sv
                    break
            if simpleSV == None:
                raise RuntimeError("Could not locate soft volume '%s' - please correct the softvolume property in %s" %(simpleSVName,rootName))
            return simpleSV
        return None
