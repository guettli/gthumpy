#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 $Id: ChangeDirectory.py 178 2011-11-09 10:38:16Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/ChangeDirectory.py $
"""

# Python
import glob
import os

import gtk
import datetime

from kiwi.ui.objectlist import Column

# gthumpy
import filebrowser
from Utils import try_unicode, filename_to_base_dir
import Global
from gthumpy import GthumpyUtils


class GthumpyTreeNode(object):
    skip=False
    empty=False
    dummy=False
    loaded=True
    
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.pathname)
    
    def __init__(self, pathname, dummy=False):
        assert isinstance(pathname, basestring), pathname
        self.pathname=pathname
        self.dummy=dummy
        if not os.path.isdir(pathname):
            self.skip=True
            return
        self.name=os.path.basename(pathname)
        if self.name.startswith('.'):
            self.skip=True
            return
        if dummy:
            return
        try:
            self.description=try_unicode(open(os.path.join(pathname, 'description.txt')).read())
        except IOError:
            self.description=''
        try:
            files=os.listdir(self.pathname)
        except OSError:
            return
        files.sort()
        dir_count=0
        file_count=0
        img_count=0
        for file in files:
            if file in ['.xvpics']:
                continue
            file=os.path.join(self.pathname, file)
            if os.path.isdir(file):
                dir_count+=1
            else:
                file_count+=1
                if file.lower().endswith('.jpg'):
                    img_count+=1
        self.dir_count=dir_count
        self.file_count=file_count
        self.img_count=img_count
        if not self.dir_count:
            self.empty=True


class Tree(filebrowser.Tree):
    def __init__(self, *args, **kwargs):
        TreeNode=kwargs.pop('TreeNode', None)
        if not TreeNode:
            kwargs['TreeNode']=GthumpyTreeNode
        filebrowser.Tree.__init__(self, *args, **kwargs)

class ChangeDirectory(object):
    def start(self):
        Global.app.cursorHourglass()
        window=gtk.Window()
        window.set_position(gtk.WIN_POS_CENTER)
        window.set_modal(True)
        window.set_transient_for(Global.app.window)
        self.window=window
        Global.app.load_size_of_win(self)
        window.connect("delete-event", self.onDelete)
        self.tree=Tree([Column('name'), 
                        Column('img_count', justify=gtk.JUSTIFY_RIGHT), 
                        Column('dir_count', justify=gtk.JUSTIFY_RIGHT), 
                        Column('file_count', justify=gtk.JUSTIFY_RIGHT),
                        Column('description')])
        self.tree._treeview.connect('row-activated', self.on_activated)
        vbox=gtk.VBox()
        vbox.add(self.tree)
        self.only_without_stars=gtk.CheckButton('Nur Bilder ohne Sternchen laden')
        vbox.pack_start(self.only_without_stars, False)
        load_current_dir=gtk.Button('Aktuellstes Verzeichnis laden')
        load_current_dir.connect('clicked', self.load_most_current_directory)
        vbox.pack_start(load_current_dir, False)

        self.window.add(vbox)
        if os.path.exists(Global.app.dir):
            self.tree.expand_path(Global.app.dir)
        self.window.show_all()
        gtk.main()
        Global.app.cursorHourglass(False)

    def load_most_current_directory(self, widget, data=None):
        base=filename_to_base_dir(Global.app.dir)
        for i in range(400):
            start=datetime.date.today()+datetime.timedelta(days=2-i)
            first_try=os.path.join(base, str(start.year), '%02d' % start.month, '%02d' % start.day)
            try:
                first_try=glob.glob('%s*' % first_try)[0]
            except IndexError:
                continue
            break
        next=GthumpyUtils.find_next(first_try, jump=GthumpyUtils.JUMP_PREV)
        self.load_directory(next)

    def restart(self):
        Global.app.cursorHourglass()
        self.window.show_all()
        if os.path.exists(Global.app.dir):
            self.tree.expand_path(Global.app.dir)
        gtk.main()
        Global.app.cursorHourglass(False)
        
    def onDelete(self, widget=None, event=None):
        Global.app.save_size_of_win(self)
        self.window.hide()
        #self.window.destroy()
        #for tree_node in self.tree.iter_values():
        #    print value
        gtk.main_quit()
        return True

    def on_activated(self, treeview, path, column):
        node=self.tree._model[path][0]
        index=self.tree._treeview.get_columns().index(column)
        if index==4:
            ed=EditDescription(os.path.join(node.pathname, 'description.txt'))
            if not ed.newtext is None:
                node.description=ed.newtext
            self.window.window.show()
            return
        self.load_directory(node.pathname)

    def load_directory(self, dir_name):
        Global.app.set_dir(dir_name)
        gtk.main_quit()
        self.window.hide()
    
class EditDescription:
    def __init__(self, filename):
        window=gtk.Window()
        self.window=window
        self.filename=filename
        if os.path.exists(filename):
            fd=open(filename) # .../2004-12-13/description.txt
            descr=unicode(fd.read().strip(), "latin1")
            fd.close()
        else:
            descr=""
        vbox=gtk.VBox()
        view=gtk.TextView()
        # klappt nicht: view.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM, 5)
        self.description=gtk.TextBuffer()
        self.description.insert(self.description.get_iter_at_offset(0),
                descr)
        view.set_buffer(self.description)
        view.set_wrap_mode(gtk.WRAP_WORD)
        view.set_editable(1)
        vbox.add(view)
        hbox=gtk.HButtonBox()
        hbox.set_layout(gtk.BUTTONBOX_SPREAD)
        button_cancel=gtk.Button("Cancel")
        button_cancel.connect("clicked", self.onDelete)
        hbox.add(button_cancel)
        button_ok=gtk.Button("OK")
        button_ok.connect("clicked", self.onOK)
        hbox.add(button_ok)
        vbox.add(hbox)
        window.add(vbox)
        window.set_size_request(500, 200)
        window.set_position(gtk.WIN_POS_MOUSE)
        window.set_modal(True)
        window.set_transient_for(Global.app.window)
        window.set_title("Gthumpy: Edit Description: %s" %
                         os.path.basename(os.path.dirname(filename)))
        window.connect("delete-event", self.onDelete)
        window.show_all()
        self.newtext=None
        gtk.main()
        
    def onOK(self, widget):
        desc=self.description.get_text(
            self.description.get_iter_at_offset(0),
            self.description.get_iter_at_offset(-1)).strip()
        fd=open(self.filename, "wt")
        fd.write(desc.encode("latin1"))
        fd.close()
        self.newtext=desc
        self.onDelete()

    def onDelete(self, widget=None, event=None):
        """
        EditDescription.onDelete
        """
        self.window.destroy()
        gtk.main_quit()
