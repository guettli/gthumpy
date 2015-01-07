#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import re
import cgi
import sys
import glob
import base64
import urllib
import string
from xml.sax import saxutils
from xml.sax import make_parser
from types import *

#My imports
import GthumpyParser
import GthumpyUtils
from GthumpyUtils import name2image
from GthumpyUtils import insert_midfix
from relative_url import relative_url
import createThumbnails
import lang
_=lang._

class Gthumpy:
    def __init__(self, config):
        self.config=config
        
    def parse_gthumpy_file(self, filename):
        self.parser.parse(filename, self.pf)

    def createHTML(self, directory):
        u'''
        Erstelle die HTML-Seiten für einen Tag
        '''
        print "createHTML: %s" % directory
        if not os.path.isdir(directory):
            raise Exception("Not a directory: %s" % directory)
        if directory[-1] in ("/", "\\"):
            directory=directory[:-1]
        self.root=directory
        self.pf=GthumpyParser.ParsedFiles(self.config)
        self.parser=GthumpyParser.GthumpyParser()
        print("Reading all .gthumpy files...")
        files=os.listdir(directory)

        # Sort files
        files=GthumpyUtils.sort_int(files, ".gthumpy")
        for file in files:
            file=os.path.join(directory, file)
            base=file[:-8]
            globfiles=glob.glob("%s*" % base)
            assert(globfiles)
            found=0
            for f in globfiles:
                if f.lower().endswith(".jpg"):
                    found=1
                    break
            if not found:
                print "No image file for %s. Deleting it" % file
                os.unlink(file)
            else:
                name=re.sub(r'(.*)\.gthumpy', r'\1', file)
                self.pf.filenames.append(name)
        print(" found %i files" % len(self.pf.filenames))
        print("Parsing files...")
        for file in self.pf.filenames:
            self.parse_gthumpy_file("%s.gthumpy" % file)
        print("  done")
        self.filloutTemplate(self.pf.filenames)
        
    def compare_dates(self, a, b):
        da=self.pf.dates[a]
        db=self.pf.dates[b]
        if da==db:
            return cmp(a, b)
        else:
            return cmp(da, db)

    def compare_directories(self, a, b):
        da=self.pf.directories[a]
        db=self.pf.directories[b]
        return cmp(da, db)
    
    def filloutTemplate(self, filenames):
        """filenames: list of filenames (with out .jpg)
        the slide show will be ordered by this list
        """
        #These default values fit to the image names
        #created with "createThumbnails.py"
        assert len(createThumbnails.image_sizes)==3, "ConfigError, image_sizes must contain three entries: %s" % (
            createThumbnails.image_sizes)
        thumbnail_extension="_res%s" % createThumbnails.image_sizes[0][0]
        
        i=-1
        for file in filenames:
            i=i+1
            self.create_html_file(
                i, file, filenames)
            # Big page (1024x768)
            #fn_orig=name2image(file, no_exception=True)
            #imageorig=urllib.quote(os.path.basename(fn_orig))
            #thumb_big=insert_midfix(fn_orig, bigimage_extension)
            #imagebig=urllib.quote(os.path.basename(thumb_big))
            #html=self.pf.template_big % locals()
            #fd=open('%s%s.html' % (file, bigimage_extension), "wt")
            #fd.write(html)
            #fd.close()
            
        #End for file in filenames

        #Create 2003-07-15/index.html            
        index_filename="%s/index.html" % self.root
        rows=[]
        number=0
        for file in filenames:
            number+=1
            title=self.pf.titles[file]
            description=self.pf.descriptions[file]
            date=self.pf.dates[file]
            fn_orig=name2image(file, no_exception=1)
            fn_thumb=insert_midfix(fn_orig, thumbnail_extension)
            if not os.path.isfile(fn_thumb):
                raise("%s does not exist %s %s" % (fn_thumb,
                                                   fn_orig,
                                                   file))
                sys.stderr.write("Warning: File '%s' not found. "
                                 "'python createThumbnails.py foo_dir'"
                                 " might help\n" % (fn_thumb))
            if title=="":
                title="&nbsp;"
            else:
                title=cgi.escape(title)
            if description=="":
                description="&nbsp;"
            else:
                description=cgi.escape(description)
            if date=="":
                date="&nbsp;"
            file_rel=relative_url(index_filename, file)
            rows.append('''
             <tr>
              <td align="right">%d</td>
              <td>%s</td>
              <td>%s</td>
              <td><a name="%s"><nobr>%s</nobr></a></td>''' % (
                number, title, description,
                base64.b64encode(file_rel), date))
            fn_thumb_rel=relative_url(index_filename, fn_thumb)
            rows.append('''
             <td align="center">
              <a href="%s.html" onclick="goto_href(this)"><img src="%s"></a>
             </td>\n''' % (urllib.quote(file_rel),
                           urllib.quote(fn_thumb_rel)))
            rows.append("</tr>")
        rows=''.join(rows)
        description_file=os.path.join(self.root, "description.txt")
        if os.path.isfile(description_file):
            description=open(description_file).read()
        else:
            description=""
        title=cgi.escape(description)
        start_link='<a href="../index.html#%s" onclick="goto_href(this)">%s</a>' % (
            base64.b64encode(os.path.basename(self.root)),
            _("Back to overview"))
        #Write created index_foo.html
        html=self.pf.template_index % locals()
        fd=open(index_filename, "wt")
        fd.write(html)
        fd.close()

    def create_html_file(self, i, file, filenames):
        #create image.html
        link_name=urllib.quote(os.path.basename(name2image(file, no_exception=True)))
        img=insert_midfix(link_name, '_res%s' % (createThumbnails.image_sizes[2][0]))
        image='<a href="%s"><script type="text/javascript">write_image("%s")</script>' \
            '<noscript><img src="%s"/></noscript></a>' % (
            link_name, link_name, img)
        title=self.pf.titles.get(file)
        if not title:
            title="&nbsp;"
        else:
            title=cgi.escape(title)
        date=self.pf.dates.get(file, "????-??-??")
        description=self.pf.descriptions.get(file)
        if not description:
            description="&nbsp;"
        else:
            description=cgi.escape(description)
        index='''
         <span style="color: gray">%sv%s</span>
         <a href="index.html#%s" onclick="goto_href(this)">%s</a>''' % (
            i+1, len(filenames), base64.b64encode(os.path.basename(file)),
            _("Directory"))
        #Create [prev] [next] links
        if i==0:
            #First page has no previous link
            prev=""
        else:
            prev="%s.html" % filenames[i-1] # filename of previous page
            prev=urllib.quote(relative_url(file, prev))
            prev='''<a href="%s" onclick="goto_href(this)">[%s]</a>''' % (
                prev, _("prev"))
        if i==len(filenames)-1:
            next=""
        else:
            next="%s.html" % filenames[i+1] # filename of next page
            next=urllib.quote(relative_url(file, next))
            next='''<a href="%s" onclick="goto_href(this)">[%s]</a>''' % (
                next, _("next"))

        sizes=[]
        for width, height in createThumbnails.image_sizes[1:]:
            # Link zu gleichem Bild, in anderer Groesse
            sizes.append('<a href="./%s.html?size=%d">%d</a>' % (
                urllib.quote(os.path.basename(file)), width, width))
        sizes=_('Size of Image: %s') % '&nbsp;'.join(sizes)
        directory=cgi.escape(os.path.basename(os.path.dirname(file)))
        fd=open('%s.html' % file, 'wt')
        html=self.pf.template_picture % locals()
        assert not '/home/' in html, (file, image)
        fd.write(html)
        fd.close()


usage="""Usage:
gthumpy directory
"""
    
if __name__=="__main__":
    argv=sys.argv
    if len(argv)!=2:
        print usage
        sys.exit()
    lang.set_lang("en")
    gt=Gthumpy()
    gt.createHTML(argv[1])




