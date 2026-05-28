import json
import logging
import math
import re
from pathlib import Path

import requests

from ..config import NOMINATIM_URL, OSM_API_CACHE_DIR, GEO_API_CACHE_TOLERANCE_METERS
from ..models import Address


# Initialization

logger = logging.getLogger(__name__)


def get_address_from_coords(lat, lon) -> Address | None:
    """Reverse geocoding using OSM Nominatim"""
    if lat is None or lon is None:
        return None

    cache_file = _find_cached_api_response(lat, lon)
    if cache_file is not None:
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return read_address_from_api_response(data)
        except Exception as e:
            logger.warning(f"Failed to read cached OSM API file {cache_file}: {e}")

    try:
        r = requests.get(
            NOMINATIM_URL,
            params={
                "lat": lat,
                "lon": lon,
                "format": "jsonv2",
                "zoom": 18,            # hohe Detailstufe
                "addressdetails": 1,
                "accept-language": "de,en"
            },
            headers={
                "User-Agent": "photoarch/1.0 (contact: geoquest@gmail.com)"
            },
            timeout=30
        )
        r.raise_for_status()
        data = r.json()

        _save_api_response_to_cache(lat, lon, data)

        return read_address_from_api_response(data)

    except Exception as e:
        logger.error(f"OSM API Error: {e}")
        return None


def read_address_from_api_response(data):
    address_dict = data.get("address")
    if address_dict:
        address = Address.from_dict(address_dict)

        # Set a meaningful name
        name = data.get("name")
        if name:
            address.name = name
        else:
            if address.road:
                address.name = f"{address.road} {address.house_number}".strip() if address.house_number else address.road
        if address.name is None:
            address.name = f"{address.city}" if address.city else ""
        address.name += f" {address.city}" if address.city else ""
        return address
    else:
        return None


def _save_api_response_to_cache(lat, lon, data):
    cache_dir = Path(OSM_API_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / _get_api_cache_filename(lat, lon)
    cache_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return cache_file


def _find_cached_api_response(lat, lon):
    cache_dir = Path(OSM_API_CACHE_DIR)
    if not cache_dir.exists():
        return None

    for cache_file in cache_dir.glob("osm_lat_*_lon_*.json"):
        coords = _coords_from_cache_filename(cache_file.name, lat, lon)
        if coords is None:
            continue
        if _distance_meters(lat, lon, coords[0], coords[1]) <= GEO_API_CACHE_TOLERANCE_METERS:
            return cache_file
    return None


def _get_api_cache_filename(lat, lon):
    lat_str = repr(lat).replace('.', '')
    lon_str = repr(lon).replace('.', '')
    return f"osm_lat_{lat_str}_lon_{lon_str}.json"


def _coords_from_cache_filename(name, target_lat, target_lon):
    match = re.match(r"^osm_lat_(-?\d+)_lon_(-?\d+)\.json$", name)
    if not match:
        return None
    try:
        lat_candidates = _decode_compact_coordinate_candidates(match.group(1))
        lon_candidates = _decode_compact_coordinate_candidates(match.group(2))
        if not lat_candidates or not lon_candidates:
            return None
        lat = min(lat_candidates, key=lambda x: abs(x - target_lat))
        lon = min(lon_candidates, key=lambda x: abs(x - target_lon))
        return lat, lon
    except ValueError:
        return None


def _decode_compact_coordinate_candidates(value):
    sign = -1 if value.startswith('-') else 1
    digits = value.lstrip('-')
    if not digits:
        return []

    candidates = []
    for pos in range(1, len(digits)):
        candidate = sign * float(digits[:pos] + '.' + digits[pos:])
        if repr(candidate).replace('.', '') == value:
            candidates.append(candidate)
    return candidates


def _distance_meters(lat1, lon1, lat2, lon2):
    # Haversine distance
    radius = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c
