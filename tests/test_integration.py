import shutil
from pathlib import Path
import pytest
from photoarch.main import main

# Paths for the test
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "data/input"
OUTPUT_DIR = BASE_DIR / "data/output"
CACHE_DIR = Path(__file__).parent.parent / ".photoarch"  # Assuming cache is in the project root


# Fixture to clean output folder before and after each test
@pytest.fixture
def clean_output():
    """Delete the output folder before and after the test"""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    if CACHE_DIR.exists():
        (CACHE_DIR / "PXL_20250708_055317372.json").unlink(missing_ok=True)
        (CACHE_DIR / "PXL_20250708_055353541.json").unlink(missing_ok=True)
        (CACHE_DIR / "PXL_20250708_095842343.json").unlink(missing_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(OUTPUT_DIR)  # cleanup after test

# Integration test
@pytest.mark.longrunning
def test_photoarch_process_photo_folder(clean_output):
    # Arrange: ensure 3 test files exist
    input_files = list(INPUT_DIR.glob("*"))
    assert len(input_files) == 3, "Please provide exactly 3 test files in data/input"

    # Act: run the main function
    main(str(INPUT_DIR), str(OUTPUT_DIR), "filename")

    # Assert
    # Check the year folder was created with correct name
    year_folders = list(OUTPUT_DIR.iterdir())
    assert len(year_folders) == 1, "More or less than exactly one year folder was created"
    year_folder = year_folders[0]
    assert year_folder.name == "2025", "Year folder should be named '2025' based on test file dates"

    # Check the month folder was created with correct name
    month_folders = list(year_folder.iterdir())
    assert len(month_folders) == 1, "More or less than exactly one month folder was created"
    month_folder = month_folders[0]
    assert month_folder.name == "07 Jul", "Month folder should be named '07 Jul' based on test file dates"

    # Check the photo folders are created with correct names
    photo_folders = list(month_folder.iterdir())
    assert len(photo_folders) == 2, "More or less than exactly two photo folders were created"
    photo_folder_1 = next((p for p in photo_folders if p.name == "2025-07-08T0753 Veranstaltungszentrum Wien blaue Gemälde Licht Mannes Trompete"), None)
    photo_folder_2 = next((p for p in photo_folders if p.name == "2025-07-08T1158 Allianz Wien Bier Sandwich steht Tisch"), None)
    assert photo_folder_1 is not None, "Photo folder 1 was not found"
    assert photo_folder_1.is_dir(), "Photo folder 1 is not a directory"
    assert photo_folder_2 is not None, "Photo folder 2 was not found"
    assert photo_folder_2.is_dir(), "Photo folder 2 is not a directory"

    # Check photo files were correctly copied to photo folder 1
    photo_folder_1_files = list(photo_folder_1.iterdir())
    assert len(photo_folder_1_files) == 3, "More or less than exactly three objects were found in photo folder 1"
    photo_folder_1_metadata_folder = next((p for p in photo_folder_1_files if p.name == "metadata"), None)
    assert photo_folder_1_metadata_folder is not None, "No metadata folder was found in photo folder 1"
    assert photo_folder_1_metadata_folder.is_dir(), "Metadata object in photo folder 1 is not a directory"
    photo_folder_1_file_1 = next((p for p in photo_folder_1_files if p.name == "PXL_20250708_055317372.jpg"), None)
    assert photo_folder_1_file_1 is not None, "Photo file 'PXL_20250708_055317372.jpg' was not found in photo folder 1"
    assert photo_folder_1_file_1.is_file(), "Object 'PXL_20250708_055317372.jpg' is not a file"
    photo_folder_1_file_2 = next((p for p in photo_folder_1_files if p.name == "PXL_20250708_055353541.jpg"), None)
    assert photo_folder_1_file_2 is not None, "Photo file 'PXL_20250708_055353541.jpg' was not found in photo folder 1"
    assert photo_folder_1_file_2.is_file(), "Object 'PXL_20250708_055353541.jpg' is not a file"

    # Check metadata files were correctly copied to photo folder 1 metadata folder
    photo_folder_1_metadata_files = list(photo_folder_1_metadata_folder.glob("*.json"))
    assert len(photo_folder_1_metadata_files) == 2, "More or less than exactly two metadata JSON files were found in photo folder 1 metadata folder"
    photo_folder_1_metadata_file_1 = next((p for p in photo_folder_1_metadata_files if p.name == "PXL_20250708_055317372.json"), None)
    assert photo_folder_1_metadata_file_1 is not None, "Metadata file 'PXL_20250708_055317372.json' was not found in photo folder 1 metadata folder"
    assert photo_folder_1_metadata_file_1.is_file(), "Object 'PXL_20250708_055317372.json' is not a file"
    photo_folder_1_metadata_file_2 = next((p for p in photo_folder_1_metadata_files if p.name == "PXL_20250708_055353541.json"), None)
    assert photo_folder_1_metadata_file_2 is not None, "Metadata file 'PXL_20250708_055353541.json' was not found in photo folder 1 metadata folder"
    assert photo_folder_1_metadata_file_2.is_file(), "Object 'PXL_20250708_055353541.json' is not a file"

    # Check photo files were correctly copied to photo folder 2
    photo_folder_2_files = list(photo_folder_2.iterdir())
    assert len(photo_folder_2_files) == 2, "More or less than exactly two objects were found in photo folder 2"
    photo_folder_2_metadata_folder = next((p for p in photo_folder_2_files if p.name == "metadata"), None)
    assert photo_folder_2_metadata_folder is not None, "No metadata folder was found in photo folder 2"
    assert photo_folder_2_metadata_folder.is_dir(), "Metadata object in photo folder 2 is not a directory"
    photo_folder_2_file_1 = next((p for p in photo_folder_2_files if p.name == "PXL_20250708_095842343.jpg"), None)
    assert photo_folder_2_file_1 is not None, "Photo file 'PXL_20250708_095842343.jpg' was not found in photo folder 2"
    assert photo_folder_2_file_1.is_file(), "Object 'PXL_20250708_095842343.jpg' is not a file"

    # Check metadata files were correctly copied to photo folder 2 metadata folder
    photo_folder_2_metadata_files = list(photo_folder_2_metadata_folder.glob("*.json"))
    assert len(photo_folder_2_metadata_files) == 1, "More or less than exactly one metadata JSON file was found in photo folder 2 metadata folder"
    photo_folder_2_metadata_file_1 = next((p for p in photo_folder_2_metadata_files if p.name == "PXL_20250708_095842343.json"), None)
    assert photo_folder_2_metadata_file_1 is not None, "Metadata file 'PXL_20250708_095842343.json' was not found in photo folder 2 metadata folder"
    assert photo_folder_2_metadata_file_1.is_file(), "Object 'PXL_20250708_095842343.json' is not a file"


# Integration test with English folder names
@pytest.mark.longrunning
def test_photoarch_process_photo_folder_english(clean_output):
    # Arrange: ensure 3 test files exist
    input_files = list(INPUT_DIR.glob("*"))
    assert len(input_files) == 3, "Please provide exactly 3 test files in data/input"

    # Act: run the main function with English folder name language
    main(str(INPUT_DIR), str(OUTPUT_DIR), "filename", folder_name_language="english")

    # Assert
    # Check the year folder was created with correct name
    year_folders = list(OUTPUT_DIR.iterdir())
    assert len(year_folders) == 1, "More or less than exactly one year folder was created"
    year_folder = year_folders[0]
    assert year_folder.name == "2025", "Year folder should be named '2025' based on test file dates"

    # Check the month folder was created with correct name
    month_folders = list(year_folder.iterdir())
    assert len(month_folders) == 1, "More or less than exactly one month folder was created"
    month_folder = month_folders[0]
    assert month_folder.name == "07 Jul", "Month folder should be named '07 Jul' based on test file dates"

    # Check the photo folders are created with correct names
    # Folder names use English keywords; exact keyword suffix depends on AI output.
    # Date-time prefix and place name are stable and asserted here.
    photo_folders = list(month_folder.iterdir())
    assert len(photo_folders) == 2, "More or less than exactly two photo folders were created"
    photo_folder_1 = next((p for p in photo_folders if p.name == "2025-07-08T0753 Veranstaltungszentrum Wien blue door light man painting trumpet"), None)
    photo_folder_2 = next((p for p in photo_folders if p.name == "2025-07-08T1158 Allianz Wien beer bottle next sandwich sitting table"), None)
    assert photo_folder_1 is not None, "Photo folder 1 was not found"
    assert photo_folder_1.is_dir(), "Photo folder 1 is not a directory"
    assert photo_folder_2 is not None, "Photo folder 2 was not found"
    assert photo_folder_2.is_dir(), "Photo folder 2 is not a directory"

    # Folder names must use English keywords (different from German keywords)
    assert photo_folder_1.name != "2025-07-08T0753 Veranstaltungszentrum Wien blaue Gemälde Licht Mannes Trompete", \
        "Photo folder 1 uses German keywords instead of English"
    assert photo_folder_2.name != "2025-07-08T1158 Allianz Wien Bier Sandwich steht Tisch", \
        "Photo folder 2 uses German keywords instead of English"

    # Check photo files were correctly copied to photo folder 1
    photo_folder_1_files = list(photo_folder_1.iterdir())
    assert len(photo_folder_1_files) == 3, "More or less than exactly three objects were found in photo folder 1"
    photo_folder_1_metadata_folder = next((p for p in photo_folder_1_files if p.name == "metadata"), None)
    assert photo_folder_1_metadata_folder is not None, "No metadata folder was found in photo folder 1"
    assert photo_folder_1_metadata_folder.is_dir(), "Metadata object in photo folder 1 is not a directory"
    photo_folder_1_file_1 = next((p for p in photo_folder_1_files if p.name == "PXL_20250708_055317372.jpg"), None)
    assert photo_folder_1_file_1 is not None, "Photo file 'PXL_20250708_055317372.jpg' was not found in photo folder 1"
    assert photo_folder_1_file_1.is_file(), "Object 'PXL_20250708_055317372.jpg' is not a file"
    photo_folder_1_file_2 = next((p for p in photo_folder_1_files if p.name == "PXL_20250708_055353541.jpg"), None)
    assert photo_folder_1_file_2 is not None, "Photo file 'PXL_20250708_055353541.jpg' was not found in photo folder 1"
    assert photo_folder_1_file_2.is_file(), "Object 'PXL_20250708_055353541.jpg' is not a file"

    # Check metadata files were correctly copied to photo folder 1 metadata folder
    photo_folder_1_metadata_files = list(photo_folder_1_metadata_folder.glob("*.json"))
    assert len(photo_folder_1_metadata_files) == 2, "More or less than exactly two metadata JSON files were found in photo folder 1 metadata folder"
    photo_folder_1_metadata_file_1 = next((p for p in photo_folder_1_metadata_files if p.name == "PXL_20250708_055317372.json"), None)
    assert photo_folder_1_metadata_file_1 is not None, "Metadata file 'PXL_20250708_055317372.json' was not found in photo folder 1 metadata folder"
    assert photo_folder_1_metadata_file_1.is_file(), "Object 'PXL_20250708_055317372.json' is not a file"
    photo_folder_1_metadata_file_2 = next((p for p in photo_folder_1_metadata_files if p.name == "PXL_20250708_055353541.json"), None)
    assert photo_folder_1_metadata_file_2 is not None, "Metadata file 'PXL_20250708_055353541.json' was not found in photo folder 1 metadata folder"
    assert photo_folder_1_metadata_file_2.is_file(), "Object 'PXL_20250708_055353541.json' is not a file"

    # Check photo files were correctly copied to photo folder 2
    photo_folder_2_files = list(photo_folder_2.iterdir())
    assert len(photo_folder_2_files) == 2, "More or less than exactly two objects were found in photo folder 2"
    photo_folder_2_metadata_folder = next((p for p in photo_folder_2_files if p.name == "metadata"), None)
    assert photo_folder_2_metadata_folder is not None, "No metadata folder was found in photo folder 2"
    assert photo_folder_2_metadata_folder.is_dir(), "Metadata object in photo folder 2 is not a directory"
    photo_folder_2_file_1 = next((p for p in photo_folder_2_files if p.name == "PXL_20250708_095842343.jpg"), None)
    assert photo_folder_2_file_1 is not None, "Photo file 'PXL_20250708_095842343.jpg' was not found in photo folder 2"
    assert photo_folder_2_file_1.is_file(), "Object 'PXL_20250708_095842343.jpg' is not a file"

    # Check metadata files were correctly copied to photo folder 2 metadata folder
    photo_folder_2_metadata_files = list(photo_folder_2_metadata_folder.glob("*.json"))
    assert len(photo_folder_2_metadata_files) == 1, "More or less than exactly one metadata JSON file was found in photo folder 2 metadata folder"
    photo_folder_2_metadata_file_1 = next((p for p in photo_folder_2_metadata_files if p.name == "PXL_20250708_095842343.json"), None)
    assert photo_folder_2_metadata_file_1 is not None, "Metadata file 'PXL_20250708_095842343.json' was not found in photo folder 2 metadata folder"
    assert photo_folder_2_metadata_file_1.is_file(), "Object 'PXL_20250708_095842343.json' is not a file"


# Integration test with --use-image-difference
@pytest.mark.longrunning
def test_photoarch_process_photo_folder_use_image_difference(clean_output):
    # Arrange: ensure 3 test files exist
    input_files = list(INPUT_DIR.glob("*"))
    assert len(input_files) == 3, "Please provide exactly 3 test files in data/input"

    # Act: run the main function with use_image_difference=True
    main(str(INPUT_DIR), str(OUTPUT_DIR), "filename", use_image_difference=True)

    # Assert: same folder structure as the default run — the two visually distinct
    # events should still be separated into two photo folders.
    year_folders = list(OUTPUT_DIR.iterdir())
    assert len(year_folders) == 1, "More or less than exactly one year folder was created"
    year_folder = year_folders[0]
    assert year_folder.name == "2025", "Year folder should be named '2025' based on test file dates"

    month_folders = list(year_folder.iterdir())
    assert len(month_folders) == 1, "More or less than exactly one month folder was created"
    month_folder = month_folders[0]
    assert month_folder.name == "07 Jul", "Month folder should be named '07 Jul' based on test file dates"

    photo_folders = list(month_folder.iterdir())
    assert len(photo_folders) == 2, "More or less than exactly two photo folders were created"

    # Check all 3 input photos were copied to the output
    all_photo_files = [
        f for folder in photo_folders
        for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in {".jpg", ".png"}
    ]
    assert len(all_photo_files) == 3, "Not all 3 input photos were copied to the output"

    # Check that embeddings are stored in each metadata JSON file
    import json
    for folder in photo_folders:
        metadata_folder = folder / "metadata"
        assert metadata_folder.is_dir(), f"No metadata folder found in {folder.name}"
        for json_file in metadata_folder.glob("*.json"):
            data = json.loads(json_file.read_text(encoding="utf-8"))
            assert "embedding" in data, f"'embedding' key missing in {json_file.name}"
            assert isinstance(data["embedding"], list), f"'embedding' is not a list in {json_file.name}"
            assert len(data["embedding"]) > 0, f"'embedding' list is empty in {json_file.name}"
