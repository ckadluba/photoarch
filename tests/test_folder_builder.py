from pathlib import Path
import unittest
from photoarch.fileops import folder_builder
from photoarch.models import FolderInfo, FileInfo, Address
from datetime import datetime, timezone, timedelta

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
        # Time and captions differ
        last = FileInfo(path=Path('a.jpg'), date=datetime(2024,1,1,0,0), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None, caption="a dog playing in a sunny park")
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,1,1,5,0), lat=0.0, lon=0.0, keywords=["bar"], camera_model=None, address=None, caption="a car speeding on the highway at night")
        self.assertTrue(folder_builder.is_new_folder([last], current))

    def test_is_new_folder_location_and_keywords(self):
        # Location and captions differ - need larger distance to reach 0.6 threshold
        # GPS distance ~1569km (much larger than threshold) = 0.4 score, time 1h = ~0.13 score,
        # captions are different so keyword score adds enough to reach threshold
        last = FileInfo(path=Path('a.jpg'), date=datetime(2024,1,1,0,0), lat=0.0, lon=0.0, keywords=["foo"], camera_model=None, address=None, caption="a dog playing in a sunny park")
        current = FileInfo(path=Path('b.jpg'), date=datetime(2024,1,1,1,0), lat=10.0, lon=10.0, keywords=["bar"], camera_model=None, address=None, caption="a car speeding on the highway at night")
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

    def test_is_new_folder_real_world_scenario(self):
        # Real-world scenario with guinea pig photo and people photo
        # last_info: 2026-02-01T13:37:03, Neubau (1070), man and woman posing
        # current_info: 2026-02-01T14:04:58, Liesing (1230), guinea pigs in snow
        # Time difference: ~27.9 minutes, GPS: ~7.2km, Keywords: completely different
                
        last_info = FileInfo(
            path=Path("PXL_20260201_123703569.jpg"),
            date=datetime(2026, 2, 1, 13, 37, 3, 569000, tzinfo=timezone(timedelta(hours=1))),
            lat=48.201975000000004,
            lon=16.351605555555558,
            keywords=["man", "photo", "posing", "woman"],
            camera_model="Pixel 8",
            address=None,
            caption="a man and a woman posing for a photo on a city street"
        )

        current_info = FileInfo(
            path=Path("PXL_20260201_140458821.jpg"),
            date=datetime(2026, 2, 1, 14, 4, 58),
            lat=48.15419722222222,
            lon=16.307141666666666,
            keywords=["two", "guinea", "pigs", "laying", "snow", "front", "red", "shed"],
            camera_model=None,
            address=None,
            caption="two guinea pigs lying in the snow in front of a red shed"
        )
                
        # Should trigger new folder: different location (~7.2km) + different captions
        # Time: ~27.9 min (~0.06 score), GPS: ~7.2km (0.4 score), captions completely different (high keyword score)
        # Total score exceeds 0.6 threshold
        result = folder_builder.is_new_folder([last_info], current_info)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
