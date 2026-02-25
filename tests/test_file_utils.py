import unittest
from pathlib import Path
from photoarch.fileops import file_utils
import tempfile
import os

class TestFileUtils(unittest.TestCase):
    def test_get_file_modified_datetime(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        dt = file_utils.get_file_modified_datetime(tmp_path)
        self.assertIsNotNone(dt)
        os.unlink(tmp_path)

    def test_does_filename_meet_criteria_image(self):
        path = Path('test.jpg')
        self.assertTrue(file_utils.does_filename_meet_criteria(path))

    def test_does_filename_meet_criteria_video(self):
        path = Path('test.mp4')
        self.assertTrue(file_utils.does_filename_meet_criteria(path))

    def test_does_filename_meet_criteria_invalid(self):
        path = Path('test.txt')
        self.assertFalse(file_utils.does_filename_meet_criteria(path))

if __name__ == '__main__':
    unittest.main()
