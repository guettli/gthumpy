import os

import sys
import random

files=[]
for file in sys.stdin:
    file=file.strip()
    files.append(file)

while True:
    file=random.choose(files)


 
