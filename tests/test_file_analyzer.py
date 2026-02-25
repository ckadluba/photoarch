import unittest
from photoarch.analysis import file_analyzer
from pathlib import Path
import os

class TestFileAnalyzer(unittest.TestCase):
    def test_analyze_file_with_cache(self):
        # Create a dummy cache file
        cache_file = file_analyzer.CACHE_DIR / "dummy.json"
        cache_file.write_text('{"path": "dummy.jpg", "date": null, "gps": null, "keywords": [], "camera": null, "address": null}')
        file_path = Path("dummy.jpg")
        info = file_analyzer.analyze_file(file_path)
        self.assertEqual(info.path.name, "dummy.jpg")
        cache_file.unlink()

    def test_analyze_file_real_image(self):
        test_image = Path("tests/data/input/PXL_20250708_095842343.jpg")
        if not test_image.exists():
            self.skipTest("Test image not found.")
        info = file_analyzer.analyze_file(test_image)
        self.assertEqual(info.path.name, test_image.name)

if __name__ == '__main__':
    unittest.main()
