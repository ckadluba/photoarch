import io
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from photoarch.ai_models_context import AiModelsContext
from photoarch.analysis.image_embedder import calculate_image_difference, get_image_embedding, get_model


TEST_IMAGE_PATH = Path("tests/data/input/PXL_20250708_095842343.jpg")
TEST_IMAGE_PATH_2 = Path("tests/data/input/PXL_20250708_055317372.jpg")


def _make_fake_image_file(tmp_path: Path, color=(255, 0, 0)) -> Path:
    """Create a small solid-color JPEG in tmp_path and return its path."""
    img = Image.new("RGB", (32, 32), color=color)
    p = tmp_path / f"test_{color[0]}_{color[1]}_{color[2]}.jpg"
    img.save(p, format="JPEG")
    return p


class TestGetModel(unittest.TestCase):
    """Tests for the lazy-loading model accessor."""

    def test_get_model_initialises_clip_model(self):
        """get_model() should load and cache the CLIP model on first call."""
        context = AiModelsContext()
        self.assertIsNone(context.clip_model)
        model = get_model(context)
        self.assertIsNotNone(model)
        self.assertIsNotNone(context.clip_model)

    def test_get_model_returns_same_instance(self):
        """get_model() should return the same instance on repeated calls."""
        context = AiModelsContext()
        m1 = get_model(context)
        m2 = get_model(context)
        self.assertIs(m1, m2)

    def test_get_model_skips_loading_when_already_set(self):
        """get_model() must not overwrite an already-set clip_model."""
        fake_model = MagicMock()
        context = AiModelsContext()
        context.clip_model = fake_model
        result = get_model(context)
        self.assertIs(result, fake_model)


class TestGetImageEmbedding(unittest.TestCase):
    """Tests for get_image_embedding()."""

    def setUp(self):
        self.context = AiModelsContext()

    def _mock_encode(self, dim=512):
        """Return a mock context whose clip_model.encode returns a fixed numpy array."""
        fake_vec = np.random.rand(dim).astype(np.float32)
        mock_model = MagicMock()
        mock_model.encode.return_value = fake_vec
        self.context.clip_model = mock_model
        return fake_vec

    def test_returns_list_of_floats(self, tmp_path=None):
        """get_image_embedding() must return a non-empty list of floats."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            img_path = _make_fake_image_file(Path(td))
            fake_vec = self._mock_encode()
            result = get_image_embedding(img_path, self.context)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(fake_vec))
        self.assertTrue(all(isinstance(v, float) for v in result))

    def test_passes_rgb_image_to_model(self):
        """The image must be converted to RGB before encoding."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            img_path = _make_fake_image_file(Path(td))
            self._mock_encode()
            get_image_embedding(img_path, self.context)
            call_args = self.context.clip_model.encode.call_args  # type: ignore[union-attr]
            encoded_image = call_args[0][0]
            self.assertEqual(encoded_image.mode, "RGB")

    def test_different_images_produce_different_embeddings(self):
        """Two different images should produce different embeddings (no model mocking)."""
        if not TEST_IMAGE_PATH.exists() or not TEST_IMAGE_PATH_2.exists():
            self.skipTest("Test images not found")
        context = AiModelsContext()
        emb1 = get_image_embedding(TEST_IMAGE_PATH, context)
        emb2 = get_image_embedding(TEST_IMAGE_PATH_2, context)
        self.assertNotEqual(emb1, emb2)

    @pytest.mark.longrunning
    def test_same_image_produces_identical_embeddings(self):
        """The same image file encoded twice must yield the identical embedding."""
        if not TEST_IMAGE_PATH.exists():
            self.skipTest("Test image not found")
        context = AiModelsContext()
        emb1 = get_image_embedding(TEST_IMAGE_PATH, context)
        emb2 = get_image_embedding(TEST_IMAGE_PATH, context)
        self.assertEqual(emb1, emb2)


class TestCalculateImageDifference(unittest.TestCase):
    """Tests for calculate_image_difference()."""

    def _unit(self, dim, index):
        """Return a unit vector with 1.0 at position index."""
        v = [0.0] * dim
        v[index] = 1.0
        return v

    def test_identical_embeddings_return_similarity_one(self):
        """Identical embeddings should return cosine similarity 1.0."""
        v = [1.0, 0.0, 0.0]
        score = calculate_image_difference(v, v)
        self.assertAlmostEqual(score, 1.0, places=5)

    def test_orthogonal_embeddings_return_zero(self):
        """Orthogonal embeddings should return cosine similarity 0.0."""
        score = calculate_image_difference(self._unit(3, 0), self._unit(3, 1))
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_opposite_embeddings_return_minus_one(self):
        """Opposite embeddings should return cosine similarity -1.0."""
        v = [1.0, 0.0, 0.0]
        neg_v = [-1.0, 0.0, 0.0]
        score = calculate_image_difference(v, neg_v)
        self.assertAlmostEqual(score, -1.0, places=5)

    def test_returns_float(self):
        """Return value must be a plain Python float."""
        score = calculate_image_difference([1.0, 0.0], [0.0, 1.0])
        self.assertIsInstance(score, float)

    def test_result_in_valid_range(self):
        """Score must be within [-1.0, 1.0] for arbitrary unit vectors."""
        import random
        random.seed(42)
        for _ in range(20):
            v1 = [random.gauss(0, 1) for _ in range(64)]
            v2 = [random.gauss(0, 1) for _ in range(64)]
            score = calculate_image_difference(v1, v2)
            self.assertGreaterEqual(score, -1.0)
            self.assertLessEqual(score, 1.0)

    def test_symmetry(self):
        """calculate_image_difference(a, b) must equal calculate_image_difference(b, a)."""
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        self.assertAlmostEqual(
            calculate_image_difference(a, b),
            calculate_image_difference(b, a),
            places=6
        )


if __name__ == "__main__":
    unittest.main()
