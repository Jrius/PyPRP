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
import array, random, binascii
from prp_AbsClasses import *
import prp_Config
from prp_Types import *
from prp_GeomClasses import *
from prp_ConvexHull import *
from prp_Functions import *
from prp_Classes import *
from prp_MatClasses import *
from prp_LightClasses import *

import bmesh


class VertexCoderElement:
    def __init__(self,base=0,count=0):
        self.base = base #FLOAT
        self.count = count #WORD

    def read(self,buf,granularity):
        if (self.count == 0):
            self.base = buf.ReadFloat()
            self.count = buf.Read16()
        if (self.count != 0):
            self.count = self.count - 1
            return (self.base + granularity * buf.Read16())
        raise RuntimeError("VertexCoderElement prematurely reached end of count")

class VertexCoderColorElement:
    def __init__(self,base=0,count=0):
        self.base = base
        self.count = count
        self.RLE = None #Bool


    def read(self,buf):
        if (self.count == 0):
            self.count = buf.Read16()
            if ((self.count & 0x8000) != 0):
                self.RLE = 1
                self.base = buf.ReadByte()
                self.count &= 0x7FFF
            else:
                self.RLE = 0
        if (self.count != 0):
            self.count = (self.count - 1)
            if self.RLE:
                return self.base
            else:
                return buf.ReadByte()
        else:
           raise RuntimeError("VertexCoderColorElement prematurely reached end of count.")


class plVertexCoder:
    # Still uses struct.pack and struct.unpack, but that is no problem

    def __init__(self):
        #State vars
        self.Elements=[]
        for i in range(30):
            self.Elements.append(VertexCoderElement())
        self.Colors=[]
        for i in range(4):
            self.Colors.append(VertexCoderColorElement())

    def read(self,bufferGroup,buf,count):
        #read encoded vertex info
        for i in range(count):
            #Vertex Coordinates
            vert=Vertex()
            vert.x=self.Elements[0].read(buf,1.0/1024.0)
            vert.y=self.Elements[1].read(buf,1.0/1024.0)
            vert.z=self.Elements[2].read(buf,1.0/1024.0)
            #Vertex weights
            for e in range(bufferGroup.GetNumSkinWeights()):
                vert.blend.append(self.Elements[3+e].read(buf,1.0/32768.0))
            if bufferGroup.GetNumSkinWeights() and bufferGroup.GetSkinIndices():
                b1,b2,b3,b4,=struct.unpack("BBBB",buf.read(4)) #4 bones
                vert.bones=[b1,b2,b3,b4] #absolute bone index
            #normals
            vert.nx = (buf.Read16() / 32767.0)
            vert.ny = (buf.Read16() / 32767.0)
            vert.nz = (buf.Read16() / 32767.0)
            #colors
            vert.color.b = self.Colors[0].read(buf)
            vert.color.g = self.Colors[1].read(buf)
            vert.color.r = self.Colors[2].read(buf)
            vert.color.a = self.Colors[3].read(buf)
            #texture coordinates
            for j in range(bufferGroup.GetUVCount()):
                tex=[]
                tex.append(self.Elements[6+(3*j)].read(buf,1.0/65536.0))
                tex.append(self.Elements[7+(3*j)].read(buf,1.0/65536.0))
                tex.append(self.Elements[8+(3*j)].read(buf,1.0/65536.0))
                vert.tex.append(tex)
            bufferGroup.fVertBuffStorage.append(vert)


    def write(self,bufferGroup,buf,count):
        #State vars
        VarA=[] #vertex coords (3)
        Vector=[] #real vector
        VBase=[] #vertex coords base
        offset=[] #offsets
        xVector=[]
        VarB=[] #vertex weights (nblends)
        BBase=[] #weight base
        VarC=[] #vertex colors RGBA (4)
        color=[] #the last color
        VarD=[] #vertex tex coords (3 * ntex)
        TBase=[] #tex coords base
        for i in range(3):
            VarA.append(0)
            Vector.append(0)
            xVector.append(0)
            VBase.append(0)
            offset.append(0)
        for i in range(bufferGroup.GetNumSkinWeights()):
            VarB.append(0)
            BBase.append(0)
        for i in range(4):
            VarC.append(0)
            color.append(0)
        for i in range(3*bufferGroup.GetUVCount()):
            VarD.append(0)
            TBase.append(0)
        compress=prp_Config.vertex_compression
        n = count
        #write encoded vertex info
        for i in range(count):
            vert=bufferGroup.fVertBuffStorage[i]
            #Vertex Coordinates
            Vector[0]=vert.x
            Vector[1]=vert.y
            Vector[2]=vert.z
            if not compress:
                #uncompressed
                for e in range(3):
                   buf.write(struct.pack("<fHH",Vector[e],1,0)) #vertex base, n_vertexs, offset
            else:
                #compressed
                for e in range(3):
                    if VarA[e]==0:
                        #first vertex with new base
                        VBase[e]=Vector[e]
                        #count vertex with same base
                        for vi in range(n-i):
                            xxvert = bufferGroup.fVertBuffStorage[vi+i]
                            xVector[0]=xxvert.x
                            xVector[1]=xxvert.y
                            xVector[2]=xxvert.z
                            off = (xVector[e]-VBase[e]) * 1024.0
                            #32768
                            if off<65536 and off>=0:
                                VarA[e]=VarA[e]+1
                            else:
                                break
                        buf.write(struct.pack("<fH",VBase[e],VarA[e]))
                    off = (Vector[e]-VBase[e]) * 1024.0
                    buf.write(struct.pack("<H",off))
                    VarA[e]=VarA[e]-1

            #Vertex weights
            if not compress:
                for e in range(bufferGroup.GetNumSkinWeights()):
                    buf.write(struct.pack("<fHH",vert.blend[e],1,0)) #blend base, n, offset
            else:
                for e in range(bufferGroup.GetNumSkinWeights()):
                    if VarB[e]==0:
                        #first
                        BBase[e]=vert.blend[e]
                        #count
                        for vi in range(n-i):
                            xxvert = bufferGroup.fVertBuffStorage[vi+i]
                            off = (xxvert.blend[e] - BBase[e]) * 32768.0
                            if off<65536 and off>=0:
                                VarB[e]=VarB[e]+1
                            else:
                                break
                        buf.write(struct.pack("<fH",BBase[e],VarB[e]))
                    off = (vert.blend[e] - BBase[e]) * 32768.0
                    buf.write(struct.pack("<H",off))
                    VarB[e]=VarB[e]-1
            if bufferGroup.GetNumSkinWeights() and bufferGroup.GetSkinIndices():
                buf.write(struct.pack("BBBB",vert.bones[0],vert.bones[1],vert.bones[2],vert.bones[3]))
            #normals
            nx = int(vert.nx * 32768.0)
            ny = int(vert.ny * 32768.0)
            nz = int(vert.nz * 32768.0)
            if nx > 32767:
                nx = 32767
            elif nx < -32767:
                nx = -32767
            if ny > 32767:
                ny = 32767
            elif ny < -32767:
                ny = -32767
            if nz > 32767:
                nz = 32767
            elif nz < -32767:
                nz = -32767
            try:
                buf.write(struct.pack("<hhh",nx,ny,nz))
            except:
                raise RuntimeError("wtf %i %i %i, %i %i %i" %(vert.nx,vert.ny,vert.nz,nx,ny,nz))
            #colors
            #vcolor=vert.color.uget()
            vcolor=[vert.color.b,vert.color.g,vert.color.r,vert.color.a]
            if not compress:
                for e in range(4):
                    buf.write(struct.pack("<H",1))
                    buf.write(struct.pack("B",vcolor[e]))
            else:
                for e in range(4):
                    if VarC[e]==0:
                        #first
                        color[e]=vcolor[e]
                        #count
                        for vi in range(n-i):
                            vicolor=[bufferGroup.fVertBuffStorage[vi+i].color.b,bufferGroup.fVertBuffStorage[vi+i].color.g,bufferGroup.fVertBuffStorage[vi+i].color.r,bufferGroup.fVertBuffStorage[vi+i].color.a]
                            if vicolor[e]==color[e]:
                                VarC[e]=VarC[e]+1
                            else:
                                break
                        if VarC[e]==1:
                            cf=0
                        else:
                            cf=0x8000
                        buf.write(struct.pack("<HB",VarC[e] | cf,color[e]))
                    VarC[e]=VarC[e]-1
            #texture coordinates
            if not compress:
                for j in range(bufferGroup.GetUVCount()):
                    for k in range(3):
                        buf.write(struct.pack("<fHH",vert.tex[j][k],1,0)) #base, n, offset
                        #buf.write(struct.pack("fHH",0,1,0))
            else:
                for j in range(bufferGroup.GetUVCount()):
                    for k in range(3):
                        e=(3*j)+k
                        if VarD[e]==0:
                            #first
                            TBase[e]=vert.tex[j][k]
                            #count
                            for vi in range(n-i):
                                xbase=bufferGroup.fVertBuffStorage[vi+i].tex[j][k]
                                off = (xbase - TBase[e]) * 65536.0
                                if off<65536 and off>=0:
                                    VarD[e]=VarD[e]+1
                                else:
                                    break
                            buf.write(struct.pack("<fH",TBase[e],VarD[e]))
                        #print vert.tex[j][k],TBase[e]
                        off=(vert.tex[j][k]-TBase[e]) * 65536.0
                        #assert((TBase[e]+(off/65536.0))==vert.tex[j][k])
                        #print i,j,k,e,off
                        buf.write(struct.pack("<H",off))
                        VarD[e]=VarD[e]-1


class plGBufferCell:
    def __init__(self):
        self.VertexIndex = 0 #DWORD
        self.ColorIndex = -1 #DWORD
        self.NumVerts = 0 #DWORD


    def read(self,buf):
        self.VertexIndex = buf.Read32()
        assert(self.VertexIndex == 0)
        self.ColorIndex = buf.ReadSigned32()
        assert(self.ColorIndex == -1)
        self.NumVerts = buf.Read32()


    def write(self,buf):
        buf.Write32(self.VertexIndex)
        buf.WriteSigned32(self.ColorIndex)
        buf.Write32(self.NumVerts)


class plGBufferColor:
    def __init__(self):
        self.DRed = 0
        self.DGreen = 0
        self.DBlue = 0
        self.DAlpha = 0
        self.SRed = 0
        self.SGreen = 0
        self.SBlue = 0
        self.SAlpha = 0


    def read(self,buf):
        self.DRed = buf.ReadByte()
        self.DGreen = buf.ReadByte()
        self.DBlue = buf.ReadByte()
        self.DAlpha = buf.ReadByte()
        self.SRed = buf.ReadByte()
        self.SGreen = buf.ReadByte()
        self.SBlue = buf.ReadByte()
        self.SAlpha = buf.ReadByte()


    def write(self,buf):
        buf.WriteByte(self.DRed)
        buf.WriteByte(self.DGreen)
        buf.WriteByte(self.DBlue)
        buf.WriteByte(self.DAlpha)
        buf.WriteByte(self.SRed)
        buf.WriteByte(self.SGreen)
        buf.WriteByte(self.SBlue)
        buf.WriteByte(self.SAlpha)


class plGBufferGroup:
    Formats = \
    { \
        "kUVCountMask"          :  0xF, \
        "kSkinNoWeights"        :  0x0, \
        "kSkin1Weight"          : 0x10, \
        "kSkin2Weights"         : 0x20, \
        "kSkin3Weights"         : 0x30, \
        "kSkinWeightMask"       : 0x30, \
        "kSkinIndices"          : 0x40, \
        "kEncoded"              : 0x80  \
    }

    Reserve = \
    { \
        "kReserveInterleaved"   :  0x1, \
        "kReserveVerts"         :  0x2, \
        "kReserveColors"        :  0x4, \
        "kReserveSeparated"     :  0x8, \
        "kReserveIsolate"       : 0x10  \
    }

    def __init__(self):
        self.VertStrideLength = 0 #Byte
        #...
        self.fVertBuffStorage = hsTArray()#<Vertex>
        self.fIdxBuffStorage = hsTArray()#<Int16>
        self.fVertBuffSizes = hsTArray()
        #...
        self.fFormat = 0 #Byte
        self.fStride = 0 #?
        self.fCells = hsTArray()#<hsTArray<plGBufferCell>>
        # Added Slice attributes
        #self.fSkinIndices=0       # Was self .blend # PyPRP unique - (int)(fFormat & kSkinIndices > 0)
        #self.fNumSkinWeights=0  # Was self .NumBlendWeights
        #self.fUVCount=0 # Was self .ntex

    def GetSkinIndices(self):
        return (self.fFormat & plGBufferGroup.Formats["kSkinIndices"] > 0)

    def SetSkinIndices(self,value):
        if value == True:
            self.fFormat = self.fFormat | plGBufferGroup.Formats["kSkinIndices"]
        else:
            self.fFormat = self.fFormat & ~plGBufferGroup.Formats["kSkinIndices"]

    def GetUVCount(self):
        return self.fFormat & plGBufferGroup.Formats["kUVCountMask"]

    def SetUVCount(self,value):
        # force to maximum of 8, to avoid trouble
        if(value > 8):
            value = 8

        # clear mask
        self.fFormat = self.fFormat & ~plGBufferGroup.Formats["kUVCountMask"]
        # set new value
        self.fFormat = self.fFormat | (value & plGBufferGroup.Formats["kUVCountMask"])

    def GetNumSkinWeights(self):
        return (self.fFormat & plGBufferGroup.Formats["kSkinWeightMask"]) >> 4

    def SetNumSkinWeights(self,value):
        # force to maximum of 3
        if(value > 3):
            value = 3

        # clean out the old value
        self.fFormat = self.fFormat & ~plGBufferGroup.Formats["kSkinWeightMask"]
        # and set the value
        self.fFormat = self.fFormat | (( value << 4 ) & plGBufferGroup.Formats["kSkinWeightMask"])


    def ICalcVertexSize(self):
        lStride = ((self.fFormat & plGBufferGroup.Formats["kUVCountMask"]) + 2) * 12;

        SkinWeightField = self.fFormat & plGBufferGroup.Formats["kSkinWeightMask"]
        if   SkinWeightField == plGBufferGroup.Formats["kSkinNoWeights"]:
            fNumSkinWeights = 0

        elif SkinWeightField == plGBufferGroup.Formats["kSkin1Weight"]:
            fNumSkinWeights = 1

        elif SkinWeightField == plGBufferGroup.Formats["kSkin2Weights"]:
            fNumSkinWeights = 2

        elif SkinWeightField == plGBufferGroup.Formats["kSkin3Weights"]:
            fNumSkinWeights = 3

        else:
            fNumSkinWeights = 0

        if fNumSkinWeights != 0:
            lStride = lStride + fNumSkinWeights * 4
            if self.fFormat & plGBufferGroup.Formats["kSkinIndices"] > 0:
                lStride = lStride + 4

        return lStride + 8;


    def read(self,buf):
        self.fFormat = buf.ReadByte()                # was self-PackedVertexFormat
        self.fStride = self.ICalcVertexSize()  # was self-VertAndColorStrideLength
        # This is written out in write(), but when read in, it
        # doesn't seem to be used anywhere
        buf.Read32()

        coder = plVertexCoder() # initialize new Vertex Coder
        VertexStorageCount = buf.Read32()
        #assert(VertexStorageCount == 1)
        for j in range(VertexStorageCount):
            if(self.fFormat & plGBufferGroup.Formats["kEncoded"]):
                count = buf.Read16()
#                print "reading geometry (%i vertexs (%i,%i,%i)) - this will take several minutes..." %(count,self.fSkinIndices,self.fNumSkinWeights,self.fUVCount)
                coder.read(self,buf,count)
            elif 1:
                # Support for uncompressed data below is untested, and
                # Isn't neccessary, since plasma doesn't do uncompressed
                # vertices :)

                # set "elif 1:" to "elif 0:" to test the code below should it become
                # neccessary
                raise RuntimeError("Encountered non-compressed vertex data - not supported")
            else:
                # This should work in theory....
                vtxSize = buf.Read32()
                self.fVertBuffSizes.append(vtxSize) # was self-VertexStorageLengths
                self.fVertBuffStarts.append(0)
                self.fVertBuffEnds.append(-1)

                vData = [vtxSize]
                for i in range(vtxSize):
                    vData[i] = buf.ReadByte()

                self.fVertBuffStorage.append(vData) # was self-VertexStorage

                colorCount = buf.Read32()
                self.fColorBuffCounts.append(colorCount) # was self-ColorStorageLengths
                if colorCount:
                    colors = hsTArray() # new array
                    for i in range(colorCount):
                        colors.append(plGBufferColor())
                    self.fColorBuffStorage.append(colors)

        count = buf.Read32()
        for j in range(count):
            idxCount = buf.Read32()
            indexList = hsTArray()
            for k in range(idxCount):
                indexList.append(buf.Read16())
            self.fIdxBuffStorage.append(indexList) # was self-IndexStorage

        for j in range(VertexStorageCount):
            count = buf.Read32()
            assert(count == 1)
            cells = hsTArray()
            for j in range(count):
                cell = plGBufferCell()
                cell.read(buf)
                cells.append(cell)
            self.fCells.append(cells) # Was self.fCells


    def write(self,buf): #Compressed Output ONLY (just as in plasma :) )
        # Ensure some format bits that are always set

        self.fFormat |= 0x80
        # RTR: We only write out one vertex storage - and so does Cyan!
        VertexStorageCount = 1
        # Calculate the size
        size = 0
        for i in range(VertexStorageCount):
            size += len(self.fVertBuffStorage)
        for i in range(len(self.fIdxBuffStorage)):
            size += len(self.fIdxBuffStorage[i])
        buf.WriteByte(self.fFormat)
        buf.Write32(size)
        coder = plVertexCoder()
        buf.Write32(VertexStorageCount)
        for i in range(VertexStorageCount):
            count = len(self.fVertBuffStorage)
            buf.Write16(count)

            if False: # Enable if neccesary
                if(count > 100000): # only say this if we have a really big number of vertices
                    print("=> Storing %i vertices of geometry - this can take some time...." % count)
                else:
                    print("=> Storing %i vertices of geometry..." % count)
            coder.write(self,buf,count)
        buf.Write32(len(self.fIdxBuffStorage))
        for i in range(len(self.fIdxBuffStorage)):
            indexStorageLength = len(self.fIdxBuffStorage[i])
            buf.Write32(indexStorageLength)
            for j in range(indexStorageLength):
                buf.Write16(self.fIdxBuffStorage.vector[i].vector[j])

        # RTR: put in one cell in a list for now
        cell = plGBufferCell()
        cell.VertexIndex = 0
        cell.ColorIndex = -1
        cell.NumVerts = len(self.fVertBuffStorage)
        cells = hsTArray()
        cells.append(cell)
        self.fCells.append(cells)
        for i in range(VertexStorageCount):
            buf.Write32(len(self.fCells.vector[i]))
            for j in range(len(self.fCells.vector[i])):
                self.fCells.vector[i].vector[j].write(buf)

class plDISpanIndex: #NOTE: This is a pile of guesswork (it still is on 28/nov/07)
    Flags = \
    { \
        "kMesh" : 0x00, \
        "kBone" : 0x01 \
    }

    def __init__(self):
        self.fFlags = 0
        self.fIndices = hsTArray()#<Int32>


    def read(self,buf):
        self.fFlags = buf.Read32()
        i = buf.Read32()
        for j in range(i):
            self.fIndices.append(buf.Read32())


    def write(self,buf):
        buf.Write32(self.fFlags)
        buf.Write32(len(self.fIndices))
        for i in self.fIndices.vector:
            buf.Write32(i)


class plSpaceTreeNode:
    def __init__(self):
        self.box = hsBounds3Ext()
        # on leaves the box matches with the mesh transformed bbox
        # on branches, the box should contain all child objects (they are also on axis)
        #self.subsets = None #plIcicle
        #self.leaf = 0
        self.flags = 0 #WORD
        # 0x01 - leaf
        # 0x00 - branch
        # 0x04 flag - unknown? (balance?)
        # 0x08 strange flag - unknown data stored in p,l.r fields
        self.parent = 0 #WORD
        # -1 on root node
        self.left = 0 #WORD
        # left child node if branch, link to mesh if leave
        self.right = 0 #WORD
        # 0 if leave, else child node


    def read(self,buf):
        self.box.read(buf)
        self.flags = buf.Read16()
        if self.flags not in [0x00,0x01,0x04,0x05,0x08]:
            raise RuntimeError("plSpaceTreeNode has unknown flag ")
        self.parent = buf.ReadSigned16()
        self.left = buf.Read16()
        self.right = buf.Read16()
        if self.flags & 0x01:
            assert(self.right==0)


    def write(self,buf):
        self.box.write(buf)
        buf.Write16(self.flags)
        buf.WriteSigned16(self.parent)
        buf.Write16(self.left)
        buf.Write16(self.right)


    def __str__(self):
        return "b:%s,t:%X,p:%04i,l:%04i,r:%04i" %(str(self.box),self.flags,self.parent,self.left,self.right)


class plSpaceTree:
    def __init__(self,version):
        self.version = version
        self.type = 0x8000 # Default to NULL tree
        self.totalNodesMinusRoot = 0
        self.numLeaves = 0
        self.nodes = hsTArray() #plSpaceTreeNode


    def read(self,buf,numIcicles):
        self.type = buf.Read16()
        if (self.type == 0x8000): # NULL
            return
        # Sanity check 1: type
        if self.version==6:
            assert(self.type==0x0240) #plSpaceTree
        else:
            assert(self.type==0x0258) #plSpaceTree
        self.totalNodesMinusRoot = buf.Read16()
        # Sanity Check 2: this binary space tree should have (2 * numIcicles) -1 nodes
        assert(self.totalNodesMinusRoot == ((2*numIcicles)-2) or (self.totalNodesMinusRoot == 0 and numIcicles == 0))
        self.numLeaves = buf.Read32()
        # Sanity Check 3: leaves vs icicles
        assert(self.numLeaves == numIcicles)
        numNodes = buf.Read32()
        # Sanity check 4: nodes vs total
        assert(numNodes == (self.totalNodesMinusRoot+1))
        for i in range(numNodes):
            node = plSpaceTreeNode()
            node.read(buf)
            # Sanity check 5: node flags
            if node.flags & 0x01:
                assert(node.left==i)
                assert(i<numIcicles)
                #print i, node.parent, numIcicles
                assert(node.parent>=numIcicles or (node.parent==-1 and numIcicles==1))
            if node.flags==0x00:
                assert(i>=numIcicles)
            if node.flags & 0x08:       #female,male,live_male,live_female
                if node.parent not in [0x0A52,0x290A,0x0000]:
                    raise RuntimeError("tree parent is %04X" % node.parent)
                if node.left not in [0xE120,0x000A,0x0000]:
                    raise RuntimeError("tree left is %04X")
                if node.right not in [0x070F,0x676E,0x0000,0x3F80]:
                    raise RuntimeError("tree right is %04X")
            self.nodes.append(node)


    def write(self,buf):
        buf.Write16(self.type)
        if self.type == 0x8000: # NULL
            return
        buf.Write16(self.totalNodesMinusRoot)
        buf.Write32(self.numLeaves)
        buf.Write32(len(self.nodes))
        for node in self.nodes.vector:
            node.write(buf)

class plDrawable(hsKeyedObject):
    Props =\
    { \
        "kPropNoDraw"       :   0x1, \
        "kPropUNUSED"       :   0x2, \
        "kPropSortSpans"    :   0x4, \
        "kPropSortFaces"    :   0x8, \
        "kPropVolatile"     :  0x10, \
        "kPropNoReSort"     :  0x20, \
        "kPropPartialSort"  :  0x40, \
        "kPropCharacter"    :  0x80, \
        "kPropSortAsOne"    : 0x100, \
        "kPropHasVisLOS"    : 0x200
    }
    Crit =\
    { \
        "kCritStatic"       :  0x1, \
        "kCritSortSpans"    :  0x2, \
        "kCritSortFaces"    :  0x8, \
        "kCritCharacter"    :  0x10
    }
    plDrawableType =\
    { \
        "kNormal"           :      0x1, \
        "kNonDrawable"      :      0x2, \
        "kEnviron"          :      0x4, \
        "kLightProxy"       :  0x10000, \
        "kOccluderProxy"    :  0x20000, \
        "kAudibleProxy"     :  0x40000, \
        "kPhysicalProxy"    :  0x80000, \
        "kCoordinateProxy"  : 0x100000, \
        "kOccSnapProxy"     : 0x200000, \
        "kGenericProxy"     : 0x400000, \
        "kCameraProxy"      : 0x800000, \
        "kAllProxies"       : 0xFF0000, \
        "kAllTypes"         : 0x0000FF  \
    }
    plSubDrawableType =\
    { \
        "kSubNormal"        :  0x1, \
        "kSubNonDrawable"   :  0x2, \
        "kSubEnviron"       :  0x4, \
        "kSubAllTypes"      : 0xFF  \
    }
    plAccessFlags =\
    { \
        "kReadSrc"          : 0x1, \
        "kWriteDst"         : 0x2, \
        "kWriteSrc"         : 0x4  \
    }
    MsgTypes =\
    { \
        "kMsgMaterial"      : 0, \
        "kMsgDISpans"       : 1, \
        "kMsgFogEnviron"    : 2, \
        "kMsgPermaLight"    : 3, \
        "kMsgPermaProj"     : 4, \
        "kMsgPermaLightDI"  : 5, \
        "kMsgPermaProjDI"   : 6  \
    }

    Mapping = \
    { \
        "Flat"  : 0, \
        "Cube"  : 1, \
        "Tube"  : 2, \
        "Sphere": 3 \
    }

class plDrawableSpans(plDrawable):
    def __init__(self,parent,name="unnamed",type=0x004C):
        hsKeyedObject.__init__(self,parent,name,type)

        self.fLocalBounds = hsBounds3Ext() # flags == 0x00: max and min vertex of the entire set
        self.fWorldBounds = hsBounds3Ext() # flags == 0x01: same
        self.fMaxWorldBounds = hsBounds3Ext() # flags == 0x01: same

        # Notice!!! Do NOT ReadVector or WriteVector with Typless Classes!
        #
        # Below are sets of 4 matrices (2 pairs, normal and inverted)
        # they contain transformations indexed in the groups with flag 0x01
        # these are bones. matrices are local, bones have a coordinate
        # interface for correct placement in the age
        self.fLocalToWorlds = hsTArray([],self.getVersion()) #hsMatrix44
        self.fWorldToLocals = hsTArray([],self.getVersion()) #hsMatrix44
        self.fLocalToBones = hsTArray([],self.getVersion()) #hsMatrix44
        self.fBoneToLocals = hsTArray([],self.getVersion()) #hshsMatrix44

        self.fMaterials = hsTArray([0x07],self.getVersion()) #hsGMaterial
        self.fSpaceTree = plSpaceTree(self.getVersion())

        self.fIcicles = hsTArray([],self.getVersion()) #plIcicle
        self.fIcicles2 = hsTArray([],self.getVersion()) #plIcicle

        self.fGroups = hsTArray([],self.getVersion()) #plGBufferGroup
        self.fDIIndices = hsTArray([],self.getVersion()) #plDISpanIndex
        self.fProps = 0 #DWORD
        self.fCriteria = 0 #DWORD
        self.fRenderLevel = plRenderLevel()

        self.fSceneNode=UruObjectRef(self.getVersion()) #link to the plSceneNode
        self.fSourceSpans = hsTArray([],self.getVersion()) #plGeometrySpan


    def changePageRaw(self,sid,did,stype,dtype):
        hsKeyedObject.changePageRaw(self,sid,did,stype,dtype)
        for i in self.fMaterials:
            i.changePageRaw(sid,did,stype,dtype)
        for icicle in self.fIcicles:
            for light in icicle.lights1:
                light.changePageRaw(sid,did,stype,dtype)
            for light in icicle.lights2:
                light.changePageRaw(sid,did,stype,dtype)
        self.fSceneNode.changePageRaw(sid,did,stype,dtype)


    def read(self,buf):
        hsKeyedObject.read(self,buf)
        self.fProps = buf.Read32()
        self.fCriteria = buf.Read32()
        self.fRenderLevel.fLevel = buf.Read32()

        self.fMaterials.ReadVector(buf)
        i = buf.Read32()
        for j in range(i):
            icicle = plIcicle(self.getVersion())
            icicle.read(buf)
            self.fIcicles.append(icicle)
        i = buf.Read32()
        for j in range(i):
            icicle = plIcicle(self.getVersion())
            icicle.read(buf)
            self.fIcicles2.append(icicle)
        count = buf.Read32()
        for i in range(count):
            idx = buf.Read32()
            # This is just the same as i; it is used to set the
            # internal NativeTransform array, which is just the
            # same as the Icicles array. So, we will do nothing with it.
        for i in range(count):
            # These references are always nil
            self.fIcicles[i].fFogEnvironment.read(buf)
        if (count):
            self.fLocalBounds.read(buf)
            self.fWorldBounds.read(buf)
            self.fMaxWorldBounds.read(buf)
        else:
            self.fLocalBounds.flags |= 2
            self.fWorldBounds.flags |= 2
            self.fMaxWorldBounds.flags |= 2
        for i in range(count):
            if (self.fIcicles[i].fProps & plSpan.Props["kPropHasPermaLights"]):
                self.fIcicles[i].fPermaLights.ReadVector(buf)
            if (self.fIcicles[i].fProps & plSpan.Props["kPropHasPermaProjs"]):
                self.fIcicles[i].fPermaProjs.ReadVector(buf)
        i = buf.Read32()
        for j in range(i):
            # There are never any geometry spans in the Cyan ages,
            # so this code will never get exercised
            geometrySpan = plGeometrySpan()
            geometrySpan.read(buf)
            self.fSourceSpans.append(geometrySpan)
        i = buf.Read32()
        for j in range(i):
            k = hsMatrix44()
            k.read(buf)
            self.fLocalToWorlds.append(k)
            l = hsMatrix44()
            l.read(buf)
            self.fWorldToLocals.append(l)
            m = hsMatrix44()
            m.read(buf)
            self.fLocalToBones.append(m)
            n = hsMatrix44()
            n.read(buf)
            self.fBoneToLocals.append(n)
        i = buf.Read32()
        for j in range(i):
            spanIndex = plDISpanIndex()
            spanIndex.read(buf) # Read Function of plDISpanIndex is written out here in plasma
            self.fDIIndices.append(spanIndex)
        i = buf.Read32()
        for j in range(i):
            bufferGroup = plGBufferGroup()
            bufferGroup.read(buf)
            self.fGroups.append(bufferGroup)
        self.fSpaceTree.read(buf,len(self.fIcicles))
        self.fSceneNode.setVersion(self.getVersion())
        self.fSceneNode.read(buf)
        assert(self.fSceneNode.verify(self.Key))


    def write(self,buf):
        hsKeyedObject.write(self,buf)
        buf.Write32(self.fProps)
        buf.Write32(self.fCriteria)
        buf.Write32(self.fRenderLevel.fLevel)
        self.fMaterials.WriteVector(buf)
        buf.Write32(len(self.fIcicles))
        for icicle in self.fIcicles.vector:
            icicle.write(buf)
        buf.Write32(len(self.fIcicles2))
        for icicle in self.fIcicles2.vector:
            icicle.write(buf)
        count=len(self.fIcicles)
        buf.Write32(count)
        for i in range(count):
            buf.Write32(i)
        for i in range(count):
            self.fIcicles[i].fFogEnvironment.write(buf)
        if count!=0:
            self.fLocalBounds.write(buf)
            self.fWorldBounds.write(buf)
            self.fMaxWorldBounds.write(buf)
        for i in range(count):
            if (self.fIcicles[i].fProps & 0x80):
                self.fIcicles[i].fPermaLights.WriteVector(buf)
            if (self.fIcicles[i].fProps & 0x100):
                self.fIcicles[i].fPermaProjs.WriteVector(buf)
        buf.Write32(len(self.fSourceSpans))
        for geometrySpans in self.fSourceSpans.vector:
            geometrySpans.write(buf)
        buf.Write32(len(self.fLocalToWorlds))
        for i in range(len(self.fLocalToWorlds)):
            self.fLocalToWorlds[i].write(buf)
            self.fWorldToLocals[i].write(buf)
            self.fLocalToBones[i].write(buf)
            self.fBoneToLocals[i].write(buf)
        buf.Write32(len(self.fDIIndices))
        for spanIndex in self.fDIIndices.vector:
            spanIndex.write(buf)
        buf.Write32(len(self.fGroups))
        for bufferGroup in self.fGroups.vector:
            bufferGroup.write(buf)
        self.fSpaceTree.write(buf)
        self.fSceneNode.update(self.Key)
        assert(self.fSceneNode.flag == 0x01)
        self.fSceneNode.write(buf)

    def _Find(page,name):
        return page.find(0x004C,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x004C,name,1)
    FindCreate = staticmethod(_FindCreate)

    def updateName(self):
        if self.fRenderLevel.fLevel==0:
            sfx="Spans"
        else:
            sfx="BlendSpans"
        root=self.getRoot()
        one="%08x" % self.fRenderLevel.fLevel
        two="%x" % self.fCriteria
        testname=str(root.name) + "_District_" + str(root.page) + "_" + one + "_" + two + sfx
        self.Key.name.set(testname)


    def import_all(self):
        for i in range(len(self.fDIIndices)):
            self.import_object(i,"obj%02i" % i)


    def find_buffer_group(self,HasSkinIdx,NumSkinWeights,UVCount,num_vertexs):
        # Find or create a buffer group corresponding to current format

        # Each Buffergroup can store a maximum of 0xffff vertices of a specific format
        # Format is based on:
        #
        # HasSkinIdx - (bool) Does it have Skin Indexes or not
        # NumSkinWeights - How many Skin Weights per vertes
        # nuvmaps - number of sets of 3 texcoords
        for idx in range(len(self.fGroups)):
            bufferGroup=self.fGroups[idx]
            if bufferGroup.GetSkinIndices()==bool(HasSkinIdx) and bufferGroup.GetNumSkinWeights()==NumSkinWeights \
                and bufferGroup.GetUVCount()==UVCount and len(bufferGroup.fVertBuffStorage)+num_vertexs<0xffff:
                return idx

        #not found - create a new bufferGroup with the required format
        bufferGroup=plGBufferGroup()
        bufferGroup.SetSkinIndices(HasSkinIdx)
        bufferGroup.SetNumSkinWeights(NumSkinWeights)
        bufferGroup.SetUVCount(UVCount)
        # add it to the list
        self.fGroups.append(bufferGroup)
        # and return new index in list
        return len(self.fGroups)-1


    def findMaterial(self,name):
        # Locate material in DrawableSpans material list, and return index
        for i in range(len(self.fMaterials)):
            if str(self.fMaterials[i].Key.name)==name:
                return i

        # If it isn't here yet, add it to the list

        # Find plMaterial
        root=self.getRoot()
        mat=root.find(0x07,name,0)

        # if it's not here, return None
        if mat==None:
            #print "WARNING: I cannot find material %s" %name
            return None

        # append plMaterial to list
        self.fMaterials.append(mat.data.getRef())

        # return index of new material
        return len(self.fMaterials)-1

    def addMaterial(self,mat,obj,prp):
        # Creates new material object, and runs material exporter on it
        # Afterwards, calls self.findMaterial to put the material in the
        # DrawableSpan's material list, and returns an index to it.

        name=mat.name

        root=self.getRoot()
        pmat=root.find(0x07,name,1)
        if(not pmat.isProcessed):
            pmat.data.FromBlenderMat(mat,obj,prp)
            pmat.isProcessed = 1

        return self.findMaterial(name)

    def export_obj(self,obj,dynamic,MaterialGroups=[],water = False):
        print("  [DrawableSpans %08x_%x]"%(self.fRenderLevel.fLevel,self.fCriteria))
        root=self.getRoot()

        # Now, we must store the vertices group by group.

        # first get the object's matrix so we can transform vertices
        # if the object doesn't get a transformation matrix

        obj_l2w=getMatrix(obj)
        #obj_l2w.transpose()
        LocalToWorld=hsMatrix44()
        LocalToWorld.set(obj_l2w)
        script = AlcScript.objects.Find(obj.name)

        # Prepare a span index object, in which we can add our span indices
        spanIndex = plDISpanIndex()

        print("   Processing Faces per Material - Totalling",len(MaterialGroups),"materials")

        # loop through the groups
        for MatGroup in MaterialGroups:
            mat = MatGroup['mat'] # For Quick reference...
            matidx = self.addMaterial(MatGroup['mat'],obj,root)

            print("   Material",MatGroup["mat"].name)

            if len(MatGroup["vertices"]) > 0xffff: # bring this down to 0x8000 again if it bothers you.
                raise RuntimeError("Vertex count on this material is too high, consider breaking up your object into several materials....")

            # Find the correct buffer group to store this, depending on
            # having skin indices, nr of vertex weights, nr of uvmaps and amount of vertices

            ThisIsJustToTeaseJennifer_P=self.find_buffer_group(False,MatGroup['WeightCount'],MatGroup['UVCount'],len(MatGroup["vertices"]))
            bufferGroup=self.fGroups[ThisIsJustToTeaseJennifer_P]


            # Mapping through the vertices :)
            vstart=len(bufferGroup.fVertBuffStorage)

            # stored info to build up a bounding box in the end of this cyce
            # we only store local coordinates, because we can just ocnvert those to world if neccesary

            lboundsmin=None # maximum vertex
            lboundsmax=None # minimum vertex

            # store each vertex
            for vert in MatGroup["vertices"]:
                # Transform the vertex
                if not dynamic:
                    vert.transform(LocalToWorld)

                # Determine minimum and maximum values, for calculation of bounding box...
                if lboundsmin is None or lboundsmax is None:
                    lboundsmin = Vertex(vert.x,vert.y,vert.z)
                    lboundsmax = Vertex(vert.x,vert.y,vert.z)
                else:
                    if vert.x < lboundsmin.x:
                        lboundsmin.x = vert.x
                    if vert.y < lboundsmin.y:
                        lboundsmin.y = vert.y
                    if vert.z < lboundsmin.z:
                        lboundsmin.z = vert.z
                    if vert.x > lboundsmax.x:
                        lboundsmax.x = vert.x
                    if vert.y > lboundsmax.y:
                        lboundsmax.y = vert.y
                    if vert.z > lboundsmax.z:
                        lboundsmax.z = vert.z

                bufferGroup.fVertBuffStorage.append(vert)
            vstop = len(bufferGroup.fVertBuffStorage)

            # Default to a 0,0,0 by 0,0,0 bounding box if no vertices processed
            if lboundsmin is None or lboundsmax is None:
                lboundsmin = Vertex(0,0,0)
                lboundsmax = Vertex(0,0,0)



            #Set the Faces

            # In plasma, plGBufferGroups, only use on index storage buffer
            # Set the index buffer to 0 - we always use only one index buffer, just as Cyan does
            # We just store the position we start and end in that buffer
            IndexBufferIdx=0

            # Create the index buffer if it isn't there yet
            if len(bufferGroup.fIdxBuffStorage) == 0:
                faces=hsTArray()
                bufferGroup.fIdxBuffStorage.append(faces)


            idxstart=len(bufferGroup.fIdxBuffStorage[IndexBufferIdx])

            # Append vertex indices of these faces
            # (Append vstart to vertex index, to convert from local index to buffer index)
            for face in MatGroup["faces"]:
                nface = []
                for index in face:
                    bufferGroup.fIdxBuffStorage[IndexBufferIdx].append(vstart + index)

            idxstop=len(bufferGroup.fIdxBuffStorage[IndexBufferIdx])

            # Now create a new icicle for this group
            icicle = plIcicle(self.getVersion())
            icicle.fSubType = plDrawable.plSubDrawableType["kSubNormal"]# <- could also be plSpan.plSpanType["kVertexSpan"]
            icicle.fMaterialIdx=matidx

            # Determine Properties!
            icicle.fProps = 0
            if MatGroup["vtxalphacol"] == True:
                icicle.fProps |= plSpan.Props["kLiteVtxNonPreshaded"]

            if water:
                icicle.fProps |= (plSpan.Props["kWaterHeight"] | plSpan.Props["kLiteVtxNonPreshaded"] | plSpan.Props["kPropRunTimeLight"] | plSpan.Props["kPropReverseSort"] | plSpan.Props["kPropNoShadow"])
                icicle.fWaterHeight = obj.location[2]
            
            flags = FindInDict(script,"visual.icicle",None)
            if type(flags) == list:
                icicle.fProps = 0
                for flag in flags:
                    if flag.lower() in plSpan.scriptProps:
                        print("    set flag: " + flag.lower())
                        icicle.fProps |= plSpan.scriptProps[flag.lower()]
            elif type(flags) == int:
                # the old way
                print("Warning: setting icicle properties as int is depreciated")
                icicle.fProps = flags
            
            
            
            # bind object properties to icicle's mindist and maxdist
            icicle.fMinDist = getStrIntPropertyOrDefault(obj,"mindist",-1)
            icicle.fMaxDist = getStrIntPropertyOrDefault(obj,"maxdist",-1)


            # Store info about the Vertex Storage
            icicle.fGroupIdx=ThisIsJustToTeaseJennifer_P
            icicle.fCellOffset=vstart
            icicle.fVStartIdx=vstart
            icicle.fVLength=vstop-vstart

            # Store info about the Face Storage
            icicle.fIBufferIdx=IndexBufferIdx
            icicle.fIPackedIdx=idxstart
            icicle.fILength=(idxstop - idxstart)


            # set transformation info
            # If the object has no CoordinateInterface, we must pass the matrix by which they are
            # transformed.
            # Else, we just give an identity matrix.
            if dynamic:
                matrix=getMatrix(obj)
                #matrix.transpose()
                icicle.fLocalToWorld.set(matrix)

                matrix.invert()
                icicle.fWorldToLocal.set(matrix)
            else: #information already transformed on non-dynamic objects
                icicle.fLocalToWorld.identity()
                icicle.fWorldToLocal.identity()


            # Create a list of all lights in this page....
            lights = []
            lights.extend(root.listobjects(0x55)) # List of plDirectionalLight in this page
            lights.extend(root.listobjects(0x56)) # List of plOmniLight in this page
            lights.extend(root.listobjects(0x57)) # List of plSpotLight in this page
            lights.extend(root.listobjects(0x6A)) # List of plLimitedDirLight in this page

            # Obtain light group
            lightGroup = MatGroup['mat'].light_group

            mylights = []

            # Only add lights for this icicle if we are not "SHADELESS"
            if not mat.use_shadeless:
                if not lightGroup == None:
                    # if a lightgroup is set, use those lights, else use all lights in the page....
                    for pllamp in lights:
                        for lobj in list(lightGroup.objects):
                            # TODO - make sure this is correct
                            #dataname = lobj.getData(True) # First param sets return of name only
                            dataname = lobj.name
                            if str(pllamp.data.Key.name) == lobj.name or str(pllamp.data.Key.name) == dataname:
                                mylights.append(pllamp)
                else:
                    mylights = lights
            else:
                print("    Object is Shadeless, not appending any lamps")

            for pllamp in mylights:
                print("    Appending Light %s as lightobject to object %s" % (str(pllamp.data.Key.name),obj.name))
                pllampref = pllamp.data.getRef()
                # see if it is a projection or not...
                if pllamp.data.fProjection.isNull():
                    icicle.fPermaLights.append(pllampref)
                else:
                    icicle.fPermaProjs.append(pllampref)

            #Set the local bounding box:
            # we already determined the minimum and maximum coordinates in local space
            icicle.fLocalBounds.min=Vertex(lboundsmin.x,lboundsmin.y,lboundsmin.z)
            icicle.fLocalBounds.max=Vertex(lboundsmax.x,lboundsmax.y,lboundsmax.z)
            icicle.fLocalBounds.flags=0x01

            #Set the world bounding box
            # first convert localspace maximum and minimum to worldspace
            wboundsmin=Vertex(lboundsmin.x,lboundsmin.y,lboundsmin.z)
            wboundsmin.transform(icicle.fLocalToWorld)
            wboundsmax=Vertex(lboundsmax.x,lboundsmax.y,lboundsmax.z)
            wboundsmax.transform(icicle.fLocalToWorld)

            # and set those
            icicle.fWorldBounds.min=wboundsmin
            icicle.fWorldBounds.max=wboundsmax
            icicle.fWorldBounds.flags=0x01

            # Append the icicle to the Drawable Spans
            self.fIcicles.append(icicle)
            # Add a reference to this icicle to our spanindex list
            spanIndex.fIndices.append(len(self.fIcicles)-1)

        # append the index list
        self.fDIIndices.append(spanIndex)


        # Return the index of this plDISpanIndex object
        return len(self.fDIIndices) - 1

# As the draw interface is linked closely to the DrawableSpans, it is included here:

class plDrawInterface(plObjInterface):

    #Actually part of plRenderLevel, but we handle it here
    scriptRenderLevels = \
    { \
        "opaque"  : 0x0, \
        "fb"      : 0x1, \
        "defrend" : 0x2, \
        "blend"   : 0x4, \
        "late"    : 0x8
    }
    
    def __init__(self,parent,name="unnamed",type=0x0016):
        plObjInterface.__init__(self,parent,name,type)
        self.reset() # contains initialization of f-variables

        self.blenderobjects=[]

    def reset(self):
        if self.getVersion()==6:
            self.fDrawables=hsTArray([0x0049],self.getVersion(),True)
            self.fRegions=hsTArray([0x00E9],self.getVersion(),True)
            self.fDrawableIndices = hsTArray()
        else:
            self.fDrawables=hsTArray([0x004C],self.getVersion(),True)
            self.fRegions=hsTArray([0x0116],self.getVersion(),True)
            self.fDrawableIndices = hsTArray()


    def addSpanSet(self,setnum,spanref):
        self.fDrawableIndices.append(setnum)
        self.fDrawables.append(spanref)


    def changePageRaw(self,sid,did,stype,dtype):
        plObjInterface.changePageRaw(self,sid,did,stype,dtype)
        self.fDrawables.changePageRaw(sid,did,stype,dtype)
        self.fRegions.changePageRaw(sid,did,stype,dtype)


    def read(self,stream):
        plObjInterface.read(self,stream)
        self.fDrawables.size = stream.Read32()
        # spans are different than normal UruObjectRef reads, since
        # they have the groups intermingled with the refs
        for i in range(self.fDrawables.size):
            gi = stream.ReadSigned32()
            self.fDrawableIndices.append(gi)
            self.fDrawables.ReadRef(stream)
        self.fRegions.ReadVector(stream)


    def write(self,stream):
        plObjInterface.write(self,stream)
        stream.Write32(self.fDrawables.size)
        for i in range(self.fDrawables.size):
            stream.WriteSigned32(self.fDrawableIndices[i])
            self.fDrawables[i].update(self.Key)
            self.fDrawables[i].write(stream)
        self.fRegions.WriteVector(stream)

    def _Find(page,name):
        return page.find(0x0016,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x0016,name,1)
    FindCreate = staticmethod(_FindCreate)

    def import_obj(self,obj):
        root = self.getRoot()
        print(" [DrawInterface %s]"%(str(self.Key.name)))

        # Import all drawables in this list
        for i in range(len(self.fDrawableIndices)):
            print("  Importing set",(i+1),"of",len(self.fDrawableIndices))
            group = self.fDrawableIndices[i]
            spanref = self.fDrawables[i]
            drawspans = root.findref(spanref)
            drawspans.data.import_mesh(obj,group)

    def _Import(scnobj,prp,obj):
        if not scnobj.draw.isNull():
            draw = prp.findref(scnobj.draw)
            if draw!=None:
                draw.data.import_obj(obj)

    Import = staticmethod(_Import)


    def _Export(page,obj,scnobj,name,SceneNodeRef,isdynamic,softVolParser, water = False):
        # --- Draw Interface ---
        drawiref=scnobj.data.draw
        if drawiref.isNull():
            drawi=page.prp.find(0x16,name,1)
            scnobj.data.draw=drawi.data.getRef()
        else:
            drawi=page.prp.findref(drawiref)
        if drawi==None:
            raise RuntimeError("ERROR: DrawInterface %s - %s not found!" %(str(scnobj.data.Key),str(drawiref)))

        drawi.data.export_obj(obj,SceneNodeRef,isdynamic,softVolParser, water)
        # update draw interface
        drawi.data.parentref=scnobj.data.getRef()

    Export = staticmethod(_Export)

    def export_obj(self,obj,SceneNodeRef,isdynamic,softVolParser, water = False):

        if obj.type != "MESH":
            return

        # Get Object Name
        name = obj.name

        #Get the Mesh data
        # to_mesh allows us to apply all modifiers firsthand
        mesh = obj.to_mesh(bpy.context.scene, True, "RENDER", True)
        
        # triangulate the newly created mesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        del bm

        #Set up some stuff
        root = self.getRoot()
        blendSpan = water
        weightCount = 0
        materialGroups = []
        spansList = {}
        objscript = AlcScript.objects.Find(obj.name)

        #Begin exporting
        print(" [Draw Interface %s]" % name)

        if obj.show_transparent:
            blendSpan = True

        # First see if we have any materials associated with the mesh:
        matcount = 0
        for mat in obj.data.materials:
            if not mat is None:
                matcount = matcount + 1

        # And if not, then fail miserably >:D
        if matcount == 0:
            try:
                defaultmat = bpy.data.materials["DEFAULT"]
            except:
                defaultmat = bpy.data.materials.new("DEFAULT")
                # setup the material: ideally we'd use shadeless and no specularity, but it might make
                # the object hard to see. So we'll just disable specularity.
                defaultmat.specular_intensity = 0
            print("    Object %s does not have a material, adding one for you..." % obj.name)
            mesh.materials.append(defaultmat)


        # Calculate the amount of UV Maps
        uvMapsCount = len(mesh.uv_layers)

        # build up a weight map if neccessary, and fill it with the default value to start with
        if len(obj.vertex_groups) > 0:
            weightCount = 1 # Blender supports only one weight :)
        
        # TODO: make sure this is correct
        if len(obj.modifiers) > 0 and len(obj.vertex_groups) > 0:
            raise RuntimeException("This object has both modifiers (" + ", ".join(m.name for m in obj.modifiers) + ") and vertex groups, which is not supported by PyPRP.")

        # recompute the normals if requested (they will be overwritten with Blender-computed normals again next time edit mode is exited for the mesh)
        if getTextPropertyOrDefault(obj, "renormal", FindInDict(objscript, "visual.renormal", None)) == "areaweighted":
            # compute vertex normals as the average of the face normals of all faces adjacent to the vertex, weighted by face area
            normals = [Mathutils.Vector((0, 0, 0)) for i in range(len(mesh.vertices))]
            for f in mesh.polygons:
                n = f.area*f.normal
                for v in f:
                    normals[v.index] += n
            for i, n in enumerate(normals):
                n.normalize()
                if n.length > 0: # keep the existing normal if the newly computed one ended up as zero (NaN after normalizing)
                    mesh.verts[i].no = n
            del normals # help the garbage collector

        # Now, we need to make groups of faces for each assigned material :)
        # initialize the MaterialGroups list
        for mat in mesh.materials:
            if not mat is None:
                useSticky = 0

                # Loop through Layers
                for mtex in mat.texture_slots:
                    if not mtex is None:
                        if mtex.texture_coords == "STICK" and mesh.vertexUV:
                            useSticky = 1

                UVCount = uvMapsCount + useSticky

                materialGroups.append({ 'faces': [], \
                                        'vertices': [], \
                                        'mat': mat, \
                                        'vtxdict': {}, \
                                        'vtxalphacol': False, \
                                        'WeightCount': weightCount, \
                                        'UVCount': UVCount, \
                                        'Sticky': useSticky \
                                      })
            else:
                # Failsafe mechanism....
                materialGroups.append(None)

        # process the faces and their vertices, and store them based on their material
        # some maps that will be heavily used
        ColorLayers = mesh.vertex_colors
        UVLayers = mesh.uv_layers

        colorMapIndex = 0
        for mface in mesh.polygons:
            if (len(mface.vertices) < 3) or (len(mface.vertices) > 4):
                raise RuntimeError("Triangulated mesh doesn't use triangles... whaaaaat ? (", len(mface.vertices) + "vertices)")

            vertIdxs = []
            baseVertexIdx = len(materialGroups[mface.material_index]["vertices"])

            index = 0
            for vector in mface.vertices:
                # convert to Plasma vertex
                v = Vertex()

                # coordinates
                v.x = mesh.vertices[vector].co[0]
                v.y = mesh.vertices[vector].co[1]
                v.z = mesh.vertices[vector].co[2]

                # normal
                v.nx = mesh.vertices[vector].normal[0]
                v.ny = mesh.vertices[vector].normal[1]
                v.nz = mesh.vertices[vector].normal[2]

                # vertex colors - TODO: bring back changes from newest version of PyPRP
                if len(ColorLayers) > 0:
                    try:
                        col_a=255
                        col_r=255
                        col_g=255
                        col_b=255
                        actindex = 0
                        for vc in ColorLayers:
                            if(vc.name.lower() == "col" or vc.name.lower() == "lightmap"): #Mesh vertex colours
                                col = vc.data[colorMapIndex].color
                                col_r=int(col.r *255)
                                col_g=int(col.g *255)
                                col_b=int(col.b *255)
                                #if col_a >= 1.0: #See if there is alpha on the colour map
                                #    col_a = mface.col[index].a
                            elif(vc.name.lower() == "alpha"): #Mesh vertex alpha
                                col = vc.data[colorMapIndex].color
                                col_a = int((col.r + col.g + col.b) / 3.0 * 255)
                                materialGroups[mface.material_index]["vtxalphacol"] = True
                                blendSpan = True
                            actindex += 1

                        v.color = RGBA(col_r,col_g,col_b,col_a)
                    except IndexError:
                        pass

                # Blend weights.
                if weightCount > 0:
                    # TODO
                    bone,weight = mesh.getVertexInfluences(vector.index)
                    v.blends = [weight,]

                # UV Maps
                for i in range(len(UVLayers)):
                    tex_u = mesh.uv_layers[i].data[mface.loop_indices[index]].uv[0]
                    tex_v = 1-mesh.uv_layers[i].data[mface.loop_indices[index]].uv[1]
                    v.tex.append([tex_u,tex_v,0])

                # Sticky Coordinates Next
                # TODO
                if materialGroups[mface.material_index]["Sticky"]:
                    sticky = [ vector.uv[0], 1 - vector.uv[1], 0 ]
                    v.tex.append(sticky)

                v_idx = -1 # to avoid unneccesary copying of vertices

                # This adds a really long waiting time...
                #Anyone know of a better way of doing this? >.>
                if True:
                    # see if we already have saved this vertex
                    try:
                        VertexDict = materialGroups[mface.material_index]["vtxdict"]
                        for j in VertexDict[v.x][v.y][v.z]:
                            vertex = materialGroups[mface.material_index]["vertices"][j]

                            if vertex.isfullyequal(v):
                                # if vertex is the same, set index to that one
                                v_idx = j
                                break # and end the search
                    except:
                        pass

                # if vertex is unique, add it
                if v_idx == -1:
                    materialGroups[mface.material_index]["vertices"].append(v)
                    v_idx = len(materialGroups[mface.material_index]["vertices"]) -1

                    # Store this one in the dict
                    VertexDict = materialGroups[mface.material_index]["vtxdict"]
                    if v.x not in VertexDict:
                        VertexDict[v.x] = {}
                    if v.y not in VertexDict[v.x]:
                        VertexDict[v.x][v.y] = {}
                    if v.z not in VertexDict[v.x][v.y]:
                        VertexDict[v.x][v.y][v.z] = []
                    VertexDict[v.x][v.y][v.z].append(v_idx)

                # and store the vertex index in our face list
                vertIdxs.append(v_idx)
                index += 1
                colorMapIndex += 1
            # TODO: bring back changes from newest versions of PyPRP
            if len(mface.vertices) == 3:
                materialGroups[mface.material_index]["faces"].append(vertIdxs)
            elif len(mface.vertices) == 4: # a quad must be separated into two triangles
                materialGroups[mface.material_index]["faces"].append([vertIdxs[0],vertIdxs[1],vertIdxs[2]]) # first triangle
                materialGroups[mface.material_index]["faces"].append([vertIdxs[0],vertIdxs[2],vertIdxs[3]]) # second triangle

        for MatGroup in materialGroups:
            if not MatGroup is None:
                mat = MatGroup['mat']
                pmat=root.find(0x07,mat.name,1)

                # export the material if needed (if it's not done before)
                ## This will create all texture layers, cubic envmaps and mipmaps, and set the blendings
                ## If no textures are associated with the material, it will take the (first) uvmap texture of
                ## the objects mesh, and use that. (For Backwards compatibility)

                if(not pmat.isProcessed):
                    pmat.data.export_mat(mat,obj)
                    pmat.isProcessed = 1

                if pmat.data.Alpha():
                    blendSpan = True

                # Create the name of this spanset
                RenderLevel = plRenderLevel()
                Criteria = 0
                Props = 0
                Suff = str(obj.pass_index)
                IntSuff = int(Suff)

                #if Suff != '0':
                #    # this seems to cause issues for my ages. Consider using sort faces (vs spans), or have an option for removing this?
                #    Criteria |= plDrawable.Crit["kCritSortSpans"] | plDrawable.Crit["kCritSortFaces"]
                #    Props = plDrawable.Props["kPropSortSpans"] | plDrawable.Props["kPropSortFaces"]
                #else:
                #    Suff = ''
                #If we force this, we could break things with incorrect guesses... ESPECIALLY if they use cluster-span-objects

                if blendSpan:
                    if IntSuff > 1:
                        RenderLevel = plRenderLevel(plRenderLevel.MajorLevel["kDefRendMajorLevel"],plRenderLevel.MajorLevel["kLateRendMajorLevel"])
                        if IntSuff > 2:
                            Criteria &= ~(plDrawable.Crit["kCritSortSpans"] | plDrawable.Crit["kCritSortFaces"])
                            Props &= ~(plDrawable.Props["kPropSortSpans"] | plDrawable.Props["kPropSortFaces"])
                    else:
                        RenderLevel = plRenderLevel(plRenderLevel.MajorLevel["kDefRendMajorLevel"],plRenderLevel.MinorLevel["kOpaqueMinorLevel"])
                    suffix = "BlendSpans" + Suff
                else:
                    suffix = "Spans" + Suff

                if water:
                    suffix = "BlendSpans" + Suff
                    RenderLevel = plRenderLevel(plRenderLevel.MajorLevel["kBlendRendMajorLevel"],plRenderLevel.MinorLevel["kOpaqueMinorLevel"])
                    Criteria = plDrawable.Crit["kCritSortFaces"]
                    Props = plDrawable.Props["kPropSortFaces"]
                
                #DO NOT TOUCH!!!
                #unless you know what *every* flag does and what needs to be set for each object!
                if (FindInDict(objscript, "visual.renderlevel", 0) != 0):
                    MAJ = 0
                    MIN = 0
                    
                    major = FindInDict(objscript, "visual.renderlevel.major", [])
                    if type(major) == list:
                        for flag in major:
                            if flag.lower() in plDrawInterface.scriptRenderLevels:
                                MAJ |= plDrawInterface.scriptRenderLevels[flag.lower()]

                    minor = FindInDict(objscript, "visual.renderlevel.minor", [])
                    if type(minor) == list:
                        for flag in minor:
                            if flag.lower() in plDrawInterface.scriptRenderLevels:
                                MIN |= plDrawInterface.scriptRenderLevels[flag.lower()]

                    RenderLevel = plRenderLevel(MAJ,MIN)
                
                flags = FindInDict(objscript, "visual.drawflags", [])
                if type(flags) == list:
                    for flag in flags:
                        if flag.lower() == "sortfaces":
                            Criteria |= plDrawable.Crit["kCritSortFaces"]
                            Props |= plDrawable.Props["kPropSortFaces"]
                        elif flag.lower() == "sortspans":
                            Criteria |= plDrawable.Crit["kCritSortSpans"]
                            Props |= plDrawable.Props["kPropSortSpans"]
                        elif flag.lower() == "character":
                            Criteria |= plDrawable.Crit["kCritCharacter"]
                            Props |= plDrawable.Props["kPropCharacter"]
                        elif flag.lower() == "static":
                            Criteria |= plDrawable.Crit["kCritStatic"]
                        elif flag.lower() == "nodraw":
                            Props |= plDrawable.Props["kPropNoDraw"]
                        elif flag.lower() == "volatile":
                            Props |= plDrawable.Props["kPropVolatile"]
                        elif flag.lower() == "noresort":
                            Props |= plDrawable.Props["kPropNoReSort"]
                        elif flag.lower() == "partialsort":
                            Props |= plDrawable.Props["kPropPartialSort"]
                        elif flag.lower() == "sortasone":
                            Props |= plDrawable.Props["kPropSortAsOne"]
                        elif flag.lower() == "hasvislos":
                            Props |= plDrawable.Props["kPropHasVisLOS"]
                
                crit = FindInDict(objscript, "visual.criteria", [])
                if type(crit) == list:
                    Criteria = 0
                    for c in crit:
                        if c.lower() == "sortfaces":
                            Criteria |= plDrawable.Crit["kCritSortFaces"]
                        elif c.lower() == "sortspans":
                            Criteria |= plDrawable.Crit["kCritSortSpans"]
                        elif c.lower() == "character":
                            Criteria |= plDrawable.Crit["kCritCharacter"]
                        elif c.lower() == "static":
                            Criteria |= plDrawable.Crit["kCritStatic"]

                Name_RenderLevel = "%08x" % RenderLevel.fLevel
                Name_Crit = "%x" % Criteria
                DSpansName = str(root.name) + "_District_" + str(root.page) + "_" + Name_RenderLevel + "_" + Name_Crit + suffix

                # Create the entry if it doesn't exist yet...
                if DSpansName not in spansList:
                    spansList[DSpansName] = {'MatGroups': [], \
                                             'RenderLevel': RenderLevel.fLevel, \
                                             'Criteria': Criteria, \
                                             'Props': Props \
                                            }

                # And append this material to it...
                spansList[DSpansName]['MatGroups'].append(MatGroup)

        for DSpans_key in list(spansList.keys()):
            DSpans = spansList[DSpans_key]
            drawspans = plDrawableSpans.FindCreate(root,DSpans_key)
            drawspans.data.fSceneNode = SceneNodeRef
            drawspans.data.fRenderLevel.fLevel = DSpans['RenderLevel']
            drawspans.data.fCriteria = DSpans['Criteria']
            drawspans.data.fProps = DSpans['Props']
            #export the object
            setnum=drawspans.data.export_obj(obj, isdynamic, DSpans['MatGroups'], water)
            self.addSpanSet(setnum, drawspans.data.getRef())

        propString = FindInDict(objscript,"visual.visregions", [])
        if type(propString) == list:
            for reg in propString:
                if (reg != None):
                    if(softVolParser != None and softVolParser.isStringProperty(str(reg))):
                        volume = softVolParser.parseProperty(str(reg),str(self.Key.name))
                    else:
                        refparser = ScriptRefParser(self.getRoot(),str(self.Key.name),"softvolume")
                        volume = refparser.MixedRef_FindCreateRef(reg)
                    vr = root.find(0x0116, volume.Key.name, 1)
                    vr.data.scenenode=SceneNodeRef
                    vr.data.BitFlags.clear()
                    vr.data.BitFlags.SetBit(plVisRegion.VecFlags["kReplaceNormal"])
                    vr.data.fRegion = volume
                    self.fRegions.append(vr.data.getRef())
        
        
        # finally, clear the temporary mesh from Blender's resources.
        bpy.data.meshes.remove(mesh)


class plInstanceDrawInterface(plDrawInterface):
    def __init__(self,parent,name="unnamed",type=0x00D2):
        plDrawInterface.__init__(self,parent,name,type)

        self.fTargetID=-1
        self.fDrawable = UruObjectRef()

    def _Find(page,name):
        return page.find(0x00D2,name,0)
    Find = staticmethod(_Find)

    def _FindCreate(page,name):
        return page.find(0x00D2,name,1)
    FindCreate = staticmethod(_FindCreate)

    def read(self,stream):
        plDrawInterface.read(self,stream)

        self.fTargetID = stream.Read32()
        self.fDrawable.read(stream)

    def write(self,stream):
        plDrawInterface.write(self,stream)

        stream.Write32(self.fTargetID )
        self.fDrawable.write(stream)

    def import_obj(self,obj):
        plDrawInterface.import_obj(self,obj)
        root = self.getRoot()
        print(" [InstanceDrawInterface %s]"%(str(self.Key.name)))

        # Import all drawables in this list

        drawspans = root.findref(self.fDrawable)
        drawspans.data.import_mesh(obj,self.fTargetID)

    def _Import(scnobj,prp,obj):
        plDrawInterface.Import(scnobj,prp,obj)
    Import = staticmethod(_Import)

    def _Export(page,obj,scnobj,name,SceneNodeRef,isdynamic=0):
        plDrawInterface.Export(page,obj,scnobj,name,SceneNodeRef,isdynamic)
    Export = staticmethod(_Export)

