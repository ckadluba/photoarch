# Photo Archive Organizer

[![Build and Test](https://github.com/ckadluba/photoarch/actions/workflows/test.yml/badge.svg)](https://github.com/ckadluba/photoarch/actions/workflows/test.yml)

## Purpose

Photo Archive Organizer is a complete Python module/package for automatically organizing and archiving photos and videos containing EXIF data (geo coordinates, date/time, and other metadata). It processes images from a flat input folder and intelligently sorts them into a structured output directory based on date, location, and content.

### Key Features

- **AI-Powered Content Analysis**: Uses a local AI vision model to generate captions and keywords for images — without cloud access. Two models are supported and can be selected via the `--captioning-ai-model` command-line parameter:
  - **BLIP-2** (`blip-2`, default): [Salesforce/blip2-flan-t5-xl](https://huggingface.co/Salesforce/blip2-flan-t5-xl) — a fast, lightweight vision-language model. Good quality captions with low memory requirements.
  - **LLaVA** (`llava`): [llava-hf/llava-1.5-7b-hf](https://huggingface.co/llava-hf/llava-1.5-7b-hf) — a large multimodal language model that produces richer, more descriptive captions at the cost of higher memory usage and longer inference time.
  
  Both models run fully offline. The selected model is automatically downloaded on first use and cached locally in the `models/` directory.
- **Semantic Caption Comparison**: Uses a Sentence-Transformer model (paraphrase-multilingual-MiniLM-L12-v2) to detect semantically similar image captions for intelligent photo grouping. This allows recognition of related concepts even when exact words differ.
- **Image Embedding Comparison** *(optional)*: Instead of comparing text captions, computes CLIP embeddings directly from raw image pixels and uses the visual similarity between images for grouping. Enable with `--use-image-difference`.
- **Geolocation Processing**: Extracts GPS coordinates from EXIF data and performs reverse geocoding to determine locations
- **Intelligent Grouping**: Automatically groups photos into folders based on:
  - Temporal proximity (time between photos)
  - Geographic distance (GPS coordinates)
  - Content similarity (semantically similar AI-generated captions)
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
pip install -e .[dev]
```
This allows you to make changes to the code and use them immediately without reinstalling.

#### Optional: Create a Virtual Environment
It is recommended to use a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .[dev]
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
  - `.photoarch/` - Temporary cache for analysis results

## Usage

### Basic Usage
Place your photos in the `input_photos/` directory and run:
```bash
python -m photoarch.main
```


### Custom Input/Output Directories
Specify custom input and output directories:
```bash
python -m photoarch --input /path/to/photos --output /path/to/sorted
```

### Using as a Python Module
You can also use the module in your own scripts:
```python
from photoarch import run

exit_code = run(
    input_dir="/path/to/photos",
    output_dir="/path/to/sorted",
    input_files_order="filename",
)
```

### Command-Line Arguments
- `--input` - Input directory containing photos (default: `input_photos`)
- `--output` - Output directory for sorted photos (default: `sorted_photos`)
- `--input-files-order` - Order to process input files: `filename` or `modified-date` (default: `filename`)
- `--dry-run` - Analyze photos and print the result folder tree without copying any files
- `--folder-name-language` - Language used for keywords in folder names: `german` or `english` (default: `german`). This only affects folder names — metadata JSON files always contain both the original English and translated German keywords and captions regardless of this setting.
- `--captioning-ai-model` - AI model used for image captioning: `blip-2` or `llava` (default: `blip-2`). See [AI Models](#ai-models) for details.
- `--use-image-difference` - Use visual image similarity (CLIP embeddings computed from pixel data) instead of semantic caption similarity for the content difference score. See [Image Embedding Comparison](#image-embedding-comparison) for details.

### Output Structure

The module creates a hierarchical folder structure:

```
sorted_photos/
├── 2025/
│   ├── 01 Jan/
│   │   ├── 2025-01-15T1430 - 15T1645 Berlin Brandenburger Tor Touristen Sehenswürdigkeit/
│   │   │   ├── metadata/
│   │   │   │   ├── PXL_20250115_143052.json
│   │   │   │   └── PXL_20250115_164532.json
│   │   │   ├── PXL_20250115_143052.jpg
│   │   │   └── PXL_20250115_164532.jpg
│   │   └── 2025-01-20T0915 München Park Springbrunnen/
│   │       ├── metadata/
│   │       │   └── PXL_20250120_091523.json
│   │       │   └── PXL_20250120_101422.json
│   │       └── PXL_20250120_091523.jpg
│   │       └── PXL_20250120_101422.mp4
│   └── 02 Feb/
│       └── 2025-02-03T1200 Hamburg Hafen/
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
  "keywordsGerman": ["Tor", "Sehenswürdigkeit", "Gitterstäben", "Himmel"],
  "caption": "a large gate with columns and a sky background",
  "captionGerman": "ein großes Tor mit Gittertäben und Himmel"
}
```

### Processing Flow

1. **File Analysis**: Each photo is analyzed for:
   - Timestamp (from EXIF or file modification date)
   - GPS coordinates (from EXIF data)
   - Location name (reverse geocoding via OpenStreetMap)
   - Image captions (AI-generated via offline model — BLIP-2 by default, LLaVA optionally)

2. **Folder Grouping**: Photos are grouped into folders based on:
   - Same month/year
   - Geographic proximity (within `FOLDER_MAX_DISTANCE_METERS`)
   - Temporal proximity (within `FOLDER_MAX_TIME_DIFFERENCE_HOURS`)
   - Content similarity: semantically similar captions (Sentence-Transformer model, default) or visually similar images (CLIP model, with `--use-image-difference`)

3. **File Organization**: Photos are copied to the output directory with:
   - Hierarchical folder structure (Year/Month/Event)
   - Descriptive folder names (Date/Time + Location + Keywords)
   - Metadata JSON files for each photo

### Configuration

You can modify constants in [photoarch/config.py](photoarch/config.py) to customize behavior:

- `FOLDER_MAX_DISTANCE_METERS` - Maximum distance for same folder (default: 1500m)
- `FOLDER_MAX_TIME_DIFFERENCE_HOURS` - Maximum time gap for same folder (default: 2 hours)
- `FOLDER_MAX_DIFFERENCE_SCORE_THRESHOLD` - Maximum overall difference score (default: 0.58)
- `STOPWORDS` - English stopwords to filter from keywords
- `STOPWORDS_GERMAN` - German stopwords to filter from keywords
- `FOLDER_FORBIDDEN_CHARS` - Characters to remove from folder names

### Caching

The module caches analysis results in `.photoarch/` to speed up repeated runs. Delete this folder to force re-analysis of all photos.

### Notes


- Only `.jpg` and `.png` images and `.mp4` videos are processed
- Reverse geocoding uses OpenStreetMap Nominatim API (rate-limited)
- Keyword translation uses Google Translate API (may be rate-limited)
- AI image captioning happens offline with a locally downloaded model (BLIP-2 or LLaVA)
- Semantic caption comparison uses the offline Sentence-Transformer model (paraphrase-multilingual-MiniLM-L12-v2)
- With `--use-image-difference`, image similarity is computed via the offline CLIP model (clip-ViT-B-32). Both scores are always logged at DEBUG level so the two approaches can be compared.
- Original files are **copied**, not moved (originals remain in input directory)
- The module works with photos and videos from different cameras and phones as long as they contain EXIF data. It was mainly tested with Google Pixel 8 and Samsung Galaxy A15 phones.

## Module Structure

The module is organized as follows:

```
photoarch/
├── ai_models_context.py               # Runtime container for loaded AI model instances
├── config.py                          # Configuration constants
├── logging_config.py                  # Logging setup
├── main.py                            # Entry point for CLI and module usage
├── models.py                          # Shared data model classes
├── analysis/
│   ├── caption_generator.py           # Abstract base class (interface) for caption generators
│   ├── caption_generator_factory.py   # Factory function create_caption_generator()
│   ├── ai_captioning_blip2.py         # Blip2CaptionGenerator (BLIP-2 model)
│   ├── ai_captioning_llava.py         # LlavaCaptionGenerator (LLaVA model)
│   ├── exif_reader.py                 # EXIF metadata extraction
│   ├── file_analyzer.py               # Orchestrates per-file analysis
│   └── image_embedder.py              # CLIP image embedding and visual similarity
├── fileops/
│   ├── file_utils.py                  # File copy and path utilities
│   └── folder_builder.py              # Output folder creation and naming
├── language/
│   ├── caption_comparer.py            # Semantic caption similarity (Sentence-Transformer)
│   ├── keyword_generator.py           # Keyword extraction from captions
│   └── keyword_reducer.py             # Deduplication and filtering of keywords
└── services/
    ├── geocoding.py                   # Reverse geocoding via OpenStreetMap Nominatim
    └── translate.py                   # Keyword translation via Google Translate
```

## AI Models

### Image Captioning

Image captioning is the core AI step that generates a text description for each photo. This description is used to produce keywords for folder naming and to compare photos for grouping. Two models are supported:

| Parameter value | Model | Description |
|---|---|---|
| `blip-2` *(default)* | [Salesforce/blip2-flan-t5-xl](https://huggingface.co/Salesforce/blip2-flan-t5-xl) | Lightweight vision-language model. Fast inference, low memory usage (~4 GB). Caption quality is good for most photos. |
| `llava` | [llava-hf/llava-1.5-7b-hf](https://huggingface.co/llava-hf/llava-1.5-7b-hf) | Large multimodal language model (7B parameters). Produces richer, more detailed captions. Requires more memory (~14 GB) and is slower. |

Both models run **fully offline** after an initial download. Models are cached in the `models/` directory.

Select the model via the `--captioning-ai-model` command-line parameter:
```bash
python -m photoarch.main --captioning-ai-model llava
```

### Semantic Caption Comparison

For grouping photos by content similarity, the [paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) Sentence-Transformer model is used. This model is always active and cannot be changed via command-line parameters.

### Image Embedding Comparison

As an alternative to caption-based grouping, the `--use-image-difference` flag enables direct visual similarity between images using [CLIP (clip-ViT-B-32)](https://huggingface.co/sentence-transformers/clip-ViT-B-32). Instead of comparing generated text captions, the model encodes the raw pixel data of each image into a vector embedding. The cosine distance between the embeddings of two images is then used as the content difference score.

This approach can be more robust for photos where the AI captioning model produces poor or generic descriptions (e.g. very dark, blurry, or abstract images).

Both the caption difference score and the image difference score are always calculated and logged at `DEBUG` level:
```
is_new_folder: decision, ..., caption_diff=0.12, image_diff=0.45 (active=image, sc=0.11, wh=0.25), ...
```

Enable with:
```bash
python -m photoarch.main --use-image-difference
```

The CLIP model is downloaded automatically on first use and cached in the `models/` directory.

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
