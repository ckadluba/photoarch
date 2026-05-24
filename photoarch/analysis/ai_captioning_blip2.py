import logging
from PIL import Image
import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration

from ..config import IMAGE_CAPTIONING_MODEL_NAME_BLIP2, MODEL_CACHE_DIR
from ..device_utils import get_optimal_device, get_device_dtype
from .caption_generator import CaptionGenerator


logger = logging.getLogger(__name__)


class Blip2CaptionGenerator(CaptionGenerator):
    def __init__(self, device: str = "auto"):
        # Auto-detect optimal device if "auto" is specified
        if device == "auto":
            self.device, self.dtype = get_optimal_device()
        else:
            self.device = device
            self.dtype = get_device_dtype(device)
        
        self._model = None
        self._processor = None

    def _load_model(self):
        if self._model is None:
            logger.info(f"Loading BLIP-2 Model on {self.device} …")
            self._processor = Blip2Processor.from_pretrained(
                IMAGE_CAPTIONING_MODEL_NAME_BLIP2,
                cache_dir=MODEL_CACHE_DIR,
                use_fast=True
            )
            
            # Load model with appropriate dtype for the device
            self._model = Blip2ForConditionalGeneration.from_pretrained(
                IMAGE_CAPTIONING_MODEL_NAME_BLIP2,
                cache_dir=MODEL_CACHE_DIR,
                dtype=self.dtype
            )
            
            # Move model to device
            self._model = self._model.to(self.device)
            self._model.eval()

    def get_caption_for_image_file(self, file_path) -> str:
        self._load_model()

        img = Image.open(file_path).convert("RGB")
        inputs = self._processor(images=img, return_tensors="pt").to(self.device)

        with torch.no_grad():
            output = self._model.generate(
                **inputs,
                max_new_tokens=50,
                num_beams=3
            )

        return self._processor.decode(output[0], skip_special_tokens=True)
