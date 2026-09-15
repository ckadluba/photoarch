"""Local English-to-German translation with OPUS-MT."""

import logging
from functools import lru_cache

import torch
from transformers import MarianMTModel, MarianTokenizer

from photoarch.config import MODEL_CACHE_DIR

logger = logging.getLogger(__name__)
_TRANSLATION_MODEL = "Helsinki-NLP/opus-mt-en-de"


class TranslationError(RuntimeError):
    """Raised when no translation could be produced."""


@lru_cache(maxsize=1)
def _load_translator() -> tuple[MarianTokenizer, MarianMTModel]:
    """Load once on first use, reusing the model files on disk."""
    logger.info("Loading local translation model %s", _TRANSLATION_MODEL)
    tokenizer = MarianTokenizer.from_pretrained(
        _TRANSLATION_MODEL, cache_dir=MODEL_CACHE_DIR
    )
    model = MarianMTModel.from_pretrained(_TRANSLATION_MODEL, cache_dir=MODEL_CACHE_DIR)
    model.eval()
    return tokenizer, model


def translate_english_to_german(text: str) -> str:
    """Translate a caption locally; empty input needs no model download."""
    if not text.strip():
        return ""

    try:
        tokenizer, model = _load_translator()
        inputs = tokenizer(text, return_tensors="pt", truncation=False)
        if inputs["input_ids"].shape[-1] > model.config.max_position_embeddings:
            raise ValueError("Caption exceeds the translation model's input limit.")
        with torch.inference_mode():
            output = model.generate(
                **inputs, max_new_tokens=model.config.max_position_embeddings
            )
        result = tokenizer.decode(output[0], skip_special_tokens=True).strip()
        if not result:
            raise ValueError("No translated text was returned.")
    except Exception as exc:
        logger.error("Translation failed: %s", exc)
        raise TranslationError("Could not translate English text to German.") from exc

    return result
