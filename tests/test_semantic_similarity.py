"""
Tests for semantic similarity service.
"""

import unittest
from photoarch.services.semantic_similarity import (
    calculate_caption_difference
)

class TestSemanticSimilarity(unittest.TestCase):
    """Test cases for semantic similarity functions."""

    def test_keywords_are_different_identical_captions(self):
        """Identical captions should have difference score close to 0."""
        score = calculate_caption_difference("a dog playing in the park", "a dog playing in the park")
        self.assertLess(score, 0.05)

    def test_keywords_are_different_similar_captions(self):
        """Similar captions should have a low difference score."""
        score = calculate_caption_difference("a dog playing in the snow", "a puppy running in snow")
        self.assertLess(score, 0.5)

    def test_keywords_are_different_different_captions(self):
        """Very different captions should have a high difference score."""
        score = calculate_caption_difference(
            "a man and a woman posing for a photo on a city street",
            "two guinea pigs lying in the snow in front of a red shed"
        )
        self.assertGreater(score, 0.3)

    def test_keywords_are_different_empty_captions(self):
        """Empty captions should return 0.0 (cannot determine difference)."""
        self.assertEqual(calculate_caption_difference("", ""), 0.0)
        self.assertEqual(calculate_caption_difference("some caption", ""), 0.0)
        self.assertEqual(calculate_caption_difference("", "some caption"), 0.0)

    def test_keywords_are_different_returns_float_in_range(self):
        """keywords_are_different should return a float between 0.0 and 1.0."""
        score = calculate_caption_difference("a dog in the park", "a cat on a sofa")
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

if __name__ == '__main__':
    unittest.main()
