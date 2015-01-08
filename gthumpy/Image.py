#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# (c) 2002-2006 Thomas Güttler: http://www.thomas-guettler.de/
# http://guettli.sf.net/

# $Id: Image.py 135 2008-04-08 21:03:57Z guettli $
# $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/Image.py $

# Python Imports
import os
import time

# Python GTK
import gtk

# My Imports
import Utils
import Global
from Flag import Flag, AllFlags

HOME = os.path.expanduser("~")
XDG_DATA_HOME = os.environ.get("XDG_DATA_HOME", os.path.join(HOME, ".local", "share"))

class Image(object):
    def __init__(self, filename):
        self.filename=filename
        self._exifdict=None
        
    def delete(self, unlink=True):
        if unlink:
            trash_file=os.path.join(XDG_DATA_HOME, 'Trash', 'files')
            if not os.path.exists(trash_file):
                os.makedirs(trash_file)
            trash_file=os.path.join(trash_file, os.path.basename(self.filename))
            os.rename(self.filename, trash_file)
            info_dir=os.path.join(XDG_DATA_HOME, 'Trash', 'info')
            if not os.path.exists(info_dir):
                os.makedirs(info_dir)
            fd=open(os.path.join(info_dir, '%s.trashinfo' % os.path.basename(self.filename)), 'wt')
            fd.write('''[Trash Info]
Path=%s
DeletionDate=%s
''' % (self.filename,
       time.strftime(time.strftime("%Y-%m-%dT%H:%M:%S"))))
            fd.close()
        curindex=Global.app.currIndex()
        myindex=self.index
        Global.app.images.remove(self)
        if Global.app.image==self:
            # The current Image gets deleted
            Global.app.image=None
            Global.app.loadImage(curindex)
        if Global.app.all:
            del(Global.app.all.liststore[myindex])
            
    def getindex(self):
        if not self in Global.app.images:
            return None
        return Global.app.images.index(self)

    index=property(getindex)

    def getselected(self):
        raise NotImplementedError("Deprecated")

    def setselected(self, bool):
        raise NotImplementedError("Deprecated")
    selected=property(getselected, setselected)


    def getexifdict(self):
        if self._exifdict is None:
            self._exifdict=Utils.exifdict(self.filename)
            if not self._exifdict.has_key("Image DateTime"):
                self._exifdict["Image DateTime"]="?"
        return self._exifdict
    
    exifdict=property(getexifdict)
    

    def __repr__(self):
        return '<%s object %s>' % (
            self.__class__.__name__, self.filename)

    def flags(self):
        """
        Return list of Flags of this image.
        """
        flags=[]
        md5name=Utils.filename2md5(self.filename)
        for flag in Global.app.editflags.allflags.allflags:
            linkname=os.path.join(flag.dirname, "links", md5name)
            if not os.path.islink(linkname):
                continue
            flags.append(flag)
        return flags
                
    def get_next(self):
        if self.index is None:
            return None
        next=self.index+1
        if next==len(Global.app.images):
            return None
        return Global.app.images[next]
    next=property(get_next)
    
