# Python Imports
import os
import sys
from types import *

# My Imports
import de
import en
langs=["de", "en"]

# Not threadsafe
transdict=None
translang=None

def set_lang(mylang):
    print "set_lang", mylang
    assert(type(mylang)==StringType)
    if not len(mylang)==2:
        raise ValueError, 'The language token must be two characters ("de", "en", ...)'
    if not mylang in langs:
        raise ValueError, "There is no %s.py in the directory lang" % mylang
    global transdict
    global translang
    transdict=globals()[mylang].transdict
    translang=mylang
    
def _(text):
    assert(type(text)==StringType)
    global transdict
    global translang
    if transdict is None:
        raise("Please call lang.set_lang(...) first")
    trans=transdict.get(text)
    if trans is None:
        if translang!="en":
            sys.stderr.write("mygettext: '%s' unkown in language %s\n" % (
                text, translang))
        trans=text
        
    return trans

def translate_template(html):
    """
    Simple replacement.
    This fails, if there are keys in the translate dictionary
    which are part of the HTML (title, head, left)
    """
    global transdict
    assert(type(html)==StringType)
    for en, mylang in transdict.items():
        html=html.replace(en, mylang)
    return html
