import shutil
from pathlib import Path
from unittest.mock import patch

import requests

from photoarch.services.geocoding import NOMINATIM_URL


OSM_CACHE_FIXTURES = Path(__file__).parent / "data" / "osm_api_cache"


def seed_osm_cache(cache_dir: Path) -> None:
    """Copy deterministic OSM responses into an isolated run cache."""
    shutil.copytree(OSM_CACHE_FIXTURES, cache_dir / "osm_api_cache")


def reject_live_geocoding():
    """Reject Nominatim calls while allowing unrelated HTTP integrations."""
    original_get = requests.get

    def guarded_get(url, *args, **kwargs):
        if url == NOMINATIM_URL:
            raise AssertionError("Tests must use the OSM cache fixtures")
        return original_get(url, *args, **kwargs)

    return patch("photoarch.services.geocoding.requests.get", side_effect=guarded_get)
