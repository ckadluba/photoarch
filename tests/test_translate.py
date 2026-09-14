import unittest
from unittest.mock import Mock, patch

from photoarch.services import translate


class TestTranslate(unittest.TestCase):
    @patch("photoarch.services.translate._requests_get")
    def test_translate_english_to_german(self, mock_get):
        text = "Hello world"
        mock_get.return_value = Mock(
            status_code=200,
            text='[[["Hallo Welt", "Hello world", null, true]], null, "en"]',
        )

        result = translate.translate_english_to_german(text)
        self.assertIsInstance(result, str)
        self.assertTrue("Hallo" in result or "Welt" in result)

    def test_translate_empty(self):
        result = translate.translate_english_to_german("")
        self.assertIsInstance(result, str)

    @patch("photoarch.services.translate._requests_get")
    def test_translate_failure_aborts_with_error(self, mock_get):
        mock_get.side_effect = RuntimeError("translation service unavailable")

        with self.assertLogs(translate.logger, level="ERROR") as logs:
            with self.assertRaises(translate.TranslationError):
                translate.translate_english_to_german("Hello world")

        self.assertIn("Translation failed", logs.output[0])

    @patch("photoarch.services.translate._requests_get")
    def test_translate_retries_302_with_location_header(self, mock_get):
        redirect_response = Mock(
            status_code=302, headers={"Location": "https://example.com/translated"}
        )
        translated_response = Mock(
            status_code=200, text='<div class="t0">Hallo Welt</div>'
        )
        mock_get.side_effect = [redirect_response, translated_response]

        with self.assertLogs(translate.logger, level="WARNING") as logs:
            result = translate.translate_english_to_german("Hello world")

        self.assertEqual(result, "Hallo Welt")
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(mock_get.call_args.args[0], "https://example.com/translated")
        self.assertIn("HTTP 302", logs.output[0])

    @patch("photoarch.services.translate.time.sleep")
    @patch("photoarch.services.translate._requests_get")
    def test_translate_retries_429_after_retry_after(self, mock_get, mock_sleep):
        rate_limited_response = Mock(status_code=429, headers={"Retry-After": "2"})
        translated_response = Mock(
            status_code=200, text='<div class="t0">Hallo Welt</div>'
        )
        mock_get.side_effect = [rate_limited_response, translated_response]

        with self.assertLogs(translate.logger, level="WARNING") as logs:
            result = translate.translate_english_to_german("Hello world")

        self.assertEqual(result, "Hallo Welt")
        mock_sleep.assert_called_once_with(2.0)
        self.assertEqual(mock_get.call_count, 2)
        self.assertIn("HTTP 429", logs.output[0])
        self.assertIn("Retry-After: 2", logs.output[0])


if __name__ == "__main__":
    unittest.main()
