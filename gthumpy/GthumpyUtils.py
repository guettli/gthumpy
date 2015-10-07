# -*- coding: iso-8859-1 -*-

import re
import os
import sys
import glob
import urllib
import StringIO

from Utils import try_unicode

image_extensions=['jpg', 'jpeg', 'png', 'avi', 'mov', 'mp4']

JUMP_NEXT=1
JUMP_PREV=-1

jump_verbose={
    JUMP_NEXT: 'next',
    JUMP_PREV: 'previous',
    }

def image_extension(filename):
    if '_res' in filename:
        return False
    low=filename.lower()
    if low.endswith('.avi.png'):
        # Previews of AVI files
        return False
    if low.endswith('.mov.png'):
        # Previews of AVI files
        return False
    match=re.match(r'^.*\.(\w{3,5})$', low)
    if not match:
        return False
    extension=match.group(1)
    if not extension in image_extensions:
        return False
    return extension
    
def log(log_string):
    sys.stderr.write("%s\n" % log_string)
    
def image2name(filename):
    """ fooImage.jpg --> fooImage"""
    return re.sub(r'(.*)\.[^.]*', r'\1', filename)

class NoImageException(Exception):
    pass

def name2image(name, no_exception=False):
    """ 'fooImage' --> 'fooImage.jpg' """
    files=glob.glob(name + ".*")
    image_files=[]
    for f in files:
        if not image_extension(f):
            continue
        if f.endswith('.mp4.png'):
            continue
        image_files.append(f)
    if len(image_files)>1:
        if not no_exception:
            raise Exception("Found more than one file that could be an " + \
                            "image: " + str(image_files))
        else:
            return ""
    elif len(image_files)==0:
        if not no_exception:
            raise NoImageException("Found no image file for " + name + \
                                ". Possible files: " + str(files))
        else:
            # TODO: Doofer Trick, damit das erstellen von
            # HTML-Seiten auch funktioniert, falls
            # nur foo_res???.JPG vorhanden.
            return "%s.JPG" % name
    return image_files[0]
    
def search_recursive(regex, dir, func):
    """Search recursively in a directory.
    If the regular expression matches the filename, call function
    on this file. func takes the filename as argument
    """
    if os.path.isdir(dir):
        l=os.listdir(dir)
        l.sort()
        for file in l:
            filename=os.path.join(dir, file)
            if re.match(regex, file):
                func(filename)
            search_recursive(regex, filename, func)

def insert_midfix(filename, midfix):
    "('foo.jpg', '.bar') --> 'foo.bar.jpg'"
    return re.sub(r'(.*)\.([^.]*)', r'\1' + midfix + r'.\2', filename)

def encode(string):
    return re.sub(r'[^-a-zA-Z0-9_]', r'_', string)


def sort_int(files, endswith=None):
    decorated=[]
    regex=re.compile(r'[0-9]+|[a-z]+')
    for file in files:
        if endswith is None or file.lower().endswith(endswith):
            new=[]
            for part in regex.findall(file.lower()):
                if part in ['img']:
                    continue
                if len(part)==3 and part.startswith('st'):
                    # Canon Powershot STA_1234.JPG
                    continue
                new.append(part)
            parts=new
            decorated.append((parts, file))
    decorated.sort()
    files=[]
    for parts, file in decorated:
        files.append(file)
    return files

MAX_DEPTH=20
def find_this_or_child_directory(curr_dir, jump=JUMP_NEXT, rec_depth=0):
    images, sub_dirs = get_images_and_subdirs(curr_dir, jump=jump, rec_depth=rec_depth)
    if images:
        return curr_dir
    for dir in sub_dirs:
        try:
            return find_this_or_child_directory(dir, jump, rec_depth+1)
        except NoMatchFound:
            continue
    raise NoMatchFound()

def get_images_and_subdirs(curr_dir, jump=JUMP_NEXT, rec_depth=0):
    if rec_depth>MAX_DEPTH:
        raise NoMatchFound()
    files=sorted(os.listdir(curr_dir))
    if jump==JUMP_PREV:
        files=reversed(files)
    sub_dirs=[]
    images=[]
    for file in files:
        file=os.path.join(curr_dir, file)
        extension=image_extension(file)
        if extension:
            images.append(file)
        if os.path.isdir(file):
            sub_dirs.append(file)
    return (images, sub_dirs)

def find_child_directory(curr_dir, jump=JUMP_NEXT, rec_depth=0):
    images, sub_dirs = get_images_and_subdirs(curr_dir, jump, rec_depth)
    for sub_dir in sub_dirs:
        try:
            return find_this_or_child_directory(sub_dir, jump, rec_depth)
        except NoMatchFound:
            continue
    raise NoMatchFound()

class NoMatchFound(Exception):
    pass

def find_next_directory(curr_dir, jump=JUMP_NEXT, rec_depth=0):
    try:
        return find_child_directory(curr_dir, jump=jump, rec_depth=rec_depth)
    except NoMatchFound:
        pass
    try:
        return find_sibbling_directory(curr_dir, jump, rec_depth)
    except NoMatchFound:
        print 'No Next dir found %s' % curr_dir
        return None

class DirectoryDoesNotExist(ValueError):
    pass

def find_sibbling_directory(curr_dir, jump=JUMP_NEXT, rec_depth=0):
    u'''
    Find next directory with images
    '''
    if rec_depth>MAX_DEPTH:
        raise NoMatchFound()

    dirname, basename = os.path.split(curr_dir)
    if not basename:
        raise Exception('No next/prev directory found. self.dir=%s' % (
                'TODO'))

    files=sorted(os.listdir(dirname))
    try:
        idx=files.index(basename)
    except ValueError:
        raise DirectoryDoesNotExist('%s not in files of %s: %s?' % (
                basename, dirname, files))
    while True:
        idx+=jump
        if idx==len(files) or idx==-1:
            # current dir is already last/first
            return find_sibbling_directory(dirname, jump, rec_depth+1)
        next_dir=os.path.join(dirname, files[idx])
        if not os.path.isdir(next_dir):
            continue
        try:
            return find_this_or_child_directory(next_dir, jump, rec_depth+1)
        except NoMatchFound:
            continue
    raise NoMatchFound()

def find_next_dir_and_description(curr_dir, jump=JUMP_NEXT):
    next=find_next_directory(curr_dir, jump)
    if not next:
        return (next, '')
    descr_file=os.path.join(next, 'description.txt')
    if not os.path.exists(descr_file):
        return (next, '')
    return (next, try_unicode(open(descr_file).read()))

def test_sort_int():
    l=[
        "a/IMG_9000.jpg",
        "a/STA_1000.jpg"]
    l_ist=sort_int(l)
    assert l_ist==[ 'a/STA_1000.jpg', 'a/IMG_9000.jpg'], l_ist

                
                

        



