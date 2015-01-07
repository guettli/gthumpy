#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from glob import glob
import sys
import os
import re

usage= \
"""
Move ranges of images

args: from_file to_file [from_dir] to_dir

from_dir defaults to "."

example:
 move-range.py 1301 1329 ../2003-05-20
"""


if len(sys.argv)!=4 and len(sys.argv)!=5:
    print usage
    sys.exit()

start=sys.argv[1]
start=int(start)
end=sys.argv[2]
end=int(end)
if len(sys.argv)==4:
    startdir=os.getcwd()
    dir=sys.argv[3]
else:
    dir=sys.argv[4]
    startdir=sys.argv[3]

if not os.path.isdir(dir):
    os.mkdir(dir)
    print "Created %s" % dir

files=os.listdir(startdir)

print "start: %s end: %s startdir: %s dir: %s" % (
    start, end, startdir, dir)

counter=0
for i in range(start, end+1):
    to_move=[]
    for file in files:
        if file.find(str(i))!=-1:
            to_move.append(file)
    for file in to_move:
        counter+=1
        os.rename(os.path.join(startdir, file),
                  os.path.join(dir, file))

print "%s files where moved" % counter
