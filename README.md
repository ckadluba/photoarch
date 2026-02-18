# Photo Archive Organizer

[![Build and Test](https://github.com/ckadluba/photoarch/actions/workflows/test.yml/badge.svg)](https://github.com/ckadluba/photoarch/actions/workflows/test.yml)

## Purpose

Photo Archive Organizer is a complete Python module/package for automatically organizing and archiving photos and videos containing EXIF data (geo coordinates, date/time, and other metadata). It processes images from a flat input folder and intelligently sorts them into a structured output directory based on date, location, and content.

### Key Features

- **AI-Powered Content Analysis**: Uses the BLIP-2 (Bootstrapping Language-Image Pre-training) model to generate captions and keywords for images used locally without cloud access. AI processing happens offline. The model is automatically downloaded on first execution of the module.
- **Geolocation Processing**: Extracts GPS coordinates from EXIF data and performs reverse geocoding to determine locations
- **Intelligent Grouping**: Automatically groups photos into folders based on:
  - Temporal proximity (time between photos)
  - Geographic distance (GPS coordinates)
  - Content similarity (AI-generated keywords)
- **Metadata Preservation**: Creates JSON metadata files for each photo with extracted information
- **Multi-language Support**: Translates AI-generated keywords to German
- **Structured Output**: Organizes photos in a hierarchical `YYYY/Month/Date-Location-Keywords` folder structure

This module is designed for photographers and developers who want to automatically organize large collections of photos into meaningful groups without manual sorting. It is extensible and can be integrated into larger Python projects.

## Disclaimer

This software is provided under the **Apache License 2.0** and is offered **AS IS**, without warranty of any kind, express or implied.

The authors and contributors accept **NO RESPONSIBILITY** for:
- Data loss or corruption
- Incorrect metadata extraction
- API rate limits or failures (OpenStreetMap Nominatim, Google Translate)
- Unexpected behavior or results

**Important**: Always maintain backups of your original photos before processing them with this module. Test with a small subset of images first to ensure the results meet your expectations.

## Prerequisites

### 1. ExifTool
Download and install ExifTool for video metadata extraction:
  - Download from: [https://exiftool.org/](https://exiftool.org/)
  - Windows: Place `exiftool.exe` in the project root directory or add to PATH
  - Linux/Mac: Install via package manager (e.g., `apt install exiftool` or `brew install exiftool`)

### 2. Python Installation


Install required Python packages:
```bash
pip install -r requirements.txt
```

#### Install in Editable Mode
To install the module in editable mode (for development):
```bash
pip install -e .
```
This allows you to make changes to the code and use them immediately without reinstalling.

#### Optional: Create a Virtual Environment
It is recommended to use a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Module Installation

#### Using as a Module
To use in your own Python project:
```python
import photoarch
```

#### Running as a Standalone Module
To run from the command line:
```bash
python -m photoarch.main
```

### 4. Directory Structure
Ensure the following directories exist (they will be created automatically if missing):
  - `input_photos/` - Place your photos here (or specify alternative path using `--input` command line parameter)
  - `sorted_photos/` - Output directory (will be created; can also be specified using `--output`)
  - `.cache/` - Temporary cache for analysis results

## Usage


### Basic Usage
Place your photos in the `input_photos/` directory and run:
```bash
python -m photoarch.main
```

### Custom Input/Output Directories
Specify custom input and output directories:
```bash
python -m photoarch.main --input /path/to/photos --output /path/to/sorted
```

### Using as a Python Module
You can also use the module in your own scripts:
```python
from photoarch import main
main.run(input_dir="/path/to/photos", output_dir="/path/to/sorted")
```

### Custom Input/Output Directories
Specify custom input and output directories:
```bash
python -m photoarch.main --input /path/to/photos --output /path/to/sorted
```

### Using as a Python Module
You can also use the module in your own scripts:
```python
from photoarch import main
main.run(input_dir="/path/to/photos", output_dir="/path/to/sorted")
```

### Command-Line Arguments
- `--input` - Input directory containing photos (default: `input_photos`)
- `--output` - Output directory for sorted photos (default: `sorted_photos`)

### Output Structure

The module creates a hierarchical folder structure:

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
  "cameraModel": "Google Pixel 8",
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
  "captionGerman": "ein großes Tor mit Gittertäben und Himmel"
}
```

### Processing Flow

1. **File Analysis**: Each photo is analyzed for:
   - Timestamp (from EXIF or file modification date)
   - GPS coordinates (from EXIF data)
   - Location name (reverse geocoding via OpenStreetMap)
   - Content keywords (AI-generated via offline BLIP-2 model)

2. **Folder Grouping**: Photos are grouped into folders based on:
   - Same month/year
   - Geographic proximity (within `FOLDER_MAX_DISTANCE_METERS`)
   - Temporal proximity (within `FOLDER_MAX_TIME_DIFFERENCE_HOURS`)
   - Content similarity (shared keywords)

3. **File Organization**: Photos are copied to the output directory with:
   - Hierarchical folder structure (Year/Month/Event)
   - Descriptive folder names (Date/Time + Location + Keywords)
   - Metadata JSON files for each photo

### Configuration

You can modify constants in [photoarch/config.py](photoarch/config.py) to customize behavior:

- `FOLDER_MAX_DISTANCE_METERS` - Maximum distance for same folder (default: 1000m)
- `FOLDER_MAX_TIME_DIFFERENCE_HOURS` - Maximum time gap for same folder (default: 3 hours)
- `STOPWORDS` - English stopwords to filter from keywords
- `STOPWORDS_GERMAN` - German stopwords to filter from keywords
- `FOLDER_FORBIDDEN_CHARS` - Characters to remove from folder names

### Caching

The module caches analysis results in `.cache/` to speed up repeated runs. Delete this folder to force re-analysis of all photos.

### Notes


- Only `.jpg` images and `.mp4` videos are processed
- Reverse geocoding uses OpenStreetMap Nominatim API (rate-limited)
- Keyword translation uses Google Translate API (may be rate-limited)
- AI analysis of the image happens offline with a downloaded BLIP-2 model
- Original files are **copied**, not moved (originals remain in input directory)
- The module works with photos and videos from different cameras and phones as long as they contain EXIF data. It was mainly tested with Google Pixel 8 and Samsung Galaxy A15 phones.

## Module Structure

The module is organized as follows:

- `photoarch/analysis/`: EXIF reading, AI captioning, file analysis
- `photoarch/fileops/`: File and folder utilities
- `photoarch/services/`: Geocoding and language translation
- `photoarch/config.py`: Configuration constants
- `photoarch/main.py`: Entry point for CLI and module usage

## Extending the Module


You can add your own analysis, file operations, or services by creating new modules in the respective subfolders and importing them in your scripts.

## Running Tests

Tests are located in the `tests/` directory. To run all tests, use:
```bash
pytest
```
Or to run a specific test file:
```bash
pytest tests/test_integration.py
```

Make sure you have the `pytest` package installed:
```bash
pip install pytest
```

Test input files should be placed in `tests/data/input/` as required by the integration test.

## License

Apache License 2.0 - See LICENSE file for details
Christian Kadluba 2026
