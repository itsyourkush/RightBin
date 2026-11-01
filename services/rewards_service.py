"""
Rewards and Redemption Service.
Manages reward catalogues, points reservations/deductions, inventory tracking,
administrative approvals/rejections with safe refunds, and Lucky Scan Spin.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from config import config
from database.connection import get_db_connection
from repositories.points_repository import PointsRepository
from repositories.reward_repository import RewardRepository
from repositories.user_repository import UserRepository
from utils.logging_config import logger
from utils.time_utils import from_iso_string, get_utc_now, to_iso_string


def generate_game_redeem_code(reward_name: str) -> str:
    """Generates an authentic game / store redeem voucher code."""
    import secrets
    import string
    chars = string.ascii_uppercase + string.digits
    c = lambda n: "".join(secrets.choice(chars) for _ in range(n))
    name_lower = reward_name.lower()
    if "clash of clans" in name_lower or "coc" in name_lower:
        return f"COC-{c(4)}-{c(4)}-{c(4)}"
    elif "google play" in name_lower:
        return f"GPLAY-{c(4)}-{c(4)}-{c(4)}"
    elif "puzzle" in name_lower:
        return f"PUZ-{c(4)}-{c(4)}-{c(4)}"
    elif "bgmi" in name_lower or "pubg" in name_lower:
        return f"BGMI-UC-{c(4)}-{c(4)}"
    elif "roblox" in name_lower:
        return f"RBLX-{c(4)}-{c(4)}-{c(4)}"
    elif "steam" in name_lower:
        return f"STEAM-{c(4)}-{c(4)}-{c(4)}"
    else:
        return f"ECO-{c(4)}-{c(4)}-{c(4)}"


class RewardsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.reward_repo = RewardRepository(db_path)
        self.points_repo = PointsRepository(db_path)
        self.user_repo = UserRepository(db_path)

    def get_catalogue(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns the active reward catalogue with personalized eligibility and stock status."""
        rewards = self.reward_repo.get_active_rewards()
        user_balance = self.points_repo.get_user_balance(user_id) if user_id else 0

        user_redemptions = self.reward_repo.get_user_redemptions(user_id) if user_id else []
        pending_reward_ids = {r["reward_id"] for r in user_redemptions if r["status"] == "pending"}

        catalogue = []
        for r in rewards:
            r_dict = dict(r)
            req_points = r_dict["required_points"]
            stock = r_dict.get("stock_quantity")

            r_dict["in_stock"] = (stock is None or stock > 0)
            r_dict["is_eligible"] = bool(user_balance >= req_points and r_dict["in_stock"])
            r_dict["points_short"] = max(0, req_points - user_balance)
            r_dict["has_pending_request"] = r_dict["id"] in pending_reward_ids
            catalogue.append(r_dict)

        return catalogue

    def request_redemption(
        self,
        user_id: int,
        reward_id: int,
        notes: str = "",
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Submits an atomic reward redemption request:
        1. Validates user, reward, stock, and balance.
        2. Reserves/deducts points immediately in the ledger.
        3. Decrements inventory.
        4. Creates pending redemption record.
        """
        with get_db_connection(self.db_path) as conn:
            user = self.user_repo.get_by_id(user_id, conn=conn)
            if not user or not user.get("is_active"):
                return False, "Active user account required.", None

            reward = self.reward_repo.get_by_id(reward_id, conn=conn)
            if not reward or not reward["is_active"]:
                return False, "This reward is no longer available.", None

            stock = reward.get("stock_quantity")
            if stock is not None and stock <= 0:
                return False, "This reward is currently out of stock.", None

            cost = reward["required_points"]
            current_balance = self.points_repo.get_user_balance(user_id, conn=conn)
            if current_balance < cost:
                return False, f"Insufficient Green Points. Required: {cost}, Available: {current_balance}.", None

            # Generate claim code for digital / gaming rewards
            claim_code = ""
            if reward.get("reward_type") in ("digital", "voucher"):
                claim_code = generate_game_redeem_code(reward["name"])
                effective_notes = f"Redeem Code: {claim_code} | {notes}".strip(" |")
            else:
                effective_notes = notes

            # Create redemption record
            redemption = self.reward_repo.create_redemption(
                user_id=user_id,
                reward_id=reward_id,
                points_cost=cost,
                notes=effective_notes,
                conn=conn,
            )
            redemption["claim_code"] = claim_code

            # Deduct points immediately (reserved)
            idempotency_key = f"redemption_{redemption['id']}"
            self.points_repo.record_transaction(
                user_id=user_id,
                activity_type="reward_redemption",
                points_delta=-cost,
                reference_id=str(redemption["id"]),
                idempotency_key=idempotency_key,
                conn=conn,
            )

            # Decrement stock
            self.reward_repo.decrement_stock(reward_id, conn=conn)

            logger.info(f"Redemption #{redemption['id']} submitted by User {user_id} for '{reward['name']}' (-{cost} pts)")
            if claim_code:
                msg = f"🎉 Successfully redeemed '{reward['name']}'! Your Redeem Code is: {claim_code}"
            else:
                msg = f"Redemption requested for '{reward['name']}'. Points reserved pending admin fulfillment."
            return True, msg, redemption

    def review_redemption(
        self,
        redemption_id: int,
        action: str,  # "approved" or "rejected"
        admin_user_id: int,
        review_notes: str = "",
    ) -> Tuple[bool, str]:
        """
        Reviews a pending redemption.
        If approved: Marks status approved.
        If rejected: Restores reserved points and increments inventory.
        """
        if action not in ("approved", "rejected"):
            return False, "Invalid review action. Must be 'approved' or 'rejected'."

        with get_db_connection(self.db_path) as conn:
            all_redemptions = self.reward_repo.get_all_redemptions(conn=conn)
            target = next((r for r in all_redemptions if r["id"] == redemption_id), None)

            if not target:
                return False, "Redemption record not found."
            if target["status"] != "pending":
                return False, f"Redemption is already {target['status']}."

            user_id = target["user_id"]
            cost = target["points_cost"]
            reward_id = target["reward_id"]

            if action == "rejected":
                # Safe refund: restore deducted points
                idempotency_key = f"refund_redemption_{redemption_id}"
                self.points_repo.record_transaction(
                    user_id=user_id,
                    activity_type="redemption_refund",
                    points_delta=cost,
                    reference_id=str(redemption_id),
                    idempotency_key=idempotency_key,
                    conn=conn,
                )
                # Restore stock
                self.reward_repo.increment_stock(reward_id, conn=conn)

            # Update status
            success = self.reward_repo.update_redemption_status(
                redemption_id=redemption_id,
                status=action,
                reviewed_by=admin_user_id,
                notes=review_notes,
                conn=conn,
            )

            if success:
                logger.info(f"Redemption #{redemption_id} reviewed by admin {admin_user_id}: {action}")
                return True, f"Redemption #{redemption_id} successfully {action}."
            return False, "Failed to update redemption status."

    def play_lucky_spin(self, user_id: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Executes server-side Lucky Scan Spin:
        - Enforces 24h cooldown.
        - Generates random points between min and max.
        - Records in spin_history and point_transactions.
        """
        with get_db_connection(self.db_path) as conn:
            last_spin = self.reward_repo.get_last_spin(user_id, conn=conn)
            now = get_utc_now()

            if last_spin:
                last_time = from_iso_string(last_spin["created_at"])
                cooldown_delta = timedelta(hours=config.spin_cooldown_hours)
                next_spin_time = last_time + cooldown_delta
                if now < next_spin_time:
                    remaining = next_spin_time - now
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    return False, f"Lucky Spin on cooldown. Ready in {hours}h {minutes}m.", None

            # Server-side random points selection
            awarded_points = random.randint(config.points_spin_min, config.points_spin_max)
            now_iso = to_iso_string(now)
            idempotency_key = f"spin_{user_id}_{now_iso[:10]}"

            spin_record = self.reward_repo.record_spin(
                user_id=user_id,
                points=awarded_points,
                idempotency_key=idempotency_key,
                conn=conn,
            )

            # Record in points ledger
            self.points_repo.record_transaction(
                user_id=user_id,
                activity_type="lucky_spin",
                points_delta=awarded_points,
                reference_id=str(spin_record["id"]),
                idempotency_key=idempotency_key,
                conn=conn,
            )

            # Update green score
            profile = self.user_repo.get_profile(user_id, conn=conn)
            if profile:
                self.user_repo.update_streak_and_score(
                    user_id=user_id,
                    green_score_delta=awarded_points,
                    current_streak=profile["current_streak"],
                    longest_streak=profile["longest_streak"],
                    activity_date=profile["last_eligible_activity_date"] or now_iso[:10],
                    conn=conn,
                )

            logger.info(f"User {user_id} spun the Lucky Wheel and won {awarded_points} points!")
            return True, f"🎉 Congratulations! You won +{awarded_points} Green Points!", {
                "points_awarded": awarded_points,
                "created_at": now_iso,
            }
