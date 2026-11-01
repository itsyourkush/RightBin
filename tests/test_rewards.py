"""
Unit tests for Rewards and Redemption Service.
"""

import pytest
from services.rewards_service import RewardsService
from repositories.points_repository import PointsRepository
from repositories.reward_repository import RewardRepository


def test_reward_eligibility_and_redemption_flow(temp_db, test_user, test_admin):
    rewards_svc = RewardsService(temp_db)
    pts_repo = PointsRepository(temp_db)
    reward_repo = RewardRepository(temp_db)
    uid = test_user["id"]
    admin_id = test_admin["id"]

    # Initial catalogue: user has 0 points, so not eligible for 500-pt reward
    catalogue = rewards_svc.get_catalogue(uid)
    tote_bag = next(r for r in catalogue if "Tote Bag" in r["name"])
    assert tote_bag["is_eligible"] is False
    assert tote_bag["points_short"] == 500

    # Try requesting redemption with 0 balance -> Rejected
    ok, msg, _ = rewards_svc.request_redemption(uid, tote_bag["id"])
    assert ok is False
    assert "insufficient" in msg.lower()

    # Credit 600 points to user
    pts_repo.record_transaction(uid, "test_credit", 600, reference_id="test")
    assert pts_repo.get_user_balance(uid) == 600

    # Now eligible!
    catalogue = rewards_svc.get_catalogue(uid)
    tote_bag = next(r for r in catalogue if "Tote Bag" in r["name"])
    assert tote_bag["is_eligible"] is True

    # Request redemption: 500 points should be deducted immediately
    initial_stock = tote_bag["stock_quantity"]
    ok, msg, red = rewards_svc.request_redemption(uid, tote_bag["id"])
    assert ok is True
    assert red["status"] == "pending"
    # Balance should now be 100
    assert pts_repo.get_user_balance(uid) == 100

    # Stock should be decremented
    updated_reward = reward_repo.get_by_id(tote_bag["id"])
    assert updated_reward["stock_quantity"] == initial_stock - 1

    # Admin Rejection: should refund 500 points and restore stock
    ok, msg = rewards_svc.review_redemption(red["id"], "rejected", admin_id, "Out of local stock")
    assert ok is True
    assert pts_repo.get_user_balance(uid) == 600
    restored_reward = reward_repo.get_by_id(tote_bag["id"])
    assert restored_reward["stock_quantity"] == initial_stock


def test_lucky_spin_and_cooldown(temp_db, test_user):
    rewards_svc = RewardsService(temp_db)
    pts_repo = PointsRepository(temp_db)
    uid = test_user["id"]

    # First spin succeeds
    ok, msg, spin_data = rewards_svc.play_lucky_spin(uid)
    assert ok is True
    pts = spin_data["points_awarded"]
    assert 5 <= pts <= 25
    assert pts_repo.get_user_balance(uid) == pts

    # Second spin immediately afterwards should be blocked by cooldown
    ok, msg, _ = rewards_svc.play_lucky_spin(uid)
    assert ok is False
    assert "cooldown" in msg.lower()


def test_gaming_rewards_and_code_generation(temp_db, test_user):
    from services.rewards_service import generate_game_redeem_code
    rewards_svc = RewardsService(temp_db)
    pts_repo = PointsRepository(temp_db)
    uid = test_user["id"]

    # Verify code generation prefixes
    coc_code = generate_game_redeem_code("Clash of Clans 500 Gems Voucher")
    assert coc_code.startswith("COC-")

    gplay_code = generate_game_redeem_code("Google Play Store $5 Gift Code")
    assert gplay_code.startswith("GPLAY-")

    puzzle_code = generate_game_redeem_code("Puzzle Games VIP Booster Code")
    assert puzzle_code.startswith("PUZ-")

    # Give user 300 points
    pts_repo.record_transaction(uid, "test_game_points", 300, reference_id="game_test")

    # Redeem Puzzle Games code (100 pts)
    catalogue = rewards_svc.get_catalogue(uid)
    puzzle_reward = next(r for r in catalogue if "Puzzle" in r["name"])
    ok, msg, red = rewards_svc.request_redemption(uid, puzzle_reward["id"])

    assert ok is True
    assert "PUZ-" in red["claim_code"]
    assert "claim_code" in red
    assert pts_repo.get_user_balance(uid) == 200


def test_dustbin_wayfinding_categories():
    from components.dustbin_guide import STANDARD_DUSTBINS
    assert len(STANDARD_DUSTBINS) == 4

    bin_colors = [b["color"] for b in STANDARD_DUSTBINS]
    assert "#1E88E5" in bin_colors  # Blue bin
    assert "#2E7D32" in bin_colors  # Green bin
    assert "#F57C00" in bin_colors  # Yellow bin

    # Verify Plastic maps to Blue bin
    blue_bin = next(b for b in STANDARD_DUSTBINS if b["id"] == "blue_bin")
    assert "Plastic" in blue_bin["matched_categories"]
    assert "Paper" in blue_bin["matched_categories"]

    # Verify Organic maps to Green bin
    green_bin = next(b for b in STANDARD_DUSTBINS if b["id"] == "green_bin")
    assert "Organic" in green_bin["matched_categories"]

