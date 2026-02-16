import shutil
from pathlib import Path
from datetime import datetime
import argparse

from .config import *
from .models import *
from .helpers import *


def main(input_dir: str, output_dir: str):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists() or not input_path.is_dir():
        print(f"Input directory {input_path} does not exist or is not a directory.")
        return

    print("\n")
    print(f"Analyzing files in {input_path} …")
    files = sorted(input_path.iterdir(), key=lambda f: f.name)

    file_infos: list[FileInfo] = []
    folder_infos: list[FolderInfo] = []
    for file_info in files:
        # Analyze the file
        datetime_start = datetime.now()
        print(f"Analyzing file ({len(file_infos) + 1}/{len(files)}) {file_info.name} …")

        file_info = analyze_file(file_info)
        if file_info.skip:
            continue  # Skip files that do not match the criteria

        # Print elapsed time for analysis
        elapsed_time = datetime.now() - datetime_start
        print(f"Analysis took {elapsed_time.total_seconds():.1f} seconds")

        # Create a new folder and finish the previous one if the file is different enough
        if is_new_folder(file_infos, file_info):
            finish_last_folder_info(folder_infos, file_infos, output_path)
            assert file_info.date is not None  # Date is guaranteed to be set for non-skipped files
            create_folder_info(folder_infos, file_info.date)

        file_infos.append(file_info)
        folder_infos[-1].files.append(file_info)

    # Finish the last folder
    finish_last_folder_info(folder_infos, file_infos, output_path)

    print("\n")
    print(f"Copying files to {output_path} …")

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
