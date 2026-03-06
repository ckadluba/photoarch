from collections import Counter
import numpy as np
from re import sub
from sentence_transformers import SentenceTransformer

from ..config import FOLDER_FORBIDDEN_CHARS


# Initialization

_model = None


# Code

def get_model():
    """
    Lazy-load the embedding model.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def cosine_similarity(a, b):
    """
    Compute cosine similarity between two vectors.
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def cluster_words(words, embeddings, similarity_threshold=0.75):
    """
    Greedy clustering of semantically similar words.
    """
    clusters = []

    for word, emb in zip(words, embeddings):

        placed = False

        for cluster in clusters:
            rep_emb = cluster["embedding"]

            if cosine_similarity(emb, rep_emb) > similarity_threshold:
                cluster["words"].append(word)
                placed = True
                break

        if not placed:
            clusters.append({
                "embedding": emb,
                "words": [word]
            })

    return clusters


def select_top_words(keywords, top_n):
    """
    Cleans a list of keywords:
    - Clean special characters that are not allowed in folder names
    - Remove duplicates (case-insensitive)
    - Merge semantically similar words
    - Select top-N most frequent words
    - Preserve original capitalization

    :param keywords: list of strings
    :param top_n: maximum number of keywords for the folder name
    :return: cleaned list of top-N keywords
    """

    if not keywords:
        return []

    # Clean special characters
    folder_sanitized_keywords = [sub(FOLDER_FORBIDDEN_CHARS, "", k) for k in keywords]

    # Track original variants
    word_variants = {}
    for word in folder_sanitized_keywords:
        lower = word.lower()
        if lower not in word_variants:
            word_variants[lower] = []
        word_variants[lower].append(word)

    # Count frequencies
    lowercase_counts = Counter([w.lower() for w in folder_sanitized_keywords])
    unique_words = list(lowercase_counts.keys())

    # Generate embeddings
    model = get_model()
    embeddings = model.encode(unique_words)

    # Cluster semantically similar words
    clusters = cluster_words(unique_words, embeddings)

    representatives = []

    for cluster in clusters:
        words = cluster["words"]

        # Choose most frequent word in cluster
        rep_lower = max(words, key=lambda w: lowercase_counts[w])
        representatives.append((rep_lower, lowercase_counts[rep_lower]))

    # Sort by frequency
    representatives.sort(key=lambda x: x[1], reverse=True)

    # Convert back to most common capitalization variant
    result = []

    for lower_word, _ in representatives[:top_n]:
        variants = word_variants[lower_word]
        most_common_variant = Counter(variants).most_common(1)[0][0]
        result.append(most_common_variant)

    return result