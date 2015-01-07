#!/usr/bin/env python
import os
import sys
import glob
import time
import datetime

import Utils
import glib

MAX_SIZE=3000

def main():
    while True:
        missing_tif=create_small_jpgs()
        if not missing_tif:
            break
        print '%s missing tif files. I wait and try again ...' % missing_tif
        time.sleep(10)

def create_small_jpgs():
    panorama_dir=os.path.join(os.environ['HOME'], 'panoramas')
    if not os.path.isdir(panorama_dir):
        print 'Does not exist: %s' % panorama_dir
        sys.exit(3)
    missing_tif=0
    now=datetime.datetime.now()
    for fn in sorted(os.listdir(panorama_dir)):
        fn_abs=os.path.join(panorama_dir, fn)
        if not os.path.isdir(fn_abs):
            continue
        source_dir=os.path.join(fn_abs, 'source-dir.txt')
        if not os.path.exists(source_dir):
            continue
        source_dir=open(source_dir).read().strip()
        if not os.path.exists(source_dir):
            print '%s does not exist (%s)' % (source_dir, fn_abs)
            continue
        try:
            pto=glob.glob(os.path.join(fn_abs, '*.pto'))[0]
        except IndexError:
            missing_tif+=1
            print '%s .pto does not exist (up to now)' % fn_abs
            continue
        tif='%s.tif' % pto.rsplit('.', 1)[0]
        if not os.path.exists(tif):
            missing_tif+=1
            print '%s .tif does not exist (up to now)' % fn_abs
            continue
        jpg=os.path.join(source_dir, '%s.jpg' % fn)
        if os.path.exists(jpg):
            mtime=datetime.datetime.fromtimestamp(os.path.getmtime(jpg))
            if now-mtime<datetime.timedelta(hours=1):
                # file is young, report
                print 'OK, already done', jpg
            continue
        try:
            pb=Utils.scale2pixbuf(MAX_SIZE, MAX_SIZE, tif)
        except glib.GError, exc:
            print exc
            missing_tif+=1
            print 'I guess TIF gets written ...'
            continue
        pb.save(jpg, 'jpeg')
        print 'created', jpg
    return missing_tif

if __name__=='__main__':
    main()
