import unittest
from unittest.mock import Mock, patch

import torch

from photoarch.services import translate


class TestTranslate(unittest.TestCase):
    @patch("photoarch.services.translate._load_translator")
    def test_translate_english_to_german(self, mock_load):
        tokenizer, model = Mock(), Mock()
        mock_load.return_value = tokenizer, model
        inputs = {"input_ids": torch.tensor([[1, 2, 3]])}
        tokenizer.return_value = inputs
        model.config.max_position_embeddings = 512
        model.generate.return_value = [[4, 5, 0]]
        tokenizer.decode.return_value = " Hallo Welt "

        self.assertEqual(
            translate.translate_english_to_german("Hello world"), "Hallo Welt"
        )
        tokenizer.assert_called_once_with(
            "Hello world", return_tensors="pt", truncation=False
        )
        model.generate.assert_called_once_with(**inputs, max_new_tokens=512)
        tokenizer.decode.assert_called_once_with([4, 5, 0], skip_special_tokens=True)

    @patch("photoarch.services.translate._load_translator")
    def test_translate_empty_does_not_load_model(self, mock_load):
        for text in ("", "  \n"):
            self.assertEqual(translate.translate_english_to_german(text), "")
        mock_load.assert_not_called()

    @patch("photoarch.services.translate._load_translator")
    def test_translate_failure_preserves_cause(self, mock_load):
        error = RuntimeError("model unavailable")
        mock_load.side_effect = error
        with (
            self.assertLogs(translate.logger, level="ERROR"),
            self.assertRaises(translate.TranslationError) as caught,
        ):
            translate.translate_english_to_german("Hello world")
        self.assertIs(caught.exception.__cause__, error)

    @patch("photoarch.services.translate._load_translator")
    def test_empty_output_and_generation_failure_raise_translation_error(
        self, mock_load
    ):
        tokenizer, model = Mock(), Mock()
        mock_load.return_value = tokenizer, model
        tokenizer.return_value = {"input_ids": torch.tensor([[1]])}
        model.config.max_position_embeddings = 512
        model.generate.return_value = [[0]]
        tokenizer.decode.return_value = "  "
        with self.assertRaises(translate.TranslationError):
            translate.translate_english_to_german("Hello")
        model.generate.side_effect = RuntimeError("inference failed")
        with self.assertRaises(translate.TranslationError):
            translate.translate_english_to_german("Hello")

    @patch("photoarch.services.translate._load_translator")
    def test_long_input_is_not_silently_truncated(self, mock_load):
        tokenizer, model = Mock(), Mock()
        mock_load.return_value = tokenizer, model
        tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        model.config.max_position_embeddings = 2
        with self.assertRaises(translate.TranslationError):
            translate.translate_english_to_german("Long caption")
        model.generate.assert_not_called()

    @patch("photoarch.services.translate.MarianMTModel.from_pretrained")
    @patch("photoarch.services.translate.MarianTokenizer.from_pretrained")
    def test_model_is_loaded_once_and_uses_disk_cache(self, mock_tokenizer, mock_model):
        translate._load_translator.cache_clear()
        self.addCleanup(translate._load_translator.cache_clear)
        first = translate._load_translator()
        self.assertIs(translate._load_translator(), first)
        for loader in (mock_tokenizer, mock_model):
            loader.assert_called_once_with(
                "Helsinki-NLP/opus-mt-en-de", cache_dir=translate.MODEL_CACHE_DIR
            )
        mock_model.return_value.eval.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
