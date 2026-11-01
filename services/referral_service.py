"""
Referral Service.
Manages referral codes, links new registrations, prevents self-referrals,
and awards verification bonuses when referred users complete their first scan.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from config import config
from database.connection import get_db_connection
from repositories.points_repository import PointsRepository
from repositories.referral_repository import ReferralRepository
from repositories.user_repository import UserRepository
from utils.logging_config import logger
from utils.security import generate_referral_code


class ReferralService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.referral_repo = ReferralRepository(db_path)
        self.points_repo = PointsRepository(db_path)
        self.user_repo = UserRepository(db_path)

    def get_user_referral_code(self, user_id: int) -> str:
        """Generates a clean personal referral code for a user."""
        return f"ECO-USER{user_id:04d}"

    def parse_user_id_from_code(self, referral_code: str) -> Optional[int]:
        """Parses user ID from referral code string (e.g., 'ECO-USER0002')."""
        if not referral_code:
            return None
        code = referral_code.strip().upper()
        if code.startswith("ECO-USER"):
            num_part = code[len("ECO-USER"):]
            if num_part.isdigit():
                return int(num_part)
        return None

    def register_referral(self, referral_code: str, new_user_id: int) -> Tuple[bool, str]:
        """Validates referral code and records pending referral."""
        referrer_id = self.parse_user_id_from_code(referral_code)
        if referrer_id is None:
            return False, "Invalid referral code format."

        if referrer_id == new_user_id:
            return False, "Self-referral is not permitted."

        referrer = self.user_repo.get_by_id(referrer_id)
        if not referrer or not referrer.get("is_active"):
            return False, "Referral code does not belong to an active member."

        existing = self.referral_repo.get_by_referred_id(new_user_id)
        if existing:
            return False, "User has already used a referral code."

        bonus = config.points_referral_bonus
        self.referral_repo.create_referral(
            referrer_user_id=referrer_id,
            referred_user_id=new_user_id,
            referral_code=referral_code.strip().upper(),
            reward_points=bonus,
        )
        logger.info(f"Referral registered: User {new_user_id} referred by {referrer_id}")
        return True, "Referral code applied successfully."

    def check_and_reward_on_first_scan(self, new_user_id: int) -> bool:
        """
        Triggered when a user completes their first accepted scan.
        Awards referral bonus to the referrer if a pending referral exists.
        """
        with get_db_connection(self.db_path) as conn:
            ref = self.referral_repo.get_by_referred_id(new_user_id, conn=conn)
            if not ref or ref["status"] != "pending":
                return False

            ref_id = ref["id"]
            referrer_id = ref["referrer_user_id"]
            bonus = ref["reward_points"]
            idempotency_key = f"referral_{ref_id}"

            # Award bonus points to referrer
            self.points_repo.record_transaction(
                user_id=referrer_id,
                activity_type="referral_bonus",
                points_delta=bonus,
                reference_id=str(ref_id),
                idempotency_key=idempotency_key,
                conn=conn,
            )

            # Update green score of referrer
            profile = self.user_repo.get_profile(referrer_id, conn=conn)
            if profile:
                self.user_repo.update_streak_and_score(
                    user_id=referrer_id,
                    green_score_delta=bonus,
                    current_streak=profile["current_streak"],
                    longest_streak=profile["longest_streak"],
                    activity_date=profile["last_eligible_activity_date"] or "",
                    conn=conn,
                )

            # Mark referral as rewarded
            self.referral_repo.mark_referral_rewarded(ref_id, conn=conn)
            logger.info(f"Referral #{ref_id} verified: Awarded +{bonus} pts to referrer {referrer_id}")
            return True

    def get_user_referral_summary(self, user_id: int) -> Dict[str, Any]:
        """Returns referral statistics for a user's dashboard/profile."""
        code = self.get_user_referral_code(user_id)
        referrals = self.referral_repo.get_user_referrals(user_id)

        total_referred = len(referrals)
        successful_referrals = sum(1 for r in referrals if r["status"] == "rewarded")
        points_earned = sum(r["reward_points"] for r in referrals if r["status"] == "rewarded")

        return {
            "referral_code": code,
            "total_referred": total_referred,
            "successful_referrals": successful_referrals,
            "points_earned": points_earned,
            "referral_list": referrals,
        }
