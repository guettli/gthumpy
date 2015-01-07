# -*- coding: iso-8859-1 -*-

#My Imports
import GthumpyUtils
import Utils

#Python Imports
import re
import glob
import os.path
import sys
from xml.sax import saxutils
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# TODO: Change strange class ParsedFiles to a dictionary
# of a new class (e.g. GthumpyFile)

#Singleton
class ParsedFiles:
    def __init__(self, config):
        self.config=config
        self.template=[]
        self.filenames=[]
        self.dates={}        # {'fooImage' : '2002-03-23', ...}
        self.titles={}       # {'fooImage' : 'myTitle', ...}
        self.descriptions={} # {'fooImage' : 'blu bla', ...}
        self.directories={}  # {'fooImage' : 'dir', 'fooImage2': 'dir2', ...}

        template_picture=os.path.join(self.config.template_dir,
                                   "template_picture.html")
        self.template_picture=open(template_picture).read()

        template_index=os.path.join(self.config.template_dir, self.config.template_index)
        self.template_index=open(template_index).read()
    
class GthumpyParser(ContentHandler):
    supported_elements=["gthumpy", "title", "description", "date"]

    title=''
    description=''
    def characters(self, content):
        self.content.append(content.encode("latin1"))

    def startElement(self, name, atts):
        if not name in self.supported_elements:
            se=str(self.supported_elements)
            msg="Element ' " + name + "' not in list of supported " + \
                 "elements: " + se
            raise Exception(msg)
        self.content=[]
            
    def endElement(self, name):
        content=''.join(self.content).strip()
        if name=="date":
            if not content:
                content="????-??-??"
            if not re.match(
                r'[0-9?][0-9?][0-9?][0-9?]-[0-9?][0-9?]?-[0-9?][0-9?]?',
                content):
                msg="<date> must be in the format: yyyy-mm-dd\n" + \
                     "file: " + self.file
                raise Exception(msg)
            self.date=content
        elif name=="gthumpy":
            #root-element
            pass
        elif name=="description":
            self.description=content
        elif name=="title":
            self.title=content
        else:
            raise Exception("Unknown element: '%s'", (name))

    def parse(self, gthumpy_filename, parsedFiles=None):
        file=GthumpyUtils.image2name(gthumpy_filename)
        self.file=file
        p=make_parser()
        p.setContentHandler(self)
        assert os.path.exists(gthumpy_filename), gthumpy_filename
        input_source=saxutils.prepare_input_source(gthumpy_filename)
        try:
            p.parse(input_source)
        except:
            print "Error while parsing %s" % gthumpy_filename
            print sys.exc_info()[0]
            raise
        image=GthumpyUtils.name2image(file)
        exifdict=Utils.exifdict(image)
        self.date=re.sub(r'^(\d\d\d\d:\d\d:\d\d \d\d:\d\d)(:\d\d\s*)$', r'\1',
                         str(exifdict.get("Image DateTime", "????-??-??")))
        if parsedFiles:
            pf=parsedFiles
            pf.directories[file]=gthumpy_filename
            for tag in ["date", "title", "description"]:
                if hasattr(self, tag):
                    list=getattr(pf, tag + "s")
                    list[file]=getattr(self, tag)
                else:
                    raise "Internal Error: Tag '%s' was not parsed: %s %s %s" % (
                        tag, file, self, dir(self))
                
