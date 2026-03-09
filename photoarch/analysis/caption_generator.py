from abc import ABC, abstractmethod


class CaptionGenerator(ABC):
    @abstractmethod
    def get_caption_for_image_file(self, file_path) -> str:
        ...
