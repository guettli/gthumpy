# -*- coding: iso-8859-1 -*-

"""
 $Id: EditFlags.py 166 2010-02-01 19:57:13Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/EditFlags.py $
"""

# Python Imports
import os

# Python GTK
import gtk
import gobject

# Kiwi Imports
from kiwi.ui import dialogs
from kiwi.ui.objectlist import ObjectTree, Column

# My Imports
import Utils
import Global
from Image import Image
from Flag import Flag, AllFlags

class EditFlags:
    last_flag=None
    oldsize=(600, 400)
    def __init__(self, default=False, dialog=True, parent=None):
        assert os.path.isdir(Global.app.config.flags_dir)
        self.dialog=dialog
        if dialog:
            # Displayed as PopUp (All Images -> ActionMenu -> Flag selected Images)
            self.window=gtk.Dialog(
                "Edit Flags", parent,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT)
            #print self.window.get_resizable()
            self.window.resize(*self.oldsize)
            vbox=self.window.vbox
        else:
            assert not default
            self.window=Global.app.flagscontainer
            vbox=gtk.VBox()
            self.window.add(vbox)
        self.objecttree=ObjectTree([
            Column("name", sorted=True, expand=True),
            Column("checked", title=" ", data_type=bool, editable=True),
            Column("length", data_type=int)
            ])
        self.allflags=AllFlags(self.objecttree)
        vbox.add(self.objecttree)
        self.close_on_first=gtk.CheckButton("Close on first change")
        self.close_on_first.set_active(True)
        self.loadflagfiles()
        if dialog:
            vbox.pack_start(self.close_on_first, False)
        else:
            self.close_on_first.set_active(False)
        bb=gtk.VButtonBox()
        self.newflag=gtk.Entry()
        self.newflag.connect("activate", self.onAdd)
        bb.add(self.newflag)
        btnew=gtk.Button("Add Flag")
        btnew.connect("clicked", self.onAdd)
        bb.add(btnew)
        if not dialog:
            load=gtk.Button("Load files of selected flag")
            load.connect("button-press-event", self.onLoad)
            bb.add(load)
        vbox.pack_start(bb, False)
        
        if dialog:
            cancel=gtk.Button("Close")
            cancel.connect("clicked", self.onDelete)
            vbox.pack_start(cancel, False)
            self.window.show_all()
            self.window.connect("delete-event", self.onDelete)
            self.window.run()
        else:
            self.window.show_all()

    def onLoad(self, widget, event):
        """
        Load files of active flag
        """
        fi=self.objecttree.get_selected()
        if not fi:
            print 'onLoad Nothing selected'
            return
        linkdir=os.path.join(fi.dirname, "links")
        files=os.listdir(linkdir)
        files.sort()
        print 'onLoad'
        images=[]
        for file in files:
            fileabs=os.path.join(linkdir, file)
            if not os.path.islink(fileabs):
                print 'no Link', fileabs
                continue
            file=os.readlink(fileabs)
            if not os.path.exists(file):
                print 'Does not exist', file
                continue
            print 'onLoad append', file
            images.append((file.split('/'), file))
        images.sort()
        Global.app.images=[Image(file) for deco, file in images]
        Global.app.image=None
        Global.app.dirname="Files of Flag %s" % (fi.name)
        if Global.app.all:
            Global.app.all.onDelete(destroy=True)
        Global.app.loadImage()
        
    def loadflagfiles(self):
        """
        Read available flags
        """
        if not self.dialog:
            self.allflags.image=Global.app.image
        if not Global.app.image:
            assert not self.dialog
            return
        self.allflags.load()
        
    def onAdd(self, widget):
        name=self.newflag.get_text().strip()
        if not name:
            return
        if "/" in name or "\\" in name:
            print "Flagname not valid", name
            return
        flag=self.objecttree.get_selected()
        if flag:
            if not Utils.yesNoDialog(Global.app.window, 
                "Create new flag below %s (yes).\n Or create toplevel flag (no)" %
                                 flag.name):
                flag=False
        if not flag:
            dirname=os.path.join(Global.app.config.flags_dir, name)
        else:
            dirname=os.path.join(flag.dirname, name)
        if os.path.exists(dirname):
            return
        os.mkdir(dirname)
        linkdir=os.path.join(dirname, "links")
        os.mkdir(linkdir)
        self.loadflagfiles()
        self.newflag.set_text("")

    def onDelete(self, widget=None, event=None):
        "EditFlags.onDelete"
        self.window.destroy()
        Global.app.editflags.loadflagfiles()

                
            
