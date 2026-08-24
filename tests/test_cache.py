import json
from datetime import datetime
from pathlib import Path

import pytest

from photoarch.cache import get_analysis_cache_file, write_json_atomic
from photoarch.main import copy_files
from photoarch.models import FileInfo, FolderInfo


def test_analysis_cache_key_includes_model_and_source_state(tmp_path):
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"first")

    git_cache = get_analysis_cache_file(tmp_path / "cache", source, "git")
    blip_cache = get_analysis_cache_file(tmp_path / "cache", source, "blip-2")

    source.write_bytes(b"changed content")
    changed_cache = get_analysis_cache_file(tmp_path / "cache", source, "git")

    assert git_cache != blip_cache
    assert git_cache != changed_cache


def test_atomic_json_write_leaves_no_temporary_file(tmp_path):
    destination = tmp_path / "cache" / "entry.json"

    write_json_atomic(destination, {"value": "ok"})

    assert json.loads(destination.read_text(encoding="utf-8")) == {"value": "ok"}
    assert list(destination.parent.iterdir()) == [destination]


def test_failed_json_write_removes_temporary_file(tmp_path):
    destination = tmp_path / "cache" / "entry.json"

    with pytest.raises(TypeError):
        write_json_atomic(destination, {"value": object()})

    assert list(destination.parent.iterdir()) == []


def test_copy_files_outputs_only_media_and_final_metadata(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output" / "2025" / "01 Jan" / "event"
    input_dir.mkdir()
    source = input_dir / "photo.jpg"
    source.write_bytes(b"photo")
    file_info = FileInfo(path=Path("photo.jpg"), date=datetime(2025, 1, 1))
    folder_info = FolderInfo(
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 1),
        place=None,
        keywords=set(),
        keywords_german=set(),
        files=[file_info],
        path=output_dir,
    )

    copy_files([folder_info], input_dir, tmp_path / "output", dry_run=False)

    output_files = sorted(
        path.relative_to(tmp_path / "output")
        for path in (tmp_path / "output").rglob("*")
        if path.is_file()
    )
    assert output_files == [
        Path("2025/01 Jan/event/metadata/photo.json"),
        Path("2025/01 Jan/event/photo.jpg"),
    ]
