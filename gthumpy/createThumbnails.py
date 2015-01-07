#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import re
import glob
import sys
import string
import shutil
import threading
import tempfile

from GthumpyUtils import search_recursive
from GthumpyUtils import insert_midfix
from GthumpyUtils import image2name

###Start config

known_extension=["jpg"]
gthumpy_template="template.gthumpy"

# Sizes of the created thumbnails (for static HTML pages)
# aspect ratio is kept.
image_sizes=[
    [150, 150],  # thumbnail
    [500, 500],  # slideshow 
    [800, 600],  #[1024, 768], # big image
    ]
###End config

def interactive(filename):
    extension=re.sub(r'.*\.([^.]*)', r'\1', filename)
    if not string.lower(extension) in known_extension:
        #print "File:", filename, "has no known graphic extension"
        return 
    if re.match(r'[^.]*_res.*\.[^.]*', filename):
        #Matches foo_resNUMBER.jpg
        #image is already a thumbnail
        return
    if os.path.isfile("%s.gthumpy" % image2name(filename)):
        #foo.gthumpy already exits
        return
    size="%sx%s" % (preview_size[0], str(preview_size[0]))
    pid=0
    while 1:
        if pid!=0:
                os.kill(pid, 15)
        pid=os.spawnv(os.P_NOWAIT, "/usr/bin/display", ["", "-geometry",
                                                        "+0+0",
                                                        "-size",
                                                        size, filename])
        print "Displaying", filename
        print "Rotate or delete?\n" + \
              "return:   don't rotate\n" + \
              "r:        turn right (clockwise 90°)\n" + \
              "l:        turn left\n" + \
              "ll or rr: turn 180 degrees\n" + \
              "d:       delete" + \
              "s:       skip (don't create foo.gthumpy with editor)"
        degrees=0
        answer=sys.stdin.readline()
        answer=answer.strip()
        answer=answer.lower()
        if answer=="l":
            degrees=-90
        elif answer=="r":
            degrees=90
        elif answer in ["ll", "rr"]:
            degrees=180
        elif answer=="":
            degrees=0
            break
        elif answer=="d":
            os.remove(filename)
            #Remove resized images, too
            files=insert_midfix(filename, "_res*")
            files=glob.glob(files)
            for file in files:
                print "deleting", file
                os.remove(file)
            os.kill(pid, 15)
            return
        elif answer=="s":
            degrees=0
            break
        else:
            print "Wrong input"
            continue
        sys.stdout.write("rotating ...")
        sys.stdout.flush()
        rotate(filename, degrees)
        print " done."
    if answer!="s":
        threading.Thread(target=resize_batch,
                         args=[filename]).start()
        gthumpy_file="%s.gthumpy" % image2name(filename)
        if not os.path.isfile(gthumpy_file):
            shutil.copyfile(gthumpy_template, gthumpy_file)
            os.spawnv(os.P_WAIT, "/usr/bin/emacs", ["", "-nw", gthumpy_file])
    os.kill(pid, 15)

def resize_batch(filename):
    extension=re.sub(r'.*\.([^.]*)', r'\1', filename)
    if not string.lower(extension) in known_extension:
        print "File:", filename, "has no known graphic extension"
        return 
    if not os.path.isfile(filename):
        print filename, "not a file"
        return
    if re.search(r'_res\d\d\d', filename):
        #Matches foo_resNUMBER.jpg
        #image is already a thumbnail
        return
    for x, y in image_sizes:
        resize(filename, x, y)

def rotate(filename, degrees):
    #fd=os.system("convert -rotate '%s' '%s' '%s'" % (degrees, filename,
    #                                                 filename))
    if degrees==90:
        opt=9
    elif degrees==180:
        opt=1
    elif degrees in [-90, 270]:
        opt=2
    else:
        raise("Unkown degrees: %s" % degrees)
    os.system("exiftran -i -%d '%s'" % (
        opt, filename))

def resize(filename, x, y, mktemp=0, new_filename=None):
    """
    filename: Image which should be scaled
    x, y: new image size (ratio is kept)
    mktemp: if true, a temporary file will be created
    new_filename: use this filename for the created file
    """
    if not os.path.isfile(filename):
        print filename, "not a file"
        return
    if mktemp and new_filename:
        raise "Either use mktemp xor give a new_filename"
    if mktemp:
        new_filename=tempfile.mktemp()
    elif not new_filename:
        new_filename=insert_midfix(filename, '_res%s' % (x))
    if os.path.isfile(new_filename):
        if os.path.getmtime(filename)<os.path.getmtime(new_filename):
            return new_filename
    ret=os.system("convert -geometry %sx%s '%s' '%s'" % (
        x, y, filename, new_filename))
    if ret!=0:
        print "File:", filename, "can't be converted"
        return None
    print new_filename, "created"
    return new_filename

usage="""Usage:
create-thumbnails.py directory [dir2 ...]
create *_resNNNN files
"""

if __name__=="__main__":
    argv=sys.argv
    if len(argv)<2:
        print usage
        sys.exit()
    for dir in argv[1:]:
        search_recursive(".*", dir, resize_batch)






