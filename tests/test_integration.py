import shutil
from pathlib import Path
import pytest
from photoarch.main import main

# Paths for the test
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "data/input"
OUTPUT_DIR = BASE_DIR / "data/output"
CACHE_DIR = Path(__file__).parent.parent / ".cache"  # Assuming cache is in the project root


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
def test_photoarch_integration(clean_output):
    # Arrange: ensure 3 test files exist
    input_files = list(INPUT_DIR.glob("*"))
    assert len(input_files) == 3, "Please provide exactly 3 test files in data/input"

    # Act: run the main function
    main(str(INPUT_DIR), str(OUTPUT_DIR))

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
    photo_folder_1 = photo_folders[0]
    photo_folder_2 = photo_folders[1]
    assert photo_folder_1.name == "2025-07-08T0753 Veranstaltungszentrum Wien blaue daran Gemälde Licht Mannes Trompete Tür", \
        "Photo folder 1 should be named '2025-07-08T0753 Veranstaltungszentrum Wien blaue daran Gemälde Licht Mannes Trompete Tür' based on test files"
    assert photo_folder_2.name == "2025-07-08T1158 Allianz Wien Bier Flasche neben Sandwich steht Tisch", \
        "Photo folder 2 should be named '2025-07-08T1158 Allianz Wien Bier Flasche neben Sandwich steht Tisch' based on test files"

    # Check photo files were correctly copied to photo folder 1
    photo_folder_1_files = list(photo_folder_1.iterdir())
    assert len(photo_folder_1_files) == 3, "More or less than exactly three objects were found in photo folder 1"
    photo_folder_1_metadata_folder = photo_folder_1_files[0]
    assert photo_folder_1_metadata_folder.is_dir() and photo_folder_1_metadata_folder.name == "metadata", \
        "The first object in photo folder 1 should be the metadata folder"
    photo_folder_1_file_2 = photo_folder_1_files[1]
    assert photo_folder_1_file_2.is_file() and photo_folder_1_file_2.name == "PXL_20250708_055317372.jpg", \
        "The second object in photo folder 1 should be the photo file 'PXL_20250708_055317372.jpg'"
    photo_folder_1_file_3 = photo_folder_1_files[2]
    assert photo_folder_1_file_3.is_file() and photo_folder_1_file_3.name == "PXL_20250708_055353541.jpg", \
        "The third object in photo folder 1 should be the photo file 'PXL_20250708_055353541.jpg'"

    # Check metadata files were correctly copied to photo folder 1 metadata folder
    photo_folder_1_metadata_files = list(photo_folder_1_metadata_folder.glob("*.json"))
    assert len(photo_folder_1_metadata_files) == 2, "More or less than exactly two metadata JSON files were found in photo folder 1 metadata folder"
    photo_folder_1_metadata_ = photo_folder_1_metadata_files[0]
    assert photo_folder_1_metadata_.is_file() and photo_folder_1_metadata_.name == "PXL_20250708_055317372.json", \
        "The first metadata file in photo folder 1 should be 'PXL_20250708_055317372.json'"
    photo_folder_1_metadata_2 = photo_folder_1_metadata_files[1]
    assert photo_folder_1_metadata_2.is_file() and photo_folder_1_metadata_2.name == "PXL_20250708_055353541.json", \
        "The second metadata file in photo folder 1 should be 'PXL_20250708_055353541.json'"

    # Check photo files were correctly copied to photo folder 2
    photo_folder_2_files = list(photo_folder_2.iterdir())
    assert len(photo_folder_2_files) == 2, "More or less than exactly two objects were found in photo folder 2"
    photo_folder_2_metadata_folder = photo_folder_2_files[0]
    assert photo_folder_2_metadata_folder.is_dir() and photo_folder_2_metadata_folder.name == "metadata", \
        "The first object in photo folder 2 should be the metadata folder"
    photo_folder_2_file_2 = photo_folder_2_files[1]
    assert photo_folder_2_file_2.is_file() and photo_folder_2_file_2.name == "PXL_20250708_095842343.jpg", \
        "The second object in photo folder 2 should be the photo file 'PXL_20250708_095842343.jpg'"

    # Check metadata files were correctly copied to photo folder 2 metadata folder
    photo_folder_2_metadata_files = list(photo_folder_2_metadata_folder.glob("*.json"))
    assert len(photo_folder_2_metadata_files) == 1, "More or less than exactly one metadata JSON file was found in photo folder 2 metadata folder"
    photo_folder_2_metadata_ = photo_folder_2_metadata_files[0]
    assert photo_folder_2_metadata_.is_file() and photo_folder_2_metadata_.name == "PXL_20250708_095842343.json", \
        "The first metadata file in photo folder 2 should be 'PXL_20250708_095842343.json'"
