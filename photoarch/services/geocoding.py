import requests

from ..config import *
from ..models import *


def get_address_from_coords(lat, lon) -> Address | None:
    """Reverse geocoding using OSM Nominatim"""
    if lat is None or lon is None:
        return None
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

        return read_address_from_api_response(data)

    except Exception as e:
        print(f"OSM API Error: {e}")
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
