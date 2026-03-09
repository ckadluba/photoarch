from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .analysis.caption_generator import CaptionGenerator
    from sentence_transformers import SentenceTransformer


class AiModelsContext:
    def __init__(self, captioner: Optional[CaptionGenerator] = None, sentence_transformer: Optional[SentenceTransformer] = None):
        self.captioner = captioner
        self.sentence_transformer = sentence_transformer
