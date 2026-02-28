"""
Semantic similarity service using sentence-transformers for caption comparison.
This module provides functions to compare captions semantically using sentence embeddings.
"""

import logging
from functools import lru_cache
from sentence_transformers import SentenceTransformer, util

from ..config import SEMANTIC_SIMILARITY_MODEL


# Initialization

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model (singleton pattern)."""
    global _model
    if _model is None:
        logger.info(f"Loading semantic similarity model: {SEMANTIC_SIMILARITY_MODEL}")
        _model = SentenceTransformer(SEMANTIC_SIMILARITY_MODEL)
        logger.info("Semantic similarity model loaded successfully")
    return _model

@lru_cache(maxsize=1000)
def get_embedding(word: str):
    """Get embedding for a word with caching for performance."""
    model = get_model()
    return model.encode(word, convert_to_tensor=True)

def calculate_caption_difference(caption1: str, caption2: str) -> float:
    """
    Calculate how different two captions are by comparing their sentence embeddings.
    
    Args:
        caption1: First caption
        caption2: Second caption
        
    Returns:
        float: Difference score from 0.0 (identical) to 1.0 (completely different).
               Returns 0.0 if either caption is empty.
    """
    if not caption1 or not caption2:
        return 0.0
    emb1 = get_embedding(caption1.lower())
    emb2 = get_embedding(caption2.lower())
    similarity = util.cos_sim(emb1, emb2).item()
    difference = 1.0 - (1.0 + similarity) / 2.0  # Convert similarity (-1.0 to 1.0) to difference (0.0 to 1.0)
    return difference
    