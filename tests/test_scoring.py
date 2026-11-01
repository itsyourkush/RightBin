"""
Unit tests for Gamification and Scoring Service.
"""

import pytest
from services.gamification_service import GamificationService
from repositories.scan_repository import ScanRepository
from repositories.points_repository import PointsRepository
from repositories.user_repository import UserRepository


def test_first_scan_awards_bonus(temp_db, test_user):
    gamification = GamificationService(temp_db)
    scan_repo = ScanRepository(temp_db)
    pts_repo = PointsRepository(temp_db)
    uid = test_user["id"]

    # Record first scan
    scan = scan_repo.record_scan(uid, "Plastic", 0.95, True, "unique_hash_1", "v1", 0)
    result = gamification.process_scan_gamification(
        user_id=uid,
        scan_id=scan["id"],
        predicted_category="Plastic",
        confidence=0.95,
        prediction_accepted=True,
        image_hash="unique_hash_1",
    )

    # 10 base + 5 first scan of day = 15 points
    assert result["points_awarded"] == 15
    assert result["is_first_scan_of_day"] is True
    assert result["current_streak"] == 1
    assert pts_repo.get_user_balance(uid) == 15

    # Check Rookie badge unlocked
    unlocked_names = [b["name"] for b in result["unlocked_badges"]]
    assert "Recycling Rookie" in unlocked_names


def test_duplicate_scan_awards_zero_points(temp_db, test_user):
    gamification = GamificationService(temp_db)
    scan_repo = ScanRepository(temp_db)
    uid = test_user["id"]

    same_hash = "repeated_bottle_hash"
    # First scan of this item
    scan1 = scan_repo.record_scan(uid, "Metal", 0.90, True, same_hash, "v1", 0)
    res1 = gamification.process_scan_gamification(uid, scan1["id"], "Metal", 0.90, True, same_hash)
    assert res1["points_awarded"] > 0

    # Second scan with identical hash
    scan2 = scan_repo.record_scan(uid, "Metal", 0.90, True, same_hash, "v1", 0)
    res2 = gamification.process_scan_gamification(uid, scan2["id"], "Metal", 0.90, True, same_hash)
    assert res2["is_duplicate"] is True
    assert res2["points_awarded"] == 0


def test_low_confidence_awards_zero_points(temp_db, test_user):
    gamification = GamificationService(temp_db)
    scan_repo = ScanRepository(temp_db)
    uid = test_user["id"]

    scan = scan_repo.record_scan(uid, "Glass", 0.40, False, "blur_hash_3", "v1", 0)
    res = gamification.process_scan_gamification(uid, scan["id"], "Glass", 0.40, False, "blur_hash_3")

    assert res["points_awarded"] == 0
    assert "below threshold" in res["reasons"][0]


def test_level_calculation(temp_db):
    gamification = GamificationService(temp_db)

    lvl0 = gamification.calculate_level_info(0)
    assert lvl0["current_level"] == "Green Starter"
    assert lvl0["next_level"] == "Eco Learner"

    lvl1 = gamification.calculate_level_info(60)
    assert lvl1["current_level"] == "Eco Learner"
    assert lvl1["next_level"] == "Smart Recycler"

    lvl_max = gamification.calculate_level_info(1000)
    assert lvl_max["current_level"] == "Planet Protector"
    assert lvl_max["next_level"] is None
