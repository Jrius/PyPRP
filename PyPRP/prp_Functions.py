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

# Help library

from bpy import *
import bpy
import mathutils
import random, hashlib, math, binascii, struct

def isKickable(obj):
    if not needsCoordinateInterface(obj):
        return False
    if obj.rigid_body and obj.rigid_body.enabled and obj.rigid_body.type == "ACTIVE":
        return True
    return False

def needsCoordinateInterface(obj):
    if obj.type != "MESH":
        return True
    if obj.show_axis:
        return True
    if obj.animation_data != None:
        return True
    if obj.rigid_body != None and obj.rigid_body.enabled and obj.rigid_body.type == "ACTIVE":
        return True
    return False

def distance(p1,p2):
    a1=p1[0]
    a2=p2[0]
    b1=p1[1]
    b2=p2[1]
    c1=p1[2]
    c2=p2[2]
    return math.sqrt(pow(a1-a2,2) + pow(b1-b2,2) + pow(c1-c2,2))

def centerNew():
    objs = Object.Get()
    for o in objs: #Make all objects use 'Center New'
        if o.type == 'Mesh':
            me = o.getData()
            mat = o.matrix_basis
            me.transform(mat)
            me.update()
            mat = mathutils.Matrix([1.0,0.0,0.0,0.0],[0.0,1.0,0.0,0.0],[0.0,0.0,1.0,0.0],[0.0,0.0,0.0,1.0])
            o.setMatrix(mat)
            bb = o.getBoundBox()
            cu = [bb[0][n]+(bb[-2][n]-bb[0][n])/2.0 for n in [0,1,2]]
            mat = o.matrix_basis
            mat = mathutils.Matrix(mat[0][:],mat[1][:],mat[2][:],[-cu[0],-cu[1],-cu[2],1.0])
            me.transform(mat)
            me.update()
            mat = mathutils.Matrix(mat[0][:],mat[1][:],mat[2][:],[cu[0],cu[1],cu[2],1.0])
            o.setMatrix(mat)

def cleanMeshes():
    objs = Object.Get()
    for o in objs:
        if o.type == 'Mesh': #Applies all scales and rotations (imitates CTRL+A behaviour)
            me = o.getData()
            mat = Mathutils.Matrix(o.matrix[0][:],o.matrix[1][:],o.matrix[2][:],[.0,.0,.0,1.0])
            me.transform(mat)
            me.update()
            o.setEuler(0.0,0.0,0.0)
            o.setSize(1.0,1.0,1.0)


def addProp(object,name,val):
    object[name] = val


def getProp(object,property):
    try:
        object[property]
    except (AttributeError, RuntimeError, KeyError):
        return None


def getMatrix(object):
    try:
        m=mathutils.Matrix(object.matrix_basis)
    except TypeError:
        i=object.matrix_basis
        m=mathutils.Matrix([i[0][0],i[0][1],i[0][2],i[0][3]],
                                   [i[1][0],i[1][1],i[1][2],i[1][3]],
                                   [i[2][0],i[2][1],i[2][2],i[2][3]],
                                   [i[3][0],i[3][1],i[3][2],i[3][3]])
    return m


def alcHex2Ascii(what,size=4):
    if size==4:
        type=">I"
    elif size==2:
        type=">H"
    else:
        type=">B"
    a=struct.pack(type,what)
    return(binascii.hexlify(a).upper())


def alcAscii2Hex(name,size=4):
    if size==4:
        type=">I"
    elif size==2:
        type=">H"
    else:
        type=">B"

    while len(name)<size*2:
        name = "0" + name
    b=binascii.unhexlify(str(name))
    r, = struct.unpack(type,b)
    return(r)


def alcUniqueName(name,seed1=0,seed2=0,key="x"):
    if seed1==0 or seed2==0:
        w = str(name) + "%i" %int(random.random()*10000)
        rid=hashlib.md5(w.encode('ascii')).hexdigest().upper()
        mname = str(name)[:10] + "%s%s" %(key[:1],rid[:6])
        return mname
    else:
        rid=((int(random.random()*10000)*100+setidx)*10 + i)
        mname = name[:10] + "%s%06X" %(key[:1],rid)
        return mname

def alcCreateLinkInPoint(name="LinkInPointDefault",where=None,page=0):
    obj = bpy.data.objects.new(name, None)
    scene = bpy.context.scene
    scene.objects.link(obj)
    #obj["name"] = name
    obj["type"] = "swpoint"
    if page!=0:
        obj["page_num"] = page
    if where==None:
        obj.location = scene.cursor_location
    else:
        matrix=where.get()
        obj.setMatrix(matrix)
    obj.show_name = True
    return obj

def alcCreateRegion(name="Region",where=None,page=0):
    rgnsize = 4
    rgnoffset = 0 - (rgnsize/2)
    obj = alcCreateBox(name,rgnsize,rgnoffset,rgnoffset,rgnoffset)
    obj["type"] = "region"

    if page!=0:
        obj["page_num"] = page
    if where==None:
        obj.location = bpy.context.scene.cursor_location
    else:
        matrix=where.get()
        obj.setMatrix(matrix)
    obj.draw_type = "WIRE"
    return obj

def alcCreatePanicLnkRegion(name="PanicLnkRgn",where=None,page=0):
    obj = alcCreateRegion(name,where,page)
    obj["regiontype"] = "panic"
    return obj

def alcCreateFootstepRegion(name="FootStepRgn",where=None,page=0):
    obj = alcCreateRegion(name,where,page)
    obj["regiontype"] = "footstep"
    obj["surface"] = "stone"
    return obj

def alcCreateMesh(name,vertices,faces):
    obj = bpy.data.meshes.new(name)
    obj.from_pydata(vertices, [], faces)
    obj.validate()
    obj.update()
    scene = bpy.context.scene
    sobj=bpy.data.objects.new(name, obj)
    scene.objects.link(sobj)
    sobj.name = name
    return sobj


def alcCreateBox(name,size,x=0,y=0,z=0,bReverse=False):
    obj = bpy.data.meshes.new(name)
    coords = [ [x,y,z], [size+x,y,z], [x,size+y,z], [x,y,size+z], [size+x,size+y,size+z], [size+x,size+y,z], [size+x,y,size+z], [x,size+y,size+z] ]
    if bReverse:
        faces = [ [0,1,5,2], [5,4,7,2], [1,6,4,5], [0,3,6,1], [3,7,4,6], [0,2,7,3] ]
    else:
        faces = [ [0,2,5,1], [5,2,7,4], [1,5,4,6], [0,1,6,3], [3,6,4,7], [0,3,7,2] ]
    obj.from_pydata(coords, [], faces)
    obj.validate()
    obj.update()
    scene = bpy.context.scene
    sobj = bpy.data.objects.new(name, obj)
    scene.objects.link(sobj)
    return sobj


def alcCreatePlane(name,size,x=0,y=0,z=0):
    obj = bpy.data.meshes.new(name)
    coords = [ [x,y,z], [size+x,y,z], [x,size+y,z], [size+x,size+y,z] ]
    face = [0,1,3,2]
    obj.from_pydata(coords, [], [face])
    obj.validate()
    obj.update()
    scene = bpy.context.scene
    sobj = bpy.data.objects.new(name, obj)
    sobj.draw_type = "WIRE"
    scene.objects.link(sobj)
    return sobj


def alcFindBlenderText(name):
    try:
        out=bpy.data.texts[name]
    except KeyError:
        if name=="AlcScript" or name=="Book": raise RuntimeError("You must create the age informations before being able to export ! (Add->PyPRP Book)")
        out=bpy.data.texts.new(name)
    return out


def alcFindBlenderTextNofail(name):
    try:
        out=bpy.data.texts[name]
    except KeyError:
        out=bpy.data.texts.new(name)
    return out


def deldefaultproperty(obj,propertyname,defaultvalue):
    try:
        p=obj[propertyname]
        if(p == defaultvalue):
            del obj[p]
    except (AttributeError, RuntimeError, KeyError):
        print("Error removing %s property" % propertyname)

def getFloatPropertyOrDefault(obj,propertyname,defaultvalue):
    try:
        var=float(obj[propertyname])
    except (AttributeError, RuntimeError, KeyError):
        var=defaultvalue
    return var

def getHexPropertyOrDefault(obj,propertyname,bytesize,defaultvalue):
    try:
        p=obj[propertyname]
        if(type(p) == type("STRING")):
            var=alcAscii2Hex(str(p.getData()),bytesize)
        else:
            var=defaultvalue
    except (AttributeError, RuntimeError, KeyError):
        var=defaultvalue
    return var

def getTextPropertyOrDefault(obj,propertyname,defaultvalue):
    try:
        p=obj[propertyname]
        var=str(p)
    except (AttributeError, RuntimeError, KeyError):
        var=defaultvalue
    return var

def getStrIntPropertyOrDefault(obj,propertyname,defaultvalue):
    try:
        p=obj[propertyname]
        var=int(p)
    except (AttributeError, RuntimeError, KeyError, ValueError):
        var=defaultvalue
    return var

def getIntPropertyOrDefault(obj,propertyname,defaultvalue):
    try:
        p=obj[propertyname]
        var=int(p)
    except (AttributeError, RuntimeError, KeyError, ValueError):
        var=defaultvalue
    return var

def getBoolPropertyOrDefault(obj,propertyname,defaultvalue):
    try:
        p=obj[propertyname]
        var=bool(p)
    except (AttributeError, RuntimeError, KeyError):
        var=bool(defaultvalue)
    return var

def alcCreateSoftVolumePlane():
    tempname = alcUniqueName("SoftVol",0,0,'plane')
    rgnsize = 4
    rgnoffset = 0 - (rgnsize/2)
    obj = alcCreatePlane(tempname,rgnsize,rgnoffset,rgnoffset,0)
    scene = bpy.context.scene
    obj["type"] = "svconvex"
    obj.location = scene.cursor_location
    return obj


def alcCreateSoftVolumeCube():
    tempname = alcUniqueName("SoftVol",0,0,'cube')
    rgnsize = 4
    rgnoffset = 0 - (rgnsize/2)
    obj = alcCreateBox(tempname,rgnsize,rgnoffset,rgnoffset,rgnoffset,True)
    obj["type"]="svconvex"
    obj.location = bpy.context.scene.cursor_location
    obj.draw_type = "WIRE"
    return obj


# ###################################################
# #                                                 #
# #       Various Blender Dialog Functions:         #
# #                                                 #
# ###################################################

class AgreementDialog:
    def __init__(self):
        self.Result = 0

    def Show(self):
        self.Result = 0 # initialize value to 0 if no button pressed
        Blender.Draw.UIBlock(self.AgreeDraw)
        return self.Result

    def AgreeDraw(self):
            xmouse, ymouse = Blender.Window.GetMouseCoords()

            ybase = ymouse + 5
            xbase = xmouse + 0

            # The text to display:
            Blender.Draw.Label("IMPORTANT: (Importing Cyan age)"                        , xbase - 152, ybase - 0 , 308, 15)
            Blender.Draw.Label("By continuing this import, you agree not to use any "   , xbase - 152, ybase - 15, 308, 15)
            Blender.Draw.Label("of Cyan's IP (including textures) in your own projects" , xbase - 152, ybase - 30, 308, 15)
            Blender.Draw.Label("without their written permission!"                      , xbase - 152, ybase - 45, 308, 15)
            Blender.Draw.Label("Do you accept this?"                                    , xbase - 152, ybase - 65, 308, 15)
            # The buttons to draw
            Blender.Draw.PushButton("I Accept"                                      , 1 , xbase - 57 , ybase - 85, 55 , 20, "", self.AgreeDlgEvent)
            Blender.Draw.PushButton("I Decline"                                     , 2 , xbase + 2  , ybase - 85, 55 , 20, "", self.AgreeDlgEvent)

    def AgreeDlgEvent(self,event,val):
        if event == 1:
            self.Result = 1
        elif event == 2:
            self.Result = -1

    def ShowDeclineInfo(self):
        block = []
        block.append("Because you did not accept, we cannot continue import.")
        block.append("Aborting import now!")

        Blender.Draw.PupBlock("Import error",block)


class InfoDialog:
    def __init__(self,caption,text):
        self.text = text
        self.caption = caption
        #self.maxlen = 48
        self.labellen = 300
        self.maxlen = int((3 * self.labellen) / 20 )

    def Show(self):
        Blender.Draw.UIBlock(self.Draw)

    def Draw(self):

            xmouse, ymouse = Blender.Window.GetMouseCoords()

            ybase = ymouse + 0
            xbase = xmouse + 0

            mylines = self.text.splitlines()
            lines = []
            for line in mylines:
                while len(line) > 0:
                    lines.append(line[0:self.maxlen])
                    linelen = len(line)
                    line = line[self.maxlen:linelen]

            ypos = 0
            ypos = len(lines) * 15 + 10

            # prepare a separator line
            separator = ""
            for i in range(self.maxlen):
                separator += "_"

            # Draw the caption first:
            Blender.Draw.Label(separator , xbase - (self.labellen/2), ybase + ypos + 18, self.labellen, 15)
            Blender.Draw.Label(self.caption + ":"   , xbase - (self.labellen/2), ybase + ypos + 20, self.labellen, 15)

            for line in lines:
                Blender.Draw.Label(line, xbase - (self.labellen/2), ybase + ypos, self.labellen, 15)
                ypos -= 15

            Blender.Draw.PushButton("Ok", 1 , xbase - 25 , ybase, 50 , 20, "", self.ButtonEvent)

    def ButtonEvent(self,event,value):
        pass

def TestBlenderVersion(minimum):
    return # assuming user isn't stupid...
    
    # Failsafe to allow both integer and float version numbers (e.g. 245 as well as 2.45)
    if type(minimum) == float:
        minimum = int(minimum * 100)

    version = Blender.Get('version')

    if version < minimum:
        InfoDialog("PyPRP error","PyPRP needs Blender version %0.2f or higher.\nYou are currently running version %0.2f.\nPlease upgrade!" % (float(minimum)/100.0,float(version/100.0)) ).Show()
        raise RuntimeError("Pyprp requires blender %0.2f or higher" % (float(minimum)/100.0))

