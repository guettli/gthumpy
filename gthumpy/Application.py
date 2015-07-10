# -*- coding: iso-8859-1 -*-
# (c) 2002-2006 Thomas Güttler: http://www.thomas-guettler.de/
# http://guettli.sf.net/

"""
 $Id: Application.py 179 2011-12-27 22:16:00Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/Application.py $
"""

#Python Imports
import codecs
import os
import re
import sys
import glob
import time
import popen2
import random
import shutil
import logging
import datetime
import tempfile
import subprocess
import xml.sax.saxutils

import gtk
import gobject

#My Imports
import Utils
import Global
import createThumbnails
import GthumpyUtils
import GthumpyParser
from Config import Config
from ImageCache import ImageCache
from FullScreen import FullScreen
from ChangeDirectory import ChangeDirectory
from AllPictures import AllPictures
from EditFlags import EditFlags, Flag
from Image import Image


class Application:
    def __init__(self, config, dir=None):
        Global.app=self
        self.config=config
        self.all=None
        self.fullscreen=None
        self.slide=False
        self.image=None
        self.image_mtime=None
        self.image_loaded=None
        self.parser=None
        self.cursorHourglassCount=0
        self.uimanager=gtk.UIManager()
        self.actiongroup=gtk.ActionGroup("actiongroup")
        self.actiongroup.add_actions(
            [
            # Menu
            ('File', None, '_File'),
            ('Go', None, '_Go'),
            ('Edit', None, '_Edit'),
            ('View', None, '_View'),
            ('Get', gtk.STOCK_CONNECT, '_Get Pictures', None, None, self.onGetPictures),
            
            # File
            ('Open', gtk.STOCK_OPEN, '_Open', None, None, self.onOpen),
            ('Quit', gtk.STOCK_QUIT, '_Quit me!', None,
             'Quit the Program', self.onDelete),
            
            # Go
            ('CD', gtk.STOCK_GO_UP, '_Change Directory', None, None, self.onCD),
            ('First', gtk.STOCK_GOTO_FIRST, '_First', None, None, self.onFirst),
            ('Last', gtk.STOCK_GOTO_LAST, '_Last', None, None, self.onLast),
            ('Prev', gtk.STOCK_GO_BACK, '_Prev', None, None, self.onPrev),
            ('Next', gtk.STOCK_GO_FORWARD, '_Next', None, None, self.onNext),
            
            # Edit
            ('EditPicture', gtk.STOCK_EXECUTE, '_Edit Picture', None,
             None, self.onEdit),
            ('Rotate 90', None, '_Rotate 90', None,
             'Rotate 90 (right)', self.onRotate),
            ('Rotate -90', None, 'R_otate -90', None,
             'Rotate -90 (left)', self.onRotateLeft),
            ('Rotate 180', None, 'Ro_tate 180', None,
             'Rotate 180 (up side down)', self.onRotate180),
            ('Delete', gtk.STOCK_DELETE, '_Delete', None,
             "Delete this Image", self.onDeleteImage),

            # View
            ('All', gtk.STOCK_INDEX, '_All Pictures', None, 'All Pictures', self.onAll),
            ('Fullscreen', gtk.STOCK_FULLSCREEN, '_Fullscreen', 'F11',
             None, self.onFullscreen),
            ('Videos', gtk.STOCK_MEDIA_PLAY, '_Videos', None, None, self.onVideos),
            ('Slide', gtk.STOCK_MEDIA_FORWARD, '_Slide', None, None, self.onSlide),
            ('Exif', gtk.STOCK_DIALOG_QUESTION, '_Exif', None, None, self.onExif),
            ])
        self.uimanager.insert_action_group(self.actiongroup, 0)
        self.uimanager.add_ui_from_file(os.path.join(
            os.path.dirname(__file__), "menu.xml"))
                                     
        self.window = gtk.Window()
        self.window.add_accel_group(self.uimanager.get_accel_group())
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_title("Gthumpy: Edit Metadata")
        self.window.connect("delete-event", self.onDelete)
        self.window.connect("key-press-event", self.onKeyEvent)

        # Funktioniert leider nicht.
        self.window.connect("scroll-event", self.onScrollEvent)
        
        self.window.set_border_width(10)
        self.tooltips=gtk.Tooltips()
        vbox = gtk.VBox()
        self.window.add(vbox)
        vbox.pack_start(self.uimanager.get_widget('/menubar'), False)
        vbox.pack_start(self.uimanager.get_widget('/toolbar'), False)

        # Date and Title
        self.hbox=gtk.HBox()
        self.infoLabel=gtk.Label("")
        self.hbox.add(self.infoLabel)

        self.hbox.add(gtk.Label("Title"))
        self.title=gtk.Entry()
        self.hbox.add(self.title)
        vbox.add(self.hbox)

        self.only_without_stars=gtk.CheckButton("Only without stars")
        self.hbox.add(self.only_without_stars)
        self.only_without_stars.connect("toggled", self.on_only_without_stars)

        # Description
        d=gtk.VBox()

        self.directory_title=gtk.Label()
        self.directory_title.set_selectable(True)
        d.add(self.directory_title)

        view=gtk.TextView()
        self.description=gtk.TextBuffer()
        view.set_buffer(self.description)
        view.set_wrap_mode(gtk.WRAP_WORD)
        view.set_editable(1)
        d.add(view)
        vbox.add(d)

        # Flags | Image
        h_flags_image=gtk.HBox()
        self.flagscontainer=gtk.Frame()
        self.flagscontainer.set_shadow_type(gtk.SHADOW_IN)
        h_flags_image.pack_start(self.flagscontainer)
        self.editflags=EditFlags(dialog=False)

        # Image. Set with self.loadImage()
        self.gtkimage=gtk.Image()
        self.gtkimage.set_size_request(self.config.width, self.config.height)
        h_flags_image.pack_start(self.gtkimage, expand=False)
        vbox.add(h_flags_image)

        # Last Image which was loaded in the small window (not fullscreen)
        self.last_filename_small=None

        # ImageCache
        self.imageCache=ImageCache()
        self.load_size_of_win(self)

        if not dir:
            save_last_dir=os.path.join(self.config.config_dir, 'last_dir.txt')
            if os.path.exists(save_last_dir):
                dir=open(save_last_dir).read().strip()
        if dir and os.path.isdir(dir):
            self.set_dir(dir)
        else:
            self.set_dir(os.environ['HOME'])
            
        gobject.timeout_add(1500, self.loadImagePolling)
        
    def on_only_without_stars(self, widget):
        self.set_dir(self.dir)
            
    def onRotateMenu(self, widget, event):
        self.rotatemenu.popup(None, None, None, event.button, event.time)

    def onFlags(self, widget=None, event=None, default=False):
        self.cursorHourglass(True)
        EditFlags(default=default)
        self.cursorHourglass(False)

    def set_dir(self, dir):
        only_without_stars=self.only_without_stars.get_active()
        files=[]
        dir=dir.rstrip("/")
        avis=0
        for file in os.listdir(dir):
            file=os.path.join(dir, file)
            if not os.path.isfile(file):
                continue
            extension=GthumpyUtils.image_extension(file)
            if not extension:
                continue
            files.append(file)
            if extension in Utils.video_extensions:
                avis+=1
        action=self.actiongroup.get_action("Videos")
        action.set_property("short-label", "%d Videos" % avis)
        action.set_property("label", "%d Videos" % avis)
        action.set_sensitive(bool(avis))
            
        files=GthumpyUtils.sort_int(files)
        self.images=[]
        for file in files:
            image=Image(file)
            if only_without_stars:
                skip=False
                for flag in image.flags():
                    if flag.slash_name.startswith('/stars/'):
                        skip=True
                        break
                if skip:
                    #print 'skipping', image, image.flags()
                    continue # no star Flag set
            self.images.append(image)
        self.dir=dir
        self.dirname=os.path.basename(dir)
        self.loadImage(0)
        self.window.show_all()
        if self.all:
            self.all.window.destroy()
        self.all=None
        self.create_previews=list(files)
        
        # Letztes Verzeichnis merken
        save_last_dir=os.path.join(self.config.config_dir, 'last_dir.txt')
        fd=open(save_last_dir, 'wt')
        fd.write('%s\n' % dir)
        fd.close()

        # Using idle_add creates to much load.
        gobject.timeout_add(500, self.onIdle_CreatePreviews, priority=gobject.PRIORITY_LOW)
        
    def onIdle_CreatePreviews(self, priority=None):
        if not self.create_previews:
            return False
        file=self.create_previews.pop(0)
        start=time.time()
        Utils.file2preview(file)

        # Wait as long as the creation/lookup of the thumbnail needed.
        # This way we only create a cpu load of 0.5
        duration=int(1000*(time.time()-start))
        gobject.timeout_add(duration,
                            self.onIdle_CreatePreviews, priority=gobject.PRIORITY_LOW)
        return False
    
    def onFullscreen(self, widget=None):
        if self.fullscreen:
            return self.fullscreen.onDelete()
        self.fullscreen=FullScreen(self)
        self.fullscreen.loadImage()

    def onEdit(self, widget=None):
        self.cursorHourglass()
        subprocess.Popen(['gimp', self.image.filename]) # Start in background
        self.cursorHourglass(False)

    def onSlide(self, widget=None):
        self.slide=True
        self.onFullscreen()
        while gtk.events_pending():
            gtk.main_iteration(False)
        while self.slide:
            time.sleep(3)
            self.onNext()
            while gtk.events_pending():
                gtk.main_iteration(False)

    def onExif(self, widget=None):
        rows=[]

        if False:
            cmd="exiv2 '%s'" % self.image.filename
            pipe=popen2.Popen4(cmd)
            for line in pipe.fromchild:
                line=line.strip()
                if not line:
                    continue
                match=re.match(r'^(.+?)\s*:\s*(.*?)$', line)
                if not match:
                    print "onExif. Strange output: %s" % line
                    continue
                key=match.group(1).strip()
                value=match.group(2).strip()
                rows.append((key, value))
            ret=pipe.wait()
            if ret:
                print "cmd (%s) failed: ret=%s" % (cmd, ret)
        else:
            items=Utils.exifdict(self.image.filename).items()
            items.sort()
            for key, value in items:
                value=value.__str__()
                if isinstance(value, list):
                    # Exif UserComment PowerShot S80
                    continue
                rows.append((key, value))
                
        if self.fullscreen:
            parent=self.fullscreen.window
        else:
            parent=self.window
        dialog=gtk.Dialog("Exif Info of %s" %
                          os.path.basename(self.image.filename),
                          parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          (gtk.STOCK_OK, gtk.RESPONSE_OK)
                          )
        table=gtk.Table(len(rows), 2)
        table.set_col_spacings(5)
        i=0
        for key, value in rows:
            label=gtk.Label(key)
            label.set_alignment(0, 0.5)
            table.attach(label, 0, 1, i, i+1)
            label=gtk.Label(value)
            label.set_alignment(0, 0.5)
            table.attach(label, 1, 2, i, i+1)
            i+=1
        dialog.vbox.add(table)
        dialog.vbox.show_all()
        ret=dialog.run()
        dialog.destroy()
        
    def onKeyEvent(self, widget, event):
        if self.slide:
            self.slide=False
        if len(event.string)==1 and ord(event.string)==27: # ESC
            if self.fullscreen:
                self.fullscreen.onDelete()
            else:
                self.onFullscreen()
            return

        if False: # For debugging key events.
            if len(event.string)==1:
                myord=ord(event.string)
            else:
                myord=""
            rev=dict()
            for attr in dir(gtk.keysyms):
                value=getattr(gtk.keysyms, attr, None)
                if isinstance(value, (long, int)):
                    rev[value]=attr
            print "onKeyEvent state=%s keyval=%s s='%s' ord(s)=%s len(s)=%s " \
                  "hardware_keycode=%s" %(
                event.state,
                rev.get(event.keyval, event.keyval),
                repr(event.string),
                myord,
                len(event.string), event.hardware_keycode)

        k=event.string.lower()
        if self.fullscreen:
            if k in ["n", " "] or (not k and event.keyval in
                                   [gtk.keysyms.Right, gtk.keysyms.Down]):
                # Cursor right, Cursor down
                return self.onNext()
            elif k=="p" or (not k and event.keyval in [gtk.keysyms.Left, gtk.keysyms.Up, gtk.keysyms.BackSpace]):
                # p, Cursor left, Cursor up, Backspace
                return self.onPrev()
            elif (not k and event.keyval==gtk.keysyms.Home):
                # Pos1/Home
                return self.onFirst()
            elif (not k and event.keyval==gtk.keysyms.End):
                # End
                return self.onLast()
            elif k=="f" and event.state&gtk.gdk.SHIFT_MASK:
                # F
                return self.onFlags(default=True)
            elif k=="f":
                return self.onFlags()
            elif k=='e':
                return self.onEdit()
            elif (not k and event.keyval==gtk.keysyms.Delete):
                # Delete / Entf.
                self.onDeleteImage()
                return
            elif k and k in '12345':
                # Set stars flag
                star_flag_parent_dir=os.path.join(Global.app.config.flags_dir, 'stars')
                star_flag_dir=os.path.join(star_flag_parent_dir, str(k))
                star_flag=Global.app.editflags.allflags.flags.get(star_flag_dir)
                if not star_flag:
                    star_flag_parent=Global.app.editflags.allflags.flags.get(star_flag_parent_dir)
                    if not star_flag_parent:
                        # Create "root" flag for stars
                        star_flag_parent=Flag(
                            os.path.basename(star_flag_parent_dir), os.path.dirname(star_flag_parent_dir),
                            None)
                        Global.app.editflags.allflags.flags[star_flag_parent_dir]=star_flag_parent
                        Global.app.editflags.allflags.objecttree.append(star_flag_parent.parent, star_flag_parent)
                    try:
                        os.makedirs(star_flag_dir)
                    except OSError, exc:
                        if exc.errno!=17:
                            raise
                    star_flag=Flag(str(k), star_flag_dir, star_flag_parent, self.image)
                    Global.app.editflags.allflags.flags[star_flag_dir]=star_flag
                    Global.app.editflags.allflags.objecttree.append(star_flag.parent, star_flag)
                star_flag.setchecked(True)
                return self.onNext()
            elif k and k in 'oO':
                star_flag_dir=os.path.join(Global.app.config.flags_dir, 'Auswahl', 'ok')
                star_flag=Global.app.editflags.allflags.flags.get(star_flag_dir)
                star_flag.setchecked(True)
                return self.onNext()
            elif k and k in 'rR':
                star_flag_dir=os.path.join(Global.app.config.flags_dir, 'Auswahl', 'ok')
                star_flag=Global.app.editflags.allflags.flags.get(star_flag_dir)
                star_flag.setchecked(False)
                self.image.delete(unlink=False)
                return True
                
        if event.keyval in [gtk.keysyms.Page_Down, gtk.keysyms.Page_Up] and event.state&gtk.gdk.SHIFT_MASK:
            # Shift-PageDown
            # Jump to next directory with images.
            if event.keyval==gtk.keysyms.Page_Up:
                jump=GthumpyUtils.JUMP_PREV
            else:
                jump=GthumpyUtils.JUMP_NEXT
            return self.onNextDir(jump=jump)

        if event.keyval in [gtk.keysyms.Page_Down]:
            # PageDown
            self.onNext()
            return True # Don't scroll in scrolledwindow
        
        elif event.keyval in [gtk.keysyms.Page_Up]:
            # PageUp
            self.onPrev()
            return True # Don't scroll in scrolledwindow
        
        elif event.keyval in [gtk.keysyms.Home]:
            return self.onFirst()

        elif event.keyval in [gtk.keysyms.End]:
            return self.onLast()

        elif (len(k)==1 and ord(k)==24 and event.hardware_keycode==53):
            # Ctrl-x
            self.onDeleteImage(ask=False)
            return
        elif (len(k)==1 and ord(k)==18 and event.hardware_keycode==27):
            # Ctrl-r (turn *right*)
            self.onRotate(None, 90)
            return
        elif (len(k)==1 and ord(k)==12 and event.hardware_keycode==46):
            # Ctrl-l (turn *left*)
            self.onRotate(None, -90)
            return
        elif (len(k)==1 and ord(k)==21 and event.hardware_keycode==30):
            # Ctrl-u (upside down)
            self.onRotate(None, 180)
            return
        elif (len(k)==1 and ord(k)==6 and event.hardware_keycode==41
              and event.state&gtk.gdk.SHIFT_MASK):
            # Ctrl-f Flags
            self.onFlags(default=True)
            return
        elif (len(k)==1 and ord(k)==6 and event.hardware_keycode==41):
            # Ctrl-f Flags
            self.onFlags()
            return

    def onScrollEvent(self, widget, event):
        # Funktioniert leider nicht.
        print 'onScroll', widget, event
        if event.direction == gtk.gdk.SCROLL_UP:
            self.onPrev()
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.onNext()
        return True
    
    def onRotateLeft(self, widget=None):
        return self.onRotate(angle=-90)

    def onRotate180(self, widget=None):
        return self.onRotate(angle=180)
    
    def onRotate(self, widget=None, angle=90):
        #print "rotate %s" % angle
        self.cursorHourglass()
        createThumbnails.rotate(self.image.filename, int(angle))
        short=self.image.filename[:-4] # cut ".jpg"
        files=glob.glob("%s_res*" % short)
        for file in files:
            #print "deleting %s" % file
            os.unlink(file)
        self.loadImage()
        self.cursorHourglass(False)

    def onFirst(self, widget=None):
        self.loadImage(0)

    def onLast(self, widget=None):
        self.loadImage(len(self.images)-1)

    def onNext(self, widget=None):
        if not self.images:
            return
        #layout=self.gtkimage.create_pango_layout('#################')
        #x, y = layout.get_pixel_size()
        #gc=self.window.window.new_gc()
        #self.window.window.draw_layout(gc, x, y, layout)
        try:
            index=self.images.index(self.image)+1
        except ValueError:
            index=1
        #if index>=len(self.images):
        #    if self.on_next_hook:
        #        return self.on_next_hook(index)
        self.loadImage(index)

    def onPrev(self, widget=None):
        if not self.images:
            return
        index=self.images.index(self.image)-1
        self.loadImage(index)

    def onVideos(self, widget=None):
        avis=[]
        for file in os.listdir(self.dir):
            if file.rsplit('.')[-1].lower() in Utils.video_extensions:
                avis.append(os.path.join(self.dir, file))
        avis.sort()
        if avis:
            if self.fullscreen:
                # Delete fullscreen Image since the video is fullscreen, too
                self.fullscreen.onDelete()
                self.fullscreen=None
                self.loadImage()
            #os.system("totem --fullscreen %s &" % ' '.join(avis))
            self.cursorHourglass()
            #os.system("vlc --fullscreen %s &" % ' '.join(avis))
            cmd=['totem', '--fullscreen']
            cmd.extend(avis)
            subprocess.Popen(cmd)
            self.cursorHourglass(False)

    def onGetPictures(self, widget=None):
        raise NotImplementedError()

        
    def onDelete(self, widget=None, event=None):
        "Application.onDelete"
        if self.all:
            self.all.onDelete(destroy=True)
        self.save_size_of_win(self)
        self.window.destroy()
        gtk.main_quit()

    change_directory=None
    def onCD(self, widget):
        if not self.change_directory:
            self.change_directory=ChangeDirectory()
            self.change_directory.start()
        else:
            self.change_directory.restart()

    def nextDirDialog(self, jump=GthumpyUtils.JUMP_NEXT):
        '''
        Ask if user wants to jump to next dir.
        '''
        next, descr = GthumpyUtils.find_next_dir_and_description(self.dir, jump=jump)
        weekday=''
        if next:
            weekday=Utils.filename_to_date(next)
            if weekday:
                weekday=weekday.strftime('%A, %d. %B %Y')
        if Utils.yesNoDialog(self.window, u'End of %s.\n\nJump to %s dir %s?\n\n%s\n%s' % (
                self.dir,
                GthumpyUtils.jump_verbose[jump], next, weekday, descr), default=True):
            self.onNextDir(jump=jump, next=next)
            if not self.images:
                return None
            return self.images[0]

        index=self.currIndex()
        if jump==GthumpyUtils.JUMP_PREV:
            index=len(self.images)-1
        else:
            index=0
        return self.images[index]
        
    def onNextDir(self, jump=GthumpyUtils.JUMP_NEXT, next=None):
        u'''
        go to next dir, don't ask.

        next: None, if the next directory is not known (Shift-PageUp)
              or a directory if known: PageUp, nextDirDialog(), onNextDir()
        '''
        self.cursorHourglass()
        for i in range(100):
            if next is None:
                try:
                    next=GthumpyUtils.find_next(self.dir, jump=jump)
                except OSError, exc:
                    md = gtk.MessageDialog(self.window, 
                                           gtk.DIALOG_DESTROY_WITH_PARENT, 
                                           gtk.MESSAGE_INFO, 
                                           gtk.BUTTONS_CLOSE, str(exc))
                    md.run()
                    md.destroy()
                    break
            if not next: 
                break # kein nächstes Verzeichnise
            self.set_dir(next)
            if self.images:
                break # OK, Verzeichnis gefunden.
        self.cursorHourglass(False)
        return True # Don't scroll in scrolledwindow

    def onAll(self, widget):
        if self.all:
            # AllPictures wurde schon aufgerufen
            self.all.scroll_to_current()
            self.all.window.show_all()
        else:
            # Erster Aufruf
            self.all=AllPictures()
            gobject.idle_add(self.all.load)


    def currIndex(self):
        if self.image not in self.images:
            return 0
        return self.images.index(self.image)
    
    def saveMetadata(self):
        if not self.image:
            return # no image loaded yet
        gthumpy="%s.gthumpy" % GthumpyUtils.image2name(self.image.filename)
        title=self.title.get_text().strip()
        text=self.description.get_text(
            self.description.get_iter_at_offset(0),
            self.description.get_iter_at_offset(-1)).strip()
        if not title and not text:
            if os.path.exists(gthumpy):
                os.unlink(gthumpy)
            return
        esc=xml.sax.saxutils.escape
        try:
            fd=open(gthumpy, "wt")
        except IOError:
            # Datei wurde inzwischen gelöscht?
            return
        fd.write(
            '''<?xml version="1.0" encoding="iso-8859-1"?>
<gthumpy>
 <title>%s</title>
 <description>%s</description>
</gthumpy>''' %  (
                esc(title.encode("latin1")),
                esc(text.encode("latin1"))
                ))
        fd.close()

    def loadImage(self, index=None):
        self.cursorHourglass(main_iteration=False)
        self.saveMetadata()
        self.image=self.index2image(index)
        self.load_description()
        gobject.idle_add(self.loadImageIdle, priority=gobject.PRIORITY_LOW)

    def load_description(self):
        if not self.image:
            return
        directory=os.path.dirname(self.image.filename)
        description=os.path.join(directory, 'description.txt')
        if os.path.exists(description):
            text=open(description).read()
        else:
            text=''
        self.directory_title.set_text('%s\n%s' % (directory, Utils.try_unicode(text)))

    def index2image(self, index=None):
        #if not self.images:
        #    return None
        if index is None:
            if not self.image:
                index=0
            else:
                index=self.currIndex()

        if index<0:
            return self.nextDirDialog(GthumpyUtils.JUMP_PREV)
        if self.images and index>=len(self.images):
            return self.nextDirDialog(GthumpyUtils.JUMP_NEXT)
        if not self.images:
            return None
        index=index%len(self.images)
        return self.images[index]

    def loadImagePolling(self):
        """
        Called again and again via gobject.timeout_add()
        Check if mtime has changed.
        """
        self.loadImageIdle(hourglass=False)
        return True # call method again
    
    def loadImageIdle(self, hourglass=True, force=False):
        """
        Application.loadImage
        """
        debug=False
        exif=self.actiongroup.get_action("Exif")
        if not self.image:
            exif.set_sensitive(False)
            if hourglass:
                self.loadNoImage()
                self.cursorHourglass(False)
            return
        exif.set_sensitive(True)
        if (not force) and self.image_loaded==self.image and \
               self.image_mtime==os.path.getmtime(self.image.filename):
            if debug:
                print "Skip loading", self.image
            if hourglass:
                self.cursorHourglass(False)
            return
        self.image_loaded=self.image
        if not len(self.images):
            if debug:
                print "no image"
            if hourglass:
                self.cursorHourglass(False)
            self.loadNoImage()
            return
        #print "Loading", self.image
        self.editflags.loadflagfiles()
        self.window.set_title("Application: %s" % self.image.filename)
        mydict=dict(self.image.exifdict)
        mydict["indexplusone"]=self.image.index+1
        mydict["all"]=len(self.images)
        datetime_of_pic=self.image.exifdict.get('Image DateTime', '')
        if datetime_of_pic:
            # 2014:10:25 12:55:21
            try:
                datetime_of_pic=datetime.datetime.strptime(str(datetime_of_pic), '%Y:%m:%d %H:%M:%S')
            except ValueError:
                pass
            else:
                datetime_of_pic=datetime_of_pic.strftime('%Y-%m-%d %H:%M')
        mydict["datetime"]=datetime_of_pic
        self.infoLabel.set_text(Config.infoLabel % mydict)
        self.image_mtime=os.path.getmtime(self.image.filename)
        if self.fullscreen:
            self.fullscreen.loadImage()
        else:
            self.last_filename_small=self.image.filename
            #Scale Image
            if debug:
                print "getting image", self.image.filename
            pixbuf=self.imageCache.get(self.image.filename, *self.size())
            self.gtkimage.set_from_pixbuf(pixbuf)
            self.gtkimage.show()

        gthumpy="%s.gthumpy" % GthumpyUtils.image2name(self.image.filename)
        if not self.parser:
            self.parser=GthumpyParser.GthumpyParser()
        if os.path.exists(gthumpy):
            self.parser.parse(gthumpy)

        self.title.set_text(unicode(self.parser.title, "latin1"))
        self.description.delete(
            self.description.get_iter_at_offset(0),
            self.description.get_iter_at_offset(-1))
        self.description.insert(self.description.get_iter_at_offset(0),
                                unicode(
            self.parser.description, "latin1"))#, -1)

        #self.editflags.loadflagfiles()
        if hourglass:
            self.cursorHourglass(False)
        return
    
    def loadNoImage(self):
        self.cursorHourglass(True)
        assert not self.images
        assert not self.image
        self.window.set_title("Application: -")
        self.infoLabel.set_text("0v0")
        self.title.set_text("")
        self.description.delete(
            self.description.get_iter_at_offset(0),
            self.description.get_iter_at_offset(-1))
        self.gtkimage.clear()
        self.cursorHourglass(False)
        

    def onDeleteImage(self, widget=None, event=None, ask=True):
        if self.fullscreen:
            window=self.fullscreen.window
        else:
            window=self.window
        if ask:
            do=Utils.yesNoDialog(window, "Delete this image?")
        else:
            do=True
        if do:
            self.image.delete()
            self.loadImage()
            
    def cursorHourglass(self, set=True, main_iteration=True):
        """
        self.cursorHourglassCount is like a stack.
        Only the change from zero to one and from one to zero
        changes the cursor.
        """
        debug=False
        if debug:
            import traceback
            print 'cursorHourglass set=%s main_i=%s Stack:' % (set, main_iteration)
            traceback.print_stack()
        windows=[]
        if self.window:
            windows.append(self.window)
        if self.fullscreen:
            windows.append(self.fullscreen.window)
        if self.all:
            windows.append(self.all.window)
        if not hasattr(self, "watch_cursor"):
            self.watch_cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
        if set:
            # While loading the first image window.window is None
            if not self.cursorHourglassCount:
                # Set Hourglass Cursor
                for window in windows:
                    if (not window) or (not window.window):
                        continue
                    #old
                    #window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                    if not hasattr(window, "cursor_win"):
                        window.cursor_win = gtk.gdk.Window(
                            window.window,
                            gtk.gdk.screen_width(),
                            gtk.gdk.screen_height(),
                            gtk.gdk.WINDOW_CHILD,
                            0,
                            gtk.gdk.INPUT_ONLY)
                    window.cursor_win.set_cursor(self.watch_cursor)
                    window.cursor_win.show()
                    
            self.cursorHourglassCount+=1
            if main_iteration:
                while gtk.events_pending():
                    gtk.main_iteration(False)

        else:
            # Unset
            if self.cursorHourglassCount:
                for window in windows:
                    if (not window) or (not window.window):
                        continue
                    if not hasattr(window, "cursor_win"):
                        continue
                    if self.fullscreen and window==self.fullscreen.window:
                        cursor=self.fullscreen.cursor
                    else:
                        cursor=None
                    #old:
                    #window.window.set_cursor(cursor)

                    window.cursor_win.hide()
            self.cursorHourglassCount-=1
            assert(self.cursorHourglassCount>=0)

    def getallflagdirs(self):
        flags=[]
        for root, dirs, files in os.walk(self.config.flags_dir):
            dirsnew=[]
            for dir in dirs:
                if dir=="links":
                    continue
                dirsnew.append(dir)
            dirs[:]=dirsnew
            dirs.sort()
            for dir in dirs:
                flags.append(os.path.join(root, dir))
        return flags
    
    def getNeighbours(self, maxsize=5):
        """
        images: 1 2 3 4 5
                    |--------> current image
                    
                5 3 1 2 4  --> sequence in cache  TODO: Doku OK?
        """
        if self.image is None or not maxsize:
            return []
        neighbours=[]
        for i in range(maxsize-1):
            if i%2:
                vector=-1
            else:
                vector=1
            idx=self.currIndex() + vector*((i+2)/2)
            if idx<0:
                idx=len(self.images)+idx
            idx=idx%len(self.images)
            neighbours.append(self.images[idx])
        return neighbours
    
    def size(self):
        if self.fullscreen:
            width=self.fullscreen.width
            height=self.fullscreen.height
        else:
            width=self.config.width
            height=self.config.height
        return width, height

    def onOpen(self, widget):
        fc=gtk.FileChooserDialog(
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            parent=self.window,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        fc.set_local_only(True)
        ret=fc.run()
        dest=fc.get_filename()
        fc.destroy()
        if ret!=gtk.RESPONSE_OK:
            return
        if not os.path.isdir(dest):
            return
        self.set_dir(dest)

    def save_size_of_win(self, object):
        size=object.window.get_size()
        file=os.path.join(self.config.sizes_dir, object.__class__.__name__)
        fd=open(file, 'wt')
        fd.write("%s %s\n" % size)
        fd.close()

    def load_size_of_win(self, object):
        file=os.path.join(self.config.sizes_dir, object.__class__.__name__)
        if not os.path.exists(file):
            return
        size=open(file).read().strip()
        object.window.resize(*[int(i) for i in size.split()])
    
        
    
