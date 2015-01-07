#!/usr/bin/python

import sys
import pyexiv2

image=pyexiv2.Image(sys.argv[1])
image.readMetadata()
print image['Exif.Photo.DateTimeOriginal']
#for exif_key in image.exifKeys():
#    print exif_key, image[exif_key]
