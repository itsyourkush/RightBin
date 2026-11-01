"""
Location and Geolocation Utilities.
Provides Haversine distance calculations, EXIF GPS coordinate extraction,
location proximity clustering, and preset campus/community recycling stations.
"""

from __future__ import annotations

import io
import math
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ExifTags

from config import config


# Predefined campus and municipal areas with verified GPS centroids
PRESET_AREAS: List[Dict[str, Any]] = [
    {
        "id": "area_north_campus",
        "name": "North Campus Area (Cafeteria Zone)",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "radius_meters": 100.0,
        "description": "Main dining hall, food court, and north student center",
    },
    {
        "id": "area_central_library",
        "name": "Central Quad Area (Library Zone)",
        "latitude": 28.6155,
        "longitude": 77.2105,
        "radius_meters": 100.0,
        "description": "University library, reading gardens, and central admin plaza",
    },
    {
        "id": "area_science_labs",
        "name": "Science Block Area (Labs Zone)",
        "latitude": 28.6180,
        "longitude": 77.2150,
        "radius_meters": 100.0,
        "description": "Research laboratories, lecture halls, and engineering block",
    },
    {
        "id": "area_south_dorms",
        "name": "South Dorms Area (Residential Zone)",
        "latitude": 28.6120,
        "longitude": 77.2050,
        "radius_meters": 100.0,
        "description": "Student housing, residence halls, and recreation center",
    },
    {
        "id": "area_green_park",
        "name": "East Park Area (Community Green)",
        "latitude": 28.6210,
        "longitude": 77.2200,
        "radius_meters": 100.0,
        "description": "Public community botanical park, sports field, and trails",
    },
]

# Alias for backwards compatibility
PRESET_RECYCLING_LOCATIONS = PRESET_AREAS


def haversine_distance_meters(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Computes the great-circle distance between two GPS coordinates using the Haversine formula.
    Returns distance in meters.
    """
    earth_radius_m = 6371000.0  # Mean radius of Earth in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_m * c


def is_same_location(
    lat1: Optional[float],
    lon1: Optional[float],
    name1: Optional[str],
    lat2: Optional[float],
    lon2: Optional[float],
    name2: Optional[str],
    proximity_threshold_m: float = 75.0,
) -> bool:
    """
    Determines if two scan locations represent the same physical location.
    Checks:
    1. If both have valid GPS coordinates: returns True if distance <= proximity_threshold_m.
    2. If coordinates are missing or identical: checks case-insensitive name match.
    """
    # 1. Coordinate-based comparison (highest precision)
    if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
        try:
            dist = haversine_distance_meters(float(lat1), float(lon1), float(lat2), float(lon2))
            return dist <= proximity_threshold_m
        except (ValueError, TypeError):
            pass

    # 2. Name-based comparison fallback
    n1 = (name1 or "").strip().lower()
    n2 = (name2 or "").strip().lower()
    if n1 and n2 and n1 == n2:
        return True

    return False


# Alias is_same_area to is_same_location
is_same_area = is_same_location


def _convert_dms_to_dd(dms_tuple, ref: str) -> float:
    """Converts GPS Degrees/Minutes/Seconds tuple to Decimal Degrees."""
    degrees = float(dms_tuple[0])
    minutes = float(dms_tuple[1])
    seconds = float(dms_tuple[2])
    dd = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ("S", "W"):
        dd = -dd
    return dd


def extract_exif_gps(image_input: Any) -> Optional[Tuple[float, float]]:
    """
    Extracts genuine camera latitude and longitude from image EXIF metadata if present.
    Supports Pillow 10+ IFD.GPSInfo, ExifTags GPSTAGS, and raw GPS info dictionaries.
    Commonly embedded when photos are captured by smartphones (iPhone/Android).
    """
    try:
        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, io.BytesIO):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            return None

        exif = img.getexif()
        if not exif:
            return None

        gps_info = None

        # Modern Pillow 10+ approach
        if hasattr(ExifTags, "IFD") and hasattr(ExifTags.IFD, "GPSInfo"):
            try:
                gps_info = exif.get_ifd(ExifTags.IFD.GPSInfo)
            except Exception:
                pass

        # Fallback to searching tags
        if not gps_info:
            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                if tag_name == "GPSInfo" or tag_id == 34853:
                    gps_info = value
                    break

        if not gps_info or not isinstance(gps_info, dict):
            return None

        # Extract latitude & longitude
        # Tag 1: GPSLatitudeRef ('N' or 'S'), Tag 2: GPSLatitude
        # Tag 3: GPSLongitudeRef ('E' or 'W'), Tag 4: GPSLongitude
        lat_data = gps_info.get(2)
        lat_ref = gps_info.get(1)
        lon_data = gps_info.get(4)
        lon_ref = gps_info.get(3)

        if lat_data and lat_ref and lon_data and lon_ref:
            lat = _convert_dms_to_dd(lat_data, str(lat_ref))
            lon = _convert_dms_to_dd(lon_data, str(lon_ref))
            return round(lat, 6), round(lon, 6)
    except Exception:
        pass
    return None
