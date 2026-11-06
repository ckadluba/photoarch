import unittest
from pathlib import Path

from photoarch.analysis import exif_reader


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
        exif_data_original = "Date/Time Original              : 2024:01:01 12:34:56.000+02:00"
        dt_original = exif_reader.get_date_from_exif_data(exif_data_original)
        self.assertIsNotNone(dt_original)

    def test_get_date_from_exif_data_original_without_timezone(self):
        exif_data_original_no_tz = "Date/Time Original              : 2024:01:01 12:34:56"
        dt_original_no_tz = exif_reader.get_date_from_exif_data(exif_data_original_no_tz)
        self.assertIsNotNone(dt_original_no_tz)

    def test_get_date_from_exif_data_create(self):
        exif_data_create = "Create Date                     : 2025:03:03 16:51:59"
        dt_create = exif_reader.get_date_from_exif_data(exif_data_create)
        self.assertIsNotNone(dt_create)

    def test_get_date_from_exif_data_modify(self):
        exif_data_modify = "File Modification Date/Time     : 2024:01:01 12:34:56+02:00"
        dt_modify = exif_reader.get_date_from_exif_data(exif_data_modify)
        self.assertIsNotNone(dt_modify)

    def test_get_date_from_exif_data_invalid(self):
        exif_data_invalid = "No valid date here"
        dt_invalid = exif_reader.get_date_from_exif_data(exif_data_invalid)
        self.assertIsNone(dt_invalid)

    def test_get_date_from_exif_data_ignores_placeholder_original_date(self):
        exif_data = (
            "Date/Time Original              : 0000:00:00 00:00:00\n"
            "Create Date                     : 2025:03:03 16:51:59"
        )
        dt = exif_reader.get_date_from_exif_data(exif_data)
        self.assertIsNotNone(dt)
        self.assertEqual(
            (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second),
            (2025, 3, 3, 16, 51, 59),
        )

    def test_get_date_from_exif_data_returns_none_for_only_invalid_dates(self):
        exif_data = (
            "Date/Time Original              : 0000:00:00 00:00:00\n"
            "Create Date                     : 0000:00:00 00:00:00\n"
            "File Modification Date/Time     : 0000:00:00 00:00:00+00:00"
        )
        self.assertIsNone(exif_reader.get_date_from_exif_data(exif_data))

if __name__ == '__main__':
    unittest.main()
