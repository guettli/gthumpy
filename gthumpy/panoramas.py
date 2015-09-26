#!/usr/bin/env python
import glob
import sys
import itertools
import subprocess

import os
import Utils

MAX_SIZE = 3000

import argparse

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--all-dirs-in-this-dir', action='store_true', default=False)
    parser.add_argument('directories', nargs='+')
    args=parser.parse_args()
    if not args.all_dirs_in_this_dir:
        # ~/panoramas/2015--foo/
        do_panoramas_in_dirs(args.directories)
    else:
        # ~/panoramas
        for upper_dir in args.directories:
            do_panoramas_in_dirs([os.path.abspath(
                os.path.join(upper_dir, dir)) for dir in sorted(os.listdir(upper_dir))])

def do_panoramas_in_dirs(directories):
    for directory in directories:
        panorama = Panorama.create_panorama_object_or_none(directory)
        if not panorama:
            continue
        panorama.create_panorama_jpg_from_source_files()

def is_target_out_of_date(target_file_name, source_file_names):
    '''
    Makefile like: return True if target is out of date.
    If one source file is newer, return True.
    '''
    if not os.path.exists(target_file_name):
        return True
    return max([os.path.getmtime(source) for source in source_file_names])>os.path.getmtime(target_file_name)

def create_panoramas_in_directory(panorama_dir):
    if not os.path.isdir(panorama_dir):
        print 'Does not exist: %s' % panorama_dir
        sys.exit(3)
    for fn in sorted(os.listdir(panorama_dir)):
        fn_abs = os.path.join(panorama_dir, fn)
        panorama = Panorama.create_panorama_object_or_none(fn_abs)
        if not panorama:
            continue
        panorama.create_panorama_jpg_from_source_files()


class Panorama(object):
    def __init__(self, directory):
        self.directory = os.path.abspath(directory)

    @property
    def base_name(self):
        return os.path.basename(self.directory)

    @property
    def tif(self):
        return os.path.join(self.directory, '%s.tif' % self.base_name)

    @property
    def panorama_jpg(self):
        return os.path.join(self.source_dir, '%s.jpg' % self.base_name)

    @property
    def source_dir(self):
        return open(self.source_dir_file).read().strip()

    @property
    def source_dir_file(self):
        return os.path.join(self.directory, 'source-dir.txt')

    @property
    def pto(self):
        return os.path.join(self.directory, '%s.pto' % self.base_name)

    @property
    def source_files(self):
        return sorted([file for file in os.listdir(self.directory) if file.lower().endswith('.jpg')])

    def pto_file_crop_was_done(self):
        '''
        pto_gen creates a pto file. But only if last step (pano_modify --crop) was
        successfull, the pto file is complete.
        Check for
        pre-crop : p f0 w1307 h1142 v95  E0.0352164 R0 n"TIFF_m c:LZW r:CROP"
        post-crop: p f0 w1867 h1631 v95  E0.0632719 R0 S125,1744,83,1179 n"TIFF_m c:LZW r:CROP"
        '''
        for line in open(self.pto):
            if not line.startswith('p '):
                continue
            for item in line.split():
                if item.startswith('S'):
                    return True
        return False

    def create_pto(self):
        if not is_target_out_of_date(self.pto, self.source_files):
            if self.pto_file_crop_was_done():
                return
        for cmd in [
            ['pto_gen', '-o', self.pto] + self.source_files,
            ('cpfind', '-o', self.pto, '--multirow', '--celeste', self.pto),
            ('cpclean', '-o', self.pto, self.pto),
            ('linefind', '-o', self.pto, self.pto),
            ('autooptimiser', '-a', '-m', '-l', '-s', '-o', self.pto, self.pto),
            ('pano_modify', '--canvas=AUTO', '--crop=AUTO', '-o', self.pto, self.pto),
            ]:
            subprocess.check_call(cmd)

    def create_tif(self):
        if not is_target_out_of_date(self.tif, itertools.chain(self.source_files, [self.pto])):
            return
        for cmd in [
            ('PTBatcher', '-a', self.pto, '-o', self.tif),
            ('PTBatcher', '-b'),
            ('notify-send', 'Created panorama %s' % self.base_name),
        ]:
            subprocess.call(cmd)

    def create_panorama_jpg_from_source_files(self):
        os.chdir(self.directory)

        self.create_pto()

        self.create_tif()

        self.create_panorama_jpg()

    def create_panorama_jpg(self):
        if not os.path.exists(self.source_dir_file):
            print 'Not source-dir found', self.source_dir_file
            return
        if not is_target_out_of_date(self.panorama_jpg,
                                     itertools.chain(self.source_files, [self.pto, self.tif])):
            print 'target not out of date. Skipping', self.panorama_jpg
            return
        if not os.path.exists(self.tif):
            print '%s does not exist. Can not create panorama_jpg' % self.tif
            return
        pb = Utils.scale2pixbuf(MAX_SIZE, MAX_SIZE, self.tif)
        pb.save(self.panorama_jpg, 'jpeg')
        print 'created', self.panorama_jpg

    @classmethod
    def create_panorama_object_or_none(cls, directory):
        if not os.path.isdir(directory):
            print 'directory %s does not exist' % directory
            return
        return cls(directory)
