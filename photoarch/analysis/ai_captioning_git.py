import logging
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForCausalLM

from ..config import IMAGE_CAPTIONING_MODEL_NAME_GIT, MODEL_CACHE_DIR
from ..device_utils import get_optimal_device, get_device_dtype
from .caption_generator import CaptionGenerator


logger = logging.getLogger(__name__)


class GitCaptionGenerator(CaptionGenerator):
    def __init__(self, device: str = "auto"):
        # Auto-detect optimal device if "auto" is specified
        if device == "auto":
            initial_device, initial_dtype = get_optimal_device()
            # GIT works well with MPS/CUDA/CPU
            if initial_device == "mps":
                logger.info("Using Apple Metal Performance Shaders (MPS) for GIT")
                self.device = "mps"
                self.dtype = torch.float32
            elif initial_device == "cuda":
                logger.info("Using CUDA for GIT")
                self.device = "cuda"
                self.dtype = torch.float16
            else:
                logger.info("Using CPU for GIT")
                self.device = "cpu"
                self.dtype = torch.float32
        else:
            self.device = device
            self.dtype = get_device_dtype(device)
        
        self._model = None
        self._processor = None

    def _load_model(self):
        if self._model is None:
            logger.info(f"Loading GIT Model on {self.device} …")
            logger.debug(f"Device details - Type: {self.device}, Dtype: {self.dtype}")
            
            self._processor = AutoProcessor.from_pretrained(
                IMAGE_CAPTIONING_MODEL_NAME_GIT,
                cache_dir=MODEL_CACHE_DIR
            )
            logger.debug("Processor loaded")
            
            self._model = AutoModelForCausalLM.from_pretrained(
                IMAGE_CAPTIONING_MODEL_NAME_GIT,
                cache_dir=MODEL_CACHE_DIR,
                torch_dtype=self.dtype
            )
            logger.debug(f"Model loaded from pretrained")
            
            # Move model to device
            self._model = self._model.to(self.device)
            self._model.eval()
            logger.info(f"Model loaded and ready on device {self.device}")

    def get_caption_for_image_file(self, file_path) -> str:
        logger.debug(f"Starting caption generation for {file_path}")
        self._load_model()
        logger.debug("Model loaded successfully")

        logger.debug("Loading and processing image")
        img = Image.open(file_path).convert("RGB")
        logger.debug("Image loaded")

        logger.debug("Processing inputs")
        inputs = self._processor(images=img, return_tensors="pt").to(self.device)
        logger.debug("Inputs prepared and moved to device")

        logger.debug("Starting generation")
        with torch.no_grad():
            generated_ids = self._model.generate(
                pixel_values=inputs.pixel_values,
                max_length=100,
                num_beams=1,
                do_sample=False
            )
        logger.debug("Generation completed")

        caption = self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        logger.debug(f"Generated caption: {caption}")
        
        return caption.strip()
