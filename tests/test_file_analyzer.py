import unittest
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from photoarch.analysis import file_analyzer
from photoarch.cache import get_analysis_cache_file
from photoarch.analysis.ai_captioning_blip2 import Blip2CaptionGenerator
from photoarch.ai_models_context import AiModelsContext
from photoarch.services.translate import TranslationError
from tests.support import reject_live_geocoding, seed_osm_cache


class TestFileAnalyzer(unittest.TestCase):
    def test_analyze_file_aborts_when_translation_is_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "photo.jpg"
            file_path.write_bytes(b"")
            cache_dir = Path(temp_dir) / "cache"
            context = AiModelsContext(captioner=Mock())
            context.captioner.get_caption_for_image_file.return_value = "a caption"

            with (
                patch.object(file_analyzer, "does_filename_meet_criteria", return_value=True),
                patch.object(file_analyzer, "get_exif_data_from_file", return_value=None),
                patch.object(file_analyzer, "translate_english_to_german", return_value=""),
                patch.object(file_analyzer, "get_keywords_from_caption", return_value=[]),
            ):
                with self.assertLogs(file_analyzer.logger, level="ERROR") as logs:
                    with self.assertRaises(TranslationError):
                        file_analyzer.analyze_file(
                            file_path, context, cache_dir=cache_dir
                        )

            self.assertIn("Translation failed for photo.jpg", logs.output[0])
            self.assertFalse(
                get_analysis_cache_file(cache_dir, file_path, "blip-2").exists()
            )

    def test_analyze_file_with_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            cache_dir = Path(temp_dir) / "cache"
            file_path = Path(temp_dir) / "dummy.jpg"
            cache_file = get_analysis_cache_file(cache_dir, file_path, "blip-2")
            cache_file.parent.mkdir(parents=True)
            cache_file.write_text('{"path": "dummy.jpg", "date": null, "lat": null, "lon": null, "keywords": [], "cameraModel": "Test Camera Model", "address": null}')

            # Act
            info = file_analyzer.analyze_file(file_path, cache_dir=cache_dir)

            # Assert
            self.assertEqual(info.path.name, "dummy.jpg")
            self.assertEqual(info.camera_model, "Test Camera Model")

    @pytest.mark.longrunning
    def test_analyze_file_real_image(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            test_image = Path("tests/data/input/PXL_20250708_095842343.jpg")
            context = AiModelsContext(captioner=Blip2CaptionGenerator(device="cpu"))
            cache_dir = Path(temp_dir) / "cache"
            seed_osm_cache(cache_dir)

            # Act
            with (
                reject_live_geocoding(),
                patch(
                    "photoarch.analysis.file_analyzer.translate_english_to_german",
                    return_value="Auf einem Tisch steht eine Flasche Bier neben einem Sandwich",
                ),
            ):
                info = file_analyzer.analyze_file(test_image, context, cache_dir=cache_dir)

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
