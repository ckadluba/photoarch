import logging
from sentence_transformers import SentenceTransformer, util
from typing import TYPE_CHECKING

from ..config import SEMANTIC_SIMILARITY_MODEL_NAME, MODEL_CACHE_DIR

if TYPE_CHECKING:
    from ..ai_models_context import AiModelsContext


# Initialization

logger = logging.getLogger(__name__)


def get_model(context: AiModelsContext) -> SentenceTransformer:
    """Lazy-load the sentence transformer model (singleton pattern)."""
    if context.sentence_transformer is None:
        logger.info(f"Loading semantic similarity model: {SEMANTIC_SIMILARITY_MODEL_NAME}")
        context.sentence_transformer = SentenceTransformer(SEMANTIC_SIMILARITY_MODEL_NAME, cache_folder=MODEL_CACHE_DIR)
        logger.info("Semantic similarity model loaded successfully")
    return context.sentence_transformer


def calculate_caption_difference(caption1: str, caption2: str, context: AiModelsContext) -> float:
    """
    Calculate how different two captions are by comparing their sentence embeddings.
    
    Args:
        caption1: First caption
        caption2: Second caption
        context: AI models context for model caching.
        
    Returns:
        float: Difference score from 0.0 (identical) to 1.0 (completely different).
               Returns 0.0 if either caption is empty.
    """
    if not caption1 or not caption2:
        return 0.0
    model = get_model(context)
    emb1 = model.encode(caption1.lower(), convert_to_tensor=True)
    emb2 = model.encode(caption2.lower(), convert_to_tensor=True)
    similarity = util.cos_sim(emb1, emb2).item()
    difference = 1.0 - (1.0 + similarity) / 2.0  # Convert similarity (-1.0 to 1.0) to difference (0.0 to 1.0)
    return difference
    