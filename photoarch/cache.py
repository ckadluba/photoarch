import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

ANALYSIS_CACHE_VERSION = 1


def get_analysis_cache_file(
    cache_dir: Path,
    file_path: Path,
    captioning_ai_model: str,
) -> Path:
    """Return a cache path scoped to the source file and analysis settings."""
    try:
        stat = file_path.stat()
        source_state = f"{stat.st_size}:{stat.st_mtime_ns}"
    except FileNotFoundError:
        source_state = "missing"

    identity = "\0".join(
        (
            str(file_path.resolve()),
            source_state,
            captioning_ai_model,
            str(ANALYSIS_CACHE_VERSION),
        )
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return cache_dir / "analysis" / f"{file_path.stem}-{digest}.json"


def write_json_atomic(path: Path, data: Any) -> None:
    """Atomically replace a JSON cache file without exposing partial content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temporary_file:
            json.dump(data, temporary_file, indent=2, ensure_ascii=False)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)
