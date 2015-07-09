#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# (c) 2002-2006 Thomas Güttler: http://www.thomas-guettler.de/
# http://guettli.sf.net/

# Python Imports
import os
import sys

# Python GTK
import pygtk
pygtk.require("2.0")
import gtk

try:
    import kiwi
except ImportError:
    sys.path.append(os.path.join(os.environ["HOME"], "pyaddons", "lib",
                                 "python%s" % sys.version[:3],
                                 "site-packages"))
# My Imports
import Utils
from Config import Config
from Application import Application

def usage():
    print """
Usage: %s [dir]

If you don't specify "dir". Your gthump.config file is read, and the latest directory which has pictures without a ".gthumpy" file is used.

$Id: editMetadata.py 163 2008-12-14 20:27:55Z guettli $
$HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/editMetadata.py $
""" % (
    os.path.basename(sys.argv[0]))

# Let ctrl-c break dialogs, too.
#import signal
#signal.signal(signal.SIGINT, signal.SIG_DFL)
        
def main():
    sys.stdout=Utils.FlushStream(sys.stdout)
    filelist=[]
    config=Config()
    if len(sys.argv)==2:
        dir=os.path.abspath(sys.argv[1])
    else:
        dir=None
    app=Application(config, dir)
    gtk.main()


if __name__ == "__main__":
    main()
