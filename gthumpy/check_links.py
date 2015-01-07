# -*- coding: iso-8859-1 -*-

import os
import re
import sys
import urllib

href_regex=re.compile(r'''^.*<a\s*href=["']([^"!#?]*)([#?].*?)?["'].*$''')

def check_links(mydir):
    for file in os.listdir(mydir):
        file=os.path.join(mydir, file)
        if os.path.isdir(file):
            check_links(file)
        if not file.endswith(".html"):
            continue
        fd=open(file)
        i=0
        for line in fd:
            i+=1
            match=href_regex.match(line)
            if not match:
                continue
            href=urllib.unquote(match.group(1))
            link_to=os.path.join(mydir, href)
            if not os.path.isfile(link_to):
                print "%s: not found %s (line: %s)" % (file, href, i)
        
if __name__=="__main__":
    if len(sys.argv)==2:
        mydir=sys.argv[1]
    else:
        mydir="."
    check_links(mydir)
