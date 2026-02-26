"""
Semantic similarity service using sentence-transformers for keyword comparison.
This module provides functions to compare keywords semantically rather than by exact string match.
"""

import logging
from functools import lru_cache
from sentence_transformers import SentenceTransformer, util

from ..config import SEMANTIC_SIMILARITY_MODEL, SEMANTIC_SIMILARITY_THRESHOLD


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


def word_similarity(word1: str, word2: str) -> float:
    """
    Calculate semantic similarity between two words.
    
    Returns:
        float: Cosine similarity score between 0.0 and 1.0
    """
    emb1 = get_embedding(word1.lower())
    emb2 = get_embedding(word2.lower())
    similarity = util.cos_sim(emb1, emb2).item()
    return similarity


def has_similar_keyword(keywords1: set[str], keywords2: set[str], threshold: float = SEMANTIC_SIMILARITY_THRESHOLD) -> bool:
    """
    Check if any keyword in keywords1 is semantically similar to any keyword in keywords2.
    
    Args:
        keywords1: First set of keywords
        keywords2: Second set of keywords  
        threshold: Minimum similarity score to consider words as similar (default from config)
        
    Returns:
        bool: True if at least one pair of keywords is similar
    """
    if not keywords1 or not keywords2:
        return False
    
    # First check for exact matches (fast path)
    if not keywords1.isdisjoint(keywords2):
        logger.debug(f"Keywords have exact match: {keywords1 & keywords2}")
        return True
    
    # Check semantic similarity for each pair
    for kw1 in keywords1:
        for kw2 in keywords2:
            similarity = word_similarity(kw1, kw2)
            if similarity >= threshold:
                logger.debug(f"Found similar keywords: '{kw1}' ~ '{kw2}' (similarity: {similarity:.3f})")
                return True
    
    logger.debug(f"No similar keywords found between {keywords1} and {keywords2}")
    return False


def keywords_are_different(keywords1: set[str], keywords2: set[str], threshold: float = SEMANTIC_SIMILARITY_THRESHOLD) -> bool:
    """
    Check if two keyword sets are semantically different (no similar keywords).
    This is the inverse of has_similar_keyword.
    
    Args:
        keywords1: First set of keywords
        keywords2: Second set of keywords
        threshold: Minimum similarity score to consider words as similar
        
    Returns:
        bool: True if no keyword pair is similar
    """
    return not has_similar_keyword(keywords1, keywords2, threshold)
