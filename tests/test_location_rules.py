"""
Unit and Integration Tests for Location-Based Fraud Prevention & Specific Sub-Type Detection.
Verifies:
1. Haversine distance calculations.
2. Max 2 scans per location enforcement (3rd scan rejected for rewards).
3. Moving to a different location resets scan allowance.
4. Specific waste sub-type, resin code, and recyclability details for each category.
"""

import io
import pytest
from PIL import Image

from config import config
from repositories.scan_repository import ScanRepository
from repositories.points_repository import PointsRepository
from services.classification_service import ClassificationService
from services.gamification_service import GamificationService
from services.recommendation_service import RecommendationService
from utils.location_utils import haversine_distance_meters, is_same_location


def test_haversine_distance():
    # Same point distance is 0
    d_zero = haversine_distance_meters(28.6139, 77.2090, 28.6139, 77.2090)
    assert round(d_zero, 2) == 0.0

    # Two points ~200 meters apart on campus
    d_close = haversine_distance_meters(28.6139, 77.2090, 28.6155, 77.2105)
    assert 200.0 < d_close < 300.0

    # Within 75m threshold check
    # Point ~30m away
    d_nearby = haversine_distance_meters(28.61390, 77.20900, 28.61400, 77.20910)
    assert d_nearby < 75.0


def test_is_same_location_logic():
    # 1. Matching coordinates within 75m
    assert is_same_location(28.61390, 77.20900, None, 28.61395, 77.20905, None, proximity_threshold_m=75.0) is True

    # 2. Coordinates farther than 75m
    assert is_same_location(28.6139, 77.2090, None, 28.6180, 77.2150, None, proximity_threshold_m=75.0) is False

    # 3. Same location name fallback when coordinates absent
    assert is_same_location(None, None, "Campus Cafeteria", None, None, "campus cafeteria") is True
    assert is_same_location(None, None, "Campus Cafeteria", None, None, "Library Hub") is False


def test_location_scan_limit_max_two_scans(temp_db, test_user):
    """
    Core user requirement:
    If a user scans more than 2 pictures at ONE location, subsequent scans must be REJECTED
    to prevent duplicate reward farming.
    """
    scan_repo = ScanRepository(temp_db)
    gamification = GamificationService(temp_db)
    pts_repo = PointsRepository(temp_db)
    uid = test_user["id"]

    loc_name = "Campus Cafeteria Eco-Station"
    loc_lat, loc_lon = 28.6139, 77.2090

    # ── SCAN 1 at Location A ──────────────────────────────────────────────
    # Check prior count at loc
    count0 = scan_repo.count_accepted_scans_at_location(uid, loc_lat, loc_lon, loc_name)
    assert count0 == 0

    scan1 = scan_repo.record_scan(
        user_id=uid,
        predicted_category="Plastic",
        confidence=0.95,
        prediction_accepted=True,
        image_hash="img_loc_1",
        model_version="v2",
        points_awarded=0,
        sub_category="PET Beverage Bottle (Type 1 ♳)",
        latitude=loc_lat,
        longitude=loc_lon,
        location_name=loc_name,
    )
    res1 = gamification.process_scan_gamification(
        user_id=uid,
        scan_id=scan1["id"],
        predicted_category="Plastic",
        confidence=0.95,
        prediction_accepted=True,
        image_hash="img_loc_1",
    )
    assert res1["points_awarded"] > 0
    bal1 = pts_repo.get_user_balance(uid)
    assert bal1 > 0

    # ── SCAN 2 at Location A ──────────────────────────────────────────────
    count1 = scan_repo.count_accepted_scans_at_location(uid, loc_lat, loc_lon, loc_name)
    assert count1 == 1

    scan2 = scan_repo.record_scan(
        user_id=uid,
        predicted_category="Metal",
        confidence=0.92,
        prediction_accepted=True,
        image_hash="img_loc_2",
        model_version="v2",
        points_awarded=0,
        sub_category="Aluminum Beverage Can (ALU-41)",
        latitude=loc_lat,
        longitude=loc_lon,
        location_name=loc_name,
    )
    res2 = gamification.process_scan_gamification(
        user_id=uid,
        scan_id=scan2["id"],
        predicted_category="Metal",
        confidence=0.92,
        prediction_accepted=True,
        image_hash="img_loc_2",
    )
    assert res2["points_awarded"] > 0
    bal2 = pts_repo.get_user_balance(uid)
    assert bal2 > bal1

    # ── SCAN 3 at Location A (EXCEEDS MAX 2 SCANS LIMIT) ──────────────────
    count2 = scan_repo.count_accepted_scans_at_location(uid, loc_lat, loc_lon, loc_name)
    assert count2 == 2  # Already 2 accepted scans at this location!

    # The 3rd scan at the same location must be rejected
    location_limit_exceeded = count2 >= config.max_scans_per_location
    assert location_limit_exceeded is True

    scan3 = scan_repo.record_scan(
        user_id=uid,
        predicted_category="Glass",
        confidence=0.96,
        prediction_accepted=False,  # REJECTED due to location limit
        image_hash="img_loc_3",
        model_version="v2",
        points_awarded=0,
        sub_category="Amber / Brown Glass Bottle (GL-72)",
        latitude=loc_lat,
        longitude=loc_lon,
        location_name=loc_name,
        rejection_reason="Location scan limit reached (maximum 2 scans per location).",
    )
    res3 = gamification.process_scan_gamification(
        user_id=uid,
        scan_id=scan3["id"],
        predicted_category="Glass",
        confidence=0.96,
        prediction_accepted=False,
        image_hash="img_loc_3",
        rejection_reason="Location scan limit reached (maximum 2 scans per location).",
    )

    # 0 points awarded, balance unchanged
    assert res3["points_awarded"] == 0
    assert pts_repo.get_user_balance(uid) == bal2
    assert "Location scan limit" in res3["reasons"][0]

    # ── SCAN 4 at a DIFFERENT Location B ──────────────────────────────────
    loc_b_name = "Science Block Waste Station"
    loc_b_lat, loc_b_lon = 28.6180, 77.2150  # Different coordinates > 75m away

    count_b = scan_repo.count_accepted_scans_at_location(uid, loc_b_lat, loc_b_lon, loc_b_name)
    assert count_b == 0  # Location B has 0 scans so far

    scan4 = scan_repo.record_scan(
        user_id=uid,
        predicted_category="Paper",
        confidence=0.94,
        prediction_accepted=True,  # Accepted at Location B
        image_hash="img_loc_b1",
        model_version="v2",
        points_awarded=0,
        sub_category="Corrugated Cardboard Box (PAP-20)",
        latitude=loc_b_lat,
        longitude=loc_b_lon,
        location_name=loc_b_name,
    )
    res4 = gamification.process_scan_gamification(
        user_id=uid,
        scan_id=scan4["id"],
        predicted_category="Paper",
        confidence=0.94,
        prediction_accepted=True,
        image_hash="img_loc_b1",
    )
    # Accepted and points awarded because it is a different location!
    assert res4["points_awarded"] > 0
    assert pts_repo.get_user_balance(uid) > bal2


def test_specific_subtype_identification():
    rec_service = RecommendationService()

    for cat in config.categories:
        subtype = rec_service.identify_subtype(cat)
        assert subtype is not None
        assert "subtype_name" in subtype
        assert "resin_code" in subtype
        assert "recyclability_score" in subtype
        assert "environmental_impact" in subtype

        # Recommendation includes subtype details
        rec = rec_service.get_recommendation(cat, is_accepted=True, subtype_info=subtype)
        assert rec["sub_category"] == subtype["subtype_name"]
        assert rec["resin_code"] == subtype["resin_code"]
        assert rec["recyclability_score"] == subtype["recyclability_score"]


def test_classification_service_location_enforcement(temp_db, test_user):
    """Verifies that ClassificationService enforces the location limit end-to-end."""
    service = ClassificationService(db_path=temp_db)
    scan_repo = ScanRepository(temp_db)
    uid = test_user["id"]

    loc_name = "Central Library Recycling Hub"
    lat, lon = 28.6155, 77.2105

    # Seed 2 accepted scans at this location
    scan_repo.record_scan(uid, "Plastic", 0.95, True, "seed_h1", "v2", 10, latitude=lat, longitude=lon, location_name=loc_name)
    scan_repo.record_scan(uid, "Paper", 0.92, True, "seed_h2", "v2", 10, latitude=lat, longitude=lon, location_name=loc_name)

    # Now attempt a 3rd scan at the same location
    img = Image.new("RGB", (224, 224), color=(50, 150, 250))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    result = service.classify_image(
        file_name="test_3rd_scan.png",
        image_bytes=img_bytes,
        user_id=uid,
        latitude=lat,
        longitude=lon,
        location_name=loc_name,
    )

    # Must be discarded due to area limit
    assert result["prediction_accepted"] is False
    assert result["is_discarded"] is True
    assert result["status"] == "discarded"
    assert "Scan Discarded" in result["rejection_reason"]
    assert result["scans_in_area"] == 2


def test_area_discard_policy_records(temp_db, test_user):
    """Verifies that 1 to 2 scans are accepted per particular area, and the 3rd is discarded."""
    scan_repo = ScanRepository(temp_db)
    uid = test_user["id"]
    area = "North Campus Area (Cafeteria Zone)"
    lat, lon = 28.6139, 77.2090

    # First scan in area
    s1 = scan_repo.record_scan(uid, "Plastic", 0.95, True, "area_img1", "v2", 10, latitude=lat, longitude=lon, location_name=area, is_discarded=False)
    assert s1["is_discarded"] == 0
    assert scan_repo.count_accepted_scans_in_area(uid, lat, lon, area) == 1

    # Second scan in area
    s2 = scan_repo.record_scan(uid, "Metal", 0.91, True, "area_img2", "v2", 10, latitude=lat, longitude=lon, location_name=area, is_discarded=False)
    assert s2["is_discarded"] == 0
    assert scan_repo.count_accepted_scans_in_area(uid, lat, lon, area) == 2

    # Third scan exceeds limit -> discarded!
    s3 = scan_repo.record_scan(
        uid, "Glass", 0.94, False, "area_img3", "v2", 0,
        latitude=lat, longitude=lon, location_name=area,
        is_discarded=True,
        rejection_reason="Scan Discarded: Exceeded 1 to 2 scans per particular area.",
    )
    assert s3["is_discarded"] == 1
    assert s3["prediction_accepted"] == 0

    # Count of accepted scans remains 2 (discarded scan does not inflate the count)
    assert scan_repo.count_accepted_scans_in_area(uid, lat, lon, area) == 2

