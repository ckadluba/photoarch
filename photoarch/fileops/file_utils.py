from pathlib import Path
from datetime import datetime

from ..config import *


def get_file_modified_datetime(path: Path) -> datetime | None:
    """Get timestamp from file modified date or None if not available"""
    try:
        timestamp = path.stat().st_mtime
        return datetime.fromtimestamp(timestamp)
    except Exception:
        print(f"Could not read modified date for {path.name}.")
        return None

def does_filename_meet_criteria(file_path: Path) -> bool:
    """Check if filename meets criteria to be included in folders"""
    return file_path.suffix.lower() in IMAGE_FILE_EXTENSIONS.union(VIDEO_FILE_EXTENSIONS)
