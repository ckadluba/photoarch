import logging
from PIL import Image
import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration

from ..config import *


# Initialization

logger = logging.getLogger(__name__)


# Code

class CaptionGenerator:
    def __init__(self, device: str = "cpu"):
        self.device = device
        self._model = None
        self._processor = None

    def _load_model(self):
        if self._model is None:
            logger.info("Loading BLIP-2 Model (CPU) …")
            self._processor = Blip2Processor.from_pretrained(
                MODEL_NAME,
                cache_dir=MODEL_CACHE_DIR,
                use_fast=True
            )

            self._model = Blip2ForConditionalGeneration.from_pretrained(
                MODEL_NAME,
                cache_dir=MODEL_CACHE_DIR,
                dtype=torch.float32
            )
            self._model.eval()

    def get_caption_for_image_file(self, file_path) -> str:
        self._load_model()
        try:
            img = Image.open(file_path).convert("RGB")

            inputs = self._processor(images=img, return_tensors="pt").to(self.device)

            with torch.no_grad():
                output = self._model.generate(
                    **inputs,
                    max_new_tokens=50,
                    num_beams=3
                )

            return self._processor.decode(output[0], skip_special_tokens=True)

        except Exception as e:
            logger.error(f"Error during AI analysis of {file_path.name}: {e}")
            return ""

