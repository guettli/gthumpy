#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
Erstelle eine CD mit Bilder

Thomas Guettler Juni 2004

"""


import os
import re
import sys
import glob
import shutil
import tempfile

pictures_dir="/home/guettli/pictures/ixus"

def usage():
    print "Usage: %s id_file.txt" % (os.path.basename(sys.argv[0]))

def main():
    # read file
    if len(sys.argv)!=2:
        usage()
        sys.exit()
    file=sys.argv[1]
    pics={}
    fd=open(file)
    regex=re.compile(r'^(\d+)\s*(\d*)\s*$')
    for line in fd.readlines():
        line=line.strip()
        if not line or line.startswith("#"):
            continue
        match=regex.match(line)
        if not match:
            raise("Fehler in Zeile %s von %s" %(
                line, file))
        pic=match.group(1)
        pic=int(pic)
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

    assert(os.path.isdir(pictures_dir))
    files=find_files(pictures_dir)
    tempdir=tempfile.mktemp()
    os.mkdir(tempdir)
    pics_dir=os.path.join(tempdir, "pics")
    html_dir=os.path.join(tempdir, "html")
    print "Verzeichnis der Bilder", html_dir
    os.mkdir(pics_dir)
    os.mkdir(html_dir)
    fd=open(os.path.join(tempdir, "autorun.inf"), "wb")
    fd.write("[autorun]\r\nopen=html\\index.html\r\n")
    fd.close()

    for pic, count in items:
        file=files.get(pic)
        if not file:
            raise("Kann Bild %s nicht finden!" % pic)
        assert(count==1)
        dest=os.path.join(pics_dir, os.path.basename(file))
        shutil.copyfile(file, dest)
        base=file[:-4]
        res_files=glob.glob("%s_res*" % base)
        assert(res_files)
        imgdir=os.path.basename(os.path.dirname(
            file))
        imgdir_dest=os.path.join(html_dir, imgdir)
        if not os.path.isdir(imgdir_dest):
            os.mkdir(imgdir_dest)
            shutil.copyfile(
                os.path.join(os.path.dirname(file),
                             "description.txt"),
                os.path.join(imgdir_dest,
                             "description.txt"))
        for rfile in res_files:
            shutil.copyfile(rfile, os.path.join(
                imgdir_dest,
                os.path.basename(rfile)))
        shutil.copyfile("%s.gthumpy" % base,
                        os.path.join(
            imgdir_dest, "%s.gthumpy" % os.path.basename(file)[:-4]))
    print "Jetzt make-my-pictures '%s' aufrufen" % html_dir
    
img_regex=re.compile('^..._(\d+).jpg$', re.IGNORECASE)
def find_files(dir, files={}):
    for filename in os.listdir(dir):
        file=os.path.join(dir, filename)
        if os.path.isdir(file):
            find_files(file, files)
        else:
            match=img_regex.match(filename)
            if match:
                pic=match.group(1)
                pic=int(pic)
                old=files.get(pic)
                if old:
                    raise("Fehler, Bild existiert mehrmals: alt:%s neu:%s" % (
                        old, file))
                files[pic]=file
    return files

if __name__=="__main__":
    main()
                
