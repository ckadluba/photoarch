import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image
from sentence_transformers import SentenceTransformer, util

from ..config import IMAGE_EMBEDDING_MODEL_NAME, MODEL_CACHE_DIR

if TYPE_CHECKING:
    from ..ai_models_context import AiModelsContext


# Initialization

logger = logging.getLogger(__name__)


def get_model(context: "AiModelsContext") -> SentenceTransformer:
    """Lazy-load the CLIP model for image embeddings (singleton pattern)."""
    if context.clip_model is None:
        logger.info(f"Loading image embedding model: {IMAGE_EMBEDDING_MODEL_NAME}")
        context.clip_model = SentenceTransformer(IMAGE_EMBEDDING_MODEL_NAME, cache_folder=MODEL_CACHE_DIR)
        logger.info("Image embedding model loaded successfully")
    return context.clip_model


def get_image_embedding(image_path: Path, context: "AiModelsContext") -> list[float]:
    """Compute a CLIP embedding from raw image data and return it as a list of floats."""
    model = get_model(context)
    image = Image.open(image_path).convert("RGB")
    return model.encode(image).tolist()


def calculate_image_difference(emb1: list[float], emb2: list[float]) -> float:
    """
    Calculate the difference between two pre-computed image embeddings.

    Returns:
        float: Difference score from 0.0 (identical) to 1.0 (different).
    """
    import torch
    t1 = torch.tensor(emb1)
    t2 = torch.tensor(emb2)
    similarity = util.cos_sim(t1, t2).item()

    # For image embeddings, we might want to treat higher similarity as more similar, 
    # so instead of a scaled score, we can return similarity directly and cut off negative values.
    return 1.0 - max(0.0, similarity)