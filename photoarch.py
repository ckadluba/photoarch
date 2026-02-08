import subprocess
from collections import Counter
from dataclasses import dataclass, field

import requests
from dataclasses_json import dataclass_json, LetterCase, config
import shutil
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse
from PIL import Image
from deep_translator import GoogleTranslator
from geopy.distance import geodesic
import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration


# Constants and configuration

INPUT_DIR = Path("./input_photos")
OUTPUT_DIR = Path("./sorted_photos")
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

# Model paths
MODEL_NAME = "Salesforce/blip2-flan-t5-xl"
MODEL_CACHE_DIR = "./models"

# English Stopwords for keyword generation
STOPWORDS = {
    "a", "an", "and", "the", "of", "in", "on", "with", "for", "at", "by", "from",
    "to", "up", "down", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "can", "will", "just", "don", "should",
    "now", "it", "is", "are", "was", "were", "be", "been", "being", "have", "has", 
    "having", "do", "does", "did", "doing", "his", "her", "its", "they", "them", "this", 
    "that"
}

# German Stopwords for keyword generation
STOPWORDS_GERMAN = {
    "ein", "eine", "einer", "eines", "einem", "einen", "und", "der", "die", "das", 
    "von", "in", "an", "auf", "mit", "für", "bei", "durch", "aus", "zu", "nach", 
    "vor", "hinter", "über", "unter", "wieder", "weiter", "dann", "einmal", "hier",
    "dort", "da", "wann", "wo", "warum", "wie", "alle", "jeder", "jede", "jedes", 
    "beide", "einige", "wenige", "mehr", "meist", "meiste", "andere", "manche", 
    "solche", "kein", "keine", "nicht", "nur", "eigen", "selbst", "gleich", "so", 
    "als", "auch", "sehr", "kann", "wird", "werden", "soll", "sollte", "jetzt", 
    "es", "ist", "sind", "war", "waren", "sein", "gewesen", "haben", "hat", "hatte",
    "tun", "tut", "tat", "sein", "ihr", "ihre", "sein", "seine", "sie", "ihnen", 
    "dies", "diese", "dieser", "dieses", "dem", "den", "des", "im", "am", "zum", 
    "zur", "ins", "vom", "beim", "bei", "über", "unter", "um"
}

# OpenStreetMap Nominatim URL
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

FOLDER_MAX_DISTANCE_METERS = 1000  # Maximum distance in meters to consider photos in the same folder
FOLDER_MAX_TIME_DIFFERENCE_HOURS = 3  # Maximum time difference in hours to consider photos in the same folder
FOLDER_FORBIDDEN_CHARS = r'[:/\\\"\'<>&|,;]'

# Month names for folder naming
MONTH_NAMES = [
    "01 Jan", "02 Feb", "03 Mar", "04 Apr", "05 May", "06 Jun",
    "07 Jul", "08 Aug", "09 Sep", "10 Oct", "11 Nov", "12 Dec"
]

print("Loading BLIP-2 Model (CPU) …")
_blip_processor = Blip2Processor.from_pretrained(
    MODEL_NAME,
    cache_dir=MODEL_CACHE_DIR,
    use_fast=True
)

_blip_model = Blip2ForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    cache_dir=MODEL_CACHE_DIR,
    dtype=torch.float32
)
_blip_model.eval()


# Classes

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Address:
    name: Optional[str] = None
    amenity: Optional[str] = None
    house_number: Optional[str] = None
    road: Optional[str] = None
    neighbourhood: Optional[str] = None
    suburb: Optional[str] = None
    city_district: Optional[str] = None
    city: Optional[str] = None
    iso31662_lvl4: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> "Address":
        if not data:
            return Address()
        return Address(
            name=data.get("name"),
            amenity=data.get("amenity"),
            house_number=data.get("house_number"),
            road=data.get("road"),
            neighbourhood=data.get("neighbourhood"),
            suburb=data.get("suburb"),
            city_district=data.get("city_district"),
            city=data.get("city"),
            iso31662_lvl4=data.get("iso31662_lvl4"),
            postcode=data.get("postcode"),
            country=data.get("country"),
            country_code=data.get("country_code"),
        )

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class FileInfo:
    schema_version: int = 1

    path: Path = field(
        default=Path(""),
        metadata=config(
            encoder=str,
            decoder=Path
        )
    )

    date: Optional[datetime] = field(
        default=None,
        metadata=config(
            encoder=lambda d: d.isoformat(),
            decoder=datetime.fromisoformat,
            mm_field=None
        )
    )

    lat: Optional[float] = None
    lon: Optional[float] = None
    address: Optional[Address] = None

    keywords: list[str] = field(default_factory=list)
    keywords_german: list[str] = field(default_factory=list)
    caption: str = ""
    caption_german: str = ""

    skip: bool = field(
        default=False,
        metadata=config(exclude=lambda _: True)
    )

@dataclass
class FolderInfo:
    start_date: datetime
    end_date: Optional[datetime]
    place: Optional[str]
    keywords_german: set[str]
    files: list[FileInfo]
    path: Optional[Path] = None


# Helpers

def get_file_datetime(path: Path) -> datetime | None:
    """Get timestamp from filename or None if name does not match criteria"""
    match = re.match(r"PXL_(\d{8})_(\d{6})\d{0,3}", path.name)
    if match is None:
        return None
    else:
        date, time = match.groups()
        return datetime.strptime(date + time, "%Y%m%d%H%M%S")

def get_exif_data_from_file(path: Path) -> str | None:
    result = subprocess.run(
        ["exiftool", path],
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout if result.returncode == 0 else None

def get_date_from_exif_data(exif_data: str) -> datetime | None:
    """Extract date/time from EXIF data string"""
    match = re.search(r"Date/Time Original\s*:\s*(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2})", exif_data)
    if match is None:
        return None
    else:
        exif_date_str = match.group(1)
        return datetime.strptime(exif_date_str, "%Y:%m:%d %H:%M:%S")

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

def get_address_from_coords(lat, lon) -> Address | None:
    """Reverse Geocoding via OSM Nominatim"""
    if lat is None or lon is None:
        return None
    try:
        r = requests.get(
            NOMINATIM_URL,
            params={
                "lat": lat,
                "lon": lon,
                "format": "jsonv2",
                "zoom": 18,            # hohe Detailstufe
                "addressdetails": 1,
                "accept-language": "de,en"                
            },
            headers={
                "User-Agent": "photoarch/1.0 (contact: geoquest@gmail.com)"
            },
            timeout=30
        )
        r.raise_for_status()
        data = r.json()

        return read_address_from_api_response(data)

    except Exception as e:
        print(f"OSM API Error: {e}")
        return None

def read_address_from_api_response(data):
    
    address_dict = data.get("address")
    if address_dict:
        address = Address.from_dict(address_dict)
                    
        # Set a sensible name
        name = data.get("name")
        if name:
            address.name = name
        else:
            if address.road:
                address.name = f"{address.road} {address.house_number}".strip() if address.house_number else address.road
        if address.name is None:
            address.name = f"{address.city}" if address.city else ""
        address.name += f" {address.city}" if address.city else ""
        return address
    
    else:
        return None

def get_caption_for_image_file(file_path) -> str:
    try:
        img = Image.open(file_path).convert("RGB")

        inputs = _blip_processor(images=img, return_tensors="pt")
        with torch.no_grad():
            output = _blip_model.generate(
                **inputs,
                max_new_tokens=50,
                num_beams=3
            )
        return _blip_processor.decode(output[0], skip_special_tokens=True)

    except Exception as e:
        print(f"Error during AI analysis of {file_path.name}: {e}")
        return ""


def get_keywords_from_caption(caption, stopwords) -> list[str]:
    keywords_full = caption.split()
    keywords_no_stopwords = [k for k in keywords_full if k.lower() not in stopwords]
    keywords_unique = list(dict.fromkeys(keywords_no_stopwords)) 

    return keywords_unique

def translate_english_to_german(text: str) -> str:
    result: str = ""

    translator = GoogleTranslator(source="en", target="de")

    try:
        result = translator.translate(text)
    except Exception:
        result = ""

    return result

def analyze_file(file_path: Path) -> FileInfo:
    """Analyze image and return FileInfo"""

    # Use cache entry if available
    cache_file = CACHE_DIR / (file_path.stem + ".json")
    if cache_file.exists():
        print(f"Using cached {cache_file.name}.")
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
    
    # Get date from filename and validate
    date = get_file_datetime(file_path)
    if date is None:
        print(f"Filename does not match criteria {file_path.name}. Will skip.")
        file_info.skip = True
        return file_info
    else:
        print(f"Analyzing file {file_path.name}.")
        
        file_info.date = date

        exif_data = get_exif_data_from_file(file_path)
        if exif_data is None:
            print(f"Could not read EXIF data from {file_path.name}.")

        # Get date and time from EXIF if available (overrides filename date)
        date_time = get_date_from_exif_data(exif_data) if exif_data else None
        if date_time is None:
            print(f"Could not read date from EXIF data of {file_path.name}. Using filename date.")
        else:
            file_info.date = date_time
        
        # Get GPS from EXIF data
        lat, lon = None, None
        lat, lon = get_gps_from_exif_data(exif_data) if exif_data else (None, None)
        if lat is None or lon is None:
            print(f"Could not read GPS data from {file_path.name}.")
        file_info.lat = lat
        file_info.lon = lon
        
        # Get address from coordinates
        address = get_address_from_coords(file_info.lat, file_info.lon)
        if address is None:
            print(f"Could not read address from {file_path.name}.")
        file_info.address = address

        # BLIP AI analysis for keywords and caption
        if file_path.suffix.lower() in [".jpg"]:
            caption = get_caption_for_image_file(file_path)
            keywords = get_keywords_from_caption(caption, STOPWORDS)
            caption_german = translate_english_to_german(caption)
            keywords_german = get_keywords_from_caption(caption_german, STOPWORDS_GERMAN)
            file_info.caption = caption
            file_info.caption_german = caption_german
            file_info.keywords = keywords
            file_info.keywords_german = keywords_german
            
        elif file_path.suffix.lower() in [".mp4"]:
            file_info.keywords.append("Video")
            file_info.keywords_german.append("Video")

    # Save to cache
    cache_file.write_text(
        json.dumps(
            file_info.to_dict(),
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return file_info

def is_new_folder(file_infos: list[FileInfo], current_info: FileInfo) -> bool:
    """Heuristics to determine if a new folder should be started based on last and current file info
    
       1. Always start a new folder if no previous files exist
       2. Start new folder if month or year changed
       3. Start a new folder if at least two of the following criteria differ:
          3.1 GPS distance > FOLDER_MAX_DISTANCE_METERS
          3.2 time difference > FOLDER_MAX_TIME_DIFFERENCE_HOURS
          3.3 All keywords are different"""

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
    time_delta = abs((current_info.date - last_info.date).total_seconds()) / 3600
    if time_delta > FOLDER_MAX_TIME_DIFFERENCE_HOURS:
        time_diff = True

    # Check if keywords differ significantly (simple check)
    keyword_difference = False
    last_keywords = set(last_info.keywords)
    current_keywords = set(current_info.keywords)
    if last_keywords.isdisjoint(current_keywords):
        keyword_difference = True

    # Return true to start new folder if at least two criteria differ
    return sum([gps_distance, time_diff, keyword_difference]) >= 2

def create_folder_info(folder_infos: list[FolderInfo], start_date: datetime):
    folder_info = FolderInfo(
        start_date = start_date,
        end_date=None,
        place=None,
        keywords_german=set(),
        files=[]
    )
    folder_infos.append(folder_info)

def sanitize_for_folder_name(text: str) -> str:
    """Entfernt verbotene Zeichen aus einem String."""
    if not text:
        return ""
    return re.sub(FOLDER_FORBIDDEN_CHARS, "", text)

def sanitize_folder_info(folder_info):
    """Bereinigt place und keywords im folder_info für Ordnernamen."""
    if folder_info.place:
        folder_info.place = sanitize_for_folder_name(folder_info.place)
    
    if folder_info.keywords_german:
        folder_info.keywords_german = [sanitize_for_folder_name(k) for k in folder_info.keywords_german]

def create_folder_name(folder_info, output_dir: Path):
    assert folder_info.end_date is not None  # Folder end_date will not be None at this point 
    folder_name: str = f"{folder_info.start_date.strftime('%Y-%m-%dT%H%M')}"
    folder_name += f"{' - ' + folder_info.end_date.strftime('%dT%H%M') if folder_info.end_date.day != folder_info.start_date.day else ''}"
    folder_name += f"{' ' + folder_info.place if folder_info.place is not None else ''}"
    folder_name += f"{' ' + ' '.join(folder_info.keywords_german) if folder_info.keywords_german else ''}"

    folder_info.path = output_dir 
    folder_info.path /= str(folder_info.start_date.year)
    folder_info.path /= MONTH_NAMES[folder_info.start_date.month - 1]
    folder_info.path /= folder_name

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


# Begin of main script

def main(input_dir: str, output_dir: str):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    print("\n")
    print("Analyzing files …")
    files = sorted(input_path.iterdir(), key=lambda f: f.name)

    file_infos: list[FileInfo] = []
    folder_infos: list[FolderInfo] = []
    for file_info in files:
        
        # Analyze file
        file_info = analyze_file(file_info)
        if file_info.skip:
            continue # Skip files that did not match criteria
        
        # Create new and finish old folder if file is different enough
        if is_new_folder(file_infos, file_info):
            finish_last_folder_info(folder_infos, file_infos, output_path)
            assert file_info.date is not None  # Date is guaranteed to be set for non-skipped files
            create_folder_info(folder_infos, file_info.date)
                
        file_infos.append(file_info)
        folder_infos[-1].files.append(file_info)
        
    # Finish last folder
    finish_last_folder_info(folder_infos, file_infos, output_path)

    print("\n")
    print("\nCopying files …")
        
    for folder_info in folder_infos:
        assert folder_info.path is not None  # Path is guaranteed to be set for all folders at this point
        print(f"- {folder_info.path.name} [{len(folder_info.files)}]")
        folder_meta_path = folder_info.path / "metadata"
        folder_meta_path.mkdir(parents=True, exist_ok=True)
        for file_info in folder_info.files:
            print(f"   - {file_info.path}")
            photo_file_src_path = input_path / file_info.path
            photo_file_dst_path = folder_info.path / file_info.path
            shutil.copy(photo_file_src_path, photo_file_dst_path)
            file_meta_name = file_info.path.stem + ".json"
            meta_file_src_path = CACHE_DIR / file_meta_name
            meta_file_dst_path = folder_meta_path / file_meta_name
            shutil.copy(meta_file_src_path, meta_file_dst_path)

    print("Finished.")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Sort and organize photos by date, location, and AI-generated content.")
    parser.add_argument("--input", type=str, default=str(INPUT_DIR), help=f"Input directory containing photos (default: {INPUT_DIR})")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR), help=f"Output directory for sorted photos (default: {OUTPUT_DIR})")
    args = parser.parse_args()

    main(args.input, args.output)
