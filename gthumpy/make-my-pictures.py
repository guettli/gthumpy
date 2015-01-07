#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

#My Imports:
import createThumbnails
import gthumpy
import indexForAllDirs
import GthumpyUtils
from check_links import check_links
from Config import Config
import lang
_=lang._

#Python Imports
import os
import re
import sys
import shutil
import getopt

def usage():
    print """Usage: %s [--no-reverse] [--template-index file] [startdir]
Create Thumbnails and HTML pages for directory startdir.
""" % (os.path.basename(sys.argv[0]))
    
def main():
    config=Config()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["no-reverse",
                                                      "template-index="])
    except getopt.GetoptError, exc:
        print exc
        usage()
        sys.exit(1)

    reverse=True
    for o, a in opts:
        if o=="--no-reverse":
            reverse=False
        elif o=="--template-index":
            config.template_index=a
        else:
            raise Exception("unparsed %s %s" % (o, a))
    
    if len(args)>1:
        usage()
        sys.exit(1)
        
    lang.set_lang(config.lang)
    if not args:
        startdir=config.image_dir
    else:
        startdir=args[0]
        if not os.path.exists(startdir):
            print "%s does not exist" % startdir
            usage()
            sys.exit(3)
            
    files=os.listdir(startdir)
    files.sort()
    for dir in files:
        dir=os.path.join(startdir, dir)
        if not os.path.isdir(dir):
            continue
        print "Working on %s" % dir

        #Create Thumbnails:
        files=os.listdir(dir)
        new_files=[]
        for file in files:
            file=os.path.join(dir, file)
            new_files.append(file)
        files=new_files
        files=GthumpyUtils.sort_int(files, ".jpg")
        for file in files:
            createThumbnails.resize_batch(file)

        #Makefile-like behavior: Create HTML files only
        #if gthumpy-file is newer than html-file
        create=False
        mtime_html=None
        for file in os.listdir(dir):
            if not file.endswith(".gthumpy"):
                continue
            file=os.path.join(dir, file)
            name=re.sub(r'(.*)\.gthumpy', r'\1', file)
            if not os.path.isfile("%s.html" % name):
                #at least one html file does not exist
                create=True
                break
            mtime_html=os.path.getmtime("%s.html" % name)
            if  mtime_html < os.path.getmtime(file):
                #at least one gthumpy file was changed
                create=True
                break
        description=os.path.join(dir, "description.txt")
        if mtime_html and os.path.isfile(description) and \
           os.path.getmtime(description)>mtime_html:
            create=True
        if not os.path.exists(os.path.join(dir, "index.html")):
            create=True
        if create:
            print "Creating html files: %s" % dir
            gt=gthumpy.Gthumpy(config)
            gt.createHTML(dir)
        else:
            print "Skipping creation of html files %s" % dir

    indexForAllDirs.indexForAllDirs(startdir, reverse)
    miscdir=os.path.join(startdir, "misc")
    origdir=os.path.join(os.path.dirname(sys.argv[0]), "misc")
    if not os.path.isdir(origdir):
        raise("Cannot find %s. Needed for gthumpy.js and style.css" %
              origdir)
    if not os.path.isdir(miscdir):
        os.mkdir(miscdir)
    for file in ["gthumpy.js", "style.css"]:
        shutil.copyfile(
            os.path.join(origdir, file),
            os.path.join(miscdir, file))

    print "checking links"
    check_links(startdir)    

if __name__=="__main__":
    main()
