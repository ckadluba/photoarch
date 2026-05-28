from .caption_generator import CaptionGenerator
from .ai_captioning_blip2 import Blip2CaptionGenerator
from .ai_captioning_llava import LlavaCaptionGenerator
from .ai_captioning_git import GitCaptionGenerator


def create_caption_generator(model: str = "git", device: str = "auto") -> CaptionGenerator:
    if model == "llava":
        return LlavaCaptionGenerator(device=device)
    elif model == "blip-2":
        return Blip2CaptionGenerator(device=device)
    else:
        # Default to GIT
        return GitCaptionGenerator(device=device)
