import pytest

from tests.support import reject_live_geocoding, seed_osm_cache


@pytest.fixture
def run_paths(tmp_path):
    """Give every integration test isolated output and cache directories."""
    output_dir = tmp_path / "output"
    cache_dir = tmp_path / "cache"
    output_dir.mkdir()
    seed_osm_cache(cache_dir)

    with reject_live_geocoding():
        yield output_dir, cache_dir
