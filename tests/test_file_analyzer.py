import unittest
import pytest
from pathlib import Path

from photoarch.analysis import file_analyzer
from photoarch.analysis.ai_captioning_blip2 import Blip2CaptionGenerator
from photoarch.ai_models_context import AiModelsContext


class TestFileAnalyzer(unittest.TestCase):
    def test_analyze_file_with_cache(self):
        # Arrange
        file_analyzer.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = file_analyzer.CACHE_DIR / "dummy.json"
        cache_file.write_text('{"path": "dummy.jpg", "date": null, "lat": null, "lon": null, "keywords": [], "cameraModel": "Test Camera Model", "address": null}')
        file_path = Path("dummy.jpg")

        # Act
        info = file_analyzer.analyze_file(file_path)

        # Assert
        self.assertEqual(info.path.name, "dummy.jpg")
        self.assertEqual(info.camera_model, "Test Camera Model")
        cache_file.unlink()

    @pytest.mark.longrunning
    def test_analyze_file_real_image(self):
        # Arrange
        test_image = Path("tests/data/input/PXL_20250708_095842343.jpg")
        context = AiModelsContext(captioner=Blip2CaptionGenerator(device="cpu"))

        # Act
        info = file_analyzer.analyze_file(test_image, context)

        # Assert
        self.assertEqual(info.path.name, test_image.name)
        self.assertEqual(info.date.year, 2025)
        self.assertEqual(info.date.month, 7)
        self.assertEqual(info.date.day, 8)
        self.assertEqual(info.date.hour, 11)
        self.assertEqual(info.date.minute, 58)
        self.assertEqual(info.date.second, 42)
        self.assertEqual(info.date.microsecond, 343000)
        self.assertEqual(info.camera_model, "Pixel 8")
        self.assertEqual(info.lat, 48.170674999999996)
        self.assertEqual(info.lon, 16.333144444444443)
        self.assertEqual(info.address.name, "Allianz Wien")
        self.assertEqual(info.address.postcode, "1120")
        self.assertEqual(info.keywords[0], "bottle")
        self.assertEqual(info.keywords[1], "beer")
        self.assertEqual(info.keywords[2], "sitting")
        self.assertEqual(info.keywords[3], "table")
        self.assertEqual(info.keywords[4], "next")
        self.assertEqual(info.keywords[5], "sandwich")
        self.assertEqual(info.keywords_german[0], "Tisch")
        self.assertEqual(info.keywords_german[1], "steht")
        self.assertEqual(info.keywords_german[2], "Flasche")
        self.assertEqual(info.keywords_german[3], "Bier")
        self.assertEqual(info.keywords_german[4], "neben")
        self.assertEqual(info.keywords_german[5], "Sandwich")
        self.assertEqual(info.caption, "a bottle of beer is sitting on a table next to a sandwich")
        self.assertEqual(info.caption_german, "Auf einem Tisch steht eine Flasche Bier neben einem Sandwich")

if __name__ == '__main__':
    unittest.main()
