# Python Imports
import os
import re
import sys
import shutil

"""
 $Id: Config.py 152 2008-08-27 21:15:14Z guettli $
 $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/Config.py $
"""

known_vars=["image_dir", "lang", "template_dir", "flags_dir", "width",
            "height"]
int_vars=["width", "height"]


class Config:
    infoLabel="%(indexplusone)sv%(all)s %(datetime)s"
    lang="en"
    image_dir=None
    configfile=None
    template_dir=None
    template_index="template_index.html"
    flags_dir=None
    width=1024 # Default, if not value in .config/gthumpy/gthumpy.conf
    height=None # By default calculated: width*3/4
    style=None  # {True: style_selected, False: style_normal}
    
    def __init__(self):
        conffiles=[os.path.join(os.environ["HOME"], os.environ.get("XDG_CONFIG_HOME", ".config"),
                            "gthumpy", "gthumpy.conf"),
               os.path.join(os.path.dirname(__file__), "gthumpy.conf")]
        conf=None
        for f in conffiles:
            if os.path.isfile(f):
                print "Using config from %s" % f
                conf=f
                break
        if not conf:
            print "No config found. Searched: %s" % conffiles
            sys.exit(1)

        fd=open(conf)
        for line in fd:
            line=line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            match=re.match(r'^(.*?)=(.*)$', line)
            if not match:
                raise("ParseError: %s" % line)
            var=match.group(1).strip()
            value=match.group(2).strip()
            assert var in known_vars, \
               "Unkown var: %s in %s" % (line, conf)
            if var in int_vars:
                value=int(value)
            setattr(self, var, value)
        if not self.template_dir:
            self.template_dir=os.path.join(
                os.path.dirname(__file__), "templates")
        datadir=os.environ.get(
            "XDG_DATA_HOME",
            os.path.join(os.environ["HOME"], ".local", "share"))
        self.config_dir=os.path.join(datadir, "gthumpy")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        self.flags_dir=os.path.join(self.config_dir, "flags")
        if not os.path.exists(self.flags_dir):
            os.makedirs(self.flags_dir)

        self.sizes_dir=os.path.join(self.config_dir, "sizes")
        if not os.path.exists(self.sizes_dir):
            os.makedirs(self.sizes_dir)

        if not self.height:
            self.height=self.width*3/4
        self.configfile=conf
    
