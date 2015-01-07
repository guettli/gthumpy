#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 $Id: Utils.py 179 2011-12-27 22:16:00Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/Utils.py $
"""

# Python Imports
import gc
import os
import re
import sys
import time
import hashlib
import tempfile
import subprocess
import datetime

# Python GTK
import pygtk
pygtk.require("2.0")
import gtk
import gobject

import debuglog

PREVIEW_SIZE=256

class FlushStream:
    """
    Flush this stream after each write
    """
    def __init__(self, fd):
        self.fd=fd
    def write(self, bytes):
        self.fd.write(bytes)
        self.fd.flush()
        

exiftran_failed=False


def callafterwait(func, waitsecs, *args, **kwargs):
    time.sleep(waitsecs)
    return func(*args, **kwargs)

def max_width_height(width_orig, height_orig, width_max, height_max):
    width_orig=float(width_orig)
    height_orig=float(height_orig)
    width_max=float(width_max)
    heiht_max=float(height_max)
    if (width_orig/width_max) > (height_orig/height_max):
        height=int((height_orig/width_orig)*width_max)
        width=int(width_max)
    else:
        width=int((width_orig/height_orig)*height_max)
        height=int(height_max)
    return width, height

video_extensions=['avi', 'mov', 'mp4']
def scale2pixbuf(width_max, height_max, filename=None, return_size=False,
                 pixbuf=None):
    """
    Scale to width_max and height_max.
    Keep aspect ratio
    """
    start=time.time()
    if filename:
        temp=None
        if '.' in filename:
            ext=filename.rsplit('.', 1)[-1].lower()
        else:
            ext=None
        if ext in video_extensions:
            temp=tempfile.mktemp()
            avi_to_preview(filename, temp)
            filename=temp
        pixbuf=gtk.gdk.pixbuf_new_from_file(filename)
        if temp:
            os.unlink(temp)
        if debuglog.scale:
            print "pixbuf_new_from_file %0.3f" % (time.time()-start)
    else:
        assert pixbuf
    width_orig=pixbuf.get_width()
    height_orig=pixbuf.get_height()
    width, height = max_width_height(
        width_orig, height_orig,
        width_max, height_max)
    startscale=time.time()
    pixbuf=pixbuf.scale_simple(int(width), int(height), gtk.gdk.INTERP_BILINEAR)
    #pixbuf=pixbuf.scale_simple(width, height, gtk.gdk.INTERP_NEAREST)
    if debuglog.scale:
        print "scale_simple %0.3f " % (time.time()-startscale)
    gc.collect() # Tell Python to clean up the memory
    if debuglog.scale:
        print "scale all %0.3f " % (time.time()-start)
    if return_size:
        return pixbuf, width_orig, height_orig
    return pixbuf

freedesktop_thumbnails=None
#   True  --> Use ~/.thumbnails/
#   False --> Creating $HOME/.thumbnails/normal failed. Don't use ~/.thumbnails/
#   None  --> Uninitialized: Did not check if ~/.thumbnails/normal/ exists yet.
file2preview_skip=['txt', 'db', 'xmp']
def file2preview(file):
    """
    Create a preview for an image.
    Storage the preview according to the "Freedesktop Preview Standard":
    http://jens.triq.net/thumbnail-spec/index.html
    
    Code inspired by Comix:
    http://comix.sourceforge.net/
    """
    ext=file.rsplit('.', 1)[-1].lower()
    if ext in file2preview_skip:
        return
    debug=False # True
    global freedesktop_thumbnails
    if freedesktop_thumbnails==False:
        return scale2pixbuf(PREVIEW_SIZE, PREVIEW_SIZE, file)
    thumbdirall=os.path.join(os.environ["HOME"], ".thumbnails")
    thumbdir=os.path.join(thumbdirall, "large")
    if freedesktop_thumbnails==None:
        try:
            if not os.path.exists(thumbdirall):
                os.mkdir(thumbdirall)
                os.chmod(thumbdirall, 0700)
            if not os.path.exists(thumbdir):
                os.mkdir(thumbdir)
                os.chmod(thumbdir, 0700)
            freedesktop_thumbnails=True
        except Exception, e:
            print "Failed to create %s: %s" % (thumbdir, e)
            freedesktop_thumbnails=False
            return scale2pixbuf(PREVIEW_SIZE, PREVIEW_SIZE, file)
    mtime=os.path.getmtime(file)
    uri="file://%s" % os.path.abspath(file)
    hash=hashlib.md5()
    hash.update(uri)
    preview=os.path.join(thumbdir, "%s.png" % hash.hexdigest())
    if os.path.exists(preview):
        pixbuf=gtk.gdk.pixbuf_new_from_file(preview)
        mtime_pre=pixbuf.get_option('tEXt::Thumb::MTime')
        if not mtime_pre:
            mtime_pre=0
        mtime_pre=int(mtime_pre)
        if mtime==mtime_pre:
            # The preview is up-to-date
            if debug:
                print "%s taking preview %s" % (file, preview)
            return pixbuf
        else:
            if debug:
                print "Preview of %s not up-to-date %s!=%s" % (file, mtime, mtime_pre)
    if debug:
        print "Create preview for %s: %s" % (file, preview)
    try:
        pixbuf, width, height = scale2pixbuf(PREVIEW_SIZE, PREVIEW_SIZE, file, return_size=True)
    except Exception, exc:
        print exc
        return None
    try:
        tmp=os.path.join(thumbdir, "_tmp_%s_%s_%s.png" % (
            os.uname()[1], os.path.basename(sys.argv[0]), os.getpid()))
        attr_dict={
            "tEXt::Thumb::MTime": str(int(mtime)),
            "tEXt::Thumb::URI": uri,
            "tEXt::Thumb::Size": str(os.path.getsize(file)),
            "tEXt::Thumb::Document::Pages": "1",
            "tEXt::Thumb::Image:Width": str(int(width)),
            "tEXt::Thumb::Image:Height": str(int(height)),
            "tEXt::Software": "gthumpy"}
        info=gtk.gdk.pixbuf_get_file_info(file)
        if info:
            attr_dict["tEXt::Thumb::Mimetype"]=info[0]['mime_types'][0]
        pixbuf.save(tmp, "png", attr_dict)
        os.rename(tmp, preview)
        os.chmod(preview, 0600)
    except Exception, e:
        print "Saving preview %s of %s failed: %s" % (preview, file, e)
    return pixbuf

def yesNoDialog(window, message, default=False):
    dialog=gtk.MessageDialog(window, gtk.DIALOG_MODAL |
                             gtk.DIALOG_DESTROY_WITH_PARENT,
                             gtk.MESSAGE_QUESTION,
                             gtk.BUTTONS_YES_NO, message)
    if default:
        h_button_box=dialog.vbox.get_children()[1]
        yes_button=h_button_box.get_children()[0]
        yes_button.grab_default()
    response=dialog.run()
    dialog.destroy()
    if response==gtk.RESPONSE_YES:
        return True
    else:
        return False


def exifdict(filename):
    import EXIF
    fd=open(filename)
    exifdict={}
    try:
        items=EXIF.process_file(fd).items()
    except ValueError, exc:
        print exc
        return exifdict
    for key, value in items:
        if key in ['JPEGThumbnail', 'TIFFThumbnail',
                   'EXIF MakerNote']:
            continue
        next=False
        for ignore in ['MakerNote Tag']:
            if key.startswith(ignore):
                next=True
                break
        if next:
            continue
        exifdict[key]=value
    return exifdict

def filename_to_date(filename, fallback=None):
    match=re.search(r'(\d\d\d\d).?(\d\d).?(\d\d)', filename)
    if not match:
        return fallback
    date=datetime.date(*[int(i) for i in match.groups()])
    return date

def filename2md5(filename):
    assert os.path.isabs(filename), filename
    uri="file://%s" % filename
    hash=hashlib.md5()
    hash.update(uri)
    return hash.hexdigest()

encoding=['utf8', 'latin1']
def try_unicode(string):
    if isinstance(string, unicode):
        return string
    assert isinstance(string, str), string
    for enc in encoding:
        try:
            return string.decode(enc)
        except UnicodeError:
            continue
    raise ValueError('Failed to convert %r' % string)

def usage():
    print '''Usage: %s file.png file2.jpg dir-with-files ...
Create previews in ~/.thubnails/normal/''' % os.path.basename(sys.argv[0])
    
def main():
    files=sys.argv[1:]
    if not files:
        usage()
        sys.exit(1)
    for file in files:
        if not os.path.exists(file):
            print '%s does not exist.' % file
            usage()
            sys.exit(1)
    for file in files:
        if os.path.isfile(file):
            file2preview(file)
            continue
        if not os.path.isdir(file):
            continue
        for root, dirs, files in os.walk(file):
            dirs.sort()
            files.sort()
            for file in files:
                if file.endswith('.gthumpy'):
                    continue
                file=os.path.join(root, file)
                file2preview(file)
                #print file

def avi_to_preview(filename, preview):
    cmd=['totem-video-thumbnailer', filename, preview]
    try:
        ret=subprocess.call(cmd)
    except OSError:
        print 'cmd failed: %s' % cmd
        raise
    assert ret==0, 'subprocess failed: %s' % cmd
    
if __name__=='__main__':
    main()
