# Photo Archive Organizer

## Purpose

This Python script automatically organizes and archives photos and videos taken with a Google Pixel phone (or similar devices). It processes images from a flat input folder and intelligently sorts them into a structured output directory based on date, location, and content.

### Key Features

- **AI-Powered Content Analysis**: Uses the BLIP-2 (Bootstrapping Language-Image Pre-training) model to generate captions and keywords for images used locally without cloud access. AI processing happens offline. The model is automatically downloaded on first execution of the script.
- **Geolocation Processing**: Extracts GPS coordinates from EXIF data and performs reverse geocoding to determine locations
- **Intelligent Grouping**: Automatically groups photos into folders based on:
  - Temporal proximity (time between photos)
  - Geographic distance (GPS coordinates)
  - Content similarity (AI-generated keywords)
- **Metadata Preservation**: Creates JSON metadata files for each photo with extracted information
- **Multi-language Support**: Translates AI-generated keywords to German
- **Structured Output**: Organizes photos in a hierarchical `YYYY/Month/Date-Location-Keywords` folder structure

The script is designed for photographers who want to automatically organize large collections of photos into meaningful groups without manual sorting.

## Disclaimer

This software is provided under the **Apache License 2.0** and is offered **AS IS**, without warranty of any kind, express or implied.

The authors and contributors accept **NO RESPONSIBILITY** for:
- Data loss or corruption
- Incorrect metadata extraction
- API rate limits or failures (OpenStreetMap Nominatim, Google Translate)
- Unexpected behavior or results

**Important**: Always maintain backups of your original photos before processing them with this script. Test with a small subset of images first to ensure the results meet your expectations.

## Prerequisites

### 1. ExifTool

Download and install ExifTool for video metadata extraction:

- Download from: [https://exiftool.org/](https://exiftool.org/)
- Windows: Place `exiftool.exe` in the project root directory or add to PATH
- Linux/Mac: Install via package manager (e.g., `apt install exiftool` or `brew install exiftool`)

### 2. Python Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Directory Structure

Ensure the following directories exist (they will be created automatically if missing):

- `input_photos/` - Place your photos here (or specify alternative path using `--input` command line parameter)
- `sorted_photos/` - Output directory (will be created)
- `.cache/` - Temporary cache for analysis results

## Usage

### Basic Usage

Place your photos in the `input_photos/` directory and run:

```bash
python sort-photos.py
```

### Custom Input/Output Directories

Specify custom input and output directories:

```bash
python sort-photos.py --input /path/to/photos --output /path/to/sorted
```

### Command-Line Arguments

- `--input` - Input directory containing photos (default: `input_photos`)
- `--output` - Output directory for sorted photos (default: `sorted_photos`)

### Output Structure

The script creates a hierarchical folder structure:

```
sorted_photos/
├── 2025/
│   ├── 01 Jan/
│   │   ├── 2025-01-15T1430 - 15T1645 Berlin Brandenburger Tor Tourist Landmark/
│   │   │   ├── metadata/
│   │   │   │   ├── PXL_20250115_143052.json
│   │   │   │   └── PXL_20250115_164532.json
│   │   │   ├── PXL_20250115_143052.jpg
│   │   │   └── PXL_20250115_164532.jpg
│   │   └── 2025-01-20T0915 Munich Park Fountain/
│   │       ├── metadata/
│   │       │   └── PXL_20250120_091523.json
│   │       │   └── PXL_20250120_101422.json
│   │       └── PXL_20250120_091523.jpg
│   │       └── PXL_20250120_101422.mp4
│   └── 02 Feb/
│       └── 2025-02-03T1200 Hamburg Harbor/
│           ├── metadata/
│           │   └── PXL_20250203_120045.json
│           └── PXL_20250203_120045.jpg
```

### Metadata Files

Each photo has an accompanying JSON metadata file containing:

```json
{
  "path": "PXL_20250115_143052.jpg",
  "date": "2025-01-15T14:30:52",
  "lat": 52.516275,
  "lon": 13.377704,
  "address": {
    "name": "Brandenburger Tor Berlin",
    "amenity": "landmark",
    "road": "Pariser Platz",
    "city": "Berlin",
    "postcode": "10117",
    "country": "Germany",
    "countryCode": "de"
  },
  "keywords": ["gate", "landmark", "building", "sky"],
  "keywordsGerman": ["Tor", "Sehenswürdigkeit", "Gittertäben", "Himmel"],
  "caption": "a large gate with columns and a sky background",
  "captionGerman": "ein großes Tor mit Gittertäben und Himmel",
  "skip": false
}
```

### Processing Flow

1. **File Analysis**: Each photo is analyzed for:
   - Timestamp (from filename)
   - GPS coordinates (from EXIF data)
   - Location name (reverse geocoding via OpenStreetMap)
   - Content keywords (AI-generated via offline BLIP-2 model)

2. **Folder Grouping**: Photos are grouped into folders based on:
   - Same month/year
   - Geographic proximity (within 1000m)
   - Temporal proximity (within 3 hours)
   - Content similarity (shared keywords)

3. **File Organization**: Photos are copied to the output directory with:
   - Hierarchical folder structure (Year/Month/Event)
   - Descriptive folder names (Date + Location + Keywords)
   - Metadata JSON files for each photo

### Configuration

You can modify constants in [sort-photos.py](sort-photos.py) to customize behavior:

- `FOLDER_MAX_DISTANCE_METERS` - Maximum distance for same folder (default: 1000m)
- `FOLDER_MAX_TIME_DIFFERENCE_HOURS` - Maximum time gap for same folder (default: 3 hours)
- `STOPWORDS` - English stopwords to filter from keywords
- `STOPWORDS_GERMAN` - German stopwords to filter from keywords
- `FOLDER_FORBIDDEN_CHARS` - Characters to remove from folder names

### Caching

The script caches analysis results in `.cache/` to speed up repeated runs. Delete this folder to force re-analysis of all photos.

### Notes

- The script expects Google Pixel phone filename format: `PXL_YYYYMMDD_HHMMSS*.jpg`
- Only `.jpg` images and `.mp4` videos are processed
- Reverse geocoding uses OpenStreetMap Nominatim API (rate-limited)
- Keyword translation uses Google Translate API (may be rate-limited)
- AI analysis of the image happens offline with a downloaded BLIP-2 model
- Original files are **copied**, not moved (originals remain in input directory)

## License

Apache License 2.0 - See LICENSE file for details
Christian Kadluba 2026
