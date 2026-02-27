"""
Tests for semantic similarity service.
"""

import unittest
from photoarch.services.semantic_similarity import (
    word_similarity,
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

    def test_keywords_are_different_identical_captions(self):
        """Identical captions should have difference score close to 0."""
        score = keywords_are_different("a dog playing in the park", "a dog playing in the park")
        self.assertLess(score, 0.05)

    def test_keywords_are_different_similar_captions(self):
        """Similar captions should have a low difference score."""
        score = keywords_are_different("a dog playing in the snow", "a puppy running in snow")
        self.assertLess(score, 0.5)

    def test_keywords_are_different_different_captions(self):
        """Very different captions should have a high difference score."""
        score = keywords_are_different(
            "a man and a woman posing for a photo on a city street",
            "two guinea pigs lying in the snow in front of a red shed"
        )
        self.assertGreater(score, 0.3)

    def test_keywords_are_different_empty_captions(self):
        """Empty captions should return 0.0 (cannot determine difference)."""
        self.assertEqual(keywords_are_different("", ""), 0.0)
        self.assertEqual(keywords_are_different("some caption", ""), 0.0)
        self.assertEqual(keywords_are_different("", "some caption"), 0.0)

    def test_keywords_are_different_returns_float_in_range(self):
        """keywords_are_different should return a float between 0.0 and 1.0."""
        score = keywords_are_different("a dog in the park", "a cat on a sofa")
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


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
