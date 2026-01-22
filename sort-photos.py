import subprocess
#from calendar import month
from collections import Counter
from dataclasses import dataclass, asdict
import shutil
from os import path
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse
from PIL import Image
from deep_translator import GoogleTranslator
import piexif
from geopy.distance import geodesic
#from sentence_transformers import SentenceTransformer
from transformers import BlipProcessor, BlipForConditionalGeneration
import requests


# Constants and configuration

INPUT_DIR = Path("input_photos")
OUTPUT_DIR = Path("sorted_photos")
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

BLIP_MODEL_PATH = Path("models/blip-image-captioning-base")

# Englische Stopwords für Keywords
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

TRANSLATION_CACHE_FILE = Path(CACHE_DIR / "translation_cache.json")

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

# In-Memory translation cache
_translation_cache: dict[str, str] = {}


# Classes

@dataclass
class Address:
    name: Optional[str] = None
    amenity: Optional[str] = None
    houseNumber: Optional[str] = None
    road: Optional[str] = None
    neighbourhood: Optional[str] = None
    suburb: Optional[str] = None
    cityDistrict: Optional[str] = None
    city: Optional[str] = None
    Iso31662Lvl4: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    countryCode: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Address":
        if not data:
            return Address()
        return Address(
            name=data.get("name"),
            amenity=data.get("amenity"),
            houseNumber=data.get("houseNumber"),
            road=data.get("road"),
            neighbourhood=data.get("neighbourhood"),
            suburb=data.get("suburb"),
            cityDistrict=data.get("cityDistrict"),
            city=data.get("city"),
            Iso31662Lvl4=data.get("Iso31662Lvl4"),
            postcode=data.get("postcode"),
            country=data.get("country"),
            countryCode=data.get("countryCode"),
        )

@dataclass
class FileInfo:
    path: Path
    date: Optional[datetime]
    lat: Optional[float]
    lon: Optional[float]
    address: Address
    keywords: list[str]
    keywordsGerman: list[str]
    caption: str
    skip: bool = False

    def to_dict(self) -> dict:
        data = asdict(self)
        data["path"] = str(self.path)
        data["date"] = self.date.isoformat() if self.date else None
        data["address"] = self.address.to_dict() if self.address else None
        return data

    @staticmethod
    def from_dict(data: dict) -> "FileInfo":
        return FileInfo(
            path=Path(data["path"]),
            date=datetime.fromisoformat(data["date"]) if data["date"] else None,
            lat=data.get("lat"),
            lon=data.get("lon"),
            address=Address.from_dict(data.get("address")),
            keywords=data.get("keywords", []),
            keywordsGerman=data.get("keywordsGerman", []),
            caption=data.get("caption", ""),
            skip=data.get("skip", False),
        )

@dataclass
class FolderInfo:
    start_date: datetime
    end_date: datetime
    place: str
    keywordsGerman: set[str]
    files: list[FileInfo]


# Helpers

def get_file_datetime(path: Path):
    """Get timestamp from filename or None if name does not match criteria"""
    match = re.match(r"PXL_(\d{8})_(\d{6})\d{0,3}", path.name)
    if match is None:
        return None
    else:
        date, time = match.groups()
        return datetime.strptime(date + time, "%Y%m%d%H%M%S")

def get_exif_gps(img_path):
    """Read GPS coordinates from image EXIF data using piexif"""
    try:
        img = Image.open(img_path)
        if "exif" not in img.info:
            return None, None
        exif_dict = piexif.load(img.info["exif"])
        gps_ifd = exif_dict.get("GPS", {})

        if not gps_ifd:
            return None, None

        def rational_to_deg(r):
            # piexif speichert als ((num, den), (num, den), (num, den))
            if isinstance(r, (list, tuple)) and len(r) == 3:
                deg = r[0][0]/r[0][1] + r[1][0]/r[1][1]/60 + r[2][0]/r[2][1]/3600
                return deg
            return None

        lat_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode()
        lon_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode()
        lat = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
        lon = gps_ifd.get(piexif.GPSIFD.GPSLongitude)

        if lat and lon:
            lat = rational_to_deg(lat)
            lon = rational_to_deg(lon)
            if lat_ref == 'S':
                lat = -lat
            if lon_ref == 'W':
                lon = -lon
            return lat, lon
        return None, None
    except Exception as e:
        print(f"EXIF GPS Fehler: {e}")
        return None, None

def dms_to_decimal(dms, direction):
    degrees, minutes, seconds = map(float, dms)
    decimal = degrees + minutes / 60 + seconds / 3600
    if direction in ["S", "W"]:
        decimal *= -1
    return decimal

def get_gps_from_video(path):
    result = subprocess.run(
        ["exiftool", path],
        stdout=subprocess.PIPE,
        text=True
    ).stdout

    lat_match = re.search(
        r"GPS Latitude\s*:\s*(\d+)\s*deg\s*(\d+)'[\s]*(\d+\.?\d*)\"\s*([NS])",
        result
    )

    lon_match = re.search(
        r"GPS Longitude\s*:\s*(\d+)\s*deg\s*(\d+)'[\s]*(\d+\.?\d*)\"\s*([EW])",
        result
    )

    if not lat_match or not lon_match:
        return None

    lat = dms_to_decimal(lat_match.groups()[:3], lat_match.group(4))
    lon = dms_to_decimal(lon_match.groups()[:3], lon_match.group(4))

    return lat, lon

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
                "addressdetails": 1
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
                address.name = f"{address.road} {address.houseNumber}".strip() if address.houseNumber else address.road
        address.name += f" {address.city}" if address.city else ""
        return address
    
    else:
        return None

def get_keywords_for_image_file(file_path) -> tuple[str, list[str]]:
    try:
        img = Image.open(file_path).convert("RGB")
        inputs = blip_processor(images=img, return_tensors="pt")
        out = blip_model.generate(**inputs)
        caption = blip_processor.decode(out[0], skip_special_tokens=True)
                
        # very simple keyword extraction
        keywords_full = caption.split()
        keywords_filtered = [k for k in keywords_full if k.lower() not in STOPWORDS]
        keywords: list[str] = [k.lower() for k in keywords_filtered ]
        
        return caption, keywords

    except Exception as e:
        print(f"Error during AI analysis of {file_path.name}: {e}")

def translate_keywords_to_german(keywords: list[str]) -> list[str]:
    if not keywords:
        return []

    translator = GoogleTranslator(source="en", target="de")
    result = []

    for kw in keywords:
        kw = kw.strip().lower()
        if not kw:
            continue

        if kw in _translation_cache:
            result.append(_translation_cache[kw])
            continue

        try:
            de = translator.translate(kw)
        except Exception:
            de = kw

        if de:
            de = de.capitalize()

            _translation_cache[kw] = de
            save_translation_cache()

            result.append(de)

    # Doppelte entfernen, Reihenfolge behalten
    return list(dict.fromkeys(result))

def analyze_file(file_path: Path) -> FileInfo:
    """Analyze image and return FileInfo"""

    # Use cache entry if available
    cache_file = CACHE_DIR / (file_path.stem + ".json")
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return FileInfo.from_dict(json.load(f))
    
    # Create new FileInfo
    file_info = FileInfo(
        path=Path(file_path.name),
        date=None,
        lat=None,
        lon=None,
        address=None,
        keywords=[],
        keywordsGerman=[],
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

        # Get GPS from EXIF
        if file_path.suffix.lower() in [".jpg"]:
            lat, lon = get_exif_gps(file_path)
        elif file_path.suffix.lower() in [".mp4"]:
            lat, lon = get_gps_from_video(file_path)
        if lat is None or lon is None:
            print(f"Could not read GPS data from {file_path.name}.")
        file_info.lat = lat
        file_info.lon = lon
        
        # Get address from coordinates
        address = get_address_from_coords(file_info.lat, file_info.lon)
        file_info.address = address

        # BLIP AI analysis for keywords and caption
        if file_path.suffix.lower() in [".jpg"]:
            caption, keywords = get_keywords_for_image_file(file_path)
            file_info.caption = caption
            file_info.keywords = keywords
            
            file_info.keywordsGerman = translate_keywords_to_german(keywords)
            
        elif file_path.suffix.lower() in [".mp4"]:
            file_info.keywords.append("Video")
            file_info.keywordsGerman.append("Video")

    # Save to cache
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(file_info.to_dict(), f, ensure_ascii=False)

    return file_info

def is_new_folder(file_infos: list[FileInfo], current_info: FileInfo) -> bool:
    """Heuristics to determine if a new folder should be started based on last and current file info
    
       1. Always start a new folder if no previous files exist
       2. Start new folder if month or year changed
       3. Start a new folder if at least two of the following criteria differ:
          3.1 GPS distance > threshold
          3.2 POI changed if available
          3.3 time difference > threshold
          3.4 All keywords are different"""

    if file_infos is None or len(file_infos) == 0:
        #print("Start new folder. First image.")
        return True 

    last_info = file_infos[-1]

    # New folder if month or year changed
    if last_info.date.year != current_info.date.year or last_info.date.month != current_info.date.month:
        #print("Start new folder. Year/month changed, last: {last_info.date}, current: {current_info.date}.")
        return True

    # Check GPS distance
    gps_distance = False
    last_geo = (last_info.lat, last_info.lon)
    current_geo = (current_info.lat, current_info.lon)
    distance = geodesic(last_geo, current_geo).meters
    if distance > FOLDER_MAX_DISTANCE_METERS:  # mehr als 1000 Meter
        #print(f"Start new folder. Distance changed, last_geo: {last_geo}, current_geo: {current_geo}, distance: {distance}.")
        gps_distance = True
        
    # Check time difference
    time_diff = False
    time_delta = abs((current_info.date - last_info.date).total_seconds()) / 3600
    if time_delta > FOLDER_MAX_TIME_DIFFERENCE_HOURS:
        #print(f"Start new folder. Time difference more than {FOLDER_MAX_TIME_DIFFERENCE_HOURS} hours, last: {last_info.date}, current: {current_info.date}, diff sec: {time_diff}.")
        time_diff = True

    # Check if keywords differ significantly (simple check)
    keyword_difference = False
    last_keywords = set(last_info.keywords)
    current_keywords = set(current_info.keywords)
    if last_keywords.isdisjoint(current_keywords):
        #print(f"Start new folder. Keywords differ significantly, last={last_keywords}, current={current_keywords}")
        keyword_difference = True

    # Return true to start new folder if at least two criteria differ
    return sum([gps_distance, time_diff, keyword_difference]) >= 2

def create_folder_info(folder_infos: list[FolderInfo], start_date: datetime):
    folder_info = FolderInfo(
        start_date = start_date,
        end_date=None,
        place=None,
        keywordsGerman=set(),
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
    
    if folder_info.keywordsGerman:
        folder_info.keywordsGerman = [sanitize_for_folder_name(k) for k in folder_info.keywordsGerman]

def finish_last_folder_info(folder_infos: list[FolderInfo], file_infos: list[FileInfo]) -> bool:
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
        if f.keywordsGerman:
            keyword_counter.update(k for k in f.keywordsGerman if k)

    if file_info.keywordsGerman:
        keyword_counter.update(k for k in file_info.keywordsGerman if k)
    folder_info.keywordsGerman = [k for k, _ in keyword_counter.most_common(7)]

    # Sanitize for folder name
    sanitize_folder_info(folder_info)

    # Create folder name and destination path
    folder_name: str = f"{folder_info.start_date.strftime('%Y-%m-%d %H-%M')}"
    folder_name += f"{' - ' + folder_info.end_date.strftime('%d') if folder_info.end_date.day != folder_info.start_date.day else ''}"
    folder_name += f"{' ' + folder_info.place if folder_info.place is not None else ''}"
    folder_name += f"{' ' + ' '.join(folder_info.keywordsGerman) if folder_info.keywordsGerman else ''}"

    folder_info.path = output_dir 
    folder_info.path /= str(folder_info.start_date.year)
    folder_info.path /= MONTH_NAMES[folder_info.start_date.month - 1]
    folder_info.path /= folder_name

    return True

def load_translation_cache(TRANSLATION_CACHE_FILE, _translation_cache):
    print("Load language translation cache …")
    if TRANSLATION_CACHE_FILE.exists():
        _translation_cache.update(json.loads(TRANSLATION_CACHE_FILE.read_text(encoding="utf-8")))

def save_translation_cache():
    TRANSLATION_CACHE_FILE.write_text(
        json.dumps(_translation_cache, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# Begin of main script

# Parse command line arguments
parser = argparse.ArgumentParser(description="Sort and organize photos by date, location, and AI-generated content.")
parser.add_argument("--input", type=str, default=str(INPUT_DIR), help=f"Input directory containing photos (default: {INPUT_DIR})")
parser.add_argument("--output", type=str, default=str(OUTPUT_DIR), help=f"Output directory for sorted photos (default: {OUTPUT_DIR})")
args = parser.parse_args()

input_dir = Path(args.input)
output_dir = Path(args.output)

# Load BLIP models
print("Load BLIP image AI model …")
blip_processor = BlipProcessor.from_pretrained(BLIP_MODEL_PATH)
blip_model = BlipForConditionalGeneration.from_pretrained(BLIP_MODEL_PATH)

load_translation_cache(TRANSLATION_CACHE_FILE, _translation_cache)

print("\n")
print("Analyzing files …")
files = sorted(input_dir.iterdir(), key=lambda f: f.name)

file_infos: list[FileInfo] = []
folder_infos: list[FolderInfo] = []
for file_info in files:
    
    # Analyze file
    file_info = analyze_file(file_info)
    if file_info.skip:
        continue # Skip files that did not match criteria
    
    # Create new and finish old folder if file is different enough
    if is_new_folder(file_infos, file_info):
        finish_last_folder_info(folder_infos, file_infos)
        create_folder_info(folder_infos, file_info.date)
            
    file_infos.append(file_info)
    folder_infos[-1].files.append(file_info)
    
# Finish last folder
finish_last_folder_info(folder_infos, file_infos)

    
print("\n")
print("\nCopying files …")
    
for folder_info in folder_infos:
    print(f"- {folder_info.path.name} [{len(folder_info.files)}]")
    folder_meta_path = folder_info.path / "metadata"
    folder_meta_path.mkdir(parents=True, exist_ok=True)
    for file_info in folder_info.files:
        print(f"   - {file_info.path}")
        shutil.copy(input_dir / file_info.path, folder_info.path / file_info.path)
        file_meta_name = file_info.path.stem + ".json"
        shutil.copy(CACHE_DIR / file_meta_name, folder_meta_path / file_meta_name)

print("Finished.")