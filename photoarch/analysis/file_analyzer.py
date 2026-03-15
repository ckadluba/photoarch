import logging
import json
from pathlib import Path

from ..config import (
    INPUT_DIR_STR, OUTPUT_DIR_STR, CACHE_DIR_STR,
    IMAGE_FILE_EXTENSIONS, VIDEO_FILE_EXTENSIONS,
    STOPWORDS, STOPWORDS_GERMAN, KEYWORD_GENERIC_VIDEO
)
from ..models import FileInfo
from ..ai_models_context import AiModelsContext
from ..fileops.file_utils import get_file_modified_datetime, does_filename_meet_criteria
from ..services.geocoding import get_address_from_coords
from ..services.translate import translate_english_to_german
from ..language.keyword_generator import get_keywords_from_caption
from .exif_reader import get_exif_data_from_file, get_date_from_exif_data, get_camera_from_exif_data, get_gps_from_exif_data
from .caption_generator_factory import create_caption_generator
from .image_embedder import get_image_embedding


# Initialization

INPUT_DIR = Path(INPUT_DIR_STR)
OUTPUT_DIR = Path(OUTPUT_DIR_STR)
CACHE_DIR = Path(CACHE_DIR_STR)

logger = logging.getLogger(__name__)


# Code

def analyze_file(file_path: Path, ai_models_context: AiModelsContext | None = None, captioning_ai_model: str = "blip-2") -> FileInfo:
    """Analyze image and return FileInfo"""

    # Use cache entry if available
    cache_file = CACHE_DIR / (file_path.stem + ".json")
    if cache_file.exists():
        logger.info(f"Using cached {cache_file.name}.")
        with open(cache_file, "r", encoding="utf-8") as f:
            return FileInfo.from_json(f.read())
    
    # Create new FileInfo
    file_info = FileInfo(
        path=Path(file_path.name),
        date=None,
        lat=None,
        lon=None,
        address=None,
        keywords=[],
        keywords_german=[],
        caption="",
        skip=False
    )
    
    # Check filename criteria
    if not does_filename_meet_criteria(file_path):
        logger.info(f"Filename does not match criteria {file_path.name}. Will skip.")
        file_info.skip = True
        return file_info

    # Process file
    exif_data = get_exif_data_from_file(file_path)
    if exif_data is None:
        logger.warning(f"Could not read EXIF data from {file_path.name}.")

    # Get date and time from EXIF if available (overrides filename date)
    date_time = get_date_from_exif_data(exif_data) if exif_data else None
    if date_time is None:
        logger.warning(f"Could not read date from EXIF data of {file_path.name}. Using file modified date as fallback.")
        file_info.date = get_file_modified_datetime(file_path)
    else:
        file_info.date = date_time

    # Get camera model from EXIF if available
    camera_model = get_camera_from_exif_data(exif_data) if exif_data else None
    if camera_model is None:
        logger.warning(f"Could not read camera model from EXIF data of {file_path.name}.")
    file_info.camera_model = camera_model

    # Get GPS from EXIF data
    lat, lon = None, None
    lat, lon = get_gps_from_exif_data(exif_data) if exif_data else (None, None)
    if lat is None or lon is None:
        logger.warning(f"Could not read GPS data from {file_path.name}.")
    file_info.lat = lat
    file_info.lon = lon
    
    # Get address from coordinates
    address = get_address_from_coords(file_info.lat, file_info.lon)
    if address is None:
        logger.warning(f"Could not read address from {file_path.name}.")
    file_info.address = address

    # AI analysis for keywords and caption
    if file_path.suffix.lower() in IMAGE_FILE_EXTENSIONS:
        if ai_models_context is None:
            ai_models_context = AiModelsContext()
        if ai_models_context.captioner is None:
            logger.info(f"Initializing captioner ({captioning_ai_model}) …")
            ai_models_context.captioner = create_caption_generator(captioning_ai_model, device="cpu")
        caption = ai_models_context.captioner.get_caption_for_image_file(file_path)
        keywords = get_keywords_from_caption(caption, STOPWORDS)
        caption_german = translate_english_to_german(caption)
        keywords_german = get_keywords_from_caption(caption_german, STOPWORDS_GERMAN)
        file_info.caption = caption
        file_info.caption_german = caption_german
        file_info.keywords = keywords
        file_info.keywords_german = keywords_german
        file_info.embedding = get_image_embedding(file_path, ai_models_context)
        
    elif file_path.suffix.lower() in VIDEO_FILE_EXTENSIONS:
        file_info.keywords.append(KEYWORD_GENERIC_VIDEO)
        file_info.keywords_german.append(KEYWORD_GENERIC_VIDEO)

    # Save to cache
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file.write_text(
        json.dumps(
            file_info.to_dict(),
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return file_info
