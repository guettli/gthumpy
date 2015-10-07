import shutil
import os
import tempfile
import unittest
from cached_property import cached_property

from gthumpy.GthumpyUtils import find_next_directory, JUMP_PREV, JUMP_NEXT, find_this_or_child_directory, \
    find_child_directory, NoMatchFound


class TestSimple(unittest.TestCase):

    @property
    def test_name(self):
        return self.id()

    @property
    def image_file_name(self):
        file_name=os.path.join(os.path.dirname(__file__), 'schlern-panorama.jpg')
        assert os.path.exists(file_name), file_name
        return file_name

    @cached_property
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp(prefix=self.test_name)
        dirs=[]
        for dir in ['01', '01-a', '01-b', '02']:
            new_dir=os.path.join(temp_dir, dir)
            dirs.append(new_dir)
            os.mkdir(new_dir)
            shutil.copy(self.image_file_name, os.path.join(new_dir, 'foo.jpg'))
        return temp_dir

    def find_and_return_basename(self, dir_name, jump=JUMP_NEXT):
        return os.path.basename(find_next_directory(os.path.join(self.temp_dir, dir_name), jump=jump))

    def test_find_next_directory(self):
        self.assertEqual('01-b', self.find_and_return_basename('02', jump=JUMP_PREV))
        self.assertEqual('01', os.path.basename(find_next_directory(self.temp_dir)))
        self.assertEqual('01-a', self.find_and_return_basename('01'))
        self.assertEqual('02', self.find_and_return_basename('01-b'))
        self.assertEqual('01-a', self.find_and_return_basename('01-b', jump=JUMP_PREV))

    def test_findthis_or_child_directory(self):
        self.assertEqual('01', os.path.basename(find_this_or_child_directory(self.temp_dir)))
        self.assertEqual('01', os.path.basename(find_this_or_child_directory(os.path.join(self.temp_dir, '01'))))

    def test_find_child_directory(self):
        self.assertEqual('01', os.path.basename(find_child_directory(self.temp_dir)))
        self.assertRaises(NoMatchFound, find_child_directory, os.path.join(self.temp_dir, '01'))
