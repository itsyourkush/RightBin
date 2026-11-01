"""
Plant-a-Tree Award Service.
Manages eligibility verification, tree planting claim requests,
and administrative verification/fulfillment audits.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from config import config
from database.connection import get_db_connection
from repositories.points_repository import PointsRepository
from repositories.referral_repository import ReferralRepository
from repositories.user_repository import UserRepository
from utils.logging_config import logger


class TreeAwardService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.referral_repo = ReferralRepository(db_path)
        self.points_repo = PointsRepository(db_path)
        self.user_repo = UserRepository(db_path)

    def get_user_tree_status(self, user_id: int) -> Dict[str, Any]:
        """Checks user eligibility and prior claims for the Plant-a-Tree initiative."""
        profile = self.user_repo.get_profile(user_id)
        current_score = profile["green_score"] if profile else 0
        threshold = config.tree_award_points_threshold

        claims = self.referral_repo.get_user_tree_claims(user_id)
        has_pending = any(c["status"] in ("submitted", "verified") for c in claims)
        has_fulfilled = any(c["status"] == "fulfilled" for c in claims)

        is_eligible = bool(current_score >= threshold and not has_pending)

        return {
            "current_green_score": current_score,
            "threshold": threshold,
            "is_eligible": is_eligible,
            "has_pending_claim": has_pending,
            "has_fulfilled_claim": has_fulfilled,
            "claims": claims,
        }

    def submit_claim(self, user_id: int, notes: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Submits a tree planting award request."""
        status = self.get_user_tree_status(user_id)
        if not status["is_eligible"]:
            if status["has_pending_claim"]:
                return False, "You already have a tree planting claim pending review.", None
            return False, f"Requires at least {config.tree_award_points_threshold} Green Score points.", None

        claim = self.referral_repo.submit_tree_claim(user_id, notes=notes)
        logger.info(f"Tree award claim #{claim['id']} submitted by User {user_id}")
        return True, "Your Plant-a-Tree claim has been submitted for verification!", claim

    def review_claim(self, claim_id: int, status: str, admin_user_id: int, notes: str = "") -> Tuple[bool, str]:
        """Admin review of tree planting claim (status: 'verified', 'fulfilled', or 'rejected')."""
        valid_statuses = ("verified", "fulfilled", "rejected")
        if status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        success = self.referral_repo.update_tree_claim_status(
            claim_id=claim_id,
            status=status,
            reviewed_by=admin_user_id,
            notes=notes,
        )
        if success:
            logger.info(f"Tree claim #{claim_id} updated to '{status}' by Admin {admin_user_id}")
            return True, f"Claim #{claim_id} status updated to {status}."
        return False, "Failed to update claim status."
