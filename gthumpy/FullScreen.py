# -*- coding: iso-8859-1 -*-

"""
 $Id: FullScreen.py 180 2011-12-28 22:38:50Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/FullScreen.py $
"""

# Python GTK
import gtk

# My Imports
import Global

class FullScreen:
    def __init__(self, parent):
        self.window=gtk.Window()
        self.window.set_transient_for(parent.window)
        self.window.set_decorated(False)
        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.box=gtk.VBox(False, 0)
        self.window.add(self.box)
        self.window.fullscreen()
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0))
        self.window.connect("key-press-event", Global.app.onKeyEvent)
        self.window.show_all()
        self.cursor=gtk.gdk.Cursor( # Invisible
            gtk.gdk.Pixmap(None, 1, 1, 1),
            gtk.gdk.Pixmap(None, 1, 1, 1),
            gtk.gdk.Color(0,0,0),
            gtk.gdk.Color(0,0,0),
            0, 0)
        self.window.window.set_cursor(self.cursor)
        self.window.connect("delete-event", self.onDelete)
        screen=self.window.get_screen()
        monitor=screen.get_monitor_geometry(screen.get_monitor_at_window(self.window.window))
        self.width=monitor.width
        self.height=monitor.height
        self.gtkimage=None

    def loadImage(self):
        """
        Fullscreen.loadImage
        """
        image=Global.app.image
        if not image:
            return
        pixbuf=Global.app.imageCache.get(image.filename, *Global.app.size())
        if self.gtkimage:
            self.gtkimage.destroy()
        gtkimage=gtk.Image()
        gtkimage.set_from_pixbuf(pixbuf)
        self.box.add(gtkimage)
        self.gtkimage=gtkimage
        self.window.show_all()

    def onDelete(self, widget=None, event=None):
        """
        Fullscreen.onDelete
        """
        self.window.destroy()
        Global.app.fullscreen=None
        Global.app.cursorHourglass(main_iteration=False)
        Global.app.loadImageIdle(force=True)
