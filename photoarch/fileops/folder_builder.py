import logging
import re
from pathlib import Path
from geopy.distance import geodesic
from datetime import datetime
from ..config import *
from ..models import FolderInfo, FileInfo
from ..ai_models_context import AiModelsContext
from ..language.caption_comparer import calculate_caption_difference
from ..analysis.image_embedder import calculate_image_difference
from ..language.keyword_reducer import select_top_words


# Initialization

logger = logging.getLogger(__name__)


# Code

def create_folder_info(folder_infos: list[FolderInfo], start_date: datetime):
    folder_info = FolderInfo(
        start_date = start_date,
        end_date=None,
        place=None,
        keywords=set(),
        keywords_german=set(),
        files=[]
    )
    folder_infos.append(folder_info)

def is_new_folder(file_infos: list[FileInfo], current_info: FileInfo, ai_models_context: AiModelsContext, use_image_difference: bool = False) -> bool:
    """Heuristics to determine if a new folder should be started based on last and current file info
    
         1. Always start a new folder if no previous files exist
         2. Start a new folder if the month or year changed
         3. Start a new folder based on weighted difference score:
             - Time difference (highest weight)
             - GPS distance (medium weight)
             - Caption/image difference (lowest weight): either caption text similarity (default)
               or pre-computed image embedding similarity (when use_image_difference=True)
             3.1 If the current or the last file has only KEYWORD_GENERIC_VIDEO as a keyword, 
                 captions are not considered in the score, since videos often have no meaningful captions 
                 from the AI analysis and would otherwise cause too many folder splits."""

    if file_infos is None or len(file_infos) == 0:
        return True 

    last_info = file_infos[-1]

    assert last_info.date is not None  # Date is guaranteed to be set for all non-skipped files
    assert current_info.date is not None  # Date is guaranteed to be set for all non-skipped files

    if last_info.date.year != current_info.date.year or last_info.date.month != current_info.date.month:
        logger.debug(f"is_new_folder: month/year change, last={last_info.date}, current={current_info.date}), start_new_folder=True")  
        return True

    # Set weights for each criterion (must sum to 1.0)
    time_weight = FILE_DIFF_SCORE_TIME_WEIGHT
    location_weight = FILE_DIFF_SCORE_LOCATION_WEIGHT
    caption_weight = FILE_DIFF_SCORE_CAPTION_WEIGHT
    if last_info.lat is None or last_info.lon is None or current_info.lat is None or current_info.lon is None:
        # If GPS data is missing, use other weights
        time_weight = FILE_DIFF_SCORE_TIME_WEIGHT_NO_GPS
        location_weight = FILE_DIFF_SCORE_LOCATION_WEIGHT_NO_GPS
        caption_weight = FILE_DIFF_SCORE_CAPTION_WEIGHT_NO_GPS

    # Calculate time difference score (normalized by threshold, multiplied by weight)
    last_date, current_date = normalize_datetimes(last_info.date, current_info.date)
    time_delta_hours = abs((current_date - last_date).total_seconds()) / 3600
    time_score = min(time_delta_hours / FOLDER_MAX_TIME_DIFFERENCE_HOURS, 1.0) * time_weight

    # Calculate GPS distance score (normalized by threshold, multiplied by weight)
    location_distance = 0.0
    location_score = 0.0
    if last_info.lat is not None and last_info.lon is not None and current_info.lat is not None and current_info.lon is not None:
        last_geo = (last_info.lat, last_info.lon)
        current_geo = (current_info.lat, current_info.lon)
        location_distance = geodesic(last_geo, current_geo).meters
        location_score = min(location_distance / FOLDER_MAX_DISTANCE_METERS, 1.0) * location_weight
    else:
        logger.debug(f"is_new_folder: missing GPS data, last_info.lat={last_info.lat}, last_info.lon={last_info.lon}, current_info.lat={current_info.lat}, current_info.lon={current_info.lon}, skipping GPS distance check")
     
    # Calculate keyword difference score (multiplied by weight)
    caption_difference_score = 0.0
    caption_difference = 0.0
    image_difference = 0.0
    last_keywords = set(last_info.keywords)
    current_keywords = set(current_info.keywords)
    # Special rule: ignore keywords if either file only has KEYWORD_GENERIC_VIDEO
    if last_keywords != {KEYWORD_GENERIC_VIDEO} and current_keywords != {KEYWORD_GENERIC_VIDEO}:
        if last_info.embedding is not None and current_info.embedding is not None:
            image_difference = calculate_image_difference(last_info.embedding, current_info.embedding)
        caption_difference = calculate_caption_difference(last_info.caption, current_info.caption, ai_models_context)
        active_difference = image_difference if use_image_difference else caption_difference
        caption_difference_score = active_difference * caption_weight

    # Calculate total difference score (max: 1.0)
    difference_score = time_score + location_score + caption_difference_score
    
    # Start new folder if difference score >= threshold (roughly equivalent to "2 of 3" criteria)
    start_new_folder = difference_score >= FOLDER_MAX_DIFFERENCE_SCORE_THRESHOLD
    logger.debug(f"is_new_folder: decision, time_diff={time_delta_hours:.2f}h (sc={time_score:.2f}, wh={time_weight:.2f}), geo_diff={location_distance:.2f}m (sc={location_score:.2f}, wh={location_weight:.2f}), caption_diff={caption_difference:.2f}, image_diff={image_difference:.2f} (active={'image' if use_image_difference else 'caption'}, sc={caption_difference_score:.2f}, wh={caption_weight:.2f}), total_score={difference_score:.2f}, start_new_folder={start_new_folder}")  
    
    return start_new_folder

def normalize_datetimes(dt1, dt2):
    """Use the same timezone for both datetimes if only one has timezone info, so that they can be compared without errors."""
    if dt1.tzinfo is None and dt2.tzinfo is not None:
        dt1 = dt1.replace(tzinfo=dt2.tzinfo)
    elif dt2.tzinfo is None and dt1.tzinfo is not None:
        dt2 = dt2.replace(tzinfo=dt1.tzinfo)

    return dt1, dt2

def finish_last_folder_info(folder_infos: list[FolderInfo], file_infos: list[FileInfo], output_dir: Path, ai_models_context: AiModelsContext, folder_name_language: str = "german") -> bool:
    if len(folder_infos) == 0 or len(file_infos) == 0:
        return False
    
    folder_info = folder_infos[-1]
    file_info = file_infos[-1]

    folder_info.end_date = file_info.date

    # Aggregate places (use only top 1 most common)
    places_all_files = [f.address.name for f in folder_info.files if f.address and f.address.name]
    if file_info.address and file_info.address.name:
        places_all_files.append(file_info.address.name)
    top_places = select_top_words(places_all_files, top_n=1, context=ai_models_context)
    folder_info.place = top_places[0] if top_places else None

    # Aggregate German keywords (use only top FOLDER_NAME_KEYWORDS most common)
    keywords_all_files = [k for f in folder_info.files if f.keywords_german for k in f.keywords_german if k]    
    if file_info.keywords_german:
        keywords_all_files.extend([k for k in file_info.keywords_german if k])
    top_unique_keywords = select_top_words(keywords_all_files, top_n=FOLDER_NAME_KEYWORDS, context=ai_models_context)
    folder_info.keywords_german = set(top_unique_keywords)

    # Aggregate English keywords (use only top FOLDER_NAME_KEYWORDS most common)
    keywords_all_files_english = [k for f in folder_info.files if f.keywords for k in f.keywords if k]
    if file_info.keywords:
        keywords_all_files_english.extend([k for k in file_info.keywords if k])
    top_unique_keywords_english = select_top_words(keywords_all_files_english, top_n=FOLDER_NAME_KEYWORDS, context=ai_models_context)
    folder_info.keywords = set(top_unique_keywords_english)

    sanitize_folder_info(folder_info)
    create_folder_name(folder_info, output_dir, folder_name_language)

    logger.debug(f"finish_last_folder_info: folder_info.path.name={folder_info.path.name if folder_info.path else 'None'}") 

    return True

def sanitize_for_folder_name(text: str) -> str:
    """Removes forbidden characters from a string."""
    if not text:
        return ""
    return re.sub(FOLDER_FORBIDDEN_CHARS, "", text)

def sanitize_folder_info(folder_info):
    """Cleans up place and keywords in folder_info for folder names."""
    if folder_info.place:
        folder_info.place = sanitize_for_folder_name(folder_info.place)
    
    if folder_info.keywords_german:
        folder_info.keywords_german = [sanitize_for_folder_name(k) for k in folder_info.keywords_german]

    if folder_info.keywords:
        folder_info.keywords = [sanitize_for_folder_name(k) for k in folder_info.keywords]

def create_folder_name(folder_info, output_dir: Path, folder_name_language: str = "german"):
    assert folder_info.end_date is not None  # Folder end_date will not be None at this point 
    folder_name: str = f"{folder_info.start_date.strftime('%Y-%m-%dT%H%M')}"
    folder_name += f"{' - ' + folder_info.end_date.strftime('%dT%H%M') if folder_info.end_date.day != folder_info.start_date.day else ''}"
    folder_name += f"{' ' + folder_info.place if folder_info.place is not None else ''}"
    if folder_name_language == "english":
        folder_name += f"{' ' + ' '.join(sorted(folder_info.keywords, key=str.lower)) if folder_info.keywords else ''}"
    else:
        folder_name += f"{' ' + ' '.join(sorted(folder_info.keywords_german, key=str.lower)) if folder_info.keywords_german else ''}"
    
    folder_info.path = output_dir 
    folder_info.path /= str(folder_info.start_date.year)
    folder_info.path /= MONTH_NAMES[folder_info.start_date.month - 1]
    folder_info.path /= folder_name

