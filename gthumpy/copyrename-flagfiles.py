#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

# Python Imports
import os
import re
import sys
import datetime

def usage():
    print """Usage: %s flagdir todir
flagdir: ~/.local/share/gthumpy/flags/MyFlag/links

""" % (
        os.path.basename(sys.argv[0]))

def main():
    if len(sys.argv)!=3:
        usage()
        sys.exit(1)
    flagdir=sys.argv[1]
    todir=sys.argv[2]
    links=os.listdir(flagdir)
    links.sort()
    dates={}
    for link in links:
        link=os.path.join(flagdir, link)
        if not os.path.islink(link):
            continue
        image=os.readlink(link)
        if not os.path.isfile(image):
            print 'Broken link: %s --> %s' % (
                link, image)
            continue
        dirname=os.path.basename(os.path.dirname(image))
        match=re.match(r'(\d\d\d\d)-(\d\d)-(\d\d).*$', dirname)
        assert match, dirname
        date=datetime.date(*[int(i) for i in match.groups()])
        mylist=dates.get(date)
        if mylist==None:
            mylist=[]
            dates[date]=mylist
        mylist.append(image)
    items=dates.items()
    items.sort()
    all=[]
    for date, mylist in items:
        count=0
        base=date.strftime('%y%m%d')
        for image in mylist:
            toname=os.path.join(todir, '%s%02d.jpg' % (base, count))
            assert not os.path.exists(toname)
            os.link(image, toname)
            count+=1
        all.append(count)
    print "%d link in %s" % (sum(all), todir)
        
        
if __name__=="__main__":
    main()
