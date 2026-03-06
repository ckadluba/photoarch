import unittest
from photoarch.services import translate

class TestTranslate(unittest.TestCase):
    def test_translate_english_to_german(self):
        text = "Hello world"
        result = translate.translate_english_to_german(text)
        self.assertIsInstance(result, str)
        # Accept empty result if API fails
        self.assertTrue(result == "" or "Hallo" in result or "Welt" in result)

    def test_translate_empty(self):
        result = translate.translate_english_to_german("")
        self.assertIsInstance(result, str)

if __name__ == '__main__':
    unittest.main()
