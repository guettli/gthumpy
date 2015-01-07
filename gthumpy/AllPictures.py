# -*- coding: iso-8859-1 -*-

"""
 $Id: AllPictures.py 152 2008-08-27 21:15:14Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/AllPictures.py $
"""

# Python Imports
import os
import time

# Python GTK
import gtk

# My Imports
import Utils
import Global
from Config import Config
import GthumpyUtils
import GthumpyParser
from ActionMenu import ActionMenu
from EditFlags import EditFlags

class AllPictures:
    main_called=False
    def __init__(self):
        if not Global.app.images:
            return
        self.deleted=False
        window=gtk.Window()
        window.set_position(gtk.WIN_POS_CENTER)
        self.window=window
        scroll=gtk.ScrolledWindow()
        self.scroll=scroll
        scroll.set_size_request(600, 400)
        vbox=gtk.VBox()
        self.progressbar=gtk.ProgressBar()
        vbox.pack_start(self.progressbar, False)

        liststore=gtk.ListStore(
            gtk.gdk.Pixbuf, # gtk.Button,   # Image Button
            str, # gtk.EventBox, # Flags
            str, # gtk.EventBox, # Date and Name
            )
        self.liststore=liststore
        treeview=gtk.TreeView(liststore)
        treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.treeview=treeview
        treeviewcolumn_image=gtk.TreeViewColumn("Image")
        treeview.append_column(treeviewcolumn_image)
        cell_image=gtk.CellRendererPixbuf()
        treeviewcolumn_image.pack_start(cell_image, False)
        treeviewcolumn_image.set_attributes(cell_image, pixbuf=0)
        
        treeviewcolumn_flags=gtk.TreeViewColumn("Flags")
        treeview.append_column(treeviewcolumn_flags)
        cell_flags=gtk.CellRendererText()
        treeviewcolumn_flags.pack_start(cell_flags, False)
        treeviewcolumn_flags.set_attributes(cell_flags, text=1)
        
        treeviewcolumn_info=gtk.TreeViewColumn("Info")
        treeview.append_column(treeviewcolumn_info)
        cell_info=gtk.CellRendererText()
        treeviewcolumn_info.pack_start(cell_info, False)
        treeviewcolumn_info.set_attributes(cell_info, text=2)
        
        treeview.connect("row-activated", self.onImage)
        treeview.connect("button_press_event", self.onButtonPressed)
        
        scroll.add(treeview)
        vbox.add(scroll)
        
        self.parser=GthumpyParser.GthumpyParser()
        currButton=None
        window.add(vbox)
        window.set_modal(True)
        window.set_transient_for(Global.app.window)
        if Global.app.dir:
            dir=os.path.basename(Global.app.dir)
        else:
            dir=Global.app.dirname
        window.set_title("All Pictures of %s" % dir)
        window.connect("delete-event", self.onDelete)
        window.show_all()
        self.window=window
        self.buttons=[]
        self.last_selected=None
        self.rows=[]
        Global.app.all=self
        Global.app.load_size_of_win(self)

    def load(self):
        image=Global.app.images[0]
        while image:
            len_images=len(Global.app.images)
            if not os.path.exists(image.filename):
                print image.filename, "does not exist"
                next=image.next
                image.delete(unlink=False)
                image=next
                continue
            i=image.index
            preview=Utils.file2preview(image.filename)
            self.liststore.append((preview, "", ""))
            try:
                self.updateRow(image)
            except GthumpyUtils.NoImageException, exc:
                print exc
                image=image.next
                continue
            self.progressbar.set_fraction((i+1)/float(len_images))
            self.progressbar.set_text("%sv%s" % (i+1, len_images))
            while gtk.events_pending():
                gtk.main_iteration(False)
            image=image.next
            
        va=self.scroll.get_vadjustment()
        if va.get_value()==0:
            # Don't jump to the current image, if the user has scrolled
            # while the window creates all thumbnails.
            self.scroll_to_current()

        self.window.show_all()
        self.main_called=True
        gtk.main()
        self.main_called=False
        
    def onImage(self, treeview, path, view_column):
        self.onDelete()
        Global.app.loadImage(path[0])
        
        
    def updateRow(self, image):
        myflags=image.flags()
        self.liststore[image.index][1]='\n'.join(
            [flag.name for flag in myflags])

        info=[]
        name=GthumpyUtils.image2name(image.filename)
        gthumpy="%s.gthumpy" % name
        if not os.path.exists(gthumpy):
            date=""
            title=""
            description=""
        else:
            self.parser.parse(gthumpy)
            title=self.parser.title
            description=self.parser.description
        date=image.exifdict.get("Image DateTime", "")
        try:
            title=unicode(title)
        except UnicodeDecodeError:
            title=unicode(title, "latin1")
        self.liststore[image.index][2]=unicode("%sv%s  %s %s\n%s" % (
            image.index+1, len(Global.app.images), date, os.path.basename(name),
            title))

    def onButtonPressed(self, widget, event):
        if event.button==3:
            # right mouse button: Context Menu
            ActionMenu(event)
            return True
        
    def scroll_to_current(self):
        index=Global.app.image.index
        self.treeview.scroll_to_cell(index)

    def onDelete(self, widget=None, event=None, destroy=False):
        """
        AllPictures.onDelete
        """
        # Don't destroy() the window. Reuse it, since it
        # can take long to create it.
        Global.app.save_size_of_win(self)
        if destroy:
            self.window.destroy()
            self.window=None
            Global.app.all=None
        else:
            self.window.hide()
        self.deleted=True
        if self.main_called:
            gtk.main_quit()
        return True


