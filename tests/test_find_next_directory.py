import shutil
import os
import tempfile
import unittest

from gthumpy.GthumpyUtils import find_next, JUMP_PREV


class TestSimple(unittest.TestCase):

    @property
    def test_name(self):
        return self.id()

    @property
    def image_file_name(self):
        file_name=os.path.join(os.path.dirname(__file__), 'schlern-panorama.jpg')
        assert os.path.exists(file_name), file_name
        return file_name

    def test_find_next_directory(self):

        temp_dir=tempfile.mkdtemp(prefix=self.test_name)
        dirs=[]
        for dir in ['01-a', '01-b', '02']:
            new_dir=os.path.join(temp_dir, dir)
            dirs.append(new_dir)
            os.mkdir(new_dir)
            shutil.copy(self.image_file_name, os.path.join(new_dir, 'foo.jpg'))

        self.assertEqual('01-b', os.path.basename(find_next(dirs[0])))
        self.assertEqual('02', os.path.basename(find_next(dirs[1])))
        self.assertEqual('01-b', os.path.basename(find_next(dirs[-1], jump=JUMP_PREV)))
        self.assertEqual('01-a', os.path.basename(find_next(dirs[-2], jump=JUMP_PREV)))
