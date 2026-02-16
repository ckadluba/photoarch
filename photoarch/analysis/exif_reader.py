import logging
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..config import *
from ..models import *


# Initialization

logger = logging.getLogger(__name__)


# Code

def get_exif_data_from_file(path: Path) -> str | None:
    ensure_exiftool_available()

    result = subprocess.run(
        ["exiftool", path],
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout if result.returncode == 0 else None

def ensure_exiftool_available():
    if not shutil.which("exiftool"):
        logger.error("ExifTool not found in PATH.")
        raise RuntimeError(
            "ExifTool is required but not installed. "
            "Install it from https://exiftool.org/"
        )

def get_date_from_exif_data(exif_data: str) -> datetime | None:
    """Extract date/time from EXIF data string"""
    match_date_time_original = re.search(r"Date/Time Original\s*:\s*(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\+\d{2}:\d{2})", exif_data)
    if match_date_time_original:
        date_str = match_date_time_original.group(1)
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S.%f%z")

    match_file_modification_date_time = re.search(r"File Modification Date/Time\s*:\s*(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}\+\d{2}:\d{2})", exif_data)
    if match_file_modification_date_time:
        date_str = match_file_modification_date_time.group(1)
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S%z")
    
    return None

def get_camera_from_exif_data(exif_data: str) -> str | None:
    """Extract camera make from EXIF data string"""
    match_camera_model_name = re.search(r"Camera Model Name\s*:\s*(.*)", exif_data)
    if match_camera_model_name:
        return match_camera_model_name.group(1).strip()

    # Fallback to "Author" field if "Camera Model Name" is not available (some videos have this instead)
    match_author = re.search(r"Author\s*:\s*(.*)", exif_data)
    if match_author:
        return match_author.group(1).strip()

    return None

def get_gps_from_exif_data(exif_data: str) -> tuple[Optional[float], Optional[float]]:

    lat_match = re.search(
        r"GPS Latitude\s*:\s*(\d+)\s*deg\s*(\d+)'[\s]*(\d+\.?\d*)\"\s*([NS])",
        exif_data
    )

    lon_match = re.search(
        r"GPS Longitude\s*:\s*(\d+)\s*deg\s*(\d+)'[\s]*(\d+\.?\d*)\"\s*([EW])",
        exif_data
    )

    if not lat_match or not lon_match:
        return None, None

    lat = dms_to_decimal(lat_match.groups()[:3], lat_match.group(4))
    lon = dms_to_decimal(lon_match.groups()[:3], lon_match.group(4))

    return lat, lon

def dms_to_decimal(dms, direction) -> float:
    degrees, minutes, seconds = map(float, dms)
    decimal = degrees + minutes / 60 + seconds / 3600
    if direction in ["S", "W"]:
        decimal *= -1
    return decimal
