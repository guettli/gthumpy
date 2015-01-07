# -*- coding: iso-8859-1 -*-

import os
import re
import sys
import shutil

file_regex=re.compile(r'IMG_(\d*).JPG', re.IGNORECASE)
def read_dir(dir, ids, files):
    for filename in os.listdir(dir):
        file=os.path.join(dir, filename)
        if os.path.isdir(file):
            read_dir(file, ids, files)
            continue
        match=file_regex.match(filename)
        if not match:
            continue
        id=match.group(1)
        if id in ids:
            old=files.get(id)
            if old:
                raise("Interner Fehler, Datei schon da %s %s "
                      % (old, file))
            files[id]=file

def main():
    if len(sys.argv) not in [4, 5]:
        print """
Usage: %s picture_id_file picture_dir out_dir [res]
""" % (os.path.basename(sys.argv[0]))
        sys.exit(1)
        
    id_regex=re.compile(r'^(\d*).*$')
    fd=open(sys.argv[1])
    ids=[]
    for line in fd:
        match=id_regex.match(line)
        if match:
            ids.append(match.group(1))
    files={}
    read_dir(sys.argv[2], ids, files)
    out_dir=sys.argv[3]
    if len(sys.argv)==5:
        res="_res%s" % sys.argv[4]
    else:
        res=""
    for id in ids:
        file=files.get(id)
        if not file:
            print "Warning: ID %s was not found" % id
            continue
        file=re.sub(r'^(.*?)(\.[jJ][pP][gG])$', '\\1%s\\2' % res, file)
        print file
        out_file=os.path.join(out_dir, os.path.basename(file))
        print "Copying to %s" % out_file
        shutil.copyfile(file, out_file)
        
if __name__=="__main__":
    main()
