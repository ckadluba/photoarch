"""
Tests for semantic similarity service.

Note: Use English keywords because semantic comparison should happen before translation.
"""

import unittest
from photoarch.services.semantic_similarity import (
    word_similarity,
    has_similar_keyword,
    keywords_are_different
)


class TestSemanticSimilarity(unittest.TestCase):
    """Test cases for semantic similarity functions."""

    def test_word_similarity_identical_words(self):
        """Identical words should have similarity close to 1.0."""
        similarity = word_similarity("snow", "snow")
        self.assertGreater(similarity, 0.99)

    def test_word_similarity_related_words_english(self):
        """Related English words should have high similarity."""
        # "snowy" and "snow" should be similar
        similarity = word_similarity("snowy", "snow")
        self.assertGreater(similarity, 0.6)

    def test_word_similarity_unrelated_words(self):
        """Unrelated words should have low similarity."""
        similarity = word_similarity("car", "beach")
        self.assertLess(similarity, 0.4)

    def test_word_similarity_case_insensitive(self):
        """Similarity check should be case-insensitive."""
        similarity1 = word_similarity("snow", "SNOW")
        similarity2 = word_similarity("Snow", "snow")
        self.assertGreater(similarity1, 0.99)
        self.assertGreater(similarity2, 0.99)

    def test_has_similar_keyword_exact_match(self):
        """Exact keyword match should return True."""
        keywords1 = {"car", "street"}
        keywords2 = {"car", "tree"}
        self.assertTrue(has_similar_keyword(keywords1, keywords2))

    def test_has_similar_keyword_semantic_match(self):
        """Semantically similar keywords should return True."""
        keywords1 = {"snowy", "street"}
        keywords2 = {"snow", "sidewalk"}
        self.assertTrue(has_similar_keyword(keywords1, keywords2))

    def test_has_similar_keyword_no_match(self):
        """Completely different keywords should return False."""
        keywords1 = {"computer", "keyboard"}
        keywords2 = {"beach", "ocean"}
        result = has_similar_keyword(keywords1, keywords2)
        self.assertFalse(result)

    def test_has_similar_keyword_empty_sets(self):
        """Empty keyword sets should return False."""
        self.assertFalse(has_similar_keyword(set(), {"car"}))
        self.assertFalse(has_similar_keyword({"car"}, set()))
        self.assertFalse(has_similar_keyword(set(), set()))

    def test_keywords_are_different_inverse_of_similar(self):
        """keywords_are_different should be inverse of has_similar_keyword."""
        keywords1 = {"car", "street"}
        keywords2 = {"bicycle", "path"}
        
        similar = has_similar_keyword(keywords1, keywords2)
        different = keywords_are_different(keywords1, keywords2)
        
        self.assertEqual(similar, not different)

    def test_keywords_are_different_with_similar_words(self):
        """Keywords with similar words should not be considered different."""
        keywords1 = {"snowy", "street"}
        keywords2 = {"snow", "road"}
        self.assertFalse(keywords_are_different(keywords1, keywords2))

    def test_has_similar_keyword_custom_threshold(self):
        """Custom threshold should affect similarity detection."""
        keywords1 = {"car"}
        keywords2 = {"vehicle"}  # Semantically related
        
        # With high threshold, might not be considered similar
        result_high = has_similar_keyword(keywords1, keywords2, threshold=0.9)
        
        # With low threshold, should be considered similar
        result_low = has_similar_keyword(keywords1, keywords2, threshold=0.5)
        
        # At least the low threshold should find them similar
        self.assertTrue(result_low)


class TestSemanticSimilarityEnglishWords(unittest.TestCase):
    """Additional tests specifically for English word variations."""

    def test_snow_variations(self):
        """Test various snow-related word forms."""
        base = "snow"
        variations = ["snowy", "snowflake", "snowing", "snowfall"]
        
        for variation in variations:
            similarity = word_similarity(base, variation)
            self.assertGreater(
                similarity, 0.5,
                f"'{base}' and '{variation}' should be somewhat similar, got {similarity:.3f}"
            )

    def test_car_variations(self):
        """Test car-related word forms."""
        base = "car"
        related = ["vehicle", "automobile", "auto"]
        
        for word in related:
            similarity = word_similarity(base, word)
            self.assertGreater(
                similarity, 0.5,
                f"'{base}' and '{word}' should be related, got {similarity:.3f}"
            )


if __name__ == '__main__':
    unittest.main()
