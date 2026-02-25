import unittest
from photoarch.services import geocoding

class TestGeocoding(unittest.TestCase):
    def test_get_address_from_coords_none(self):
        address = geocoding.get_address_from_coords(None, None)
        self.assertIsNone(address)

    def test_get_address_from_coords_invalid(self):
        address = geocoding.get_address_from_coords(999, 999)
        self.assertIsNone(address)

if __name__ == '__main__':
    unittest.main()
