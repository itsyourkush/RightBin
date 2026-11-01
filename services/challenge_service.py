"""
Challenge Service.
Manages eco-challenges, retrieves active challenges paired with user progress,
and supports administrative challenge creation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from database.connection import get_db_connection
from repositories.challenge_repository import ChallengeRepository
from utils.time_utils import to_iso_string


class ChallengeService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.challenge_repo = ChallengeRepository(db_path)

    def get_challenges_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Returns all currently active challenges enriched with user's progress and completion status."""
        active = self.challenge_repo.get_active_challenges()
        user_participations = {
            p["challenge_id"]: p
            for p in self.challenge_repo.get_user_all_participations(user_id)
        }

        results = []
        for ch in active:
            ch_dict = dict(ch)
            ch_id = ch_dict["id"]
            part = user_participations.get(ch_id)

            progress = part["progress"] if part else 0
            is_completed = bool(part and part.get("completed_at"))
            is_rewarded = bool(part and part.get("rewarded_at"))

            target = ch_dict["criteria_value"]
            progress_pct = min(progress / target, 1.0) if target > 0 else 1.0

            ch_dict["user_progress"] = progress
            ch_dict["progress_percentage"] = round(progress_pct, 2)
            ch_dict["is_completed"] = is_completed
            ch_dict["is_rewarded"] = is_rewarded

            results.append(ch_dict)

        return results

    def create_challenge(
        self,
        title: str,
        description: str,
        criteria_type: str,
        criteria_value: int,
        target_category: Optional[str],
        bonus_points: int,
        start_at: str,
        end_at: str,
    ) -> Dict[str, Any]:
        """Creates a new eco-challenge definition (Admin operation)."""
        with get_db_connection(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO challenges (
                    title, description, criteria_type, criteria_value,
                    target_category, bonus_points, start_at, end_at, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (title, description, criteria_type, criteria_value, target_category, bonus_points, start_at, end_at),
            )
            ch_id = cur.lastrowid
            return {
                "id": ch_id,
                "title": title,
                "description": description,
                "criteria_type": criteria_type,
                "criteria_value": criteria_value,
                "target_category": target_category,
                "bonus_points": bonus_points,
                "start_at": start_at,
                "end_at": end_at,
            }
