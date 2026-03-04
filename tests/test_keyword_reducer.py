import unittest
from photoarch.fileops.keyword_reducer import select_top_words


class TestKeywordReducer(unittest.TestCase):
    
    def test_basic_functionality(self):
        """Test basic keyword selection with duplicates"""
        keywords = ["Auto", "Haus", "Auto", "Baum", "Haus", "Auto"]
        result = select_top_words(keywords, top_n=3)
        self.assertEqual(len(result), 3)
        self.assertIn("Auto", result)
        self.assertIn("Haus", result)
        self.assertIn("Baum", result)
    
    def test_frequency_ordering(self):
        """Test that keywords are ordered by frequency"""
        keywords = ["Apple", "Apple", "Apple", "Banana", "Banana", "Cherry"]
        result = select_top_words(keywords, top_n=3)
        # Apple should appear first (3 occurrences), then Banana (2), then Cherry (1)
        self.assertEqual(result[0], "Apple")
        self.assertEqual(result[1], "Banana")
        self.assertEqual(result[2], "Cherry")
    
    def test_case_insensitive_deduplication(self):
        """Test that case-insensitive deduplication works"""
        keywords = ["auto", "Auto", "AUTO", "Haus", "haus"]
        result = select_top_words(keywords, top_n=2)
        self.assertEqual(len(result), 2)
        # Should contain one variant of "auto" and one variant of "haus"
        self.assertTrue(any(w.lower() == "auto" for w in result))
        self.assertTrue(any(w.lower() == "haus" for w in result))
    
    def test_preserves_most_common_capitalization(self):
        """Test that the most common capitalization variant is preserved"""
        keywords = ["auto", "Auto", "Auto", "AUTO"]
        result = select_top_words(keywords, top_n=1)
        # "Auto" appears twice, should be the chosen variant
        self.assertEqual(result[0], "Auto")
    
    def test_top_n_limit(self):
        """Test that only top_n keywords are returned"""
        keywords = ["A", "B", "C", "D", "E", "F", "G", "H"]
        result = select_top_words(keywords, top_n=3)
        self.assertEqual(len(result), 3)
    
    def test_fewer_than_top_n(self):
        """Test behavior when input has fewer than top_n unique keywords"""
        keywords = ["Auto", "Haus"]
        result = select_top_words(keywords, top_n=5)
        self.assertEqual(len(result), 2)
    
    def test_empty_list(self):
        """Test with empty input list"""
        keywords = []
        result = select_top_words(keywords, top_n=5)
        self.assertEqual(result, [])
    
    def test_mixed_case_frequencies(self):
        """Test complex scenario with mixed cases and frequencies"""
        keywords = [
            "Hund", "Hund", "Hund",
            "katze", "Katze", "KATZE",
            "Vogel", "vogel",
            "Fisch"
        ]
        result = select_top_words(keywords, top_n=4)
        self.assertEqual(len(result), 4)
        # Hund (3), katze/Katze/KATZE (3), Vogel/vogel (2), Fisch (1)
        self.assertIn("Hund", result)
        self.assertTrue(any(w.lower() == "katze" for w in result))
        self.assertTrue(any(w.lower() == "vogel" for w in result))
        self.assertIn("Fisch", result)
    
    def test_default_top_n(self):
        """Test that default top_n is 7"""
        keywords = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        result = select_top_words(keywords)
        self.assertEqual(len(result), 7)


if __name__ == '__main__':
    unittest.main()
