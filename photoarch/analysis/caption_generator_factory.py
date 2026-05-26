from .caption_generator import CaptionGenerator
from .ai_captioning_blip2 import Blip2CaptionGenerator
from .ai_captioning_llava import LlavaCaptionGenerator
from .ai_captioning_git import GitCaptionGenerator


def create_caption_generator(model: str = "blip-2", device: str = "auto") -> CaptionGenerator:
    if model == "llava":
        return LlavaCaptionGenerator(device=device)
    elif model == "git":
        return GitCaptionGenerator(device=device)
    else:
        # Default to BLIP-2
        return Blip2CaptionGenerator(device=device)
