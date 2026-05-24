import pytest
import torch
from photoarch.analysis.caption_generator import CaptionGenerator
from photoarch.analysis.ai_captioning_blip2 import Blip2CaptionGenerator
from photoarch.analysis.ai_captioning_llava import LlavaCaptionGenerator
from photoarch.analysis.caption_generator_factory import create_caption_generator
from photoarch.device_utils import get_device_dtype
import os

def test_blip2_caption_generator_load_model():
    cg = Blip2CaptionGenerator(device="cpu")
    cg._load_model()
    assert cg._model is not None
    assert cg._processor is not None

def test_blip2_caption_generator_auto_device():
    """Test BLIP2 with auto device detection."""
    cg = Blip2CaptionGenerator(device="auto")
    assert cg.device in ["mps", "cuda", "cpu"]
    assert isinstance(cg.dtype, torch.dtype)
    assert cg.dtype == get_device_dtype(cg.device)

def test_blip2_caption_generator_cpu_device():
    """Test BLIP2 with explicit CPU device."""
    cg = Blip2CaptionGenerator(device="cpu")
    assert cg.device == "cpu"
    assert cg.dtype == torch.float32

def test_llava_caption_generator_auto_device():
    """Test LLaVA with auto device detection."""
    cg = LlavaCaptionGenerator(device="auto")
    assert cg.device in ["mps", "cuda", "cpu"]
    assert isinstance(cg.dtype, torch.dtype)
    assert cg.dtype == get_device_dtype(cg.device)

def test_llava_caption_generator_cpu_device():
    """Test LLaVA with explicit CPU device."""
    cg = LlavaCaptionGenerator(device="cpu")
    assert cg.device == "cpu"
    assert cg.dtype == torch.float32

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

def test_create_caption_generator_blip2_auto():
    """Test factory creates BLIP2 with auto device detection."""
    cg = create_caption_generator("blip-2", device="auto")
    assert isinstance(cg, Blip2CaptionGenerator)
    assert isinstance(cg, CaptionGenerator)
    assert cg.device in ["mps", "cuda", "cpu"]

def test_create_caption_generator_llava():
    cg = create_caption_generator("llava", device="cpu")
    assert isinstance(cg, LlavaCaptionGenerator)
    assert isinstance(cg, CaptionGenerator)

def test_create_caption_generator_llava_auto():
    """Test factory creates LLaVA with auto device detection."""
    cg = create_caption_generator("llava", device="auto")
    assert isinstance(cg, LlavaCaptionGenerator)
    assert isinstance(cg, CaptionGenerator)
    assert cg.device in ["mps", "cuda", "cpu"]


@pytest.mark.longrunning
@pytest.mark.skip(reason="LLaVA model download and inference can be very slow")
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
