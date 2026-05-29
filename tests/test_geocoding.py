import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from photoarch.services import geocoding


class TestGeocoding(unittest.TestCase):
    def test_get_address_from_coords_none(self):
        address = geocoding.get_address_from_coords(None, None)
        self.assertIsNone(address)

    def test_get_address_from_coords_invalid(self):
        address = geocoding.get_address_from_coords(999, 999)
        self.assertIsNone(address)

    def test_get_address_from_coords_uses_cache_within_tolerance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / geocoding._get_api_cache_filename(48.2152, 16.3994)
            cache_file.write_text(
                json.dumps(
                    {
                        "address": {"road": "Straße des Ersten Mai", "city": "Wien"},
                        "name": "Straße des Ersten Mai"
                    },
                    indent=2,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

            with patch.object(geocoding, "OSM_API_CACHE_DIR", temp_dir):
                with patch("photoarch.services.geocoding.requests.get") as mock_get:
                    address = geocoding.get_address_from_coords(48.2152, 16.3994)

            self.assertIsNotNone(address)
            self.assertEqual(address.name, "Straße des Ersten Mai Wien")
            mock_get.assert_not_called()

    def test_get_address_from_coords_saves_api_response_to_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            response_json = {
                "address": {"road": "Foo", "city": "Bar"},
                "name": "Foo"
            }
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = response_json

            with patch.object(geocoding, "OSM_API_CACHE_DIR", temp_dir):
                with patch("photoarch.services.geocoding.requests.get", return_value=mock_response):
                    address = geocoding.get_address_from_coords(48.0, 11.0)

            self.assertIsNotNone(address)
            self.assertEqual(address.name, "Foo Bar")

            expected_cache_file = Path(temp_dir) / geocoding._get_api_cache_filename(48.0, 11.0)
            self.assertTrue(expected_cache_file.exists())
            self.assertEqual(json.loads(expected_cache_file.read_text(encoding="utf-8")), response_json)

    def test_api_cache_filename_uses_o_separator(self):
        filename = geocoding._get_api_cache_filename(48.1519, -16.343799999999998)
        self.assertEqual(filename, "osm_lat_48o1519_lon_-16o343799999999998.json")

    def test_coords_from_cache_filename_parses_o_format(self):
        filename = "osm_lat_48o1519_lon_-16o343799999999998.json"
        coords = geocoding._coords_from_cache_filename(filename, 48.1519, -16.343799999999998)
        self.assertIsNotNone(coords)
        self.assertAlmostEqual(coords[0], 48.1519, places=10)
        self.assertAlmostEqual(coords[1], -16.343799999999998, places=10)

    def test_find_cached_api_response_within_tolerance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / geocoding._get_api_cache_filename(48.2152, 16.3994)
            cache_file.write_text(json.dumps({"address": {}}, indent=2, ensure_ascii=False), encoding="utf-8")

            with patch.object(geocoding, "OSM_API_CACHE_DIR", temp_dir):
                with patch.object(geocoding, "GEO_API_CACHE_TOLERANCE_METERS", 5):
                    result = geocoding._find_cached_api_response(48.2152001, 16.3994001)

            self.assertEqual(result, cache_file)

    def test_find_cached_api_response_outside_tolerance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / geocoding._get_api_cache_filename(48.2152, 16.3994)
            cache_file.write_text(json.dumps({"address": {}}, indent=2, ensure_ascii=False), encoding="utf-8")

            with patch.object(geocoding, "OSM_API_CACHE_DIR", temp_dir):
                with patch.object(geocoding, "GEO_API_CACHE_TOLERANCE_METERS", 5):
                    result = geocoding._find_cached_api_response(48.3252, 16.3994)

            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
