# -*- coding: iso-8859-1 -*-

# Python Imports
import os
import re
import sys
import base64

# My Imports
import lang
_=lang._

def indexForAllDirs(startdir, reverse=True):
    dirs={}
    for dir in os.listdir(startdir):
        if dir=="misc":
            continue
        dir=os.path.join(startdir, dir)
        if not os.path.isdir(dir):
            continue
        description_file=os.path.join(dir, "description.txt")
        if os.path.isfile(description_file):
            fd=open(description_file)
            content=fd.read()
            fd.close()
        else:
            print "### No %s" % description_file
            content=""
        dirs[dir]=content

    keys=dirs.keys()
    assert len(keys)!=0, \
           "No descriptions found in %s" % (startdir)
    keys.sort()
    if reverse:
        keys.reverse()
    
    rows=[]
    oldyear=None
    for dir in keys:
        #Berechne Anzahl der Bilder in dem Verzeichnis:
        count=0
        for file in os.listdir(dir):
            if file.endswith('.gthumpy'):
                count+=1
        match=re.match(r'.*?(\d\d\d\d)-\d\d-\d\d$', dir)
        if match:
            year=int(match.group(1))
            if oldyear is not None:
                if year!=oldyear:
                    rows.append('''
                     <tr>
                      <th align="center" colspan="3">%s</th>
                     </tr>''' % year) 
            oldyear=year
        
        basename=os.path.basename(dir)
        rows.append('''
         <tr>
          <td align="center">
           <nobr><a name="%s" href="%s/index.html"
                    onclick="goto_href(this)">%s</a></nobr>
          </td>
          <td>%s</td>
          <td align="right">%s</td>
         </tr>''' %
                  (base64.b64encode(basename),
                   basename, basename, dirs[dir], count))
        
    rows=''.join(rows)

    main='''
       <div align="center">
        <b>%s</b>
        <table border="1" class="thinborder" width="60%%">
         <tr>
          <th>%s</th>
          <th>%s</th>
          <th>%s</th>
         </tr>
         %s
        </table>
        <br>
        <b>%s</b>
        <br>
        <br>
        <br>
       </div>
      ''' % (
        _("Overview"),
        _("Directory"),
        _("Description"),
        _("Number of pictures"),
        rows,
        _("Overview"))

    overview=_("Overview")
    template='''<html>
      <head>
       <title>%(overview)s</title>
       <script src="misc/gthumpy.js" type="text/javascript"></script>
       <script type="text/javascript">
        document.default_size=800;
       </script>
       <link rel=stylesheet type="text/css" href="misc/style.css">
      </head>
      <body onLoad="mark_hash()">
       %(main)s
      </body>
     </html>
     '''
    template_file=os.path.join(startdir, 'index_all_template.ihtml')
    if os.path.exists(template_file):
        template=open(template_file).read()
    html=template % locals()
    index=os.path.join(startdir, "index.html")
    out=open(index, "w")
    out.write(html)
    out.close()
    print "Created index of all directories: %s." % index
    print "There are %s directories" % len(keys)

if __name__=="__main__":
    indexForAllDirs(sys.argv[1])
