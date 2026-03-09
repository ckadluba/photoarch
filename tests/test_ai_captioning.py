import pytest
from photoarch.analysis.caption_generator import CaptionGenerator
from photoarch.analysis.ai_captioning_blip2 import Blip2CaptionGenerator
from photoarch.analysis.ai_captioning_llava import LlavaCaptionGenerator
from photoarch.analysis.caption_generator_factory import create_caption_generator
import os

def test_blip2_caption_generator_load_model():
    cg = Blip2CaptionGenerator(device="cpu")
    cg._load_model()
    assert cg._model is not None
    assert cg._processor is not None

@pytest.mark.longrunning
def test_get_caption_for_image_file():
    """LONG RUNNING: Tests BLIP AI caption generation (model download/inference)"""
    cg = Blip2CaptionGenerator(device="cpu")
    test_image = "tests/data/input/PXL_20250708_095842343.jpg"
    if os.path.exists(test_image):
        caption = cg.get_caption_for_image_file(test_image)
        assert isinstance(caption, str)
        assert len(caption) > 0
    else:
        pytest.skip("Test image not found.")


def test_create_caption_generator_blip2():
    cg = create_caption_generator("blip-2", device="cpu")
    assert isinstance(cg, Blip2CaptionGenerator)
    assert isinstance(cg, CaptionGenerator)


def test_create_caption_generator_llava():
    cg = create_caption_generator("llava", device="cpu")
    assert isinstance(cg, LlavaCaptionGenerator)
    assert isinstance(cg, CaptionGenerator)


@pytest.mark.longrunning
def test_llava_get_caption_for_image_file():
    """LONG RUNNING: Tests LLaVA AI caption generation (model download/inference)"""
    cg = LlavaCaptionGenerator(device="cpu")
    test_image = "tests/data/input/PXL_20250708_095842343.jpg"
    if os.path.exists(test_image):
        caption = cg.get_caption_for_image_file(test_image)
        assert isinstance(caption, str)
        assert len(caption) > 0
    else:
        pytest.skip("Test image not found.")
