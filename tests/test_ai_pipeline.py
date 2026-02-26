import unittest
from unittest.mock import MagicMock, patch
from photoarch.analysis.ai_pipeline import build_caption_pipeline, get_keywords_from_caption


class TestGetKeywordsFromCaption(unittest.TestCase):
    def test_basic_keywords(self):
        result = get_keywords_from_caption("a cat sitting on the mat", set())
        self.assertIn("cat", result)
        self.assertIn("sitting", result)
        self.assertIn("mat", result)

    def test_stopwords_removed(self):
        result = get_keywords_from_caption("a cat sitting on the mat", {"a", "on", "the"})
        self.assertNotIn("a", result)
        self.assertNotIn("on", result)
        self.assertNotIn("the", result)
        self.assertIn("cat", result)

    def test_unique_and_sorted(self):
        result = get_keywords_from_caption("cat dog cat bird", set())
        self.assertEqual(result, sorted(set(result), key=str.lower))
        self.assertEqual(len(result), len(set(result)))

    def test_empty_caption(self):
        result = get_keywords_from_caption("", set())
        self.assertEqual(result, [])

    def test_forbidden_chars_removed(self):
        result = get_keywords_from_caption("cat: dog, bird.", set())
        for kw in result:
            self.assertNotIn(":", kw)
            self.assertNotIn(",", kw)
            self.assertNotIn(".", kw)


class TestBuildCaptionPipeline(unittest.TestCase):
    def _make_pipeline(self, caption_en="a cat on a mat", caption_de="eine Katze auf einer Matte"):
        mock_captioner = MagicMock()
        mock_captioner.get_caption_for_image_file.return_value = caption_en

        with patch("photoarch.analysis.ai_pipeline.translate_english_to_german", return_value=caption_de):
            pipeline = build_caption_pipeline(mock_captioner)
            result = pipeline.invoke({
                "image_path": "test.jpg",
                "caption_en": "",
                "caption_de": "",
                "keywords_en": [],
                "keywords_de": [],
            })
        return result, mock_captioner

    def test_pipeline_returns_caption_en(self):
        result, _ = self._make_pipeline()
        self.assertEqual(result["caption_en"], "a cat on a mat")

    def test_pipeline_returns_caption_de(self):
        result, _ = self._make_pipeline()
        self.assertEqual(result["caption_de"], "eine Katze auf einer Matte")

    def test_pipeline_returns_keywords_en(self):
        result, _ = self._make_pipeline()
        self.assertIsInstance(result["keywords_en"], list)
        self.assertTrue(len(result["keywords_en"]) > 0)

    def test_pipeline_returns_keywords_de(self):
        result, _ = self._make_pipeline()
        self.assertIsInstance(result["keywords_de"], list)
        self.assertTrue(len(result["keywords_de"]) > 0)

    def test_pipeline_calls_captioner_with_image_path(self):
        _, mock_captioner = self._make_pipeline()
        mock_captioner.get_caption_for_image_file.assert_called_once_with("test.jpg")

    def test_pipeline_handles_empty_captions(self):
        result, _ = self._make_pipeline(caption_en="", caption_de="")
        self.assertEqual(result["caption_en"], "")
        self.assertEqual(result["caption_de"], "")
        self.assertEqual(result["keywords_en"], [])
        self.assertEqual(result["keywords_de"], [])


if __name__ == "__main__":
    unittest.main()
