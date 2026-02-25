from pathlib import Path
import unittest
from photoarch.fileops import folder_builder
from photoarch.models import FolderInfo, FileInfo
from datetime import datetime

class TestFolderBuilder(unittest.TestCase):
    def test_create_folder_info(self):
        folder_infos = []
        start_date = datetime(2024, 1, 1)
        folder_builder.create_folder_info(folder_infos, start_date)
        self.assertEqual(len(folder_infos), 1)
        self.assertEqual(folder_infos[0].start_date, start_date)

    def test_is_new_folder_no_previous(self):
        file_infos = []
        current_info = FileInfo(path=Path('test.jpg'), date=datetime(2024,1,1), lat=None, lon=None, keywords=[], camera_model=None, address=None)
        self.assertTrue(folder_builder.is_new_folder(file_infos, current_info))

    def test_is_new_folder_month_change(self):
        last = FileInfo(path=Path('a.jpg'), date=datetime(2024,1,1), lat=1.0, lon=1.0, keywords=["foo"], camera_model=None, address=None)
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,2,1), lat=1.0, lon=1.0, keywords=["foo"], camera_model=None, address=None)
        self.assertTrue(folder_builder.is_new_folder([last], current))

    def test_is_new_folder_year_change(self):
        last = FileInfo(path=Path('a.jpg'), date=datetime(2023,12,31), lat=1.0, lon=1.0, keywords=["foo"], camera_model=None, address=None)
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,1,1), lat=1.0, lon=1.0, keywords=["foo"], camera_model=None, address=None)
        self.assertTrue(folder_builder.is_new_folder([last], current))

    def test_is_new_folder_time_and_location(self):
        # Both time and location differ enough
        last = FileInfo(path=Path('a.jpg'), date=datetime(2024,1,1,0,0), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None)
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,1,1,5,0), lat=10.0, lon=10.0, keywords=["foo"], camera_model=None, address=None)
        self.assertTrue(folder_builder.is_new_folder([last], current))

    def test_is_new_folder_time_and_keywords(self):
        # Time and keywords differ
        last = FileInfo(path=Path('a.jpg'), date=datetime(2024,1,1,0,0), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None)
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,1,1,5,0), lat=0.0, lon=0.0, keywords=["bar"], camera_model=None, address=None)
        self.assertTrue(folder_builder.is_new_folder([last], current))

    def test_is_new_folder_location_and_keywords(self):
        # Location and keywords differ
        last = FileInfo(path=Path('a.jpg'), date=datetime(2024,1,1,0,0), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None)
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,1,1,0,1), lat=10.0, lon=10.0, keywords=["bar"], camera_model=None, address=None)
        self.assertTrue(folder_builder.is_new_folder([last], current))

    def test_is_new_folder_only_time_differs(self):
        # Only time differs (should be False)
        last = FileInfo(path=Path('a.jpg'), date=datetime(2024,1,1,0,0), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None)
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,1,1,5,0), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None)
        self.assertFalse(folder_builder.is_new_folder([last], current))

    def test_is_new_folder_only_location_differs(self):
        # Only location differs (should be False)
        last = FileInfo(path=Path('a.jpg'), date=datetime(2024,1,1,0,0), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None)
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,1,1,0,1), lat=10.0, lon=10.0, keywords=["foo"], camera_model=None, address=None)
        self.assertFalse(folder_builder.is_new_folder([last], current))

    def test_is_new_folder_only_keywords_differ(self):
        # Only keywords differ (should be False)
        last = FileInfo(path=Path('a.jpg'), date=datetime(2024,1,1,0,0), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None)
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,1,1,0,1), lat=0.0, lon=0.0, keywords=["bar"], camera_model=None, address=None)
        self.assertFalse(folder_builder.is_new_folder([last], current))

    def test_is_new_folder_keywords_video_exception(self):
        # If either keywords is only generic video, keywords should not count as different
        from photoarch.config import KEYWORD_GENERIC_VIDEO
        last = FileInfo(path=Path('a.mp4'), date=datetime(2024,1,1,0,0), lat=0.0, lon=0.0, keywords=[KEYWORD_GENERIC_VIDEO], camera_model=None, address=None)
        current = FileInfo(path=Path('b.mp4'), date=datetime(2024,1,1,0,1), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None)
        self.assertFalse(folder_builder.is_new_folder([last], current))

if __name__ == '__main__':
    unittest.main()
