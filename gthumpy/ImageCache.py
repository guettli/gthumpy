# -*- coding: iso-8859-1 -*-
"""
 $Id: ImageCache.py 176 2010-12-10 15:42:29Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/ImageCache.py $

"""

# Python Imports
import gc
import os
import time
import logging
import memusage
import subprocess

# pygtk
import gtk
import gobject

# My Imports
import Utils
import Global
import debuglog

class ImageLoader(object):
    chunksize=130000
    pixbuf=None
    #background_prios={True: gobject.PRIORITY_LOW,
    #                  False: gobject.PRIORITY_DEFAULT_IDLE}
    background_prios={True: gobject.PRIORITY_DEFAULT_IDLE,
                      False: gobject.PRIORITY_HIGH_IDLE}
    nextcount=0
    def __init__(self, filename, width, height, background=False):
        if filename.rsplit('.')[-1].lower() in Utils.video_extensions:
            preview='%s.png' % filename
            if not os.path.exists(preview):
                Utils.avi_to_preview(filename, preview)
            filename=preview
        self.filename=filename
        self.width=width
        self.height=height
        self.loader=gtk.gdk.PixbufLoader()
        self.loader.connect("size-prepared", self.on_size_prepared)
        self.mtime=os.path.getmtime(filename)
        self.fd=open(filename)
        self.background=background
        self.background_old=background
        gobject.idle_add(self.next,
                         priority=self.background_prios[background])
        

    def on_size_prepared(self, pixbufloader, width, height):
        width, height = Utils.max_width_height(width, height, self.width,
                                              self.height)
        self.loader.set_size(width, height)

    def __str__(self):
        if not self.fd:
            if not self.pixbuf:
                state="closed"
            else:
                state="ready"
        else:
            state="loading"
        return '<%s %s bg=%s state=%s count=%s>' % (
            self.__class__.__name__, self.filename,
            self.background, state, self.nextcount)
    
    def next(self):
        self.nextcount+=1
        if not self.fd:
            # close() was called. Stop
            #print "self.next %s not self.fd" % self
            return False
        buf=self.fd.read(self.chunksize)
        #print "self.next %s read %d bytes" % (self, len(buf))
        if not buf:
            self.fd.close()
            self.fd=None
            reload=False
            age=None
            try:
                self.loader.close()
            except gobject.GError, err:
                age=time.time()-os.path.getmtime(self.filename)
                if age < 30:
                    # File was modified some seconds ago.
                    # Try agin
                    if debuglog.imagecache:
                        print "Error on close", err
                    reload=True
                else:
                    print "Exception bei", self, self.loader
                    raise
            if not reload:
                self.pixbuf=self.loader.get_pixbuf()
                if not self.pixbuf:
                    # PixbufLoader get not enought data to load an image
                    # May the image was modified this second, try again.
                    if debuglog.imagecache:
                        print "Not enough data. Loading again", self
                    reload=True
            if reload:
                # Error during loading. Try again.
                if age is None:
                    age=time.time()-os.path.getmtime(self.filename)
                if age<30:
                    # Let the process which writes the image some time.
                    # Wait for new data.
                    time.sleep(1)
                self.__init__(self.filename, self.width, self.height, self.background)
                return False
            if debuglog.imagecache:
                print "loaded", self
            return False # Stop
        try:
            self.loader.write(buf)
        except gobject.GError, exc:
            print 'Error', self
            raise
        if self.background!=self.background_old:
            # Priority changed
            gobject.idle_add(self.next,
                             priority=self.background_prios[self.background])
            self.background_old=self.background
            return False # Stop this, use new
        return True # Again

    def close(self):
        """
        Close if not needed any more
        """
        if self.fd:
            self.fd.close()
            self.fd=None
            try:
                self.loader.close()
            except gobject.GError:
                pass
            self.loader=None
        
class ImageCache(object):
    gc_count=0
    def __init__(self):
        self.cache={}
        
    def get(self, *args):
        filename=args[0]
        # Start loading of neighbours
        newargs=list(args)
        oldcache=set(self.cache.keys())
        newcache=set()
        newcache.add(args)
        for n in Global.app.getNeighbours():
            newargs[0]=n.filename
            bgargs=tuple(newargs)
            oldloader=self.cache.get(bgargs)
            if not oldloader:
                l=ImageLoader(*bgargs, **{"background": True})
                self.cache[bgargs]=l
            else:
                oldloader.background=True
            newcache.add(bgargs)

        # Delete old stuff in cache
        for oldarg in oldcache:
            if not oldarg in newcache:
                oldloader=self.cache[oldarg]
                oldloader.close()
                del(self.cache[oldarg])
                if debuglog.imagecache:
                    print "icache removing", oldloader
                del(oldloader)

        loader=self.cache.get(args)
        if loader and loader.pixbuf:
            # Images already loading.
            if os.path.getmtime(filename)!=loader.mtime:
                # mtime changed: reload
                del(self.cache[args])
                loader=None

        if not loader:
            # Request for a new Image
            loader=ImageLoader(*args, **{'background': False})
            if debuglog.imagecache:
                print "icache new  ", len(self.cache), loader
        else:
            # Load faster
            loader.background=False
            if debuglog.imagecache:
                print "icache cache", len(self.cache), loader

        iloop=0
        while True:
            iloop+=1
            assert iloop<2000, 'Loading took to many steps: %s' % (loader)
            if debuglog.imagecache:
                print "iloop", iloop, loader
            gtk.main_iteration()
            if loader.pixbuf:
                break
        self.gc_count+=1
        if (self.gc_count%5)==0:
            if debuglog.imagecache:
                before=memusage.memory()/1000
                gc.collect()
                after=memusage.memory()/1000
                diff=before-after
                print "icache gc", before, after, diff
            gc.collect()
        return loader.pixbuf

