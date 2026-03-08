import logging
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import argparse

from .models import FolderInfo, FileInfo
from .logging_config import setup_logging
from .analysis.file_analyzer import CACHE_DIR, INPUT_DIR, OUTPUT_DIR, analyze_file
from .fileops.folder_builder import create_folder_info, is_new_folder, finish_last_folder_info


# Initialization

logger = logging.getLogger(__name__)


# Code

def main(input_dir: str, output_dir: str, input_files_order: str, dry_run: bool = False, folder_name_language: str = "german"):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists() or not input_path.is_dir():
        logger.error(f"Input directory {input_path} does not exist or is not a directory.")
        return

    folder_infos = analyze_files(input_path, output_path, input_files_order, folder_name_language)
    copy_files(folder_infos, input_path, output_path, dry_run)

    logger.info("Finished.")


def analyze_files(input_path: Path, output_path: Path, input_files_order: str, folder_name_language: str = "german") -> list[FolderInfo]:
    logger.info(f"Analyzing files in {input_path} …")
    if input_files_order == "filename":
        files = sorted(input_path.iterdir(), key=lambda f: f.name)
    else:
        files = sorted(input_path.iterdir(), key=lambda f: f.stat().st_mtime)  # Sort files by modification time

    file_infos: list[FileInfo] = []
    folder_infos: list[FolderInfo] = []
    last_analysis_duration_seconds = 0.0
    for file_info in files:
        # Analyze the file
        datetime_start = datetime.now()

        # Estimate remaining time based on last analysis duration
        remaining_files = len(files) - len(file_infos)
        eta_seconds = remaining_files * last_analysis_duration_seconds
        logger.info(f"Analyzing file {file_info.name} ({len(file_infos) + 1}/{len(files)}), ETA: {timedelta(seconds=eta_seconds)} …")

        file_info = analyze_file(file_info)
        if file_info.skip:
            continue  # Skip files that do not match the criteria

        # Print elapsed time for analysis
        elapsed_time = datetime.now() - datetime_start
        last_analysis_duration_seconds = elapsed_time.total_seconds()
        logger.info(f"Analysis took {last_analysis_duration_seconds:.1f} seconds")

        # Create a new folder and finish the previous one if the file is different enough
        if is_new_folder(file_infos, file_info):
            finish_last_folder_info(folder_infos, file_infos, output_path, folder_name_language)
            assert file_info.date is not None  # Date is guaranteed to be set for non-skipped files
            create_folder_info(folder_infos, file_info.date)

        file_infos.append(file_info)
        folder_infos[-1].files.append(file_info)

    # Finish the last folder
    finish_last_folder_info(folder_infos, file_infos, output_path, folder_name_language)

    return folder_infos


def copy_files(folder_infos: list[FolderInfo], input_path: Path, output_path: Path, dry_run: bool):
    if dry_run:
        logger.info("Dry run — no files will be copied. Result tree:")
    else:
        logger.info(f"Copying files to {output_path} …")
    for folder_info in folder_infos:
        assert folder_info.path is not None  # Path is guaranteed to be set for all folders at this point
        logger.info(f"- {folder_info.path.name} [{len(folder_info.files)}]")
        for file_info in folder_info.files:
            logger.info(f"   - {file_info.path}")
        if not dry_run:
            folder_meta_path = folder_info.path / "metadata"
            folder_meta_path.mkdir(parents=True, exist_ok=True)
            for file_info in folder_info.files:
                photo_file_src_path = input_path / file_info.path
                photo_file_dst_path = folder_info.path / file_info.path
                shutil.copy(photo_file_src_path, photo_file_dst_path)
                file_meta_name = file_info.path.stem + ".json"
                meta_file_src_path = CACHE_DIR / file_meta_name
                meta_file_dst_path = folder_meta_path / file_meta_name
                shutil.copy(meta_file_src_path, meta_file_dst_path)

def cli():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Sort and organize photos by date, location, and AI-generated content.")
    parser.add_argument("--input", type=str, default=str(INPUT_DIR), help=f"Input directory containing photos (default: {INPUT_DIR})")
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR), help=f"Output directory for sorted photos (default: {OUTPUT_DIR})")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--input-files-order",
        default="filename",
        choices=["filename", "modified-date"],
        help="Process input files in filename or modified date order (default: filename)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Analyze and show the result tree without copying any files",
    )
    parser.add_argument(
        "--folder-name-language",
        default="german",
        choices=["german", "english"],
        help="Language used for keywords in folder names (default: german)",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)
    main(args.input, args.output, input_files_order=args.input_files_order, dry_run=args.dry_run, folder_name_language=args.folder_name_language)

if __name__ == "__main__":
    cli()
