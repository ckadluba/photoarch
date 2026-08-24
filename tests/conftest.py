import pytest


@pytest.fixture
def run_paths(tmp_path):
    """Give every integration test isolated output and cache directories."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir, tmp_path / "cache"
