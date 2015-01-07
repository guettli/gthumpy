# -*- coding: iso-8859-1 -*-

"""
 $Id: ChangeDirectory-old.py 155 2008-09-19 20:43:23Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/ChangeDirectory-old.py $
"""

# Python Imports
import os
import re

# Python GTK
import gtk

# My Imports
import Global

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
        button_cancel.connect("clicked", self.onCancel)
        hbox.add(button_cancel)
        button_ok=gtk.Button("OK")
        button_ok.connect("clicked", self.onOK)
        hbox.add(button_ok)
        vbox.add(hbox)
        window.add(vbox)
        window.set_size_request(500, 200)
        window.set_position(gtk.WIN_POS_MOUSE)
        window.show_all()
        window.set_modal(True)
        window.set_transient_for(Global.app.window)
        window.set_title("Gthumpy: Edit Description: %s" %
                         os.path.basename(os.path.dirname(filename)))
        window.connect("delete-event", self.onDelete)
        self.newtext=None
        gtk.main()

    def onOK(self, widget):
        desc=self.description.get_text(
            self.description.get_iter_at_offset(0),
            self.description.get_iter_at_offset(-1)).strip()
        fd=open(self.filename, "wt")
        fd.write(desc.encode("latin1"))
        fd.close()
        self.onDelete()
        self.newtext=desc

    def onCancel(self, widget):
        self.onDelete(widget)

    def onDelete(self, widget=None, event=None):
        """
        EditDescription.onDelete
        """
        self.window.destroy()
        gtk.main_quit()


class ChangeDirectory:
    def __init__(self):
        Global.app.cursorHourglass()
        window=gtk.Window()
        window.set_position(gtk.WIN_POS_CENTER)
        imagedir=os.path.dirname(Global.app.dir)
        self.imagedir=imagedir
        daydirs=os.listdir(imagedir)
        daydirs.sort()
        daydirs.reverse()
        dirs=[]
        for dirname in daydirs:
            file=os.path.join(imagedir, dirname)
            if not os.path.isdir(file):
                continue
            if dirname=="misc":
                continue
            count=0
            for f in os.listdir(file):
                if f.lower().endswith(".jpg"):
                    if f.find("_res")!=-1:
                        continue
                    count+=1
            descr_file=os.path.join(file, "description.txt")
            if os.path.isfile(descr_file):
                fd=open(descr_file)
                descr=unicode(fd.read().strip(), "latin1")
                fd.close()
            else:
                descr=u""
            dirs.append((dirname, count, descr))
        len_table=len(dirs)
        table=gtk.Table(len_table, 3)
        i=-1
        curr_dir=os.path.basename(Global.app.dir)
        self.dirname2label={}
        old_year=None
        currButton=None
        for dirname, count, descr in dirs:
            i+=1
            match=re.match(r'^(\d\d\d\d)\D.*', dirname)
            if match:
                year=match.group(1)
                if old_year and (old_year!=year):
                    for n in range(3):
                        len_table+=1
                        table.resize(len_table, 3)
                        sep=gtk.HSeparator()
                        sep.set_size_request(-1, 15)
                        table.attach(sep, 0, 3, i, i+1)
                        i+=1
                old_year=year

            button=gtk.Button(dirname)
            button.connect("clicked", self.onClick, dirname)
            if dirname==curr_dir:
                button.set_state(gtk.STATE_SELECTED)
                currButton=button
            table.attach(button, 0, 1, i, i+1, xoptions=gtk.SHRINK)
            label=gtk.Label(descr)
            label.set_line_wrap(True)
            label.set_justify(gtk.JUSTIFY_LEFT)
            align=gtk.Alignment(xalign=0, yalign=0.5)
            label_button=gtk.Button()
            label_button.add(align)
            label_button.connect("clicked", self.onDescription, dirname)
            align.add(label)
            self.dirname2label[dirname]=label
            count=gtk.Label(str(count))
            # left-padding for alignment needs gtk 2.4
            align_count=gtk.Alignment(xalign=0.9, yalign=0.5)
            align_count.add(count)
            #align_count.set_size_request(0, 0)
            table.attach(align_count, 1, 2, i, i+1)
            label_button.modify_bg(gtk.STATE_NORMAL,
                                   gtk.gdk.Color(65535, 65535,65535))
            table.attach(label_button, 2, 3, i, i+1)
        scroll=gtk.ScrolledWindow()
        scroll.set_size_request(600, 400)
        scroll.add_with_viewport(table)
        window.add(scroll)
        window.show_all()
        window.set_modal(True)
        window.set_transient_for(Global.app.window)
        window.set_title("Gthumpy: Change Directory")
        window.connect("delete-event", self.onDelete)
        if currButton:
            rec=currButton.get_allocation()
            va=scroll.get_vadjustment()
            #print "rec.y=%s va.upper=%s va.page_size=%s va.p_i=%s va.s_i=%s" \
            #    % (
            #rec.y, va.upper, va.page_size, va.page_increment,
            #va.step_increment)
            pos=max(min(rec.y - va.step_increment, va.upper - va.page_size), 0)
            va.set_value(pos)
        self.window=window
        Global.app.load_size_of_win(self)
        Global.app.cursorHourglass(False)
        gtk.main()

    def onDescription(self, widget, dirname):
        description=os.path.join(self.imagedir, dirname, "description.txt")
        ed=EditDescription(description)
        if ed.newtext!=None:
            self.dirname2label[dirname].set_text(ed.newtext)

    def onDelete(self, widget=None, event=None):
        Global.app.save_size_of_win(self)
        self.window.destroy()
        gtk.main_quit()

    def onClick(self, widget, data):
        Global.app.set_dir(os.path.join(
            os.path.dirname(Global.app.dir),
            data))
        gtk.main_quit()
        self.window.destroy()
