from collections import Counter
import re
from pathlib import Path
from geopy.distance import geodesic

from ..config import *
from ..models import *


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
         3. Start a new folder if at least two of the following criteria differ:
             3.1 GPS distance > FOLDER_MAX_DISTANCE_METERS
             3.2 Time difference > FOLDER_MAX_TIME_DIFFERENCE_HOURS
             3.3 All keywords are different
             3.3.1 If the current or the last file has only KEYWORD_GENERIC_VIDEO as a keyword, 
                   consider keywords as not different, since videos often have no meaningful keywords 
                   from the AI analysis and would otherwise cause too many folder splits."""

    if file_infos is None or len(file_infos) == 0:
        return True 

    last_info = file_infos[-1]

    assert last_info.date is not None  # Date is guaranteed to be set for all non-skipped files
    assert current_info.date is not None  # Date is guaranteed to be set for all non

    if last_info.date.year != current_info.date.year or last_info.date.month != current_info.date.month:
        return True

    # Check GPS distance
    gps_distance = False
    last_geo = (last_info.lat, last_info.lon)
    current_geo = (current_info.lat, current_info.lon)
    distance = geodesic(last_geo, current_geo).meters
    if distance > FOLDER_MAX_DISTANCE_METERS:  # mehr als 1000 Meter
        gps_distance = True
        
    # Check time difference
    time_diff = False
    last_date, current_date = normalize_datetimes(last_info.date, current_info.date)
    time_delta = abs((current_date - last_date).total_seconds()) / 3600
    if time_delta > FOLDER_MAX_TIME_DIFFERENCE_HOURS:
        time_diff = True

    # Check if keywords differ significantly (simple check)
    keyword_difference = False
    last_keywords = set(last_info.keywords)
    current_keywords = set(current_info.keywords)
    if (last_keywords != {KEYWORD_GENERIC_VIDEO} and current_keywords != {KEYWORD_GENERIC_VIDEO}) \
        and last_keywords.isdisjoint(current_keywords):
        keyword_difference = True

    # Return true to start new folder if at least two criteria differ
    return sum([gps_distance, time_diff, keyword_difference]) >= 2

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

