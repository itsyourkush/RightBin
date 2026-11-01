"""
Tests for Database Operations and Repository layer.
Verifies foreign keys, constraints, transactions, and idempotency.
"""

import pytest
import sqlite3

from repositories.user_repository import UserRepository
from repositories.scan_repository import ScanRepository
from repositories.points_repository import PointsRepository
from repositories.badge_repository import BadgeRepository
from repositories.reward_repository import RewardRepository
from repositories.challenge_repository import ChallengeRepository
from database.connection import get_db_connection


def test_foreign_key_enforcement(temp_db):
    """Attempting to insert a scan with non-existent user_id must raise IntegrityError."""
    with pytest.raises(sqlite3.IntegrityError):
        with get_db_connection(temp_db) as conn:
            conn.execute(
                """
                INSERT INTO waste_scans (user_id, predicted_category, confidence, prediction_accepted, image_hash, model_version, points_awarded, created_at)
                VALUES (999999, 'Plastic', 0.95, 1, 'dummyhash', 'v1', 10, '2026-01-01T00:00:00+00:00')
                """
            )


def test_user_repository_crud(temp_db, test_user):
    repo = UserRepository(temp_db)
    user = repo.get_by_id(test_user["id"])
    assert user is not None
    assert user["email"] == "alice@example.com"

    profile = repo.get_profile(test_user["id"])
    assert profile is not None
    assert profile["display_name"] == "AliceEco"
    assert profile["green_score"] == 0

    repo.update_profile_display_name(test_user["id"], "AlicePlanet")
    updated = repo.get_profile(test_user["id"])
    assert updated["display_name"] == "AlicePlanet"


def test_points_repository_and_idempotency(temp_db, test_user):
    pts_repo = PointsRepository(temp_db)
    uid = test_user["id"]

    assert pts_repo.get_user_balance(uid) == 0

    # Add points
    tx1 = pts_repo.record_transaction(uid, "waste_scan", 10, reference_id="1", idempotency_key="scan_1")
    assert tx1["points_delta"] == 10
    assert pts_repo.get_user_balance(uid) == 10

    # Duplicate idempotency key must raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        pts_repo.record_transaction(uid, "waste_scan", 10, reference_id="1", idempotency_key="scan_1")

    # Balance remains 10
    assert pts_repo.get_user_balance(uid) == 10

    # Deduct points
    tx2 = pts_repo.record_transaction(uid, "reward_redemption", -5, reference_id="red_1", idempotency_key="red_1")
    assert pts_repo.get_user_balance(uid) == 5


def test_scan_repository_duplicate_check(temp_db, test_user):
    scan_repo = ScanRepository(temp_db)
    uid = test_user["id"]

    img_hash = "abc123hash987"
    scan_repo.record_scan(uid, "Plastic", 0.92, True, img_hash, "v1", 10)

    # Check finding duplicates
    dupes = scan_repo.find_duplicate_scans(img_hash)
    assert len(dupes) == 1
    assert dupes[0]["predicted_category"] == "Plastic"

    # Category count
    counts = scan_repo.count_scans_by_category(uid)
    assert counts.get("Plastic") == 1


def test_badge_awarding(temp_db, test_user):
    badge_repo = BadgeRepository(temp_db)
    uid = test_user["id"]

    badges = badge_repo.get_all_active_badges()
    assert len(badges) >= 4
    first_badge_id = badges[0]["id"]

    assert not badge_repo.has_badge(uid, first_badge_id)
    awarded = badge_repo.award_badge(uid, first_badge_id)
    assert awarded is True

    # Duplicate award should return False (unique constraint)
    awarded_again = badge_repo.award_badge(uid, first_badge_id)
    assert awarded_again is False

    user_badges = badge_repo.get_user_badges(uid)
    assert len(user_badges) == 1
    assert user_badges[0]["id"] == first_badge_id
