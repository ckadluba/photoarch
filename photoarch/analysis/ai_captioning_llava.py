import logging
from PIL import Image
import torch
from transformers import LlavaForConditionalGeneration, AutoProcessor

from ..config import IMAGE_CAPTIONING_MODEL_NAME_LLAVA, MODEL_CACHE_DIR
from .caption_generator import CaptionGenerator


logger = logging.getLogger(__name__)


class LlavaCaptionGenerator(CaptionGenerator):
    def __init__(self, device: str = "cpu"):
        self.device = device
        self._model = None
        self._processor = None

    def _load_model(self):
        if self._model is None:
            logger.info("Loading LLaVA Model …")
            self._processor = AutoProcessor.from_pretrained(
                IMAGE_CAPTIONING_MODEL_NAME_LLAVA,
                cache_dir=MODEL_CACHE_DIR
            )
            self._model = LlavaForConditionalGeneration.from_pretrained(
                IMAGE_CAPTIONING_MODEL_NAME_LLAVA,
                cache_dir=MODEL_CACHE_DIR,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
            )
            self._model.eval()

    def get_caption_for_image_file(self, file_path) -> str:
        self._load_model()

        img = Image.open(file_path).convert("RGB")
        prompt = "USER: <image>\nDescribe this image.\nASSISTANT:"
        inputs = self._processor(text=prompt, images=img, return_tensors="pt").to(self.device)

        with torch.no_grad():
            output = self._model.generate(
                **inputs,
                max_new_tokens=50,
                num_beams=3
            )

        full_output = self._processor.decode(output[0], skip_special_tokens=True)
        if "ASSISTANT:" in full_output:
            return full_output.split("ASSISTANT:")[-1].strip()
        return full_output.strip()
