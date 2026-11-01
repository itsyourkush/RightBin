"""
Unit tests for Leaderboard Service.
"""

import pytest
from services.leaderboard_service import LeaderboardService
from repositories.points_repository import PointsRepository
from repositories.user_repository import UserRepository
from utils.security import hash_password
from utils.time_utils import to_iso_string


def test_weekly_leaderboard_ordering_and_privacy(temp_db, test_user):
    user_repo = UserRepository(temp_db)
    pts_repo = PointsRepository(temp_db)
    leaderboard_svc = LeaderboardService(temp_db)

    # Create second user
    u2 = user_repo.create_user("Bob Champion", "bob_champ@example.com", hash_password("Secret123!"), display_name="BobTheRecycler")

    now = to_iso_string()
    # test_user gets 30 points this week
    pts_repo.record_transaction(test_user["id"], "waste_scan", 30, reference_id="s1")
    # u2 gets 50 points this week
    pts_repo.record_transaction(u2["id"], "waste_scan", 50, reference_id="s2")

    lb_data = leaderboard_svc.get_weekly_leaderboard(current_user_id=test_user["id"])
    rankings = lb_data["rankings"]

    assert len(rankings) >= 2
    # Rank 1: Bob (50 points)
    assert rankings[0]["user_id"] == u2["id"]
    assert rankings[0]["display_name"] == "BobTheRecycler"
    assert rankings[0]["weekly_points"] == 50

    # Rank 2: test_user (30 points)
    assert rankings[1]["user_id"] == test_user["id"]
    assert rankings[1]["display_name"] == "AliceEco"
    assert rankings[1]["weekly_points"] == 30
    assert rankings[1]["is_current_user"] is True

    # Privacy check: email addresses must NOT be exposed in leaderboard entries
    for entry in rankings:
        assert "email" not in entry
        assert "@" not in entry["display_name"]
