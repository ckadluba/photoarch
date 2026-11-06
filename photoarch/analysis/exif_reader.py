import logging
import shutil
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


# Initialization

logger = logging.getLogger(__name__)


# Code

def get_exif_data_from_file(path: Path) -> str | None:
    ensure_exiftool_available()

    try:
        result = subprocess.run(
            ["exiftool", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=True
        )
        return result.stdout

    except subprocess.TimeoutExpired as e:
        logger.error(f"ExifTool timeout after 10s for file: {path}")
        raise RuntimeError(f"ExifTool timeout for {path}") from e

    except subprocess.CalledProcessError as e:
        logger.error(
            f"ExifTool failed for file {path} with exit code {e.returncode}: "
            f"{(e.stderr or '').strip()}"
        )
        raise RuntimeError(f"ExifTool failed for {path}") from e

def ensure_exiftool_available():
    if not shutil.which("exiftool"):
        logger.error("ExifTool not found in PATH.")
        raise RuntimeError(
            "ExifTool is required but not installed. "
            "Install it from https://exiftool.org/"
        )

def get_date_from_exif_data(exif_data: str) -> datetime | None:
    """Extract date/time from EXIF data string.

    Invalid or placeholder timestamps (for example "0000:00:00 00:00:00")
    are skipped so that the next available date field can be used.
    """
    date_time_patterns = (
        (
            r"Date/Time Original\s*:\s*(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\+\d{2}:\d{2})",
            "%Y:%m:%d %H:%M:%S.%f%z",
        ),
        (
            r"Date/Time Original\s*:\s*(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2})",
            "%Y:%m:%d %H:%M:%S",
        ),
        (
            r"Create Date\s*:\s*(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2})",
            "%Y:%m:%d %H:%M:%S",
        ),
        # Fallback of last resort: use file modification date/time
        (
            r"File Modification Date/Time\s*:\s*(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}\+\d{2}:\d{2})",
            "%Y:%m:%d %H:%M:%S%z",
        ),
    )

    for pattern, date_format in date_time_patterns:
        match = re.search(pattern, exif_data)
        if not match:
            continue
        date_time = _parse_exif_datetime(match.group(1), date_format)
        if date_time is not None:
            return date_time

    return None


def _parse_exif_datetime(date_str: str, date_format: str) -> datetime | None:
    try:
        return datetime.strptime(date_str, date_format)
    except ValueError:
        logger.debug(
            "Ignoring invalid EXIF date/time value %r (expected format %r).",
            date_str,
            date_format,
        )
        return None

def get_camera_from_exif_data(exif_data: str) -> str | None:
    """Extract camera make from EXIF data string"""
    match_camera_model_name = re.search(r"Camera Model Name\s*:\s*(.*)", exif_data)
    if match_camera_model_name:
        return match_camera_model_name.group(1).strip()

    # Fallback to "Author" field
    match_author = re.search(r"Author\s*:\s*(.*)", exif_data)
    if match_author:
        return match_author.group(1).strip()

    # Fallback to "Android Model" field
    match_android_model = re.search(r"Android Model\s*:\s*(.*)", exif_data)
    if match_android_model:
        return match_android_model.group(1).strip()

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
