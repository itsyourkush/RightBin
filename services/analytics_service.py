"""
Analytics and Dashboard Data Service.
Aggregates user metrics, category distributions, weekly activity trends,
and gamification milestones into a unified data contract.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from config import config
from database.connection import get_db_connection
from repositories.badge_repository import BadgeRepository
from repositories.challenge_repository import ChallengeRepository
from repositories.points_repository import PointsRepository
from repositories.reward_repository import RewardRepository
from repositories.scan_repository import ScanRepository
from repositories.user_repository import UserRepository
from services.gamification_service import GamificationService
from utils.time_utils import get_utc_now, to_iso_string


class AnalyticsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.user_repo = UserRepository(db_path)
        self.scan_repo = ScanRepository(db_path)
        self.points_repo = PointsRepository(db_path)
        self.badge_repo = BadgeRepository(db_path)
        self.reward_repo = RewardRepository(db_path)
        self.challenge_repo = ChallengeRepository(db_path)
        self.gamification_service = GamificationService(db_path)

    def get_dashboard_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieves the complete dashboard dataset for an authenticated user.
        Fulfills Section 10 Dashboard Data Contract.
        """
        profile = self.user_repo.get_profile(user_id)
        if not profile:
            raise ValueError(f"User {user_id} not found.")

        # 1. Authoritative Point Balance & Green Score
        balance = self.points_repo.get_user_balance(user_id)
        green_score = profile.get("green_score", 0)

        # 2. Level calculation
        level_info = self.gamification_service.calculate_level_info(balance)

        # 3. Streaks
        current_streak = profile.get("current_streak", 0)
        longest_streak = profile.get("longest_streak", 0)

        # 4. Scans stats
        total_scans = self.scan_repo.count_total_scans(user_id, only_accepted=False)
        accepted_scans = self.scan_repo.count_total_scans(user_id, only_accepted=True)
        acceptance_rate = round((accepted_scans / total_scans * 100), 1) if total_scans > 0 else 0.0

        # 5. Category breakdown
        category_counts = self.scan_repo.count_scans_by_category(user_id, only_accepted=True)
        # Ensure all standard categories have an entry
        category_distribution = {cat: category_counts.get(cat, 0) for cat in config.categories}

        # 6. Earned Badges
        earned_badges = self.badge_repo.get_user_badges(user_id)

        # 7. Recent Scans (last 10)
        recent_scans = self.scan_repo.get_user_scans(user_id, limit=10)

        # 8. Weekly Activity Trend (Scans over last 7 days)
        now = get_utc_now()
        last_7_days = []
        for i in range(6, -1, -1):
            day_dt = now - timedelta(days=i)
            day_str = day_dt.strftime("%Y-%m-%d")
            day_label = day_dt.strftime("%a")  # Mon, Tue, etc.
            count = self.scan_repo.count_accepted_scans_today(user_id, day_str)
            last_7_days.append({"date": day_str, "day": day_label, "scans": count})

        # 9. Active Challenges Progress
        all_challenges = self.challenge_repo.get_active_challenges()
        user_parts = {p["challenge_id"]: p for p in self.challenge_repo.get_user_all_participations(user_id)}
        challenges_progress = []
        for ch in all_challenges:
            part = user_parts.get(ch["id"])
            challenges_progress.append({
                "title": ch["title"],
                "progress": part["progress"] if part else 0,
                "target": ch["criteria_value"],
                "is_completed": bool(part and part.get("completed_at")),
            })

        # 10. Reward Eligibility Quick Stats
        rewards = self.reward_repo.get_active_rewards()
        eligible_rewards_count = sum(1 for r in rewards if balance >= r["required_points"])

        return {
            "user_id": user_id,
            "display_name": profile["display_name"],
            "total_scans": total_scans,
            "accepted_scans": accepted_scans,
            "acceptance_rate": acceptance_rate,
            "green_score": green_score,
            "points_balance": balance,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "level_info": level_info,
            "category_distribution": category_distribution,
            "earned_badges": earned_badges,
            "recent_scans": recent_scans,
            "weekly_trend": last_7_days,
            "challenges_progress": challenges_progress,
            "eligible_rewards_count": eligible_rewards_count,
        }

    def get_system_analytics(self) -> Dict[str, Any]:
        """Admin-level system overview analytics."""
        with get_db_connection(self.db_path) as conn:
            cur = conn.cursor()
            total_users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            total_scans = cur.execute("SELECT COUNT(*) FROM waste_scans").fetchone()[0]
            accepted_scans = cur.execute("SELECT COUNT(*) FROM waste_scans WHERE prediction_accepted = 1").fetchone()[0]
            total_points = cur.execute("SELECT COALESCE(SUM(points_delta), 0) FROM point_transactions WHERE points_delta > 0").fetchone()[0]
            total_redemptions = cur.execute("SELECT COUNT(*) FROM reward_redemptions").fetchone()[0]
            pending_redemptions = cur.execute("SELECT COUNT(*) FROM reward_redemptions WHERE status = 'pending'").fetchone()[0]
            total_tree_claims = cur.execute("SELECT COUNT(*) FROM tree_award_claims").fetchone()[0]

            return {
                "total_users": total_users,
                "total_scans": total_scans,
                "accepted_scans": accepted_scans,
                "total_points_distributed": total_points,
                "total_redemptions": total_redemptions,
                "pending_redemptions": pending_redemptions,
                "total_tree_claims": total_tree_claims,
            }
