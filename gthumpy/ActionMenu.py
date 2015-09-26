# -*- coding: iso-8859-1 -*-

"""
 $Id: ActionMenu.py 178 2011-11-09 10:38:16Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/ActionMenu.py $
"""

# Python Imports
import os
import re
import glob
import shutil
import subprocess

# Python GTK
import gtk

# My Imports
import Global
from EditFlags import EditFlags
from Flag import Flag

class ActionMenu:
    """
    Popup Menu of AllPictures
    """
    def __init__(self, event):
        model, rows = Global.app.all.treeview.get_selection().get_selected_rows()
        selected=len(rows)

        self.menu=gtk.Menu()
        msg=gtk.MenuItem("%d Files Selected" % selected)
        msg.set_sensitive(False)
        self.menu.add(msg)
        self.menu.add(gtk.SeparatorMenuItem())
        
        # Select/Deselect All
        mis=gtk.MenuItem("Select All")
        mis.connect("activate", self.onSelectAll, True)
        self.menu.append(mis)
        mis=gtk.MenuItem("Deselect All")
        mis.connect("activate", self.onSelectAll, False)
        mis.set_sensitive(selected)
        self.menu.append(mis)

        # Flag Selected
        mi=gtk.MenuItem("Flag Selected")
        mi.connect("activate", self.onFlagSelected)
        mi.set_sensitive(selected)
        self.menu.append(mi)

        if EditFlags.last_flag:
            msg=gtk.MenuItem("Set last Flag (%s)" %
                             EditFlags.flagfile2name(EditFlags.last_flag))
            msg.connect("activate", self.onSetLastFlag)
            self.menu.add(msg)

        else:
            msg=gtk.MenuItem("Set last Flag ()")
            msg.set_sensitive(False)
            self.menu.add(msg)
            
        # Move / Copy / Delete Selected
        mis=gtk.MenuItem("Move Selected Files")
        mis.connect("activate", self.onCopy, True)
        mis.set_sensitive(selected)
        self.menu.append(mis)

        mis=gtk.MenuItem("Copy Selected Files")
        mis.connect("activate", self.onCopy, False)
        mis.set_sensitive(selected)
        self.menu.append(mis)

        mis=gtk.MenuItem("Delete Selected Files")
        mis.connect("activate", self.onDeleteFiles)
        mis.set_sensitive(selected)
        self.menu.append(mis)

        mis=gtk.MenuItem("Send selected to hugin")
        mis.connect("activate", self.onSendToHugin)
        mis.set_sensitive(selected)
        self.menu.append(mis)

        mis=gtk.MenuItem("Send selected to Qtpfsgui")
        mis.connect("activate", self.onSendToQtpfsgui)
        mis.set_sensitive(selected)
        self.menu.append(mis)

        mis=gtk.MenuItem("Send selected by email")
        mis.connect("activate", self.onSendToEmail)
        mis.set_sensitive(selected)
        self.menu.append(mis)

        self.menu.show_all()
        self.menu.popup(None, None, None, event.button, event.time)


    def selectedimages(self):
        model, rows = Global.app.all.treeview.get_selection().get_selected_rows()
        images=[]
        for row in rows:
            images.append(Global.app.images[row[0]])
        return images
            
    def onSetLastFlag(self, widget=None):
        assert EditFlags.last_flag
        self.onFlag(flagfile=EditFlags.last_flag)
        
    def onSelectAll(self, widget, select=True):
        assert select in [True, False]
        selection=Global.app.all.treeview.get_selection()
        for path in Global.app.all.liststore:
            if select:
                selection.select_path(path.path)
            else:
                selection.unselect_path(path.path)
                

    def onDeleteFiles(self, widget):
        Global.app.cursorHourglass()
        for image in self.selectedimages():
            image.delete()
        Global.app.cursorHourglass(False)
           
    def onSendToHugin(self, widget):
        Global.app.cursorHourglass()
        dialog = gtk.Dialog('Basename for Panorama', Global.app.all.window,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        label=gtk.Label(u'Name of panorama')
        entry=gtk.Entry()
        dialog.vbox.pack_start(entry)
        error=gtk.Label()
        dialog.vbox.pack_start(error)
        dialog.show_all()
        while True:
            response=dialog.run()
            print response
            name=entry.get_text()
            regex=r'^[a-zA-Z0-9_-]+$'
            if not re.match(regex, name):
                error.set_text(r'Name does not match regular expression %s' % regex)
                continue
            break
        dialog.destroy()
        first_image=self.selectedimages()[0].filename
        base=os.path.basename(first_image).rsplit('.', 1)[0]
        dest=os.path.join(os.environ['HOME'], 'panoramas', '%s--%s' % (base, name))
        if not os.path.exists(dest):
            os.makedirs(dest)
        images=[]
        for image in self.selectedimages():
            images.append(os.path.join(dest, os.path.basename(image.filename)))
        self.copy_or_move(dest, move=True)
        fd=open(os.path.join(dest, 'target-file.txt'), 'wt')
        fd.write(os.path.join(os.path.dirname(first_image), '%s.jpg' % name))
        fd.close()

    def onSendToEmail(self, widget):
        Global.app.cursorHourglass()
        cmd=['thunderbird', '-compose', "attachment='%s'" % ','.join([image.filename for image in self.selectedimages()])]
        print('########### %s' % ' '.join(cmd))
        subprocess.Popen(cmd)
        Global.app.cursorHourglass(False)

    def onSendToQtpfsgui(self, widget):
        Global.app.cursorHourglass()
        images=[]
        for image in self.selectedimages():
            images.append(image.filename)
        cmd=['qtpfsgui']
        cmd.extend(images)
        pid=subprocess.Popen(cmd).pid
        Global.app.cursorHourglass(False)
        
    def onCopy(self, widget, move=False):
        fc=gtk.FileChooserDialog(
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            parent=Global.app.all.window,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        fc.set_local_only(True)
        if Global.app.image.filename:
            fc.set_filename(os.path.dirname(Global.app.image.filename))
        ret=fc.run()
        dest=fc.get_filename()
        fc.destroy()
        if not os.path.isdir(dest):
            return
        Global.app.cursorHourglass()
        if ret!=gtk.RESPONSE_OK:
            Global.app.cursorHourglass(False)
            return
        self.copy_or_move(dest, move)
        Global.app.cursorHourglass(False)

    def copy_or_move(self, dest, move=False):
        dest_files=[]
        for image in self.selectedimages():
            base=re.sub(r'^(.*)\.\w{3,4}', r'\1', image.filename)
            files=glob.glob("%s*" % base)
            assert files
            for file in files:
                dest_file=os.path.join(
                    dest, os.path.basename(file))
                shutil.copy2(file, dest_file)
                dest_files.append(dest_file)
            if move:
                image.delete()
        return dest_files

    def onFlagSelected(self, widget):
        ef=EditFlags(parent=Global.app.all.window)
        for flag in ef.allflags.allflags:
            if flag.checked:
                for image in self.selectedimages():
                    f=Flag(flag.name, flag.dirname, flag.parent, image, False)
                    f.checked=True

                    
                    
