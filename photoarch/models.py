from __future__ import annotations
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase, config
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import *


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Address:
    name: Optional[str] = None
    amenity: Optional[str] = None
    house_number: Optional[str] = None
    road: Optional[str] = None
    neighbourhood: Optional[str] = None
    suburb: Optional[str] = None
    city_district: Optional[str] = None
    city: Optional[str] = None
    iso31662_lvl4: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> "Address":
        if not data:
            return Address()
        return Address(
            name=data.get("name"),
            amenity=data.get("amenity"),
            house_number=data.get("house_number"),
            road=data.get("road"),
            neighbourhood=data.get("neighbourhood"),
            suburb=data.get("suburb"),
            city_district=data.get("city_district"),
            city=data.get("city"),
            iso31662_lvl4=data.get("iso31662_lvl4"),
            postcode=data.get("postcode"),
            country=data.get("country"),
            country_code=data.get("country_code"),
        )


@dataclass
class FolderInfo:
    start_date: datetime
    end_date: Optional[datetime]
    place: Optional[str]
    keywords_german: set[str]
    files: list[FileInfo]
    path: Optional[Path] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class FileInfo:

    # File information schema version
    schema_version: int = 1

    path: Path = field(
        default=Path(""),
        metadata=config(
            encoder=str,
            decoder=Path
        )
    )

    date: Optional[datetime] = field(
        default=None,
        metadata=config(
            encoder=lambda d: d.isoformat() if d else None,
            decoder=lambda s: datetime.fromisoformat(s) if s else None,
            mm_field=None
        )
    )

    camera_model: Optional[str] = None

    lat: Optional[float] = None
    lon: Optional[float] = None
    address: Optional[Address] = None

    keywords: list[str] = field(default_factory=list)
    keywords_german: list[str] = field(default_factory=list)
    caption: str = ""
    caption_german: str = ""

    skip: bool = field(
        default=False,
        metadata=config(exclude=lambda _: True)
    )
