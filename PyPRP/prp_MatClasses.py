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
import hashlib, random, binascii, io, copy, PIL.Image, math, struct, io, os, os.path, pickle
import prp_Config
import prp_AnimClasses
from prp_Config import *
from prp_Types import *
from prp_DXTConv import *
from prp_HexDump import *
from prp_GeomClasses import *
from prp_Functions import *
from prp_ConvexHull import *
from prp_VolumeIsect import *
from prp_AlcScript import *
from prp_AnimClasses import *
import prp_ObjClasses

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

################# Rework of the main Layer and Material Classes

class hsGMatState:
    StateIdx = \
    { \
        "kBlend" : 0x0, \
        "kClamp" : 0x1, \
        "kShade" : 0x2, \
        "kZ"     : 0x3, \
        "kMisc"  : 0x4  \
    }

    hsGMatBlendFlags =  \
    { \
        "kBlendTest"                :        0x1, \
        "kBlendAlpha"               :        0x2, \
        "kBlendMult"                :        0x4, \
        "kBlendAdd"                 :        0x8, \
        "kBlendAddColorTimesAlpha"  :       0x10, \
        "kBlendAntiAlias"           :       0x20, \
        "kBlendDetail"              :       0x40, \
        "kBlendNoColor"             :       0x80, \
        "kBlendMADD"                :      0x100, \
        "kBlendDot3"                :      0x200, \
        "kBlendAddSigned"           :      0x400, \
        "kBlendAddSigned2X"         :      0x800, \
        "kBlendMask"                :      0xF5E, \
        "kBlendInvertAlpha"         :     0x1000, \
        "kBlendInvertColor"         :     0x2000, \
        "kBlendAlphaMult"           :     0x4000, \
        "kBlendAlphaAdd"            :     0x8000, \
        "kBlendNoVtxAlpha"          :    0x10000, \
        "kBlendNoTexColor"          :    0x20000, \
        "kBlendNoTexAlpha"          :    0x40000, \
        "kBlendInvertVtxAlpha"      :    0x80000, \
        "kBlendAlphaAlways"         :   0x100000, \
        "kBlendInvertFinalColor"    :   0x200000, \
        "kBlendInvertFinalAlpha"    :   0x400000, \
        "kBlendEnvBumpNext"         :   0x800000, \
        "kBlendSubtract"            :  0x1000000, \
        "kBlendRevSubtract"         :  0x2000000, \
        "kBlendAlphaTestHigh"       :  0x4000000  \
    }

    hsGMatClampFlags = \
    { \
        "kClampTextureU"    : 0x1, \
        "kClampTextureV"    : 0x2, \
        "kClampTexture"     : 0x3  \
    }

    hsGMatShadeFlags = \
    { \
        "kShadeSoftShadow"          :        0x1, \
        "kShadeNoProjectors"        :        0x2, \
        "kShadeEnvironMap"          :        0x4, \
        "kShadeVertexShade"         :       0x20, \
        "kShadeNoShade"             :       0x40, \
        "kShadeBlack"               :       0x40, \
        "kShadeSpecular"            :       0x80, \
        "kShadeNoFog"               :      0x100, \
        "kShadeWhite"               :      0x200, \
        "kShadeSpecularAlpha"       :      0x400, \
        "kShadeSpecularColor"       :      0x800, \
        "kShadeSpecularHighlight"   :     0x1000, \
        "kShadeVertColShade"        :     0x2000, \
        "kShadeInherit"             :     0x4000, \
        "kShadeIgnoreVtxIllum"      :     0x8000, \
        "kShadeEmissive"            :    0x10000, \
        "kShadeReallyNoFog"         :    0x20000  \
    }

    hsGMatZFlags = \
    { \
        "kZIncLayer"    :  0x1, \
        "kZClearZ"      :  0x4, \
        "kZNoZRead"     :  0x8, \
        "kZNoZWrite"    : 0x10, \
        "kZMask"        : 0x1C, \
        "kZLODBias"     : 0x20 \
    }

    hsGMatMiscFlags = \
    { \
        "kMiscWireFrame"            :        0x1, \
        "kMiscDrawMeshOutlines"     :        0x2, \
        "kMiscTwoSided"             :        0x4, \
        "kMiscDrawAsSplats"         :        0x8, \
        "kMiscAdjustPlane"          :       0x10, \
        "kMiscAdjustCylinder"       :       0x20, \
        "kMiscAdjustSphere"         :       0x40, \
        "kMiscAdjust"               :       0x70, \
        "kMiscTroubledLoner"        :       0x80, \
        "kMiscBindSkip"             :      0x100, \
        "kMiscBindMask"             :      0x200, \
        "kMiscBindNext"             :      0x400, \
        "kMiscLightMap"             :      0x800, \
        "kMiscUseReflectionXform"   :     0x1000, \
        "kMiscPerspProjection"      :     0x2000, \
        "kMiscOrthoProjection"      :     0x4000, \
        "kMiscProjection"           :     0x6000, \
        "kMiscRestartPassHere"      :     0x8000, \
        "kMiscBumpLayer"            :    0x10000, \
        "kMiscBumpDu"               :    0x20000, \
        "kMiscBumpDv"               :    0x40000, \
        "kMiscBumpDw"               :    0x80000, \
        "kMiscBumpChans"            :    0xE0000, \
        "kMiscNoShadowAlpha"        :   0x100000, \
        "kMiscUseRefractionXform"   :   0x200000, \
        "kMiscCam2Screen"           :   0x400000, \
        "kAllMiscFlags"             :       0xFF  \
    }

    def __init__(self):
        self.fBlendFlags = 0x00
        self.fClampFlags = 0x00
        self.fShadeFlags = 0x00
        self.fZFlags     = 0x00
        self.fMiscFlags  = 0x00

    def read(self,buf):
        self.fBlendFlags = buf.Read32()
        self.fClampFlags = buf.Read32()
        self.fShadeFlags = buf.Read32()
        self.fZFlags     = buf.Read32()
        self.fMiscFlags  = buf.Read32()
        pass

    def write(self,buf):
        buf.Write32(self.fBlendFlags)
        buf.Write32(self.fClampFlags)
        buf.Write32(self.fShadeFlags)
        buf.Write32(self.fZFlags)
        buf.Write32(self.fMiscFlags)
        pass

class hsGMaterial(plSynchedObject):         # Type 0x07

    hsGCompFlags =  \
    { \
        "kCompShaded"            :    0x1, \
        "kCompEnvironMap"        :    0x2, \
        "kCompProjectOnto"       :    0x4, \
        "kCompSoftShadow"        :    0x8, \
        "kCompSpecular"          :   0x10, \
        "kCompTwoSided"          :   0x20, \
        "kCompDrawAsSplats"      :   0x40, \
        "kCompAdjusted"          :   0x80, \
        "kCompNoSoftShadow"      :  0x100, \
        "kCompDynamic"           :  0x200, \
        "kCompDecal"             :  0x400, \
#OBSOLETE        "kCompIsEmissive"        :  0x800, \
        "kCompIsLightMapped"     : 0x1000, \
        "kCompNeedsBlendChannel" : 0x2000  \
    }

    UpdateFlags =  \
    { \
        "kUpdateAgain" : 0x1 \
    }

    def __init__(self,parent,name="unnamed",type=0x0007):
        plSynchedObject.__init__(self,parent,name,type)

        self.fLOD = 0# Int32
        self.fLayersCount = 0
        self.fLayers = []   # hsTArray<plLayerInterface>
        self.fPiggyBacksCount = 0
        self.fPiggyBacks = [] # hsTArray<plLayerInterface>
        self.fCompFlags = 0 # UInt32
        self.fLoadFlags = 0 # UInt32
        #self.fLastUpdateTime# Single
        self.blendermaterial = None

    def _Find(page,name):
        return page.find(0x0007,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0007,name,1)
    FindCreate = staticmethod(_FindCreate)



    def write(self,stream):
        plSynchedObject.write(self,stream)

        stream.Write32(self.fLoadFlags);
        stream.Write32(self.fCompFlags);
        stream.Write32(len(self.fLayers));
        stream.Write32(len(self.fPiggyBacks));

        for key in self.fLayers:
            key.update(self.Key)
            key.write(stream)

        for key in self.fPiggyBacks:
            key.update(self.Key)
            key.write(stream)

    def read(self,stream):
        plSynchedObject.read(self,stream)

        self.fLoadFlags = stream.Read32();
        self.fCompFlags = stream.Read32();

        self.fLayersCount = stream.Read32();
        self.fPiggyBacksCount = stream.Read32();

        for i in range(self.fLayersCount):
            key = UruObjectRef(self.getVersion())
            key.read(stream)
            self.fLayers.append(key)

        for i in range(self.fPiggyBacksCount):
            key = UruObjectRef(self.getVersion())
            key.read(stream)
            self.fLayers.append(key)


    def FromBlenderMat(self,mat,obj):
        print("  [Material %s]"%(str(self.Key.name)))
        # mat is the material to convert
        # obj is the object the material links to - and only used to get the UV Maps
        self.blendermaterial=mat

        name = str(self.Key.name)
        resmanager=self.getResManager()
        root=self.getRoot()
        #mesh = obj.getData(False,True)
        mesh = obj.data

        # reset the flags to 00
        self.fFlags=0x00

        # Loop through the MTex layers of Blender, and parse every one of them as a layer.
        if (mat): #avoid crashes if we acidentally ref this function without parameters

#            if(obj.type == "MESH" and (obj.data.mode & Blender.Mesh.Modes.TWOSIDED) > 0):
 #               self.fCompFlags |= hsGMaterial.hsGCompFlags["kCompTwoSided"]

            if not mat.use_shadeless and mat.specular_intensity > 0.0 and mat.specular_color != mathutils.Color((0.0, 0.0, 0.0)):
                self.fCompFlags |= hsGMaterial.hsGCompFlags["kCompSpecular"]

            if name.lower().find("decal") != -1:
                self.fCompFlags |= hsGMaterial.hsGCompFlags["kCompDecal"]


            mtex_list = mat.texture_slots

            layerlist = []
            i=0
            for mtex in mtex_list:
                if(mtex != None):
                    if (mtex.texture.type == "BLEND" or
                        mtex.texture.type == "NONE"  or
                        mtex.texture.type == "IMAGE" or
                        mtex.texture.type == "NOISE" or
                        mtex.texture.type == "ENVIRONMENT_MAP"):

                        # we hit a problem when two textures are shared, because the mtex is different per material.
                        # because of this. we'll prefix the material name, before the layer name
                        ipo = mat.animation_data
                        channel = i
                        anim = False

                        if ipo and ipo.action:
                            # WHAT CAN BE ANIMATED:
                            #   layer offset
                            #   layer scale
                            #   material color
                            #   material alpha
                            
                            # check whether the material has animation data for this mtex
                            # this requires some string analysing which may be a bit ugly.
                            # Ideally, we would check for animation_data directly inside the mtex, however it seems it's always empty...
                            for curve in ipo.action.fcurves:
                                path = curve.data_path
                                if path.find("[") != -1:
                                    whatAnimated = path[:path.find("[")]
                                    if whatAnimated == "texture_slots":
                                        layerAnimated = int(path[   path.find("[")+1 : path.find("].")  ])
                                        paramAnimated = path[path.find("].")+2:]
                                        if layerAnimated == i:
                                            anim = True
                                elif path == "diffuse_color":
                                    anim = True
                                elif path == "alpha":
                                    anim = True

                        #layer = root.find(0x06,mat.name + "-" + mtex.texture.name,1)
                        layerlist.append({"mtex":mtex,"stencil":mtex.use_stencil,"channel":channel,"anim":anim})
                    else:
                        print("WARNING - texture type " + mtex.texture.type + " is not supported and will not be exported.")
                i+=1

            i = 0
            while i < len(layerlist):
                layer_info = layerlist[i]

                if not layer_info["stencil"]:
                    mtex = layer_info["mtex"]
                    layer = root.find(0x06,mat.name + "-" + mtex.texture.name,1)
                    if(not layer.isProcessed):
                        layer.data.FromBlenderMTex(mtex,obj,mat)
                        layer.data.FromBlenderMat(obj,mat)
                        layer.isProcessed = 1
                    if not layer_info["anim"]:
                        if layer.data.fState.fMiscFlags & hsGMatState.hsGMatMiscFlags["kMiscLightMap"]:
                            self.fCompFlags |= hsGMaterial.hsGCompFlags["kCompIsLightMapped"]
                            self.fPiggyBacks.append(layer.data.getRef())
                        else:
                            self.fLayers.append(layer.data.getRef())
                    else:
                        chan = layer_info["channel"]
                        animlayer = root.find(0x0043,layer.data.getName(),1)
                        animlayer.data.FromBlender(obj,mat,mtex,chan)
                        animlayer.data.fUnderlay = layer.data.getRef()
                        if layer.data.fState.fMiscFlags & hsGMatState.hsGMatMiscFlags["kMiscLightMap"]:
                            self.fCompFlags |= hsGMaterial.hsGCompFlags["kCompIsLightMapped"]
                            self.fPiggyBacks.append(animlayer.data.getRef())
                        else:
                            self.fLayers.append(animlayer.data.getRef())
                    i += 1
                else:
                    if i < len(layerlist) - 1: # if it's not the last one
                        mix_info = layer_info
                        # Append the next layer first, and say that it has a stencil
                        layer_info = layerlist[i+1]
                        mtex = layer_info["mtex"]
                        layer = root.find(0x06,mat.name + "-" + mtex.texture.name,1)
                        if(not layer.isProcessed):
                            layer.data.FromBlenderMat(obj,mat)
                            layer.data.FromBlenderMTex(mtex,obj,mat,False,True)
                            if layer.data.fState.fMiscFlags & hsGMatState.hsGMatMiscFlags["kMiscLightMap"]:
                                self.fCompFlags |= hsGMaterial.hsGCompFlags["kCompIsLightMapped"]
                            layer.isProcessed = 1
                        if not layer_info["anim"]:
                            self.fLayers.append(layer.data.getRef())
                        else:
                            chan = layer_info["channel"]
                            animlayer = root.find(0x0043,layer.data.name,1)
                            animlayer.data.FromBlender(obj,mat,mtex,chan)
                            animlayer.data.fUnderlay = layer.data.getRef()
                            self.fLayers.append(animlayer.data.getRef())

                        # append the stencil layer after that...
                        mtex = mix_info["mtex"]
                        mix = root.find(0x06,layer.data.getName() + "_AlphaBlend_",1)
                        self.fCompFlags |= hsGMaterial.hsGCompFlags["kCompNeedsBlendChannel"]
                        if(not mix.isProcessed):
                            mix.data.FromBlenderMTex(mtex,obj,mat,True,False)
                            mix.data.FromBlenderMat(obj,mat)
                            mix.isProcessed = 1
                        if not mix_info["anim"]:
                            self.fLayers.append(mix.data.getRef())
                        else:
                            chan = mix_info["channel"]
                            animlayer = root.find(0x0043,mix.data.name,1)
                            animlayer.data.FromBlender(obj,mat,mtex,chan)
                            animlayer.data.fUnderlay = layer.data.getRef()
                            self.fLayers.append(animlayer.data.getRef())

                        self.fCompFlags |= hsGMaterial.hsGCompFlags["kCompNeedsBlendChannel"]

                        # And ofcourse increase by 2 instead of one...
                        i += 2
                    else:
                        # just ignore it...
                        i += 1

            # Add a default layer if we didn't get and layers from the mtexes
            if(len(self.fLayers) == 0):
                #find or create this new layer:
                layer=root.find(0x06,name + "_AutoLayer_",1)

                # now see if we have a uvmapped texture on the object, and add this texture if needed
                # DRAT THAT. People need to learn using materials sometime...
                if(obj) and False:
                    # retrieve the corresponding mesh
                    meshName = obj.data.name
                    mesh = bpy.data.meshes[meshName]

                    texture_img=None
                    for f in mesh.polygons:
                        if mesh.faceUV and f.image!=None:
                            texture_img=f.image
                            break
                    if(texture_img != None):
                        #add the texture if it is there
                        layer.data.FromUvTex(texture_img,obj)
                layer.data.FromBlenderMat(obj,mat)

                self.fLayers.append(layer.data.getRef())

            # If we have two vertex color layers, the 2nd is used as alpha layer - if we have vertex alpha,
            # we need to have the renderlevel set to blending
            #if len(mesh.getColorLayerNames()) > 1:
            #    if self.fZOffset < 1:
            #        self.fZOffset = 1



    def layerCount(self):
        return len(self.fLayers)

    def Alpha(self):
        root = self.getRoot()
        UsesAlpha = False
        for layerref in self.fLayers:
            layer = root.findref(layerref)
            if(layer.type == 0x0043):
                UsesAlpha = False
            else:
                UsesAlpha = (UsesAlpha or layer.data.UsesAlpha)
        return UsesAlpha

    def TexLayerCount(self):
        root=self.getRoot()

        # count the layers that actually have a texture set.
        count = 0
        for layerref in self.fLayers:
            layer = root.findref(layerref)
            if(layer.data.fHasTexture != 0):
                count += 1
        return count

    def getBlenderTextures(self):
        return self.blendertextures

    def export_mat(self,mat,obj):
        self.FromBlenderMat(mat,obj)



class plLayerInterface(plSynchedObject):     # Type 0x41 (uru)

    plUVWSrcModifiers = \
    { \
        "kUVWPassThru"  :        0x0, \
        "kUVWNormal"    :    0x10000, \
        "kUVWPosition"  :    0x20000, \
        "kUVWReflect"   :    0x30000, \
        "kUVWIdxMask"   : 0x0000FFFF  \
    }

    def __init__(self,parent,name="unnamed",type=None):
        plSynchedObject.__init__(self,parent,name,type)

        self.fUnderlay = UruObjectRef(self.getVersion())
        self.fOverLay = UruObjectRef(self.getVersion())
        self.fOwnedChannels = 0x00
        self.fPassThruChannels = 0x00
        self.fTransform = hsMatrix44()
        self.fPreshadeColor = RGBA(0.5,0.5,0.5,1.0,type=1) # Grey
        self.fRuntimeColor = RGBA(0.5,0.5,0.5,1.0,type=1) # Grey
        self.fAmbientColor = RGBA(0.0,0.0,0.0,0.0,type=1) # Clear
        self.fOpacity = 1.0
        self.fTexture = UruObjectRef(self.getVersion())
        self.fState = hsGMatState()
        self.fUVWSrc = 0
        self.fLODBias =  -1.0
        self.fSpecularColor = RGBA(0.0,0.0,0.0,1.0,type=1) # Black
        self.fSpecularPower = 1.0
        self.fVertexShader = UruObjectRef(self.getVersion())
        self.fPixelShader = UruObjectRef(self.getVersion())
        self.fBumpEnvXfm = hsMatrix44()

    def read(self,buf):
        plSynchedObject.read(self,buf)
        self.fUnderlay.read(buf)

    def write(self,buf):
        plSynchedObject.write(self,buf)
        self.fUnderlay.write(buf)

class plLayer(plLayerInterface):             # Type 0x06

    def __init__(self,parent,name="unnamed",type=0x0006):
        plLayerInterface.__init__(self,parent,name,type)

        self.fOwnedChannels = 0x3FFF;
        self.fPreshadeColor = RGBA(0.5,0.5,0.5,1.0,type=1) # Grey
        self.fRuntimeColor = RGBA(0.5,0.5,0.5,1.0,type=1) # Grey
        self.fAmbientColor = RGBA(0.0,0.0,0.0,0.0,type=1) # Clear
        self.fSpecularColor = RGBA(0.0,0.0,0.0,1.0,type=1) # Black

        self.fTransform = hsMatrix44()
        self.fOpacity = 1.0
        self.fState = hsGMatState()
        self.fUVWSrc = 0
        self.fLODBias = -1.0
        self.fSpecularPower = 1.0
        self.fTexture = UruObjectRef(self.getVersion())
        self.fVertexShader = UruObjectRef(self.getVersion())
        self.fPixelShader = UruObjectRef(self.getVersion())
        self.fBumpEnvXfm = hsMatrix44()

        self.fRenderLevel = plRenderLevel() #used to determine RenderLevel
        self.fZBias = 0

        self.fHasTexture = 0
        self.InitToDefault()

    def _Find(page,name):
        return page.find(0x0006,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0006,name,1)
    FindCreate = staticmethod(_FindCreate)


    def InitToDefault(self):
        fState = hsGMatState();
        self.fTexture = UruObjectRef(self.getVersion())
        self.fRuntimeColor = RGBA(0.5, 0.5, 0.5, 1.0)  # Grey
        self.fPreshadeColor = RGBA(0.5, 0.5, 0.5, 1.0) # Grey
        self.fAmbientColor = RGBA(0.0, 0.0, 0.0, 0.0)        # Clear
        self.fOpacity = 1.0
        self.fTransform = hsMatrix44()
        self.fUVWSrc = 0
        self.fLODBias = -1.0
        self.fSpecularColor = RGBA(0.0, 0.0, 0.0, 1.0)       # Black
        self.fSpecularPower = 1.0
        self.fVertexShader = UruObjectRef(self.getVersion())
        self.fPixelShader = UruObjectRef(self.getVersion())
        self.fBumpEnvXfm = hsMatrix44()

        self.fRenderLevel = plRenderLevel()
        self.UsesAlpha = False

        self.fHasTexture = 0

    def read(self,stream):
        plLayerInterface.read(self,stream)
        self.fState.read(stream)
        self.fTransform.read(stream)
        self.fPreshadeColor.read(stream)    #old: self.ambient
        self.fRuntimeColor.read(stream)     #old: self.diffuse
        self.fAmbientColor.read(stream)     #old: self.emissive
        self.fSpecularColor.read(stream)    #old: self.specular
        self.fUVWSrc = stream.Read32()
        self.fOpacity = stream.ReadFloat()
        self.fLODBias = stream.ReadFloat()
        self.fSpecularPower = stream.ReadFloat()
        self.fTexture.read(stream)
        self.fVertexShader.read(stream)
        self.fPixelShader.read(stream)
        self.fBumpEnvXfm.read(stream)

    def write(self,stream):
        plLayerInterface.write(self,stream)
        self.fState.write(stream)
        self.fTransform.write(stream)
        self.fPreshadeColor.write(stream)   #old: self.ambient
        self.fRuntimeColor.write(stream)    #old: self.diffuse
        self.fAmbientColor.write(stream)    #old: self.emissive
        self.fSpecularColor.write(stream)   #old: self.specular
        stream.Write32(self.fUVWSrc)
        stream.WriteFloat(self.fOpacity)
        stream.WriteFloat(self.fLODBias)
        stream.WriteFloat(self.fSpecularPower)
        self.fTexture.write(stream)
        self.fVertexShader.write(stream)
        self.fPixelShader.write(stream)
        self.fBumpEnvXfm.write(stream)

    def FromBlenderMTex(self,mtex,obj,mat,stencil=False,hasstencil=False):
        print("   [Layer %s]"%(str(self.Key.name)))
        #prp is for current prp file... (though that should be obtainable from self.parent.prp)
        resmanager=self.getResManager()
        root=self.getRoot()

        #mesh = obj.getData(False,True)
        mesh = obj.data

        exportTexturesToPrp = prp_Config.export_textures_to_page_prp
        try:
            p = obj.getProperty("ignorePPT")
            if (bool(p.getData()) == True):
                exportTexturesToPrp = 0
        except:
            pass

        # determine what the texture prp must be
        if exportTexturesToPrp:
            texprp=root
        else:
            texprp=resmanager.findPrp("Textures")
        if texprp==None:
            raise RuntimeError("Textures PRP file not found")

        mipmap = None
        qmap = None

        if(mtex):

            # First Determine the UVW Source....
            UVLayers = mesh.uv_layers

            Use_Sticky = False
            # Loop through Layers To see which coorinate systems are used.
            for _mtex in mat.texture_slots:
                if not _mtex is None:
                    if _mtex.texture_coords == "STICK" and mesh.vertexUV:
                        Use_Sticky = True

            UVSticky = 0 # Setting Sticky gives you 1st uv layer if no Sticky Coords set...
            if Use_Sticky:
                UVSticky = len(UVLayers)

            # Check out current mapping
            if mtex.texture_coords == "STICK":
                print("    -> Using sticky mapping")
                self.fUVWSrc = UVSticky
            elif mtex.texture_coords == "UV":
                print("    -> Using UV map '%s'"%(mtex.uv_layer))
                i=0
                self.fUVWSrc = -1
                for uv in UVLayers:
                    if uv.name == mtex.uv_layer:
                        self.fUVWSrc = i
                    i+=1
                if self.fUVWSrc == -1:
                    print("    -> Err, Using first UV map")
                    self.fUVWSrc = 0
            elif mtex.texture_coords == "OBJECT":
                print("    -> Mapping as projection light")
                self.fUVWSrc = plLayerInterface.plUVWSrcModifiers["kUVWPosition"]
            else:
                print("    -> Using default first UV map")
                # Other mappings will make the map default to first uv map
                self.fUVWSrc = 0


            # process the image
            tex = mtex.texture

            #mtex type ENVMAP
            if(tex.type == "ENVIRONMENT_MAP"):
                if(tex.environment_map.source == "ANIMATED" or tex.image == None):
                    print("Envmap: creating dynamic envmap")
                    qmap = plDynamicEnvMap.FindCreate(root, tex.name)
                    qmap.data.export_obj(obj)

                else:
                    print("Envmap: creating static envmap")
                    #find or create the qmap

                    mipmapinfo = blMipMapInfo()
                    mipmapinfo.fName = tex.image.name
                    mipmapinfo.fMipMaps = True
                    mipmapinfo.fGauss = True
                    mipmapinfo.fResize = True

                    qmap = plCubicEnvironMap.Export(root,tex.image.name,tex.image,mipmapinfo,exportTexturesToPrp)

                self.fTexture = qmap.data.getRef()
                self.fHasTexture = 1

                # set default settings for qmaps:
                # self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendAlpha"]
                self.fState.fClampFlags |= 0 # | hsGMatState.hsGMatClampFlags[""]
                self.fState.fShadeFlags |= hsGMatState.hsGMatShadeFlags["kShadeEnvironMap"]
                self.fState.fZFlags     |= 0 # | hsGMatState.hsGMatZFlags[""]
                self.fState.fMiscFlags  |= ( hsGMatState.hsGMatMiscFlags["kMiscUseReflectionXform"]
                                            | hsGMatState.hsGMatMiscFlags["kMiscRestartPassHere"]
                                            )

                self.fUVWSrc            |= plLayerInterface.plUVWSrcModifiers["kUVWReflect"]

                # set the blendflags for this layer to the cubicmap flags
                #self.fRenderLevel = plRenderLevel(plRenderLevel.MajorLevel["kDefRendMajorLevel"] | plRenderLevel.MajorLevel["kBlendRendMajorLevel"],
                #                                    plRenderLevel.MinorLevel["kDefRendMinorLevel"])
                self.UsesAlpha = True

                pass
            #mtex type IMAGE
            elif(tex.type == "IMAGE"):
                # find or create the mipmap

                if(tex.image):

                    mipmapinfo = blMipMapInfo()
                    mipmapinfo.export_tex(tex)

                    # TODO - what is that ?
                    #if stencil and (not Blender.Texture.ImageFlags["USEALPHA"]):
                    #    mipmapinfo.fCalcAlpha = True

                    mipmap=plMipMap.Export(root,tex.image.name,tex.image,mipmapinfo,exportTexturesToPrp)

                    self.fTexture = mipmap.data.getRef()
                    self.fHasTexture = 1

                    # set the blendflags for this layer to the alphaflags, if it has alhpa
                    if (mipmap.data.FullAlpha or mipmap.data.OnOffAlpha):
                        self.UsesAlpha = True

                    if tex.extension == "CLIP":
                        self.fState.fClampFlags |= hsGMatState.hsGMatClampFlags["kClampTexture"]

                pass
            #mtex type BLEND
            #Builds a linear AlphaBlend
            elif(tex.type == "BLEND"):
                if mtex.texture.progression == "LINEAR":
                    # now create a blend, depending on whether it is horizontal or vertical:
                    if(tex.use_flip_axis):
                        #Vertical blend
                        blendname = "ALPHA_BLEND_FILTER_V_LIN_64x64"

                        blenddata = io.BytesIO()
                        blendwidth = 64
                        blendheight = 64

                        for y in range(blendheight,0,-1):
                            alpha = 255 *(float(y)/blendheight)
                            for x in range(0,blendwidth):
                                blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))
                    else:
                        #Horizontal blend
                        blendname = "ALPHA_BLEND_FILTER_U_LIN_64x64"

                        blenddata = io.BytesIO()
                        blendwidth = 64
                        blendheight = 64

                        for y in range(blendheight,0,-1):
                            for x in range(0,blendwidth):
                                alpha = 255 * (float(x)/blendwidth)
                                blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))

                elif mtex.texture.progression == "QUADRATIC":
                    # now create a blend, depending on whether it is horizontal or vertical:
                    if(tex.use_flip_axis):
                        #Vertical blend
                        blendname = "ALPHA_BLEND_FILTER_V_QUAD_64x64"

                        blenddata = io.BytesIO()
                        blendwidth = 4
                        blendheight = 64

                        for y in range(blendheight,0,-1):
                            alpha = 255 * math.pow(float(y)/blendheight,2)
                            for x in range(0,blendwidth):
                                blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))
                    else:
                        #Horizontal blend
                        blendname = "ALPHA_BLEND_FILTER_U_QUAD_64x64"

                        blenddata = io.BytesIO()
                        blendwidth = 64
                        blendheight = 4

                        for y in range(blendheight,0,-1):
                            for x in range(0,blendwidth):
                                alpha = 255 * math.pow(float(x)/blendwidth,2)
                                blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))

                elif mtex.texture.progression == "EASING":
                    # now create a blend, depending on whether it is horizontal or vertical:
                    if(tex.use_flip_axis):
                        #Vertical blend
                        blendname = "ALPHA_BLEND_FILTER_V_EASE_64x64"

                        blenddata = io.BytesIO()
                        blendwidth = 4
                        blendheight = 64

                        for y in range(blendheight,0,-1):
                            alpha = 255 * (1 - (0.5 + (math.cos((float(y)/blendheight) * math.pi) * 0.5)))
                            for x in range(0,blendwidth):
                                blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))
                    else:
                        #Horizontal blend
                        blendname = "ALPHA_BLEND_FILTER_U_EASE_64x64"

                        blenddata = io.BytesIO()
                        blendwidth = 64
                        blendheight = 4

                        for y in range(blendheight,0,-1):
                            for x in range(0,blendwidth):
                                alpha = 255 * (1 - (0.5 + (math.cos( (float(x)/blendwidth) * math.pi) * 0.5)))
                                blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))

                elif mtex.texture.progression == "DIAGONAL":
                    # Prepare the data for this object....
                    blendname = "ALPHA_BLEND_FILTER_DIAG_64x64"

                    blenddata = io.BytesIO()
                    blendwidth = 64
                    blendheight = 64

                    for y in range(blendheight,0,-1):
                        for x in range(0,blendwidth):
                            dist = math.sqrt(math.pow(x ,2) + math.pow(y,2))
                            alpha = 255 *(dist / math.sqrt(math.pow(blendwidth,2) + math.pow(blendheight,2)))

                            blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))

                elif mtex.texture.progression == "SPHERE":
                    # Prepare the data for this object....
                    blendname = "ALPHA_BLEND_FILTER_SPHERE_64x64"

                    blenddata = io.BytesIO()
                    blendwidth = 64
                    blendheight = 64

                    for y in range(blendheight,0,-1):
                        for x in range(0,blendwidth):
                            dist = math.sqrt(math.pow(x - (blendwidth/2),2) + math.pow(y - (blendheight/2),2))
                            alpha = 255 *(math.cos((dist / (blendwidth/2) * 0.5 * math.pi )))
                            if alpha < 0 or dist > (blendwidth/2):
                                alpha = 0
                            elif alpha > 255:
                                alpha = 255
                            blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))

                elif mtex.texture.progression == "QUADRATIC_SPHERE":
                    # Prepare the data for this object....
                    blendname = "ALPHA_BLEND_FILTER_HALO_64x64"

                    blenddata = io.BytesIO()
                    blendwidth = 64
                    blendheight = 64

                    for y in range(blendheight,0,-1):
                        for x in range(0,blendwidth):
                            dist = math.sqrt( math.pow(x - (blendwidth/2),2) + math.pow(y - (blendheight/2),2) )
                            alpha = 255 *(0.5 + (0.5 * math.cos((dist / (blendwidth/2) * math.pi ))))
                            if alpha < 0 or dist > (blendwidth/2):
                                alpha = 0
                            elif alpha > 255:
                                alpha = 255
                            blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))

                else: ## RADIAL TYPE
                    #
                    # Prepare the data for this object....
                    if(tex.use_flip_axis):
                        blendname = "ALPHA_BLEND_FILTER_V_RADIAL_64x64"
                    else:
                        blendname = "ALPHA_BLEND_FILTER_U_RADIAL_64x64"

                    blenddata = io.BytesIO()
                    blendwidth = 64
                    blendheight = 64

                    for y in range(blendheight,0,-1):
                        for x in range(0,blendwidth):
                            if(tex.use_flip_axis):
                                rely = x - (blendwidth/2)
                                relx = y - (blendheight/2)
                            else:
                                relx = x - (blendwidth/2)
                                rely = y - (blendheight/2)

                            angle = math.atan2(rely,relx) + math.pi

                            while angle < 0:
                                angle += 2* math.pi

                            while angle > (2*math.pi):
                                angle -= 2* math.pi

                            alpha = 255 *(angle/(2*math.pi))
                            if alpha < 0:
                                alpha = 0
                            blenddata.write(struct.pack("BBBB",255,255,255,int(alpha)))

                # Set clipping (clamping)
                self.fState.fClampFlags |= hsGMatState.hsGMatClampFlags["kClampTexture"]


                mipmapinfo = blMipMapInfo()
                mipmapinfo.fName = blendname
                mipmapinfo.fMipMaps = False
                mipmapinfo.fGauss = False
                mipmapinfo.fCompressionType = plBitmap.Compression["kDirectXCompression"]
                mipmapinfo.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kDXT5"]

                mipmap = plMipMap.Export_Raw(root,blendname,blenddata,blendwidth,blendheight,mipmapinfo,exportTexturesToPrp)

                # and link the mipmap to the layer
                self.fTexture = mipmap.data.getRef()
                self.fHasTexture = 1
                # alphablend layers do not affect blendflags (as far as we know now)
            
            
            elif (tex.type == "NOISE"):
                print("Tex type NOISE - exporting as dynamic text map.")
                print("[ plDynamicTextMap %s ]" % tex.name)
                tmap = plDynamicTextMap.FindCreate(root, tex.name)
                tmap.data.export_obj(obj)
                self.fTexture = tmap.data.getRef()
                self.fHasTexture = 1
                self.UsesAlpha = True


            else:
                print("WARNING - texture type " + tex.type + " is not supported and will not be exported.")


            # now process additional mtex settings


            if not stencil:
                # find the texture object, so we can get some values from it
                if not mtex.texture_coords == "OBJECT":
                    # first make a calculation of the uv transformation matrix.
                    uvmobj = bpy.data.objects.new ('temp', None)

                    # now set the scale (and rotation) to the object
                    uvmobj.scale[0] = mtex.scale[0]
                    uvmobj.scale[1] = mtex.scale[1]
                    # map Blender offsets to Plasma offsets
                    uvmobj.location[0] = 0.5 - 0.5 * mtex.scale[0] + mtex.offset[0]
                    uvmobj.location[1] = 0.5 - 0.5 * mtex.scale[1] - mtex.offset[1]
                    uvm=getMatrix(uvmobj)
                    del uvmobj
                    #uvm.transpose()
                    self.fTransform.set(uvm)

                self.fOpacity = mtex.diffuse_color_factor # factor how texture blends with color used as alpha blend value
                if not mtex.use_map_color_diffuse:
                    self.fOpacity = 1.

                if mesh.show_double_sided:
                    self.fState.fMiscFlags  |= hsGMatState.hsGMatMiscFlags["kMiscTwoSided"]


                if(mtex.blend_type == "ADD"):
                    # self.fState.fBlendFlags |= ( hsGMatState.hsGMatBlendFlags["kBlendAdd"])
                    self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendAddColorTimesAlpha"] # This is better and more intuitive
                    if mtex.use_map_alpha:
                        self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendAlphaAdd"]

                elif(mtex.blend_type == "MULTIPLY"):
                    self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendMult"]
                    if mtex.use_map_alpha:
                        self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendAlphaMult"]

                elif(mtex.blend_type == "SUBTRACT"):
                    self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendSubtract"]

                else: #(mtex.blendmode == Blender.Texture.BlendModes.MIX):
                    # Enable Normal Alpha Blending ONLY if the other alpha blend flags are not enabled
                    self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendAlpha"]
                if(mtex.invert): # set the negate colors flag if it is so required
                    self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendInvertColor"]
                
                # PATCH by Tachzusamm - set kBlendAlphaTestHigh to remove alpha edge artifacts
                if(tex.type == "IMAGE"):
                    if(mtex.use_map_alpha):
                        # this was previously bound to Premultiply
                        # But isn't it better to always enable it when using alpha ?
                        self.fState.fBlendFlags  |= hsGMatState.hsGMatBlendFlags["kBlendAlphaTestHigh"]

                # these are quite hacky - I have no other idea of what to bind them to...
                if(mtex.use_map_hardness):
                    # arg, nevermind - I doubt anyone will ever use it.
                    self.fState.fMiscFlags  |= hsGMatState.hsGMatMiscFlags["kMiscBindNext"] | hsGMatState.hsGMatMiscFlags["kMiscRestartPassHere"]

                # that one might be of use - I'm not even sure it does a difference in rendering, but whatever.
                # Binding to emit value seems fitting to me - we'll provide both.
                if(mtex.use_map_emit or mtex.use_map_ambient):
                    self.fState.fMiscFlags  |= hsGMatState.hsGMatMiscFlags["kMiscLightMap"]

        if stencil:
            # now set the various layer properties specific to alphablendmaps
            self.fState.fBlendFlags |= ( hsGMatState.hsGMatBlendFlags["kBlendAlpha"]
                                        | hsGMatState.hsGMatBlendFlags["kBlendAlphaMult"]
                                        | hsGMatState.hsGMatBlendFlags["kBlendNoTexColor"]
                                        )

            self.fState.fZFlags     |= hsGMatState.hsGMatZFlags["kZNoZWrite"]
            self.fState.fMiscFlags  |= 0 # | hsGMatState.hsGMatMiscFlags[""]
            self.fAmbientColor = RGBA(1.0,1.0,1.0,1.0)

        if hasstencil:
            self.fState.fMiscFlags  |= hsGMatState.hsGMatMiscFlags["kMiscBindNext"]  | hsGMatState.hsGMatMiscFlags["kMiscRestartPassHere"]

        if stencil or hasstencil:
            # a stencil joins two layers into one that has alpha....
            self.UsesAlpha = True




    def FromBlenderMat(self,obj,mat):
        # Now Copy Settings from the material...
        mesh = obj.data

        # get the blender basic colors and options
        matR,matG,matB = mat.diffuse_color[:] #color triplet (map to diffuse)
        if mat.use_transparency:
            matA = mat.alpha
        else:
            matA = 1

        specR,specG,specB = mat.specular_color[:] #specular color triplet (map to specular)
        specR = specR * mat.specular_intensity/2
        specG = specG * mat.specular_intensity/2
        specB = specB * mat.specular_intensity/2
        specCol=RGBA(specR,specG,specB,matA,type=1)

        mirR,mirG,mirB = mat.mirror_color[:]

        emitfactor = mat.emit
        #calculat the emissive colors
        emitR = matR * emitfactor
        emitG = matG * emitfactor
        emitB = matB * emitfactor
        emitCol=RGBA(emitR,emitG,emitB,1,type=1)



        diffuseCol=RGBA(matR,matG,matB,matA,type=1)


        # calculate the ambient colors
        ambfactor = mat.ambient
        ambR = matR * ambfactor
        ambG = matG * ambfactor
        ambB = matB * ambfactor
        ambientCol = RGBA(ambR,ambG,ambB,1,type=1)

        # Map to the layer colors
        self.fPreshadeColor = ambientCol
        self.fRuntimeColor = diffuseCol
        self.fAmbientColor = emitCol
        self.fSpecularColor = specCol



        if not mat.use_mist:
            self.fState.fShadeFlags |= hsGMatState.hsGMatShadeFlags["kShadeNoFog"]
            self.fState.fShadeFlags |= hsGMatState.hsGMatShadeFlags["kShadeReallyNoFog"]

        if mat.use_transparency:
            self.fState.fZFlags |= hsGMatState.hsGMatZFlags["kZNoZWrite"]

        if not mat.use_shadeless and mat.specular_intensity > 0.0:
            self.fState.fShadeFlags |= hsGMatState.hsGMatShadeFlags["kShadeSpecular"]
            self.fState.fShadeFlags |= hsGMatState.hsGMatShadeFlags["kShadeSpecularAlpha"]
            self.fState.fShadeFlags |= hsGMatState.hsGMatShadeFlags["kShadeSpecularColor"]
            self.fState.fShadeFlags |= hsGMatState.hsGMatShadeFlags["kShadeSpecularHighlight"]
            self.fSpecularPower = mat.specular_hardness

        if mat.offset_z > 0.0:
            self.fState.fZFlags |= hsGMatState.hsGMatZFlags["kZIncLayer"]

        # If we have two vertex color layers, the one named Alpha is used as alpha layer - if we have vertex alpha,
        # we need to have the alpha blending flag set, and we need to have
        for colLayerName in mesh.vertex_colors:
            if(colLayerName.name.lower() == "alpha"):
                self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendAlpha"]


    def FromUvTex(self,image,obj):
        resmanager=self.getResManager()
        root=self.getRoot()

        # Use default settings here...
        mipmapinfo = blMipMapInfo()
        mipmapinfo.fImageName = image.name
        mipmapinfo.fMipMaps = True
        mipmapinfo.fGauss = False
        mipmapinfo.fResize = True

        exportTexturesToPrp = prp_Config.export_textures_to_page_prp
        try:
            p = obj.getProperty("ignorePPT")
            if (bool(p.getData()) == True):
                exportTexturesToPrp = 0
        except:
            pass

        print("  Exporting Mipmap image",image.name)
        mipmap=plMipMap.Export(root,image.name,image,mipmapinfo,exportTexturesToPrp)

        print("  Processes Mipmap image",mipmap.data.Key.name)

        self.fTexture = mipmap.data.getRef()

        # allow use of alpha
        self.fState.fBlendFlags |= hsGMatState.hsGMatBlendFlags["kBlendAlpha"]

        if obj.type == "MESH":
            if mesh.show_double_sided:
                self.fState.fMiscFlags  |= hsGMatState.hsGMatMiscFlags["kMiscTwoSided"]

        # set the blendflags for this layer to the alphaflags, if it has alhpa
        if(mipmap.data.FullAlpha | mipmap.data.OnOffAlpha):
            #self.fRenderLevel = plRenderLevel(plRenderLevel.MajorLevel["kDefRendMajorLevel"],\
            #                                  plRenderLevel.MinorLevel["kDefRendMinorLevel"])
            self.UsesAlpha = True


    def FromLamp(self,mtex,lamp):
        resmanager=self.getResManager()
        root=self.getRoot()

        pass


class blMipMapInfo:

    def __init__(self):
        self.fImageName = ""
        self.fMipMaps = True
        self.fResize = True
        self.fCalcAlpha = False
        self.fGauss = False
        self.fAlphaMult = 1.0
        self.fCompressionType = plBitmap.Compression["kDirectXCompression"]
        self.fBitmapInfo = plBitmap.Info()
        self.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kError"]

    def read(self,stream):
        self.fImageName = stream.ReadSafeString(0)
        self.fMipMaps = stream.ReadBool()
        self.fResize = stream.ReadBool()
        self.fCalcAlpha = stream.ReadBool()
        self.fGauss = stream.ReadBool()
        self.fAlphaMult = stream.ReadFloat()
        self.fCompressionType = stream.ReadByte()

        if (self.fCompressionType != plBitmap.Compression["kUncompressed"]  and  self.fCompressionType != plBitmap.Compression["kJPEGCompression"]):
            self.fBitmapInfo.fDirectXInfo.fBlockSize = stream.ReadByte()
            self.fBitmapInfo.fDirectXInfo.fCompressionType = stream.ReadByte()
        else:
            self.fBitmapInfo.fUncompressedInfo.fType = stream.ReadByte()

    def write(self,stream):
        # Set compression types correctly
        if self.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kDXT1"]:
            self.fBitmapInfo.fDirectXInfo.fBlockSize = 8
        elif self.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kDXT5"]:
            self.fBitmapInfo.fDirectXInfo.fBlockSize = 16

        stream.WriteSafeString(self.fImageName,0)
        stream.WriteBool(self.fMipMaps)
        stream.WriteBool(self.fResize)
        stream.WriteBool(self.fCalcAlpha)
        stream.WriteBool(self.fGauss)
        stream.WriteFloat(self.fAlphaMult)
        stream.WriteByte(self.fCompressionType)

        if (self.fCompressionType != plBitmap.Compression["kUncompressed"]  and  self.fCompressionType != plBitmap.Compression["kJPEGCompression"]):
            stream.WriteByte(self.fBitmapInfo.fDirectXInfo.fBlockSize)
            stream.WriteByte(self.fBitmapInfo.fDirectXInfo.fCompressionType)
        else:
            stream.WriteByte(self.fBitmapInfo.fUncompressedInfo.fType)

    def equals(self,ext):

        if not self.fImageName == ext.fImageName:
            return False
        if not self.fMipMaps == ext.fMipMaps:
            return False
        if not self.fResize == ext.fResize:
            return False

        if not self.fGauss == ext.fGauss:
            return False

        if not self.fAlphaMult == ext.fAlphaMult:
            return False

        if not self.fCompressionType == ext.fCompressionType:
            return False

        if self.fCompressionType == plBitmap.Compression["kDirectXCompression"]:
            # Ignore the dxt setting if it is set to kError (used as autodetect)....
            if not self.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kError"]:
                if not ext.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kError"]:
                    if not self.fBitmapInfo.fDirectXInfo.fCompressionType == ext.fBitmapInfo.fDirectXInfo.fCompressionType:
                        return False

        elif self.fCompressionType == plBitmap.Compression["kUncompressed"]:
            if not self.fBitmapInfo.fUncompressedInfo.fType == ext.fBitmapInfo.fUncompressedInfo.fType:
                return False

        if not self.fCalcAlpha == ext.fCalcAlpha:
            return False


        return True


    def export_tex(self,tex):
        # This is only valid for image textures :)
        if not tex is None and tex.type == "IMAGE" and not tex.image == None:

            self.fImageName = tex.image.name

            if tex.invert_alpha:
                pass

            if tex.use_interpolation:
                self.fCompressionType = plBitmap.Compression["kDirectXCompression"]
                if tex.use_alpha:
                    self.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kDXT5"]
                else:
                    # Let it be auto determined....
                    self.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kError"]
            else:
                if self.fImageName[-4:] == ".jpg" or self.fImageName[-5:] == ".jpeg":
                    self.fCompressionType = plBitmap.Compression["kJPEGCompression"]
                else:
                    self.fCompressionType = plBitmap.Compression["kUncompressed"]
                    self.fBitmapInfo.fUncompressedInfo.fType = plBitmap.Uncompressed["kRGB8888"] # The only format we support
                self.fResize = False

            #if tex.imageFlags & 0x1000: #Blender.Texture.ImageFlags["GAUSS"] doesn't work... :/
            if False:
                self.fGauss = True
            else:
                self.fGauss = False

            self.fAlphaMult = tex.filter_size

            if tex.use_calculate_alpha:
                self.fCalcAlpha = True
            else:
                self.fCalcAlpha = False

            if tex.use_mipmap:
                self.fMipMaps = True
            else:
                self.fMipMaps = False

            if tex.use_mipmap or tex.use_interpolation:
                self.fResize = True
            else:
                self.fResize = False


    def clone(self):
        new = blMipMapInfo()

        new.fImageName = self.fImageName
        new.fMipMaps = self.fMipMaps
        new.fResize = self.fResize
        new.fCalcAlpha = self.fCalcAlpha
        new.fGauss = self.fGauss
        new.fAlphaMult = self.fAlphaMult
        new.fCompressionType = self.fCompressionType

        new.fBitmapInfo.fDirectXInfo.fBlockSize = self.fBitmapInfo.fDirectXInfo.fBlockSize
        new.fBitmapInfo.fDirectXInfo.fCompressionType = self.fBitmapInfo.fDirectXInfo.fCompressionType

        new.fBitmapInfo.fUncompressedInfo.fType = self.fBitmapInfo.fUncompressedInfo.fType

        return new


    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s  = "---------------"
        s += "\nImagename:" + str(self.fImageName)
        s += "\nResize Image: " + str(self.fResize)
        s += "\nMake MipMaps: " + str(self.fMipMaps)
        s += "\nCalculate Alpha:" + str(self.fCalcAlpha)
        s += "\nMipMap Gauss:" + str(self.fGauss)
        s += "\nMipmap AlphaMult:" + str(self.fAlphaMult)
        if self.fCompressionType == plBitmap.Compression["kDirectXCompression"]:
            s += "\nCompressionType: DXT"
            if self.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kDXT1"]:
                s += "\n SubType: DXT1"
            elif self.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kDXT5"]:
                s += "\n SubType: DXT5"
        elif self.fCompressionType == plBitmap.Compression["kJPEGCompression"]:
            s += "\nCompressionType: JPEG"
        elif self.fCompressionType == plBitmap.Compression["kUncompressed"]:
            s += "\nCompressionType: Uncompressed"
        s += "\n---------------\n"

        return s

class plBitmap(hsKeyedObject):               # Type 0x03

    #region Structures
    class DirectXInfo:
        def __init__(self):
            self.fCompressionType = 0 #CompressionType;
            self.fBlockSize = 0 #ubyte  #Formerly texelSize


    class UncompressedInfo:
        def __init__(self):
            self.fType = 0 #Uncompressed

    class Info:
        def __init__(self):
            self.fDirectXInfo = plBitmap.DirectXInfo() #DirectXInfo
            self.fUncompressedInfo = plBitmap.UncompressedInfo() #UncompressedInfo


    #region Constants
    CompressionType = \
    { \
        "kError" : 0, \
        "kDXT1"  : 1, \
        "kDXT2"  : 2, \
        "kDXT3"  : 3, \
        "kDXT4"  : 4, \
        "kDXT5"  : 5  \
    }

    Uncompressed =  \
    { \
        "kRGB8888"    : 0, \
        "kRGB4444"    : 1, \
        "kRGB1555"    : 2, \
        "kInten8"     : 3, \
        "kAInten88"   : 4  \
    }

    Space = \
    {  \
        "kNoSpace"        : 0, \
        "kDirectSpace"    : 1, \
        "kGraySpace"      : 2, \
        "kIndexSpace"     : 3  \
    }

    Flags = \
    {  \
        "kNoFlag"               :    0x0, \
        "kAlphaChannelFlag"     :    0x1, \
        "kAlphaBitFlag"         :    0x2, \
        "kBumpEnvMap"           :    0x4, \
        "kForce32Bit"           :    0x8, \
        "kDontThrowAwayImage"   :   0x10, \
        "kForceOneMipLevel"     :   0x20, \
        "kNoMaxSize"            :   0x40, \
        "kIntensityMap"         :   0x80, \
        "kHalfSize"             :  0x100, \
        "kUserOwnsBitmap"       :  0x200, \
        "kForceRewrite"         :  0x400, \
        "kForceNonCompressed"   :  0x800, \
        "kIsTexture"            : 0x1000, \
        "kIsOffscreen"          : 0x2000, \
        "kMainScreen"           :    0x0, \
        "kIsProjected"          : 0x4000, \
        "kIsOrtho"              : 0x8000  \
    }

    Compression = \
    { \
        "kUncompressed"         : 0, \
        "kDirectXCompression"   : 1, \
        "kJPEGCompression"      : 2  \
    }

    BITMAPVER = 2;


    def __init__(self,parent,name="unnamed",type=0x0003):
        hsKeyedObject.__init__(self,parent,name,type)
        self.BitmapInfo = plBitmap.Info() # Info

        self.fCompressionType = 1 # Compression

        self.fPixelSize = 1 #ubyte
        self.fSpace = 1     #sbyte
        self.fFlags = 0     #Flags

        self.fLowModifiedTime = 0 #uint #Formerly fInputManager
        self.fHighModifiedTime = 0 #uint #Formerly fPageMgr

        # for internal handling (From old implementation)
        self.isCubEvMapPart = 0
        self.BlenderImage=None

        self.FullAlpha = False
        self.OnOffAlpha = False

        self.MipMapInfo = blMipMapInfo()

        self.texCacheExtension = ".bmap"

    def _Find(page,name):
        return page.find(0x0003,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0003,name,1)
    FindCreate = staticmethod(_FindCreate)


    def read(self,stream, really=1,silent=1):
        hsKeyedObject.read(self,stream, really, silent)

        stream.ReadByte() #Discarded: Version
        self.fPixelSize = stream.ReadByte()
        self.fSpace = stream.ReadByte()
        self.fFlags = stream.Read16()
        self.fCompressionType = stream.ReadByte()


        if (self.fCompressionType != plBitmap.Compression["kUncompressed"]  and  self.fCompressionType != plBitmap.Compression["kJPEGCompression"]):
            self.BitmapInfo.fDirectXInfo.fBlockSize = stream.ReadByte()
            self.BitmapInfo.fDirectXInfo.fCompressionType = stream.ReadByte()
            nRead = 8
        else:
            self.BitmapInfo.fUncompressedInfo.fType = stream.ReadByte()
            nRead = 7

        self.fLowModifiedTime = stream.Read32()
        self.fHighModifiedTime = stream.Read32()

        return nRead

    def write(self, stream, really=1):
        hsKeyedObject.write(self,stream,really)

        stream.WriteByte(0x02)    # always version 0x02
        stream.WriteByte(self.fPixelSize)
        stream.WriteByte(self.fSpace)
        stream.Write16(self.fFlags)
        stream.WriteByte(self.fCompressionType)

        if (self.fCompressionType != plBitmap.Compression["kUncompressed"]  and  self.fCompressionType != plBitmap.Compression["kJPEGCompression"]):
            stream.WriteByte(self.BitmapInfo.fDirectXInfo.fBlockSize)
            stream.WriteByte(self.BitmapInfo.fDirectXInfo.fCompressionType)
            nWrote = 8
        else:
            stream.WriteByte(self.BitmapInfo.fUncompressedInfo.fType)
            nWrote = 7

        stream.Write32(self.fLowModifiedTime)
        stream.Write32(self.fHighModifiedTime)

        return nWrote

    # Version header for texture cache files
    # Update the last two digits when changing the file format
    TEXCACHEVER = "TC02"

    def TexCache_GetFilename(self):
        resmanager=self.getResManager()
        MyPath=resmanager.getBasePath()
        CachePath = MyPath + "/" + self.parent.parent.parent.age.name + "_TexCache/"

        # Make the directory if texture_cache is enabled
        if (prp_Config.texture_cache):
            try:
                os.mkdir(CachePath)
            except OSError:
                pass

        # Generate the filename
        CacheFile = CachePath + str(self.Key.name) + self.texCacheExtension

        return CacheFile

    def TexCache_Exists(self):
        if os.path.isfile(self.TexCache_GetFilename()):
            mipmapinfo = self.TexCache_LoadMipMapInfo()

            if not mipmapinfo is None:
                if self.MipMapInfo.equals(mipmapinfo):
#                    print "TEXCACHE DEBUG:"
#                    print "Mipmapinfo's match"
                    return True
#                else:
#                    print "TEXCACHE DEBUG:"
#                    print "Self's mipmapinfo:"
#                    print self.MipMapInfo
#                    print "Cachefile's mipmapinfo:"
#                    print mipmapinfo
#            else:
#                print "TEXCACHE DEBUG:"
#                print "Could not read mipmapinfo from cachefile...."

        return False

    def TexCache_Store(self,mipmapinfo=None):
        CacheFile = self.TexCache_GetFilename()
        stream=hsStream(CacheFile,"wb")

        # Write the version number
        stream.fs.write(bytes(plBitmap.TEXCACHEVER, 'ascii'))

        if mipmapinfo is None:
            self.MipMapInfo.write(stream)
        else:
            mipmapinfo.write(stream)
        # Write the alpha flags
        stream.WriteBool(self.FullAlpha)
        stream.WriteBool(self.OnOffAlpha)
        self.write(stream)
        stream.close()

    def TexCache_LoadVersionInfo(self,stream):
        try:
            versionString = stream.fs.read(4)
            if versionString == bytes(plBitmap.TEXCACHEVER, 'ascii'):
                return True
        except:
            pass
        return False

    def TexCache_LoadMipMapInfo(self):
        # load in the data from the file
        CacheFile = self.TexCache_GetFilename()
        stream=hsStream(CacheFile,"rb")
        try:
            # load the texture cache version first
            if not self.TexCache_LoadVersionInfo(stream):
                return None
            mipmapinfo = blMipMapInfo()
            mipmapinfo.read(stream)
            return mipmapinfo
        except:
            print("    WARNING: Problem reading Texture Cache (in infos)")
            print("             PLEASE REMOVE YOUR OLD TEXTURE CACHE FILES")
            return None


    def TexCache_Load(self):
        # load in the data from the file
        CacheFile = self.TexCache_GetFilename()
        print("     Reading mipmap %s from cache" % (str(self.Key.name) + ".tex"))
        stream=hsStream(CacheFile,"rb")
        try:
            # load the texture cache version first
            if not self.TexCache_LoadVersionInfo(stream):
                raise RuntimeError("Failed to read version info from texcache.")
            self.MipMapInfo.read(stream)
            # Read the alpha flags
            self.FullAlpha = stream.ReadBool()
            self.OnOffAlpha = stream.ReadBool()
            self.read(stream)
        except:
            print("    WARNING: Problem reading Texture Cache (in loading)")
            print("             PLEASE REMOVE YOUR OLD TEXTURE CACHE FILES\nInfos:")
            return None

        stream.close()

    def TexCache_Delete(self):
        CacheFile = self.TexCache_GetFilename()
        return os.remove(CacheFile)



class plMipMap(plBitmap):                    # Type 0x04

    Color = \
    { \
        "kColor8Config" :  0x0, \
        "kGray44Config" :  0x1, \
        "kGray4Config"  :  0x2, \
        "kGray8Config"  :  0x8, \
        "kRGB16Config"  : 0x10, \
        "kRGB32Config"  : 0x18, \
        "kARGB32Config" : 0x20  \
    }

    CreateDetail = \
    { \
        "kCreateDetailAlpha" :  0x1, \
        "kCreateDetailAdd"   :  0x2, \
        "kCreateDetailMult"  :  0x4, \
        "kCreateDetailMask"  :  0x7, \
        "kCreateCarryAlpha"  : 0x10, \
        "kCreateCarryBlack"  : 0x20, \
        "kCreateCarryMask"   : 0x38  \
    }

    hsGPixelType = \
    { \
        "kPixelARGB4444" : 0, \
        "kPixelARGB1555" : 1, \
        "kPixelAI88"     : 2, \
        "kPixelI8"       : 3  \
    }

    hsGCopyOptions = \
    { \
        "kCopyLODMask" : 0 \
    }

    Data = \
    { \
        "kColorDataRLE" : 0x1, \
        "kAlphaDataRLE" : 0x2  \
    }

    CompositeFlags = \
    { \
        "kForceOpaque"      :  0x1, \
        "kCopySrcAlpha"     :  0x2, \
        "kBlendSrcAlpha"    :  0x4, \
        "kMaskSrcAlpha"     :  0x8, \
        "kBlendWriteAlpha"  : 0x10  \
    }

    ScaleFilter = \
    { \
        "kBoxFilter"     : 0, \
        "kDefaultFilter" : 0  \
    }


    def __init__(self,parent,name="unnamed",type=0x0004):
        plBitmap.__init__(self,parent,name,type)

        self.fImages = []
        self.fWidth = 0
        self.fHeight = 0
        self.fRowBytes = 0

        self.fTotalSize = 0
        self.fNumLevels = 0
        self.fLevelSizes = []

        # setting of fields from plBitmap
        self.fPixelSize = 32

        # fields used for internal processing

        self.Processed = 0

        self.Cached_BlenderImage = None
        self.texCacheExtension = ".tex"

    def _Find(page,name):
        return page.find(0x0004,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0004,name,1)
    FindCreate = staticmethod(_FindCreate)

    def read(self, stream, really=1,silent=0):
        plBitmap.read(self,stream,really)

        nread = 0;
        self.fWidth = stream.Read32()
        self.fHeight = stream.Read32()
        self.fRowBytes = stream.Read32()
        self.fTotalSize = stream.Read32()
        self.fNumLevels = stream.ReadByte()


        if self.fTotalSize == 0:
            return

        self.fImages = []

        if self.fCompressionType == plBitmap.Compression["kJPEGCompression"]:
            data=tJpgImage(self.fWidth,self.fHeight)
            data.read(stream)
            self.fImages.append(data)

        elif self.fCompressionType == plBitmap.Compression["kDirectXCompression"]:
            if (self.fNumLevels > 0):
                for i in range(self.fNumLevels):
                    data=tDxtImage(self.fWidth>>i,self.fHeight>>i, self.BitmapInfo.fDirectXInfo.fCompressionType)
                    data.read(stream)
                    self.fImages.append(data)

        elif self.fCompressionType == plBitmap.Compression["kUncompressed"]:
            if (self.fNumLevels > 0):
                for i in range(self.fNumLevels):
                    data=tImage(self.fWidth>>i,self.fHeight>>i)
                    data.read(stream)
                    self.fImages.append(data)
        else:
            return

        return

    def write(self,stream, really=1,silent=0):
        plBitmap.write(self,stream,really)

        self.fRowBytes = int(self.fWidth * (self.fPixelSize / 8.0))

        padding_needed = (4 - (self.fRowBytes % 4) ) # fRowBytes needs to be padded to a multiple of 4

        if (padding_needed > 0 and padding_needed < 4):
            self.fRowbytes = self.fRowBytes + padding_needed

        stream.Write32(self.fWidth)
        stream.Write32(self.fHeight)
        stream.Write32(self.fRowBytes)

        offset_fTotalSize = stream.tell() # store offset of this field
        stream.Write32(self.fTotalSize) # write dummy fTotalSize

        self.fNumLevels=len(self.fImages)
        stream.WriteByte(self.fNumLevels)

        offset_ImageDataStart=stream.tell() # save begin position of image data
        for img in self.fImages: # write all the images
            img.write(stream)
        offset_ImageDataEnd=stream.tell() # save end position of image data


        self.fTotalSize = offset_ImageDataEnd - offset_ImageDataStart # calculate actual size
        stream.seek(offset_fTotalSize) # reposition stream to fTotalSize field
        stream.Write32(self.fTotalSize) # write actual fTotalSize
        stream.seek(offset_ImageDataEnd) # reposition stream to end of object


    def SetConfig(self,Config):
        if Config == plMipMap.Color["kColor8Config"]:
            self.fPixelSize = 8
            self.fSpace = 3
            self.fFlags = plBitmap.Flags["kNoFlag"]

        elif Config == plMipMap.Color["kGray44Config"]:
            self.fPixelSize = 8
            self.fSpace = 2
            self.fFlags = plBitmap.Flags["kAlphaChannelFlag"]

        elif Config == plMipMap.Color["kGray4Config"]:
            self.fPixelSize = 4
            self.fSpace = 2
            self.fFlags = plBitmap.Flags["kNoFlag"]

        elif Config == plMipMap.Color["kGray8Config"]:
            self.fPixelSize = 8
            self.fSpace = 1
            self.fFlags = plBitmap.Flags["kNoFlag"]

        elif Config == plMipMap.Color["kRGB16Config"]:
            self.fPixelSize = 16
            self.fSpace = 1
            self.fFlags = plBitmap.Flags["kAlphaBitFlag"]

        elif Config == plMipMap.Color["kRGB32Config"]:
            self.fPixelSize = 32
            self.fSpace = 1
            self.fFlags = plBitmap.Flags["kNoFlag"]

        elif Config == plMipMap.Color["kARGB32Config"]:
            self.fPixelSize = 32
            self.fSpace = 1
            self.fFlags = plBitmap.Flags["kAlphaChannelFlag"]

    ###################################
    ##                               ##
    ##      Interface Functions      ##
    ##                               ##
    ###################################

    def ToBlenderImage(self):
        # retrieve the image from cache if it's there
        if self.Cached_BlenderImage!=None:
            return self.Cached_BlenderImage

        print("     [MipMap %s]"%str(self.Key.name))

        # Build up a temprary file path and name
        resmanager=self.getResManager()
        BasePath=resmanager.getBasePath()
        TexPath = BasePath + "/TMP_Textures/"

        Name=stripIllegalChars(str(self.Key.name)) + ".png"
        TexFileName = TexPath + "/" + Name

        # create the temporary Texture Path
        try:
            os.mkdir(TexPath)
        except OSError:
            pass

        # get the first image in the list (return None if it isn't there)
        if len(self.fImages)==0:
            return None

        myimg = self.fImages[0]

        # save it to the temporary folder
        myimg.save(TexFileName)

        # and load it again as a blender image
        BlenderImg=bpy.data.images.load(TexFileName)
        BlenderImg.pack()

        # cache it for easy fetching
        self.Cached_BlenderImage=BlenderImg

        return BlenderImg

    def ToBlenderTex(self,name=None):
        print("     [MipMap %s]"%str(self.Key.name))

        if name == None:
            name = str(self.Key.name)

        # Form the Blender cubic env map MTex
        Tex=bpy.data.textures.new(name)
        Tex.setImage(self.ToBlenderImage())
        Tex.type  = "IMAGE"
        Tex.setImageFlags('UseAlpha')

        return Tex

    def FromBlenderImage(self,BlenderImage):
        if(self.Processed):
            return

        print("    [MipMap %s]"%str(self.Key.name))
        print("     MipMapInfo:")
        print(self.MipMapInfo)

        if ((prp_Config.texture_cache) and self.TexCache_Exists()): # unless disabled, check for the texture's cache file
            self.TexCache_Load()
        else:
            # Read in the texture filename from blender (for the name),
            # and convert the texture to an image buffer

            print("     Converting texture %s..." %str(self.Key.name))
            ImWidth, ImHeight = BlenderImage.size
            ImageBuffer=io.BytesIO()

            self.FullAlpha = False
            self.OnOffAlpha = False

            if str(BlenderImage.name)[-4:]==".gif":
                isGIF=1
                print("     Image is GIF Image")
            else:
                isGIF=0

            pix = BlenderImage.pixels[:] # copy the whole array instead of accessing it on the fly. HUUUUUUGE speedup.
            for y in range(ImHeight,0,-1):
                for x in range(ImWidth):
                    r,g,b,a = pix[(x+(y-1)*ImWidth)*4 : (x+(y-1)*ImWidth)*4+4]
                    if self.MipMapInfo.fCalcAlpha:
                        a = (r+g+b)/3.0
                    else:
                        if isGIF: # ignora alpha info, and always put it to opaque
                            a=1.0

                    #print "Color: %f %f %f - Alpha: %f" % (r,g,b,a)
                    
                    # TODO - see if that's required
                    #if a == 0 and not self.FullAlpha:
                    #    self.OnOffAlpha = True
                    #if a > 0.0 and a < 1.0:
                    #    self.OnOffAlpha = False
                    #    self.FullAlpha = True

                    ImageBuffer.write(struct.pack("BBBB",int(r*255),int(g*255),int(b*255),int(a*255)))

            # see if we should automatically determine compression type
            if self.MipMapInfo.fCompressionType == plBitmap.Compression["kDirectXCompression"] and \
                self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kError"]:
                if self.FullAlpha: # Full Alpha requires DXT5
                    print("     Image uses full alpha channel, compressing DXT5")
                    self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kDXT5"]
                elif self.OnOffAlpha: # DXT1 supports On/Off Alpha
                    self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kDXT1"]
                    print("     Image uses on/off alpha , compressing DXT1")
                else: # anything else is ok on the DXT1
                    self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kDXT1"]
                    print("     Image uses no alpha, compressing DXT1")

            # Reset the image buffer
            ImageBuffer.seek(0)

            # And use the FromRawImage function to set this texture data.

            self.FromRawImage(ImageBuffer,ImWidth,ImHeight)

            # now store the data in a file if texture_cache is enabled
            if (prp_Config.texture_cache):
                self.TexCache_Store()

        self.Processed = 1

    def FromRawImage(self, ImageBuffer, Width, Height):

        # Copy basic parameters
        self.fWidth     = Width
        self.fHeight    = Height

        # prepare the image buffer and images field
        ImageBuffer.seek(0)
        self.fImages=[]

        # Resize images to make width and height be powers of two
        # Makes it easier on the graphics card.
        # Don't do this on JPEG compression
        if self.MipMapInfo.fResize and self.MipMapInfo.fCompressionType != plBitmap.Compression["kJPEGCompression"]:

            new_w=2 ** int(math.log(self.fWidth,2))
            new_h=2 ** int(math.log(self.fHeight,2))

            if new_w!=self.fWidth or new_h!=self.fHeight:
                print("      Resizing image from %ix%i to %ix%i" % (self.fWidth,self.fHeight,new_w, new_h))
                im=Image.new("RGBA",(self.fWidth,self.fHeight))
                im.fromstring(ImageBuffer.read())
                im2=im.resize((new_w,new_h),Image.ANTIALIAS)
                ImageBuffer=io.BytesIO()
                ImageBuffer.write(im2.tostring())
                self.fWidth=new_w
                self.fHeight=new_h
            else:
                print("      Image size: %ix%i" % (self.fWidth,self.fHeight))
        else:
            print("      Image size: %ix%i" % (self.fWidth,self.fHeight))

        # Compress the image to the desired compression,
        # either DXT compression, JPEG Compression or Uncompressed (only RGB8888 colorspace supported)

        if (self.MipMapInfo.fCompressionType == plBitmap.Compression["kDirectXCompression"]):
            print("      DXT Compressing texture .... this can take a few minutes")

            if(self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kDXT1"]):
                print("     Compressing DXT1")
            elif(self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kDXT5"]):
                print("     Compressing DXT5")
            elif(self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kError"]):
                print("     Compressing kError")
                raise RuntimeError("Hmm, wait a second, we can't compress \"kError\", you'd better fix this somewhere :P")
            else:
                print("     DXT Compression unknown")
                raise RuntimeError("Okay, don't know what went wrong here... Probably you're a really smart person to be able to get this exception that should never be given....")

            myimg=tDxtImage(self.fWidth,self.fHeight,self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType)
            myimg.data=ImageBuffer  # input the buffer into the image
            print("        [compressing, please wait...]")
            myimg.fromRGBA()        # tell it to process
            print("        [done]")
            self.fImages=[myimg,]
            self.fCompressionType = plBitmap.Compression["kDirectXCompression"]
            self.BitmapInfo.fDirectXInfo.fCompressionType = self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType

            if self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kDXT1"]:
                self.BitmapInfo.fDirectXInfo.fBlockSize = 8
            elif self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kDXT5"]:
                self.BitmapInfo.fDirectXInfo.fBlockSize = 16
            else:
                raise ValueError("Can only support DXT1 and DXT5 Compression")

        elif (self.MipMapInfo.fCompressionType == plBitmap.Compression["kJPEGCompression"]):
            print("     JPEG Compressing texture ....")

            myimg=tJpgImage(self.fWidth,self.fHeight)
            myimg.data=ImageBuffer  # input the buffer into the image
            myimg.fromRGBA()        # tell it to process
            self.fImages=[myimg,]
            self.fCompressionType = plBitmap.Compression["kJPEGCompression"]
            self.BitmapInfo.fUncompressedInfo.fType = plBitmap.Uncompressed["kRGB8888"];

        elif (self.MipMapInfo.fCompressionType == plBitmap.Compression["kUncompressed"]):
            print("     Not Compressing texture")

            myimg=tImage(self.fWidth,self.fHeight)
            myimg.data=ImageBuffer  # input the buffer into the image
            myimg.fromRGBA()        # tell it to process
            self.fImages=[myimg,]
            self.fCompressionType = plBitmap.Compression["kUncompressed"]
            self.BitmapInfo.fUncompressedInfo.fType = plBitmap.Uncompressed["kRGB8888"];


        # Make the mipmaps
        # this works by copying the image that was compressed before, resizing it to half it's size, and
        # adding it to the queue - this repeats until the lowest texture...
        # ofcourse, no mipmapping for jpeg uncompressed textures :)

        if self.MipMapInfo.fCompressionType != plBitmap.Compression["kJPEGCompression"] and self.MipMapInfo.fMipMaps:
            print("     MipMapping....")
#            print "     MipMapinfo:\n",self.MipMapInfo

            print("      Level 0 %ix%i" %(self.fWidth,self.fHeight))
            i=1
            mw=self.fWidth>>i
            mh=self.fHeight>>i
            while mw!=0 and mh!=0:
                print("      Level %i %ix%i" %(i,mw,mh))
                img=copy.copy(myimg)    # copy the previous image
                img.resize_alphamult(mw,mh,self.MipMapInfo.fAlphaMult,self.MipMapInfo.fGauss)       # apply the new size

                img.fromRGBA()          # and reprocess/recompress
                self.fImages.append(img) # add to the list
                myimg=img
                i=i+1
                mw=self.fWidth>>i
                mh=self.fHeight>>i

        print("Done")

    def _FindCreateByMipMapInfo(page,name,mipmapinfo,exportTexturesToPrp):
        resmgr = page.resmanager
        tex=resmgr.findPrp("Textures")
        if not exportTexturesToPrp:
            page=tex
            if page==None:
                raise RuntimeError("    Textures PRP file not found")

        try:
            if not page.age.specialtex.index(name) is -1:
                page = tex
                if page==None:
                    raise RuntimeError("    Textures PRP file not found")
        except ValueError:
            pass

#        print "Locating mipmap for mipmapinfo:"
#        print mipmapinfo
        # See if we have already got one of these....
        idx = page.findidx(0x0004)
        for plobj in idx.listobjects():
#            print "-- MIPMAP:",plobj.data.Key.name
#            print "   MipmapInfo:"
#            print plobj.data.MipMapInfo

            if plobj.data.MipMapInfo.equals(mipmapinfo):
                return plobj

        # else, create one

        # make sure we have a unique name....
        names = [plobj.data.Key.name for plobj in idx.listobjects()]
        namebase = name
        uniquePrefix = 1
        while name in names:
            name = str(uniquePrefix) + "-" + namebase
            uniquePrefix += 1

        plobj = plMipMap.FindCreate(page,name)
        plobj.data.MipMapInfo = mipmapinfo

        return plobj


    FindCreateByMipMapInfo = staticmethod(_FindCreateByMipMapInfo)

    def _Export(page,name,blenderimage,mipmapinfo,exportTexturesToPrp):
        mipmap = plMipMap.FindCreateByMipMapInfo(page,name,mipmapinfo,exportTexturesToPrp)
        mipmap.data.SetConfig(plMipMap.Color["kARGB32Config"])
        mipmap.data.FromBlenderImage(blenderimage)
        return mipmap

    Export = staticmethod(_Export)

    def _Export_Raw(page,name,imbuffer, imwidth, imheight, mipmapinfo,exportTexturesToPrp):
        mipmap = plMipMap.FindCreateByMipMapInfo(page,name,mipmapinfo,exportTexturesToPrp)
        mipmap.data.SetConfig(plMipMap.Color["kARGB32Config"])
        mipmap.data.FromRawImage(imbuffer,imwidth,imheight)
        return mipmap

    Export_Raw = staticmethod(_Export_Raw)

class plCubicEnvironMap(plBitmap):          # Type 0x05

    Faces = {
        "kLeftFace"     : 0,
        "kRightFace"    : 1,
        "kFrontFace"    : 2,
        "kBackFace"     : 3,
        "kTopFace"      : 4,
        "kBottomFace"   : 5
    }

    def __init__(self,parent,name="unnamed",type=0x0005):
        plBitmap.__init__(self,parent,name,type)
        self.fFaces = []

        self.Processed = 0

        self.Cached_BlenderCubicMap = None
        self.texCacheExtension = ".qmap"

    def _Find(page,name):
        return page.find(0x0005,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0005,name,1)
    FindCreate = staticmethod(_FindCreate)


    def read(self, stream):
        plBitmap.read(self,stream);

        self.fFaces = []
        for i in range(6):
            mipmap = plMipMap(self.parent)
            mipmap.read(stream,0) # "Really" is set to 0, to avoid reading hsKeyedObject code
            self.fFaces.append(mipmap)

    def write(self, stream):
        plBitmap.write(self,stream);

        for i in range(6):
            self.fFaces[i].write(stream,0) # "Really" is set to 0, to avoid writing hsKeyedObject code

    ###################################
    ##                               ##
    ##      Interface Functions      ##
    ##                               ##
    ###################################

    def ToBlenderCubicMap(self):
        # retrieve the image from cache if it's there
        if self.Cached_BlenderCubicMap==None:
            print("     [CubicEnvMap %s]"%str(self.Key.name))

            # Build up a temprary file path and name
            resmanager=self.getResManager()
            BasePath=resmanager.getBasePath()
            TexPath = BasePath + "/TMP_Textures/"

            Name=stripIllegalChars(str(self.Key.name)) + ".png"
            TexFileName = TexPath + "/" + Name
            TexFileName = TexFileName.replace("*","_") # strip out unwanted characters


            # Convert images to Blender images for easy processing
            RawImages = []
            for i in (0,3,1,5,4,2):
                rawimg = self.fFaces[i].ToBlenderImage()
                RawImages.append(rawimg)

            # Stitch together 6 images
            xpart,ypart, = RawImages[0].getSize()
            print("      Size of maps: %i x %i" % (xpart,ypart))

            width = xpart*3
            height = ypart*2

            CookedImage = Image.new("RGBA",(width,height))

            try:

                ImageBuffer=io.BytesIO()
                # Copy bottom three images
                for y in range(ypart-1,-1,-1):
                    for i in range(0,3):
                        for x in range(0,xpart):
                            try:
                                r,g,b,a = RawImages[i].getPixelF(x,y)
                                ImageBuffer.write(struct.pack("BBBB",r*255,g*255,b*255,a*255))
                            except Exception as detail:
                                print("      Now in image # %i"% i)
                                print("      Size of image:",RawImages[i].getSize())
                                print("      Value of X and Y: %i, %i" % (x,y))
                                raise Exception(detail)

                # Copy top three images
                for y in range(ypart-1,-1,-1):
                    for i in range(3,6):
                        for x in range(0,xpart):
                            try:
                                r,g,b,a = RawImages[i].getPixelF(x,y)
                                ImageBuffer.write(struct.pack("BBBB",r*255,g*255,b*255,a*255))
                            except Exception as detail:
                                print("      Now in image # %i"% i)
                                print("      Size of image:",RawImages[i].getSize())
                                print("      Value of X and Y: %i, %i" % (x,y))
                                raise Exception(detail)

                # Transfer buffer to image
                ImageBuffer.seek(0)

                CookedImage.fromstring(ImageBuffer.read())

            except Exception as detail:
                print("      Exception:",detail)
                print("      Continuing")

            # And save the image...
            CookedImage.save(TexFileName)

            # Load it back in to process in blender
            self.Cached_BlenderCubicMap = bpy.data.images.load(TexFileName)

        return self.Cached_BlenderCubicMap

    def FromBlenderCubicMap(self,cubicmap):
        # if we are already set up and ready, don't continue....
        if(self.Processed):
            return

        if ((prp_Config.texture_cache) and self.TexCache_Exists()): # unless disabled, check for the texture's cache file
            self.TexCache_Load()
        else:

            print(" => Converting CubicEnvironMap %s <=" %str(self.Key.name))

            # first calculate the size of the 6 parts

            width, height = cubicmap.getSize()

            xpart = width / 3
            ypart = height / 2


            # Now parse those 6 parts one by one

            CubeSide = 0 # just there to count up from 0-5 even in a weird order

            for i in (0,2,5,1,4,3): # for correct conversion from blender to uru sequence we need this sequence
                if(i == 0):
                    ystart = height
                    yend = height - ypart
                    xstart = 0
                    xend = 0 + xpart
                elif(i == 1):
                    ystart = height
                    yend = height - ypart
                    xstart = xpart
                    xend = 0 + 2*xpart
                elif(i == 2):
                    ystart = height
                    yend = height - ypart
                    xstart = 2*xpart
                    xend = width
                elif(i == 3):
                    ystart = ypart
                    yend = 0
                    xstart = 0
                    xend = 0 + xpart
                elif(i == 4):
                    ystart = ypart
                    yend = 0
                    xstart = xpart
                    xend = 0 + 2*xpart
                elif(i == 5):
                    ystart = ypart
                    yend = 0
                    xstart = 2*xpart
                    xend = width

                ImageBuffer=io.BytesIO()
                self.FullAlpha = False
                self.OnOffAlpha = True

                if str(cubicmap.getFilename())[-4:]==".gif":
                    isGIF=1
                else:
                    isGIF=0
                for y in range(ystart,yend,-1):
                    for x in range(xstart,xend):
                        r,g,b,a = cubicmap.getPixelF(x,y-1)

                        if self.MipMapInfo.fCalcAlpha:
                            a = (r+g+b)/3
                        else:
                            if isGIF: # ignora alpha info, and always put it to opaque
                                a=1.0

                        if a == 0 and not self.FullAlpha:
                            self.OnOffAlpha = True
                        if a > 0 and a < 1:
                            OnOffAlpha = False
                            self.FullAlpha = True

                        ImageBuffer.write(struct.pack("BBBB",r*255,g*255,b*255,a*255))

                # see if we should automatically determine compression type
                if self.MipMapInfo.fCompressionType == plBitmap.Compression["kDirectXCompression"] and \
                    self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType == plBitmap.CompressionType["kError"]:
                    if self.FullAlpha: # Full Alpha requires DXT5
                        print("     Image uses full alpha channel, compressing DXT5")
                        self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kDXT5"]
                    elif self.OnOffAlpha: # DXT1 supports On/Off Alpha
                        self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kDXT1"]
                        print("     Image uses on/off alpha , compressing DXT1")
                    else: # anything else is ok on the DXT1
                        self.MipMapInfo.fBitmapInfo.fDirectXInfo.fCompressionType = plBitmap.CompressionType["kDXT1"]
                        print("     Image uses no alpha, compressing DXT1")

                print(" Setting EnvMap side %i" % CubeSide)
                CubeSide += 1

                # prepare a MipMap object
                MipMappedFace = plMipMap(self.parent)
                MipMappedFace.Key.name = str(self.Key.name) + "+%i"%(i)

                MipMappedFace.MipMapInfo = self.MipMapInfo
                # assign the texture
                MipMappedFace.FromRawImage(ImageBuffer,xpart,ypart)

                self.fFaces.append(MipMappedFace)

            # copy the plBitmap fields from the first face onto this object
            self.fSpace = self.fFaces[0].fSpace
            self.fFlags = self.fFaces[0].fFlags

            self.fCompressionType = self.fFaces[0].fCompressionType
            self.BitmapInfo.fDirectXInfo.fCompressionType = self.fFaces[0].BitmapInfo.fDirectXInfo.fCompressionType
            self.BitmapInfo.fDirectXInfo.fBlockSize = self.fFaces[0].BitmapInfo.fDirectXInfo.fBlockSize
            self.BitmapInfo.fUncompressedInfo.fType = self.fFaces[0].BitmapInfo.fUncompressedInfo.fType

            # now store the data in a file if texture_cache is enabled
            if (prp_Config.texture_cache):
                self.TexCache_Store()

        # now set that we processed it all
        self.Processed = 1


    def _Export(page,name,image,mipmapinfo,exportTexturesToPrp):
        resmgr = page.resmanager
        if not exportTexturesToPrp:
            page=resmgr.findPrp("Textures")
            if page==None:
                raise RuntimeError("    Textures PRP file not found")

        qmap=plCubicEnvironMap.FindCreate(page,name)
        qmap.data.MipMapInfo = mipmapinfo

        qmap.data.FromBlenderCubicMap(image)

        return qmap

    Export = staticmethod(_Export)

class plLayerAnimationBase(plLayerInterface):
    def __init__(self,parent,name="unnamed",type=0x00EF):
        plLayerInterface.__init__(self,parent,name,type)

        self.fEvalTime = -1.0
        self.fCurrentTime = -1.0
        self.fSegmentID = None
        self.fPreshadeColorCtl = None
        self.fRuntimeColorCtl = None
        self.fAmbientColorCtl = None
        self.fSpecularColorCtl = None
        self.fOpacityCtl = None
        self.fTransformCtl = None

    def _Find(page,name):
        return page.find(0x00EF,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x00EF,name,1)
    FindCreate = staticmethod(_FindCreate)

    def read(self, stream, size):
        plLayerInterface.read(self,stream)
        self.fPreshadeColorCtl = prp_AnimClasses.PrpController(stream.Read16(), self.getVersion())
        self.fPreshadeColorCtl.read(stream)
        self.fRuntimeColorCtl = prp_AnimClasses.PrpController(stream.Read16(), self.getVersion())
        self.fRuntimeColorCtl.read(stream)
        self.fAmbientColorCtl = prp_AnimClasses.PrpController(stream.Read16(), self.getVersion())
        self.fAmbientColorCtl.read(stream)
        self.fSpecularColorCtl = prp_AnimClasses.PrpController(stream.Read16(), self.getVersion())
        self.fSpecularColorCtl.read(stream)
        self.fOpacityCtl = prp_AnimClasses.PrpController(stream.Read16(), self.getVersion())
        self.fOpacityCtl.read(stream)
        self.fTransformCtl = prp_AnimClasses.PrpController(stream.Read16(), self.getVersion())
        self.fTransformCtl.read(stream)

    def write(self, stream):
        plLayerInterface.write(self,stream)
        self.fPreshadeColorCtl.write(stream)
        self.fRuntimeColorCtl.write(stream)
        self.fAmbientColorCtl.write(stream)
        self.fSpecularColorCtl.write(stream)
        self.fOpacityCtl.write(stream)
        self.fTransformCtl.write(stream)

class plLayerAnimation(plLayerAnimationBase):
    def __init__(self,parent=None,name="unnamed",type=0x0043):
        plLayerAnimationBase.__init__(self,parent,name,type)
        self.fTimeConvert = None

    def _Find(page,name):
        return page.find(0x0043,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0043,name,1)
    FindCreate = staticmethod(_FindCreate)

    def read(self, stream, size):
        start = stream.tell() # Keep start offset in case of trouble...
        try:
            plLayerAnimationBase.read(self, stream, size)
            if self.fTimeConvert == None:
                self.fTimeConvert = prp_AnimClasses.plAnimTimeConvert()
            self.fTimeConvert.read(stream)
        except:
            print("/---------------------------------------------------------")
            print("|  WARNING:")
            print("|   Could not read in portion of plLayerAnimation.")
            print("|   -> Skipping %i bytes ahead " % ( (start + size) - stream.tell()))
            print("|   -> Total object size: %i bytes"% (size))
            print("\---------------------------------------------------------\n")
            stream.seek(start + size) #skip to the end

    def write(self, stream):
        plLayerAnimationBase.write(self, stream)
        self.fTimeConvert.write(stream)

    def FromBlender(self,obj,mat,mtex,chan = 0):
        print("   [LayerAnimation %s]"%(str(self.Key.name)))
        # We have to grab the animation stuff here...
        ipo = mat.animation_data
        #ipo.channel = chan
        endFrame = 0
        frameRate = bpy.context.scene.render.fps
        
        MA_R = MA_G = MA_B = MA_COL = MA_OFSX = MA_OFSY = MA_SIZEX = MA_SIZEY = None
        
        for curve in ipo.action.fcurves:
            path = curve.data_path
            if path.find("[") != -1:
                whatAnimated = path[:path.find("[")]
                if whatAnimated == "texture_slots":
                    layerAnimated = int(path[   path.find("[")+1 : path.find("].")  ])
                    paramAnimated = path[path.find("].")+2:]
                    if layerAnimated == chan:
                        if paramAnimated == "offset":
                            if curve.array_index == 0:
                                MA_OFSX = curve
                            elif curve.array_index == 1:
                                MA_OFSY = curve
                        elif paramAnimated == "scale":
                            if curve.array_index == 0:
                                MA_SIZEX = curve
                            elif curve.array_index == 1:
                                MA_SIZEY = curve
            else:
                if path == "diffuse_color":
                    if curve.array_index == 0:
                        MA_R = curve
                    elif curve.array_index == 1:
                        MA_G = curve
                    elif curve.array_index == 2:
                        MA_B = curve
                elif path == "alpha":
                    MA_COL = curve

        # both offsets and scales
        if (MA_OFSX and MA_OFSY and
            MA_SIZEX and MA_SIZEY and
            (len(MA_OFSX.keyframe_points) == len(MA_SIZEX.keyframe_points))):

            KeyList = []

            # We need to get the list of BezCurves
            # Then get the value for each and create a matrix
            # Then store that in a frame and store that in the list
            xcurve = MA_OFSX.keyframe_points
            for frm in range(len(xcurve)):
                frame = prp_AnimClasses.hsMatrix44Key()
                num = xcurve[frm].co[0] * 30 / frameRate
                frame.fFrameNum = int(num)
                frame.fFrameTime = num/30.0
                
               # map dynamic offsets for Plasma
                ofsX = 0.5 - 0.5 * MA_SIZEX.keyframe_points[frm].co[1] + xcurve[frm].co[1]
                ofsY = 0.5 - 0.5 * MA_SIZEY.keyframe_points[frm].co[1] - MA_OFSY.keyframe_points[frm].co[1]

                matx = hsMatrix44()
                matx.translate((ofsX, ofsY, 0.0))
                
                # use dynamic scale
                matx.scale(MA_SIZEX.keyframe_points[frm].co[1], MA_SIZEY.keyframe_points[frm].co[1], 1.0)

                frame.fValue = matx
                KeyList.append(frame)

            self.fTransformCtl = prp_AnimClasses.PrpController(0x0234, self.getVersion()) #plMatrix44Controller
            self.fTransformCtl.data.fKeys = KeyList
            if xcurve[-1].co[0] > endFrame:
                endFrame = xcurve[-1].co[0]
        # just offsets
        elif MA_OFSX and MA_OFSY:
            KeyList = []

            # We need to get the list of BezCurves
            # Then get the value for each and create a matrix
            # Then store that in a frame and store that in the list
            xcurve = MA_OFSX.keyframe_points
            for frm in range(len(xcurve)):
                frame = prp_AnimClasses.hsMatrix44Key()
                num = xcurve[frm].co[0] * 30 / frameRate
                frame.fFrameNum = int(num)
                frame.fFrameTime = num/30.0
                
               # map dynamic offsets for Plasma
                ofsX = 0.5 - 0.5 * mtex.scale[0] + xcurve[frm].co[1]
                ofsY = 0.5 - 0.5 * mtex.scale[1] - MA_OFSY.keyframe_points[frm].co[1]

                matx = hsMatrix44()
                matx.translate((ofsX, ofsY, 0))
                
                # use static scale
                matx.scale(mtex.scale[0], mtex.scale[1], 1.0)

                frame.fValue = matx
                KeyList.append(frame)

            self.fTransformCtl = prp_AnimClasses.PrpController(0x0234, self.getVersion()) #plMatrix44Controller
            self.fTransformCtl.data.fKeys = KeyList
            if xcurve[-1].co[0] > endFrame:
                endFrame = xcurve[-1].co[0]
        # just scales
        elif MA_SIZEX and MA_SIZEY:
            KeyList = []

            # We need to get the list of BezCurves
            # Then get the value for each and create a matrix
            # Then store that in a frame and store that in the list
            xcurve = MA_SIZEX.keyframe_points
            for frm in range(len(xcurve)):
                frame = prp_AnimClasses.hsMatrix44Key()
                num = xcurve[frm].co[0] * 30 / frameRate
                frame.fFrameNum = int(num)
                frame.fFrameTime = num/30.0
                
                # map static offsets *dynamically* for Plasma
                ofsX = 0.5 - 0.5 * xcurve[frm].co[1] + mtex.offset[0]
                ofsY = 0.5 - 0.5 * MA_SIZEY.keyframe_points[frm].co[1] - mtex.offset[1]

                matx = hsMatrix44()
                matx.translate((ofsX, ofsY, 1.0))
                
                # use dynamic scales
                matx.scale(xcurve[frm].co[1], MA_SIZEY.keyframe_points[frm].co[1], 1.0)

                frame.fValue = matx
                KeyList.append(frame)

            self.fTransformCtl = prp_AnimClasses.PrpController(0x0234, self.getVersion()) #plMatrix44Controller
            self.fTransformCtl.data.fKeys = KeyList
            if xcurve[-1].co[0] > endFrame:
                endFrame = xcurve[-1].co[0]
        else:
            self.fTransformCtl = prp_AnimClasses.PrpController(0x8000, self.getVersion())

        if MA_COL:
            curve = MA_COL
            self.fOpacityCtl = prp_AnimClasses.PrpController(0x022F, self.getVersion()) #plScalarController
            endFrame = self.fOpacityCtl.data.export_curve(curve, endFrame, 0, 100)
        else:
            self.fOpacityCtl = prp_AnimClasses.PrpController(0x8000, self.getVersion())

        if MA_R or MA_G or MA_B:
            # if the material color is animated, then we change the colors that control sets (preshade and runtime)
            compoundController = prp_AnimClasses.PrpController(0x023A, self.getVersion()) #plCompoundPosController
            if MA_R:
                curve = MA_R
                controller = prp_AnimClasses.plScalarController()
                endFrame = controller.export_curve(curve, endFrame)
                compoundController.data.fXController = controller
            if MA_G:
                curve = MA_G
                controller = prp_AnimClasses.plScalarController()
                endFrame = controller.export_curve(curve, endFrame)
                compoundController.data.fYController = controller
            if MA_B:
                curve = MA_B
                controller = prp_AnimClasses.plScalarController()
                endFrame = controller.export_curve(curve, endFrame)
                compoundController.data.fZController = controller
            self.fRuntimeColorCtl = compoundController
            ambfactor = mat.ambient
            # this should have it's curves multiplied by ambfactor. I'm lazy right now
            self.fPreshadeColorCtl = compoundController
        else:
            self.fPreshadeColorCtl = prp_AnimClasses.PrpController(0x8000, self.getVersion())
            self.fRuntimeColorCtl = prp_AnimClasses.PrpController(0x8000, self.getVersion())

        ##MAJOR HACK HERE
        self.fAmbientColorCtl = prp_AnimClasses.PrpController(0x8000, self.getVersion())
        self.fSpecularColorCtl = prp_AnimClasses.PrpController(0x8000, self.getVersion())

        self.fTimeConvert = prp_AnimClasses.plAnimTimeConvert()
        self.fTimeConvert.fBegin = 0.0
        self.fTimeConvert.fLoopBegin = 0.0
        self.fTimeConvert.fEnd = (endFrame) / frameRate
        self.fTimeConvert.fLoopEnd = (endFrame) / frameRate
        self.fTimeConvert.export_obj(obj,mat,mtex,chan)

        self.fSynchFlags |= plSynchedObject.Flags["kExcludePersistentState"]
        self.fSDLExcludeList.append("Layer")

    def ToBlenderMTex(self,mtex,obj):
        print("     [Layer %s]"%(str(self.Key.name)))
        # TODO: Implement this to set mtex.colfac, mtex.neg and obj.data.mode
        print("        WARNING: Layer animation settings have not been")
        print("        converted into Blender texture settings!")


class plRenderTarget(plBitmap):
    class Proportional:
        def __init__(self):
            self.fLeft = 0.0
            self.fTop = 0.0
            self.fRight = 1.0
            self.fBottom = 1.0

    class Absolute:
        def __init__(self):
            self.fLeft = 0
            self.fTop = 0
            self.fRight = 256
            self.fBottom = 256

    class Viewport:
        def __init__(self):
            self.fProportional = plRenderTarget.Proportional()
            self.fAbsolute = plRenderTarget.Absolute()

    def __init__(self,parent=None,name="unnamed",type=0x000D):
        plBitmap.__init__(self, parent, name, type)
        self.fViewport = plRenderTarget.Viewport()
        self.fWidth = 256
        self.fHeight = 256
        self.fPixelSize = 0
        self.fZDepth = 24
        self.fStencilDepth = 0
        self.fApplyTexQuality = 0
        self.fProportionalViewport = 0
        self.fViewport.fAbsolute.fLeft = 0
        self.fViewport.fAbsolute.fTop = 0
        self.fViewport.fAbsolute.fRight = 256
        self.fViewport.fAbsolute.fBottom = 256
        self.fFlags = 0
        self.fParent = None
        # bitmap defaults
        self.fCompressionType = 0
        self.fPixelSize = 32
        self.fSpace = 0
        self.fFlags |= plBitmap.Flags["kIsTexture"]

    def _Find(page,name):
        return page.find(0x000D,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x000D,name,1)
    FindCreate = staticmethod(_FindCreate)

    def read(self, stream):
        # this reads an unKeyedObject >.>
        nRead = plBitmap.read(self, stream, 0)
        self.fWidth = stream.Read16()
        self.fHeight = stream.Read16()
        self.fProportionalViewport = stream.ReadBool()
        if(self.fProportionalViewport):
            sSize = 4
            self.fViewport.fProportional.fLeft = stream.ReadFloat()
            self.fViewport.fProportional.fTop = stream.ReadFloat()
            self.fViewport.fProportional.fRight = stream.ReadFloat()
            self.fViewport.fProportional.fBottom = stream.ReadFloat()
        else:
            sSize = 2
            self.fViewport.fAbsolute.fLeft = stream.Read16()
            self.fViewport.fAbsolute.fTop = stream.Read16()
            self.fViewport.fAbsolute.fRight = stream.Read16()
            self.fViewport.fAbsolute.fBottom = stream.Read16()
        self.fZDepth = stream.ReadByte()
        self.fStencilDepth = stream.ReadByte()
        return (nRead + 10 + 4 * sSize)

    def write(self, stream):
        nWrote = plBitmap.write(self, stream, 0)
        stream.Write16(self.fWidth)
        stream.Write16(self.fHeight)
        stream.WriteBool(self.fProportionalViewport)
        if(self.fProportionalViewport):
            sSize = 4
            stream.WriteFloat(self.fViewport.fProportional.fLeft)
            stream.WriteFloat(self.fViewport.fProportional.fTop)
            stream.WriteFloat(self.fViewport.fProportional.fRight)
            stream.WriteFloat(self.fViewport.fProportional.fBottom)
        else:
            sSize = 2
            stream.Write16(self.fViewport.fAbsolute.fLeft)
            stream.Write16(self.fViewport.fAbsolute.fTop)
            stream.Write16(self.fViewport.fAbsolute.fRight)
            stream.Write16(self.fViewport.fAbsolute.fBottom)
        stream.WriteByte(self.fZDepth)
        stream.WriteByte(self.fStencilDepth)
        return (nWrote + 10 + 4 * sSize)


class plCubicRenderTarget(plRenderTarget):
    def __init__(self,parent=None,name="unnamed",type=0x000E):
        plRenderTarget.__init__(self, parent, name, type)
        self.fFaces = list(range(6))
        self.fFaces[0] = plRenderTarget(parent, "")
        self.fFaces[1] = plRenderTarget(parent, "")
        self.fFaces[2] = plRenderTarget(parent, "")
        self.fFaces[3] = plRenderTarget(parent, "")
        self.fFaces[4] = plRenderTarget(parent, "")
        self.fFaces[5] = plRenderTarget(parent, "")

    def _Find(page,name):
        return page.find(0x000E,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x000E,name,1)
    FindCreate = staticmethod(_FindCreate)

    def read(self, stream):
        nRead = plRenderTarget.read(self, stream)
        for i in range(6):
            self.fFaces[i] = plRenderTarget()
            self.fFaces[i].fParent = self
            nRead += self.fFaces[i].read(stream)
        return nRead

    def write(self, stream):
        nWrote = plRenderTarget.write(self, stream)
        for i in range(6):
            nWrote += self.fFaces[i].write(stream)
        return nWrote

class plDynamicEnvMap(plCubicRenderTarget):
    def __init__(self,parent=None,name="unnamed",type=0x0106):
        plCubicRenderTarget.__init__(self, parent, name, type)
        self.fPos = Vertex()
        self.fHither = 0.3
        self.fYon = 10000
        self.fFogStart = -1
        self.fColor = RGBA(1.0,1.0,1.0,1.0,type=1)
        self.fRefreshRate = 0
        self.fVisRegions = hsTArray([], self.getVersion())
        self.fIncCharacters = 0

    def _Find(page,name):
        return page.find(0x0106,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0106,name,1)
    FindCreate = staticmethod(_FindCreate)

    def export_obj(self, obj):
        objscript = AlcScript.objects.Find(obj.name)
        # dynenv props
        self.fHither = FindInDict(objscript,'dynenv.hither',0.3)
        self.fYon = FindInDict(objscript,'dynenv.yon',10000)
        self.fIncCharacters = FindInDict(objscript,'dynenv.inccharacters',0)
        self.fPos = Vertex(*obj.location) # TODO - see about getting worldspace location
        self.fRefreshRate = FindInDict(objscript,'dynenv.refreshrate',0.)
        # rendertarget props
        self.fWidth = FindInDict(objscript,'dynenv.width',256)
        self.fHeight = FindInDict(objscript,'dynenv.height',256)
        self.fViewport.fAbsolute.fRight = self.fWidth
        self.fViewport.fAbsolute.fBottom = self.fHeight

    def read(self, stream):
        # fun hack, this would be a call to the void write of plBitmap,
        # which writes it with the keyedObject index. When renderTarget calls
        # plBitmap.write this is not written.
        hsKeyedObject.read(self,stream)
        plCubicRenderTarget.read(self, stream)
        self.fPos.read(stream)
        self.fHither = stream.ReadFloat()
        self.fYon = stream.ReadFloat()
        self.fFogStart = stream.ReadFloat()
        self.fColor.read(stream)
        self.fRefreshRate = stream.ReadFloat()
        self.fIncCharacters = stream.ReadByte()
        self.fVisRegions.read(stream)

    def write(self, stream):
        hsKeyedObject.write(self,stream)
        plCubicRenderTarget.write(self, stream)
        self.fPos.write(stream)
        stream.WriteFloat(self.fHither)
        stream.WriteFloat(self.fYon)
        stream.WriteFloat(self.fFogStart)
        self.fColor.write(stream)
        stream.WriteFloat(self.fRefreshRate)
        stream.WriteByte(self.fIncCharacters)
        self.fVisRegions.write(stream)

class plDynamicTextMap(plMipMap):
    def __init__(self,parent=None,name="unnamed",type=0x00AD):
        plMipMap.__init__(self,parent,name,type)
        self.fVisWidth = 512;
        self.fVisHeight = 512;
        self.fHasAlpha = False;
    
    def _Find(page,name):
        return page.find(0x00AD,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x00AD,name,1)
    FindCreate = staticmethod(_FindCreate)
    
    def read(self, stream, really=1):
        plBitmap.read(self,stream,really)
        
        self.fVisWidth = stream.Read32()
        self.fVisHeight = stream.Read32()
        self.fHasAlpha = stream.ReadBool()
        
        count = stream.Read32()
        stream.Read(count)
    
    def write(self,stream,really=1):
        plBitmap.write(self,stream,really)
        
        stream.Write32(self.fVisWidth)
        stream.Write32(self.fVisHeight)
        stream.WriteBool(self.fHasAlpha)
        
        stream.Write32(0) #DO NOT HANDLE THE INSANITY!
    
    def export_obj(self, obj):
        self.fCompressionType = 0
        self.BitmapInfo.fUncompressedInfo.fType = 0
        self.fFlags = 0x11

#############################################################
# Begin waveset stuff. This likely belongs in DrawClasses.  #
# Howver, it is also likely that no one will move it there, #
# and so it will rest here in MatClasses for all eternity.  #
#############################################################


class plWaveSet7(plMultiModifier):
    fFlags = \
    { \
        "kHasRefObject" : 0x10\
    }

    def __init__(self,parent,name="unnamed",type=0x00FB):
        plMultiModifier.__init__(self,parent,name,type)
        self.fState = plFixedWaterState7()
        self.fMaxLen = 0.0

        self.fShores = hsTArray([], self.getVersion())
        self.fDecals = hsTArray([], self.getVersion())

        self.fEnvMap = UruObjectRef(self.getVersion())
        self.fRefObj = UruObjectRef(self.getVersion())

    def _Export(page, obj, scnobj, name):
        # create waveset
        waveset = plWaveSet7.FindCreate(page, name)
        waveset.data.export_obj(obj)
        # attach to sceneobject
        scnobj.data.addModifier(waveset)
    Export = staticmethod(_Export)

    def export_obj(self, obj):
        # now we get all the values. >.<
        objscript = AlcScript.objects.Find(obj.name)
        refparser = ScriptRefParser(self.getRoot(),str(self.Key.name), 0x0001, [0x0001,])

        # add shore refs
        shoreNames = list(FindInDict(objscript, 'visual.waveset.shores', []))
        for shoreName in shoreNames:
            shoreObj = refparser.MixedRef_FindCreate(shoreName)
            print("WaveSet Shore Ref: " + shoreName)
            self.fShores.append(shoreObj.data.getRef())
        # add decal refs
        decalNames = list(FindInDict(objscript, 'visual.waveset.decals', []))
        for decalName in decalNames:
            decalObj = refparser.MixedRef_FindCreate(decalName)
            self.fDecals.append(decalObj.data.getRef())
        # allow ref to alternate envmap
        altEnv = FindInDict(objscript, 'visual.waveset.envmap', None)
        if(altEnv != None):
            # refparser time
            resmgr = self.getRoot().resmanager
            refparser = ScriptRefParser(resmgr.findPrp("Textures"), str(self.Key.name), 0x0106, [0x0106])
            envmap = refparser.MixedRef_FindCreate(altEnv, False)
            if envmap == None:
                raise RuntimeError("Cannot find envmap " + altEnv + " for your waveset.")
        else:
            # make a dummy dyanmic envmap for the waveset
            envmap = plDynamicEnvMap.FindCreate(self.getRoot(),obj.name)
            envmap.data.export_obj(obj)
        self.fEnvMap = envmap.data.getRef()
        # now we create a default waveset
        self.fMaxLen = FindInDict(objscript,'visual.waveset.maxlen',0.0)
        texstate = self.fState.fTexState
        texstate.fMaxLength = FindInDict(objscript,'visual.waveset.texstate.maxlen',6.25)
        texstate.fMinLength = FindInDict(objscript,'visual.waveset.texstate.minlen',0.78125)
        texstate.fAmpOverLen = FindInDict(objscript,'visual.waveset.texstate.ampoverlen',0.013)
        texstate.fChop = FindInDict(objscript,'visual.waveset.texstate.chop',0.5)
        texstate.fAngleDev = FindInDict(objscript,'visual.waveset.texstate.angledev',1.00356)
        
        # Use some defaults for the geostate so users with ancient hardware can see something
        geostate = self.fState.fGeoState
        geostate.fMaxLength = FindInDict(objscript,'visual.waveset.geostate.maxlen',texstate.fMaxLength)
        geostate.fMinLength = FindInDict(objscript,'visual.waveset.geostate.minlen',texstate.fMinLength)
        geostate.fAmpOverLen = FindInDict(objscript,'visual.waveset.geostate.ampoverlen',texstate.fAmpOverLen/10)
        geostate.fChop = FindInDict(objscript,'visual.waveset.geostate.chop',0.0)
        geostate.fAngleDev = FindInDict(objscript,'visual.waveset.geostate.angledev',texstate.fAngleDev)
        
        self.fState.fRippleScale = FindInDict(objscript,'visual.waveset.ripplescale',100)
        windObj = FindInDict(objscript,'visual.waveset.winddir', None)
        windSpeed = FindInDict(objscript,'visual.waveset.windspeed', 1.0)
        if windObj:
            windMat = bpy.data.objects[windObj].matrix_basis
            # now we make the wind direction the y axis of the empty, times windspeed
            windX = windMat[1][0] * windSpeed
            windY = windMat[1][1] * windSpeed
            windZ = windMat[1][2] * windSpeed
            self.fState.fWindDir = Vertex(windX, windY, windZ)
        else:
            self.fState.fWindDir = Vertex(0.0871562,0.996195,0)
        # expects list [noise, start, end]
        specnoise = FindInDict(objscript,'visual.waveset.specnoise',0.5)
        specstart = FindInDict(objscript,'visual.waveset.specstart',250)
        specend = FindInDict(objscript, 'visual.waveset.specend', 1000)
        self.fState.fSpecVec = Vertex(specnoise,specstart,specend)
        self.fState.fWaterHeight = obj.location[2]
        opac = FindInDict(objscript,'visual.waveset.depthrange.opac.start',0)
        refl = FindInDict(objscript,'visual.waveset.depthrange.refl.start',0)
        wave = FindInDict(objscript,'visual.waveset.depthrange.wave.start',0)
        self.fState.fWaterOffset = Vertex(opac, refl, wave)
        self.fState.fMaxAtten = Vertex(1, 1, 1)
        self.fState.fMinAtten = Vertex(0, 0, 0)
        opac = FindInDict(objscript,'visual.waveset.depthrange.opac.end',12)
        refl = FindInDict(objscript,'visual.waveset.depthrange.refl.end',1)
        wave = FindInDict(objscript,'visual.waveset.depthrange.wave.end',1)
        self.fState.fDepthFalloff = Vertex(opac, refl, wave)
        self.fState.fWispiness = FindInDict(objscript,'visual.waveset.wispiness',0.5)
        self.fState.fShoreTint = RGBA(1, 1, 1, 1, type=1)
        self.fState.fMaxColor = RGBA(1, 1, 1, 1, type=1)
        self.fState.fMinColor = RGBA(0.184314, 0.172549, 0.113725, 1, type=1)
        self.fState.fEdgeOpac = FindInDict(objscript,'visual.waveset.edgeopac',1)
        self.fState.fEdgeRadius = FindInDict(objscript,'visual.waveset.edgeradius',1)
        self.fState.fPeriod = FindInDict(objscript,'visual.waveset.period',1)
        self.fState.fFingerLength = FindInDict(objscript,'visual.waveset.fingerlength',1)
        # should be able to set these colors, the mat color will do for now.
        self.fState.fWaterTint = RGBA(1, 1, 1, 1, type=1)
        self.fState.fSpecularTint = RGBA(1, 1, 1, 0.983333, type=1)
        self.fState.fEnvCenter = Vertex(obj.location[0], obj.location[1], obj.location[2])
        self.fState.fEnvRefresh = FindInDict(objscript,'visual.waveset.envrefresh',3)
        self.fState.fEnvRadius = FindInDict(objscript,'visual.waveset.envradius',1000)
    def _Find(page,name):
        return page.find(0x00FB,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x00FB,name,1)
    FindCreate = staticmethod(_FindCreate)

    def read(self, stream):
        plMultiModifier.read(self, stream)
        self.fMaxLen = stream.ReadFloat()
        self.fState.read(stream)
        self.fShores.read(stream)
        self.fDecals.read(stream)
        self.fEnvMap.read(stream)
        # self.BitVector == self.fFlags in plMultiModifier
        if(self.BitVector[plWaveSet7.fFlags["kHasRefObject"]]):
            self.fRefObject.read(stream)

    def write(self, stream):
        plMultiModifier.write(self, stream)
        stream.WriteFloat(self.fMaxLen)
        self.fState.write(stream)
        self.fShores.write(stream)
        self.fDecals.write(stream)
        self.fEnvMap.write(stream)
        # self.BitVector == self.fFlags in plMultiModifier
        if(self.BitVector[plWaveSet7.fFlags["kHasRefObject"]]):
            self.fRefObj.write(stream)


class plFixedWaterState7():
    fFlags = \
    { \
        "kNoise"      : 0x00, \
        "kSpecStart"  : 0x01, \
        "kSpecEnd"    : 0x02 \
    }
    class WaveState():
        def __init__(self):
            self.fMaxLength = 0.0
            self.fMinLength = 0.0
            self.fAmpOverLen = 0.0
            self.fChop = 0.0
            self.fAngleDev = 0.0

        def read(self, stream):
            self.fMaxLength = stream.ReadFloat()
            self.fMinLength = stream.ReadFloat()
            self.fAmpOverLen = stream.ReadFloat()
            self.fChop = stream.ReadFloat()
            self.fAngleDev = stream.ReadFloat()

        def write(self, stream):
            stream.WriteFloat(self.fMaxLength)
            stream.WriteFloat(self.fMinLength)
            stream.WriteFloat(self.fAmpOverLen)
            stream.WriteFloat(self.fChop)
            stream.WriteFloat(self.fAngleDev)

    def __init__(self):
        self.fGeoState = self.WaveState()
        self.fTexState = self.WaveState()
        self.fRippleScale = 0.0
        self.fWindDir = Vertex() #hsVector3
        self.fSpecVec = Vertex()
        self.fWaterHeight = 0.0
        self.fWaterOffset = Vertex()
        self.fMaxAtten = Vertex() #hsVector3
        self.fMinAtten = Vertex()
        self.fDepthFalloff = Vertex()
        self.fWispiness = 0.0
        self.fShoreTint = RGBA(0.5,0.5,0.5,1.0,type=1) #hsColorRGBA
        self.fMaxColor = RGBA(0.5,0.5,0.5,1.0,type=1)
        self.fMinColor = RGBA(0.5,0.5,0.5,1.0,type=1)
        self.fEdgeOpac = 0.0
        self.fEdgeRadius = 0.0
        self.fPeriod = 0.0
        self.fFingerLength = 0.0
        self.fWaterTint = RGBA(0.5,0.5,0.5,1.0,type=1) #hsColorRGBA
        self.fSpecularTint = RGBA(0.5,0.5,0.5,1.0,type=1)
        self.fEnvCenter = Vertex() #hsPoint3
        self.fEnvRefresh = 0.0
        self.fEnvRadius = 0.0

    def read(self, stream):
        self.fGeoState.read(stream)
        self.fTexState.read(stream)
        self.fRippleScale = stream.ReadFloat()
        self.fWindDir.read(stream)
        self.fSpecVec.read(stream)
        self.fWaterHeight = stream.ReadFloat()
        self.fWaterOffset.read(stream)
        self.fMaxAtten.read(stream)
        self.fMinAtten.read(stream)
        self.fDepthFalloff.read(stream)
        self.fWispiness = stream.ReadFloat()
        self.fShoreTint.read(stream)
        self.fMaxColor.read(stream)
        self.fMinColor.read(stream)
        self.fEdgeOpac = stream.ReadFloat()
        self.fEdgeRadius = stream.ReadFloat()
        self.fPeriod = stream.ReadFloat()
        self.fFingerLength = stream.ReadFloat()
        self.fWaterTint.read(stream)
        self.fSpecularTint.read(stream)
        self.fEnvCenter.read(stream)
        self.fEnvRefresh = stream.ReadFloat()
        self.fEnvRadius = stream.ReadFloat()

    def write(self, stream):
        self.fGeoState.write(stream)
        self.fTexState.write(stream)
        stream.WriteFloat(self.fRippleScale)
        self.fWindDir.write(stream)
        self.fSpecVec.write(stream)
        stream.WriteFloat(self.fWaterHeight)
        self.fWaterOffset.write(stream)
        self.fMaxAtten.write(stream)
        self.fMinAtten.write(stream)
        self.fDepthFalloff.write(stream)
        stream.WriteFloat(self.fWispiness)
        self.fShoreTint.write(stream)
        self.fMaxColor.write(stream)
        self.fMinColor.write(stream)
        stream.WriteFloat(self.fEdgeOpac)
        stream.WriteFloat(self.fEdgeRadius)
        stream.WriteFloat(self.fPeriod)
        stream.WriteFloat(self.fFingerLength)
        self.fWaterTint.write(stream)
        self.fSpecularTint.write(stream)
        self.fEnvCenter.write(stream)
        stream.WriteFloat(self.fEnvRefresh)
        stream.WriteFloat(self.fEnvRadius)
