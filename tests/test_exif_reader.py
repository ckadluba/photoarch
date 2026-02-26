import unittest
from photoarch.analysis import exif_reader
from pathlib import Path
import os

class TestExifReader(unittest.TestCase):
    def test_ensure_exiftool_available(self):
        try:
            exif_reader.ensure_exiftool_available()
        except RuntimeError:
            self.skipTest("ExifTool not available.")

    def test_get_exif_data_from_file(self):
        test_image = Path("tests/data/input/PXL_20250708_095842343.jpg")
        if not test_image.exists():
            self.skipTest("Test image not found.")
        try:
            exif_data = exif_reader.get_exif_data_from_file(test_image)
            self.assertIsInstance(exif_data, str)
        except RuntimeError:
            self.skipTest("ExifTool not available.")

    def test_get_date_from_exif_data_original(self):
        exif_data = "Date/Time Original : 2024:01:01 12:34:56.000+02:00"
        dt = exif_reader.get_date_from_exif_data(exif_data)
        self.assertIsNotNone(dt)

    def test_get_date_from_exif_data_original_without_timezone(self):
        exif_data_original = "Date/Time Original : 2024:01:01 12:34:56"
        dt_original = exif_reader.get_date_from_exif_data(exif_data_original)
        self.assertIsNotNone(dt_original)

    def test_get_date_from_exif_data_modify(self):
        exif_data_modify = "File Modification Date/Time : 2024:01:01 12:34:56+02:00"
        dt_modify = exif_reader.get_date_from_exif_data(exif_data_modify)
        self.assertIsNotNone(dt_modify)

    def test_get_date_from_exif_data_invalid(self):
        exif_data_invalid = "No valid date here"
        dt_invalid = exif_reader.get_date_from_exif_data(exif_data_invalid)
        self.assertIsNone(dt_invalid)

if __name__ == '__main__':
    unittest.main()
