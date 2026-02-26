import re
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END

from .ai_captioning import CaptionGenerator
from ..services.language import translate_english_to_german
from ..config import STOPWORDS, STOPWORDS_GERMAN, FOLDER_FORBIDDEN_CHARS


# Initialization

logger = logging.getLogger(__name__)


# Code

class ImageCaptionState(TypedDict):
    image_path: str
    caption_en: str
    caption_de: str
    keywords_en: list[str]
    keywords_de: list[str]


def get_keywords_from_caption(caption: str, stopwords: set) -> list[str]:
    sanitized_caption = re.sub(FOLDER_FORBIDDEN_CHARS, "", caption)
    keywords_full = sanitized_caption.split()
    keywords_no_stopwords = [k for k in keywords_full if k.lower() not in stopwords]
    keywords_unique = list(dict.fromkeys(keywords_no_stopwords))
    # Sort alphabetically for deterministic output
    keywords_sorted = sorted(keywords_unique, key=str.lower)
    return keywords_sorted


def build_caption_pipeline(captioner: CaptionGenerator):
    """Build and compile a LangGraph pipeline that orchestrates BLIP-2 captioning,
    German translation, and keyword extraction as discrete, replaceable nodes."""

    def generate_caption(state: ImageCaptionState) -> dict:
        caption = captioner.get_caption_for_image_file(state["image_path"])
        logger.debug(f"Generated caption: {caption}")
        return {"caption_en": caption}

    def translate_caption(state: ImageCaptionState) -> dict:
        caption_de = translate_english_to_german(state["caption_en"])
        logger.debug(f"Translated caption: {caption_de}")
        return {"caption_de": caption_de}

    def extract_keywords(state: ImageCaptionState) -> dict:
        keywords_en = get_keywords_from_caption(state["caption_en"], STOPWORDS)
        keywords_de = get_keywords_from_caption(state["caption_de"], STOPWORDS_GERMAN)
        return {"keywords_en": keywords_en, "keywords_de": keywords_de}

    graph = StateGraph(ImageCaptionState)
    graph.add_node("generate_caption", generate_caption)
    graph.add_node("translate_caption", translate_caption)
    graph.add_node("extract_keywords", extract_keywords)
    graph.set_entry_point("generate_caption")
    graph.add_edge("generate_caption", "translate_caption")
    graph.add_edge("translate_caption", "extract_keywords")
    graph.add_edge("extract_keywords", END)
    return graph.compile()
