from collections import Counter
import logging
import re
from pathlib import Path
from geopy.distance import geodesic

from ..config import *
from ..models import *
from ..services.semantic_similarity import keywords_are_different


# Initialization

logger = logging.getLogger(__name__)


# Code

def create_folder_info(folder_infos: list[FolderInfo], start_date: datetime):
    folder_info = FolderInfo(
        start_date = start_date,
        end_date=None,
        place=None,
        keywords_german=set(),
        files=[]
    )
    folder_infos.append(folder_info)

def is_new_folder(file_infos: list[FileInfo], current_info: FileInfo) -> bool:
    """Heuristics to determine if a new folder should be started based on last and current file info
    
         1. Always start a new folder if no previous files exist
         2. Start a new folder if the month or year changed
         3. Start a new folder based on weighted difference score:
             - Time difference (highest weight)
             - GPS distance (medium weight)
             - Keyword difference (lowest weight)
             3.1 If the current or the last file has only KEYWORD_GENERIC_VIDEO as a keyword, 
                 keywords are not considered in the score, since videos often have no meaningful keywords 
                 from the AI analysis and would otherwise cause too many folder splits."""

    if file_infos is None or len(file_infos) == 0:
        return True 

    last_info = file_infos[-1]

    assert last_info.date is not None  # Date is guaranteed to be set for all non-skipped files
    assert current_info.date is not None  # Date is guaranteed to be set for all non-skipped files

    if last_info.date.year != current_info.date.year or last_info.date.month != current_info.date.month:
        logger.debug(f"is_new_folder: month/year change, last={last_info.date}, current={current_info.date}), start_new_folder=True")  
        return True

    # Calculate time difference score (normalized by threshold, weight: 0.4)
    last_date, current_date = normalize_datetimes(last_info.date, current_info.date)
    time_delta_hours = abs((current_date - last_date).total_seconds()) / 3600
    time_score = min(time_delta_hours / FOLDER_MAX_TIME_DIFFERENCE_HOURS, 1.0) * 0.4

    # Calculate GPS distance score (normalized by threshold, weight: 0.4)
    location_score = 0.0
    location_distance = 0.0
    if last_info.lat is not None and last_info.lon is not None and current_info.lat is not None and current_info.lon is not None:
        last_geo = (last_info.lat, last_info.lon)
        current_geo = (current_info.lat, current_info.lon)
        location_distance = geodesic(last_geo, current_geo).meters
        location_score = min(location_distance / FOLDER_MAX_DISTANCE_METERS, 1.0) * 0.4
    else:
        logger.debug(f"is_new_folder: missing GPS data, last_info.lat={last_info.lat}, last_info.lon={last_info.lon}, current_info.lat={current_info.lat}, current_info.lon={current_info.lon}, skipping GPS distance check")
     
    # Calculate keyword difference score (lowest weight: 0.3)
    keywords_score = 0.0
    last_keywords = set(last_info.keywords)
    current_keywords = set(current_info.keywords)
    # Special rule: ignore keywords if either file only has KEYWORD_GENERIC_VIDEO
    if last_keywords != {KEYWORD_GENERIC_VIDEO} and current_keywords != {KEYWORD_GENERIC_VIDEO}:
        keywords_score = keywords_are_different(last_info.caption, current_info.caption) * 0.3

    # Calculate total difference score (max: 1.0)
    difference_score = time_score + location_score + keywords_score
    
    # Start new folder if difference score >= 0.6 (roughly equivalent to "2 of 3" criteria)
    start_new_folder = difference_score >= 0.6
    logger.debug(f"is_new_folder: decision, time_delta={time_delta_hours:.2f}h (score={time_score:.2f}), location_distance={location_distance:.2f}m (score={location_score:.2f}), keyword_difference (score={keywords_score:.2f}), total_difference_score={difference_score:.2f}, start_new_folder={start_new_folder}")  

    return start_new_folder

def normalize_datetimes(dt1, dt2):
    """Use the same timezone for both datetimes if only one has timezone info, so that they can be compared without errors."""
    if dt1.tzinfo is None and dt2.tzinfo is not None:
        dt1 = dt1.replace(tzinfo=dt2.tzinfo)
    elif dt2.tzinfo is None and dt1.tzinfo is not None:
        dt2 = dt2.replace(tzinfo=dt1.tzinfo)

    return dt1, dt2

def finish_last_folder_info(folder_infos: list[FolderInfo], file_infos: list[FileInfo], output_dir: Path) -> bool:
    if len(folder_infos) == 0 or len(file_infos) == 0:
        return False
    
    folder_info = folder_infos[-1]
    file_info = file_infos[-1]

    folder_info.end_date = file_info.date

    # Aggregate places (use only top 1 most common)
    place_counter = Counter()
    for f in folder_info.files:
        if f.address and f.address.name:
            place_counter.update([f.address.name])
    if file_info.address and file_info.address.name:
        place_counter.update([file_info.address.name])
    if place_counter:
        folder_info.place = place_counter.most_common(1)[0][0]

    # Aggregate keywords (use only top 7 most common)
    keyword_counter = Counter()
    for f in folder_info.files:
        if f.keywords_german:
            keyword_counter.update(k for k in f.keywords_german if k)

    if file_info.keywords_german:
        keyword_counter.update(k for k in file_info.keywords_german if k)
    folder_info.keywords_german = {k for k, _ in keyword_counter.most_common(7)}

    sanitize_folder_info(folder_info)
    create_folder_name(folder_info, output_dir)

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

def create_folder_name(folder_info, output_dir: Path):
    assert folder_info.end_date is not None  # Folder end_date will not be None at this point 
    folder_name: str = f"{folder_info.start_date.strftime('%Y-%m-%dT%H%M')}"
    folder_name += f"{' - ' + folder_info.end_date.strftime('%dT%H%M') if folder_info.end_date.day != folder_info.start_date.day else ''}"
    folder_name += f"{' ' + folder_info.place if folder_info.place is not None else ''}"
    folder_name += f"{' ' + ' '.join(sorted(folder_info.keywords_german, key=str.lower)) if folder_info.keywords_german else ''}"
    
    folder_info.path = output_dir 
    folder_info.path /= str(folder_info.start_date.year)
    folder_info.path /= MONTH_NAMES[folder_info.start_date.month - 1]
    folder_info.path /= folder_name

