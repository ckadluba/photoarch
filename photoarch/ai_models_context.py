from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .analysis.caption_generator import CaptionGenerator


class AiModelsContext:
    def __init__(self, captioner: Optional[CaptionGenerator] = None):
        self.captioner = captioner
