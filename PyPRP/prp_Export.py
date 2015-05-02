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
"""
Name: 'PyPRP'
Blender: 245
Group: 'Export'
Submenu: 'Generate Release (.age)' e_age_final
Submenu: 'All as full age (.age)' e_age
Submenu: 'All as full age, per-page textures (.age)' et_age
Submenu: 'Selection as full age (.age)' es_age
Submenu: 'Generate single PRP with Release settings (.prp)' e_prp_final
Submenu: 'All as single prp (.prp)' e_prp
Submenu: 'All as single prp, per-page textures (.prp)' et_prp
Submenu: 'All as single prp, per-page textures+generate BuiltIn (.prp)' etb_prp
Submenu: 'Selection as single prp (.prp)' es_prp
Tooltip: 'GoW PyPRP Exporter'
"""

#temporany removed options
#Submenu: 'Selection as raw span (.raw)' es_raw_span
#Submenu: 'Selection as raw span (merge) (.raw)' esm_raw_span

__author__ = "GoW PyPRP Team"
__url__ = ("blender", "elysiun",
"Author's homepage, http://www.guildofwriters.com")
__version__ = "GoW PRP Exporter"

__bpydoc__ = """\
This script attempts to export scenes to the PRP format
used in URU.
"""

from PyPRP import prp_Config
prp_Config.startup()

import time, sys
from bpy import *
from os.path import *
from prp_ResManager import *
from prp_Types import *
from prp_AlcScript import *

from threading import Thread

## attempt at speeding up export by processing pages on different cores
class PrpExportThread(Thread):
    def __init__(self, page, selection):
        Thread.__init__(self)
        self.page = page
        self.selection = selection
    
    def run(self):
        self.page.export_all(self.selection)



def export_age(agename,basepath,selection=0,merge=0,pagename=None, doBuiltIn=False):
    print("Exporting age %s" %agename)
    # load the alcscript
    AlcScript.LoadFromBlender()
    rmgr=alcResManager(basepath,prp_Config.ver0,prp_Config.ver2)
    if merge:
        rmgr.preload()
    rmgr.export_book(agename,selection)
    age=rmgr.findAge(agename)
    age.write()
    #first load
    if merge:
        for page in age.pages:
            page.load()
    if not merge and pagename!=None:
        for page in age.pages:
            if page.name=="Textures":
                page.load()
    #pre-create PrpFile objects for all pages, otherwise we are unable to export references to objects in later pages while processing an earlier page
    for page in age.pages:
        if page.prp==None:
            page.prp=PrpFile(page)
            page.update_page()
    #now export
    for page in age.pages:
        if page.name=="Textures":
            page.export_all(selection)
    """processes = []
    for page in age.pages:
        if (pagename==None or page.name==pagename or (page.name=="BuiltIn" and doBuiltIn)) and page.name!="Textures":
            p = PrpExportThread(page, selection)
            p.start()
            processes.append(p)
    for processus in processes:
        processus.join() #"""
    for page in age.pages:
        if (pagename==None or page.name==pagename or (page.name=="BuiltIn" and doBuiltIn)) and page.name!="Textures":
            page.export_all(selection)
    #save
    print("") # for formatting of output
    for page in age.pages:
        if pagename==None or page.name=="Textures" or page.name==pagename or (page.name=="BuiltIn" and doBuiltIn):
            page.save()
    #unload
    for page in age.pages:
        page.unload()
    #generate the funny file
    print("Writing %s" %(agename + ".fni"))
    initxt=alcFindBlenderText("init")
    fnitxt=""
    for line in initxt.lines:
        fnitxt=fnitxt + line.body + "\r\n"
    fnitxt=fnitxt[:-2]
    if fnitxt!="":
        age.setInit(fnitxt)
    #generate sum files
    print("Computing Checksums...")
    old_style=0
    if prp_Config.ver2==11:
        old_style=1
    age.mfs.update()
    print("Writing %s" %(agename + ".sum"))
    age.mfs.writesum(basepath + "/" + agename + ".sum",old_style)


def open_file(filename, args):
    try:
        import psyco
        psyco.profile()
    except ImportError:
        print("Psyco not available to PyPRP...")
    start=time.clock()
    log=ptLog(sys.stdout,filename + ".log","w")
    std=sys.stdout
    sys.stdout=log
    print("Exporting %s ..." % filename)
    print("Args are %s " % args)
    ext=".raw"
    w = args.split("_")
    print(w)
    ext="." + w[1]
    basepath = dirname(filename)
    if filename.find(ext,-4) == -1:
        raise RuntimeError("ERROR: Unsuported file %s, expecting an %s file" %(filename,ext))
    #check if final
    final=0
    try:
        if w[2]=="final":
            final=1
    except IndexError:
        pass
    if final:
        prp_Config.texture_compression=1
        prp_Config.vertex_compression=0
    else:
        prp_Config.texture_compression=0
        prp_Config.vertex_compression=0
    if w[1]=="age":
        agename = basename(filename[:-4])
        if w[0]=="e":
            selection=0
            merge=0
            pass
        elif w[0]=="et":
            selection=0
            merge=0
            prp_Config.export_textures_to_page_prp = 1
            pass
        elif w[0]=="es":
            selection=1
            merge=0
            pass
        elif w[0]=="em":
            selection=0
            merge=1
            pass
        elif w[0]=="esm":
            selection=1
            merge=1
            pass
        else:
            raise RuntimeError("Unimplemented option %s" %(args))
        export_age(agename,basepath,selection,merge)
    elif w[1]=="prp":
        pagea = basename(filename[:-4])
        page=pagea.split("_")
        agename = page[0]
        pagename = pagea[len(page[0]) + 1 + len(page[1]) + 1:]
        builtin = False
        if w[0]=="e":
            selection=0
            merge=0
            pass
        elif w[0]=="et":
            selection=0
            merge=0
            prp_Config.export_textures_to_page_prp = 1
            pass
        elif w[0]=="etb": ## to generate BuiltIn file
            selection=0
            merge=0
            prp_Config.export_textures_to_page_prp = 1
            builtin = True
            pass
        elif w[0]=="es":
            selection=1
            merge=0
            pass
        elif w[0]=="em":
            selection=0
            merge=1
            pass
        elif w[0]=="esm":
            selection=1
            merge=1
            pass
        else:
            raise RuntimeError("Unimplemented option %s" %(args))
        export_age(agename,basepath,selection,merge,pagename, builtin)
    else:
        raise RuntimeError("Unimplemented option %s" %(args))
    stop=time.clock()
    print("done in %.2f seconds" % (stop-start))
    sys.stdout=std
    log.close()
