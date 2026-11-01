"""
Leaderboard Service.
Calculates weekly point rankings, applies consistent tie-breaking rules,
and returns privacy-safe user statistics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from config import config
from database.connection import get_db_connection
from repositories.points_repository import PointsRepository
from repositories.user_repository import UserRepository
from utils.time_utils import get_end_of_week_utc, get_start_of_week_utc, to_iso_string


class LeaderboardService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.points_repo = PointsRepository(db_path)
        self.user_repo = UserRepository(db_path)

    def get_weekly_leaderboard(
        self,
        current_user_id: Optional[int] = None,
        limit: int = 25,
    ) -> Dict[str, Any]:
        """
        Returns weekly rankings for the current calendar week (Monday 00:00:00 UTC to Sunday 23:59:59 UTC).
        Includes user rank, privacy-safe display name, weekly points, and current user position.
        """
        start_dt = get_start_of_week_utc()
        end_dt = get_end_of_week_utc()
        start_iso = to_iso_string(start_dt)
        end_iso = to_iso_string(end_dt)

        raw_rankings = self.points_repo.get_weekly_leaderboard(
            start_iso=start_iso,
            end_iso=end_iso,
            limit=limit,
        )

        ranked_list = []
        user_position = None

        for idx, row in enumerate(raw_rankings, start=1):
            entry = {
                "rank": idx,
                "user_id": row["user_id"],
                "display_name": row["display_name"] or f"EcoUser_{row['user_id']}",
                "weekly_points": row["weekly_points"],
                "green_score": row["green_score"],
                "is_current_user": bool(current_user_id and row["user_id"] == current_user_id),
            }
            ranked_list.append(entry)
            if current_user_id and row["user_id"] == current_user_id:
                user_position = entry

        # If current user is not in top limit, calculate their standalone weekly points
        if current_user_id and user_position is None:
            user_weekly_pts = self.points_repo.get_weekly_points_for_user(
                current_user_id, start_iso, end_iso
            )
            profile = self.user_repo.get_profile(current_user_id)
            user_position = {
                "rank": "25+",
                "user_id": current_user_id,
                "display_name": profile["display_name"] if profile else "You",
                "weekly_points": user_weekly_pts,
                "green_score": profile["green_score"] if profile else 0,
                "is_current_user": True,
            }

        return {
            "week_start": start_iso,
            "week_end": end_iso,
            "rankings": ranked_list,
            "current_user_position": user_position,
        }
