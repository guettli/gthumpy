#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
Erstelle eine CD um Bilder
nachzubestellen.
"""

import os
import re
import sys
import glob
import time
import shutil
import tempfile

pictures="/home/guettli/pictures/ixus"

def usage():
    print "Usage: %s id_file.txt" % (os.path.basename(sys.argv[0]))

def main():
    # read file
    if len(sys.argv)!=2:
        usage()
        sys.exit()
    idfile=sys.argv[1]
    pics={}
    fd=open(idfile)
    regex=re.compile(r'^([\w\d]+)\s*(\d*)\s*.*$')
    for line in fd.readlines():
        line=line.strip()
        if not line or line.startswith("#"):
            continue
        match=regex.match(line)
        if not match:
            raise("Fehler in Zeile %s von %s" %(
                line, idfile))
        pic=match.group(1)
        count=match.group(2)
        if not count:
            count=1
        else:
            count=int(count)
        old=pics.get(pic, 0)
        pics[pic]=old+count

    items=pics.items()
    items.sort()
    #for pic, count in items:
    #    print pic, count

    files=find_files(pictures)
    tempdir=tempfile.mktemp()
    os.mkdir(tempdir)
    pics_dir=os.path.join(tempdir, "pics")
    os.mkdir(pics_dir)
    for pic, count in items:
        file=files.get(pic)
        if not file:
            raise("Kann Bild %s nicht finden!" % pic)
        for i in range(1, count+1):
            dest=os.path.join(pics_dir, "%s-%02d.jpg" % (pic, i))
            shutil.copyfile(file, dest)
    os.chdir(tempdir)
    print"-----> Tempdir %s" % tempdir
    cmd="mkisofs -r -J -o pics.iso pics"
    ret=os.system(cmd)
    if ret:
        raise("Fehler bei '%s'" % cmd)

    logdir=os.path.join(os.environ["HOME"], "log", "gthumpy-make-cd")
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    logfile=os.path.join(logdir, "idfile-%s.txt" % 
                         time.strftime("%Y-%m-%d-%H-%M"))
    assert(not os.path.exists(logfile))
    shutil.copyfile(idfile, logfile)

    os.system("nautilus '%s'" % (tempdir))
    
    
img_regex=re.compile('^(?:IMG_)?(.+).jpg$', re.IGNORECASE)
def find_files(dir, files={}):
    f=os.listdir(dir)
    f.sort()
    f.reverse()
    for filename in f:
        if filename==".xvpics":
            continue
        file=os.path.join(dir, filename)
        if os.path.isdir(file):
            find_files(file, files)
        else:
            match=img_regex.match(filename)
            if match:
                pic=match.group(1)
                if re.match(r'^.*_res\d+$', pic):
                    continue
                old=files.get(pic)
                if old:
                    print "Fehler, Bild existiert mehrmals: alt:%s neu:%s" % (
                        old, file)
                    continue
                files[pic]=file
    return files

if __name__=="__main__":
    main()
                
