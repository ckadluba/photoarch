import pytest
from photoarch.analysis.ai_captioning import CaptionGenerator
import os

def test_caption_generator_load_model():
    cg = CaptionGenerator(device="cpu")
    cg._load_model()
    assert cg._model is not None
    assert cg._processor is not None

@pytest.mark.longrunning
def test_get_caption_for_image_file():
    """LONG RUNNING: Tests BLIP AI caption generation (model download/inference)"""
    cg = CaptionGenerator(device="cpu")
    test_image = "tests/data/input/PXL_20250708_095842343.jpg"
    if os.path.exists(test_image):
        caption = cg.get_caption_for_image_file(test_image)
        assert isinstance(caption, str)
        assert len(caption) > 0
    else:
        pytest.skip("Test image not found.")
