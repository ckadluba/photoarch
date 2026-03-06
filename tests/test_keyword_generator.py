import unittest
from photoarch.language.keyword_generator import get_keywords_from_caption
from photoarch.config import STOPWORDS, STOPWORDS_GERMAN


class TestKeywordGenerator(unittest.TestCase):
    
    def test_basic_english_caption(self):
        """Test basic keyword extraction from English caption"""
        caption = "a dog playing in the park"
        result = get_keywords_from_caption(caption, STOPWORDS)
        self.assertEqual(result, ["dog", "playing", "park"])
    
    def test_basic_german_caption(self):
        """Test basic keyword extraction from German caption"""
        caption = "ein Hund spielt im Park"
        result = get_keywords_from_caption(caption, STOPWORDS_GERMAN)
        self.assertEqual(result, ["Hund", "spielt", "Park"])
    
    def test_empty_caption(self):
        """Test with empty caption"""
        result = get_keywords_from_caption("", STOPWORDS)
        self.assertEqual(result, [])
    
    def test_only_stopwords_english(self):
        """Test caption containing only English stopwords"""
        caption = "a the and of in"
        result = get_keywords_from_caption(caption, STOPWORDS)
        self.assertEqual(result, [])
    
    def test_only_stopwords_german(self):
        """Test caption containing only German stopwords"""
        caption = "ein die und von in"
        result = get_keywords_from_caption(caption, STOPWORDS_GERMAN)
        self.assertEqual(result, [])
    
    def test_mixed_case_english(self):
        """Test that case is preserved in output but stopwords are case-insensitive"""
        caption = "A Beautiful Dog playing"
        result = get_keywords_from_caption(caption, STOPWORDS)
        self.assertEqual(result, ["Beautiful", "Dog", "playing"])
    
    def test_mixed_case_german(self):
        """Test that case is preserved in German output"""
        caption = "Ein Schöner Hund spielt"
        result = get_keywords_from_caption(caption, STOPWORDS_GERMAN)
        self.assertEqual(result, ["Schöner", "Hund", "spielt"])
    
    def test_duplicate_removal_english(self):
        """Test that duplicate keywords are removed while preserving order"""
        caption = "dog cat dog bird cat dog"
        result = get_keywords_from_caption(caption, STOPWORDS)
        self.assertEqual(result, ["dog", "cat", "bird"])
    
    def test_duplicate_removal_german(self):
        """Test that duplicate German keywords are removed"""
        caption = "Hund Katze Hund Vogel Katze Hund"
        result = get_keywords_from_caption(caption, STOPWORDS_GERMAN)
        self.assertEqual(result, ["Hund", "Katze", "Vogel"])
    
    def test_order_preservation(self):
        """Test that keyword order is preserved (not sorted)"""
        caption = "zebra apple mountain car"
        result = get_keywords_from_caption(caption, STOPWORDS)
        self.assertEqual(result, ["zebra", "apple", "mountain", "car"])
    
    def test_complex_english_caption(self):
        """Test complex English sentence with multiple stopwords"""
        caption = "a bottle of beer is sitting on a table next to a sandwich"
        result = get_keywords_from_caption(caption, STOPWORDS)
        self.assertEqual(result, ["bottle", "beer", "sitting", "table", "next", "sandwich"])
    
    def test_complex_german_caption(self):
        """Test complex German sentence with multiple stopwords"""
        caption = "Auf einem Tisch steht eine Flasche Bier neben einem Sandwich"
        result = get_keywords_from_caption(caption, STOPWORDS_GERMAN)
        self.assertEqual(result, ["Tisch", "steht", "Flasche", "Bier", "neben", "Sandwich"])
    
    def test_single_word_keyword(self):
        """Test caption with single keyword"""
        caption = "mountain"
        result = get_keywords_from_caption(caption, STOPWORDS)
        self.assertEqual(result, ["mountain"])
    
    def test_no_stopwords_in_caption(self):
        """Test caption without any stopwords"""
        caption = "elephant giraffe zebra"
        result = get_keywords_from_caption(caption, STOPWORDS)
        self.assertEqual(result, ["elephant", "giraffe", "zebra"])
    
    def test_punctuation_attached_to_words(self):
        """Test that punctuation attached to words is preserved"""
        caption = "dog, cat. bird!"
        result = get_keywords_from_caption(caption, STOPWORDS)
        # Note: split() will preserve punctuation attached to words
        self.assertEqual(result, ["dog,", "cat.", "bird!"])
    
    def test_multiple_spaces(self):
        """Test caption with multiple spaces between words"""
        caption = "dog  cat   bird"
        result = get_keywords_from_caption(caption, STOPWORDS)
        # split() without arguments handles multiple spaces
        self.assertEqual(result, ["dog", "cat", "bird"])


if __name__ == '__main__':
    unittest.main()