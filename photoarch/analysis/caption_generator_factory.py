from .caption_generator import CaptionGenerator
from .ai_captioning_blip2 import Blip2CaptionGenerator
from .ai_captioning_llava import LlavaCaptionGenerator


def create_caption_generator(model: str = "blip-2", device: str = "cpu") -> CaptionGenerator:
    if model == "llava":
        return LlavaCaptionGenerator(device=device)
    return Blip2CaptionGenerator(device=device)
