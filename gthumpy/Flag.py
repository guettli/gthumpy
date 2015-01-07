#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# (c) 2002-2006 Thomas Güttler: http://www.thomas-guettler.de/
# http://guettli.sf.net/

# $Id: Flag.py 173 2010-08-05 20:22:30Z guettli $
# $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/Flag.py $

# Python Imports
import os

# My Imports
import Utils
import Global

class AllFlags(object):
    """
    Container for all Flags.
    Used by ActionMenu 'flag selected' and for each image.
    """
    def __init__(self, objecttree, image=None):
        self.objecttree=objecttree
        self.image=image # EditFlags: If PopUp (Flag Selected): None
        self.flags={Global.app.config.flags_dir: None}
        self.load()
        
    def load(self):
        allflags=[]
        for root, dirs, files in os.walk(Global.app.config.flags_dir):
            dirsnew=[]
            for dir in dirs:
                if dir=="links":
                    continue
                dirsnew.append(os.path.join(root, dir))
            dirs[:]=dirsnew
            dirs.sort()
            for dir in dirs:
                if self.image and os.path.islink(os.path.join(
                    dir, "links",
                    Utils.filename2md5(self.image.filename))):
                    checked=True
                else:
                    checked=False
                parent=self.flags[root]
                flag=self.flags.get(dir)
                if not flag:
                    flag=Flag(os.path.basename(dir), dir, parent, self.image, checked)
                    self.flags[dir]=flag
                    self.objecttree.append(flag.parent, flag)
                else:
                    flag.image=self.image
                    flag.checked=checked
                allflags.append(flag)
        self.allflags=allflags
        self.objecttree.refresh()
                 
class Flag(object):
    def __init__(self, name, dirname, parent, image=None, checked=False):
        self.name=name
        self.dirname=dirname
        assert os.path.isdir(dirname), dirname
        if parent:
            assert isinstance(parent, Flag)
            parent.subflags.append(self)
        self.parent=parent
        self.image=image
        self._checked=checked
        self.subflags=[]
        
    def __repr__(self):
        return '<%s %s %s>' % (
            self.__class__.__name__, self.slash_name, self._checked)
    @property
    def slash_name(self):
        parents=[]
        f=self
        while f:
            parents.append(f.name)
            f=f.parent
        parents.append('') # First slash
        return '/'.join(reversed(parents))

    def getchecked(self):
        return self._checked

    def setchecked(self, value):
        debug=False
        if value==self._checked:
            return
        if self.image:
            linkdir=os.path.join(self.dirname, "links")
            if not os.path.exists(linkdir):
                os.mkdir(linkdir)
            link=os.path.join(linkdir, Utils.filename2md5(
                self.image.filename))
            if value:
                if not os.path.exists(link):
                    if debug:
                        print "Flag.set: link"
                    os.symlink(self.image.filename, link)
                else:
                    if debug:
                        print "Flag.set: already link"
                        
            else:
                if os.path.exists(link):
                    if debug:
                        print "Flag.set: unlink"
                    os.unlink(link)
                else:
                    if debug:
                        print "Flag.set: already unlink"
                    
        self._checked=value

    checked=property(getchecked, setchecked)

    def getlength(self):
        linkdir=os.path.join(self.dirname, "links")
        if not os.path.exists(linkdir):
            return 0
        return len(os.listdir(linkdir))
    length=property(getlength)
    
    def images(self):
        """
        Return a set of images which have this
        flag set.
        """
        ret=set()
        linkdir=os.path.join(self.dirname, "links")
        if not os.path.exists(linkdir):
            return ret
        for file in os.listdir(linkdir):
            file=os.path.join(linkdir, file)
            if not os.path.islink(file):
                continue
            image=os.path.readlink(file)
            if not os.path.exists(image):
                print "Broken Link %s --> %s" % (
                    file, image)
                continue
            ret.add(image)
        return ret

            
