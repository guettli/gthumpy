#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import datetime
import argparse

def main():
    parser=argparse.ArgumentParser(description='Export files containing pattern')
    parser.add_argument('pattern')
    parser.add_argument('out_dir')
    parser.add_argument('image_dir', default=os.path.expanduser('~/Bilder/%s' % (
        datetime.date.today().strftime('%Y'))))
    args=parser.parse_args()
    pattern=args.pattern.lower()
    if not os.path.exists(args.out_dir):
        print args.out_dir, 'does not exist'
        sys.exit(2)
    args.image_dir=args.image_dir.rstrip('/')
    outdir=os.path.join(args.out_dir, os.path.basename(args.image_dir))
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    for root, dirs, files in os.walk(args.image_dir):
        dirs.sort()
        for file in sorted(files):
            if not file.endswith('.txt'):
                continue
            file=os.path.join(root, file)
            found=False
            for line in open(file):
                if pattern in line.lower():
                    print
                    print 'copying %s: %s' % (root, line)
                    print
                    found=True
                    break
            if found:
                break
        if not found:
            continue
        for file in sorted(files):
            if file.endswith('.gthumpy'):
                continue
            file_abs=os.path.join(root, file)
            to_file=os.path.join(outdir, root[len(args.image_dir)+1:],
                                 file)
            print '%s --> %s' % (file_abs, to_file)
            to_dir=os.path.dirname(to_file)
            if not os.path.exists(to_dir):
                os.makedirs(to_dir)
            shutil.copyfile(file_abs, to_file)
            
if __name__=='__main__':
    main()
