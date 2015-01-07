#!/usr/bin/env python
from glob import glob
import shutil
import sys
import os
import re

usage= \
"""
Copy ranges of images

args: [--move] from to [extension] dir

example:
 copy-range.py 1498 1503 _res150.jpg /tmp

This is usefull if your have a directory where every picture has
number in its name.

Example:
 IMG_1498.JPG
 IMG_1499.JPG
 IMG_1500.JPG
 IMG_1501.JPG
 IMG_1503.JPG

"""

startdir=os.getcwd()

len_args=len(sys.argv)
if len_args<4:
    print usage
    sys.exit()

if sys.argv[1]=="--move":
    argv=[]
    argv.append(sys.argv[0])
    argv.extend(sys.argv[2:])
    sys.argv=argv
    move=1
    cp_or_mv="moved"
else:
    move=0
    cp_or_mv="copied"
    
start=sys.argv[1]
start=int(start)
end=sys.argv[2]
end=int(end)
len_args=len(sys.argv)
if len_args==4:
    dir=sys.argv[3]
    extension=".*"
else:
    extension=sys.argv[3]
    dir=sys.argv[4]

if not os.path.isdir(dir):
    os.mkdir(dir)
    print "Created %s" % dir

files=os.listdir(startdir)

counter=0
for i in range(start, end):
    regex=re.compile('^.*%s%s$' % (i, extension.lower()))
    for file in files:
        if regex.match(file.lower()):
            if move:
                os.rename(os.path.join(startdir, file),
                          os.path.join(dir, file))
            else:
                shutil.copy(os.path.join(startdir, file), dir)
            counter+=1
            print "%s: %s" % (cp_or_mv, file)

print "%s files where %s" % (counter, cp_or_mv)
