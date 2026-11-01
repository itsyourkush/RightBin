"""
Gamification and Scoring Service.
Maintains the authoritative Green Score, evaluates streaks, checks duplicate activities,
awards level progressions, evaluates badges, and updates eco-challenges.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from config import config
from database.connection import get_db_connection
from repositories.badge_repository import BadgeRepository
from repositories.challenge_repository import ChallengeRepository
from repositories.points_repository import PointsRepository
from repositories.scan_repository import ScanRepository
from repositories.user_repository import UserRepository
from utils.logging_config import logger
from utils.time_utils import calculate_streak, get_date_string, to_iso_string


class GamificationService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.user_repo = UserRepository(db_path)
        self.scan_repo = ScanRepository(db_path)
        self.points_repo = PointsRepository(db_path)
        self.badge_repo = BadgeRepository(db_path)
        self.challenge_repo = ChallengeRepository(db_path)

    def calculate_level_info(self, total_points: int) -> Dict[str, Any]:
        """Calculates current level, next level, and progress percentage."""
        levels = config.levels  # (name, min_points, sort_order)
        current_level = levels[0][0]
        next_level = None
        current_threshold = 0
        next_threshold = None

        for idx, (name, min_pts, _) in enumerate(levels):
            if total_points >= min_pts:
                current_level = name
                current_threshold = min_pts
                if idx + 1 < len(levels):
                    next_level = levels[idx + 1][0]
                    next_threshold = levels[idx + 1][1]
                else:
                    next_level = None
                    next_threshold = None

        if next_threshold is not None:
            span = next_threshold - current_threshold
            earned = total_points - current_threshold
            progress = min(max(earned / span, 0.0), 1.0)
            points_needed = next_threshold - total_points
        else:
            progress = 1.0
            points_needed = 0

        return {
            "current_level": current_level,
            "next_level": next_level,
            "current_threshold": current_threshold,
            "next_threshold": next_threshold,
            "points_needed": points_needed,
            "progress": round(progress, 4),
        }

    def process_scan_gamification(
        self,
        user_id: int,
        scan_id: int,
        predicted_category: str,
        confidence: float,
        prediction_accepted: bool,
        image_hash: str,
        rejection_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes scoring, streaks, badges, and challenge updates for a recorded scan.
        Guarantees that points are server-side and recorded in atomic transactions.
        """
        with get_db_connection(self.db_path) as conn:
            profile = self.user_repo.get_profile(user_id, conn=conn)
            if not profile:
                raise ValueError(f"User {user_id} profile not found.")

            today_str = get_date_string()

            # 1. Duplicate check: has this image hash been processed for this user previously?
            existing_dupes = self.scan_repo.find_duplicate_scans(image_hash, user_id=user_id, conn=conn)
            # Since current scan is already inserted or we check > 1:
            is_duplicate = len(existing_dupes) > 1

            points_to_award = 0
            is_first_scan_of_day = False
            reasons = []

            if not prediction_accepted:
                reasons.append(rejection_reason or "Prediction confidence below threshold; no points awarded.")
            elif is_duplicate:
                reasons.append("Identical image already scanned previously; duplicate scan awarded 0 points.")
            else:
                # Base classification points
                base_pts = config.points_accepted_classification
                points_to_award += base_pts
                reasons.append(f"+{base_pts} pts: Valid {predicted_category} classification.")

                # First scan of the day check
                accepted_today = self.scan_repo.count_accepted_scans_today(user_id, today_str, conn=conn)
                # If this is the only accepted scan today (count == 1)
                if accepted_today <= 1:
                    is_first_scan_of_day = True
                    bonus = config.points_first_scan_of_day
                    points_to_award += bonus
                    reasons.append(f"+{bonus} pts: First eligible scan of the day bonus!")

            # 2. Record points ledger transaction (if > 0)
            if points_to_award > 0:
                idempotency_key = f"scan_{scan_id}"
                self.points_repo.record_transaction(
                    user_id=user_id,
                    activity_type="waste_scan",
                    points_delta=points_to_award,
                    reference_id=str(scan_id),
                    idempotency_key=idempotency_key,
                    conn=conn,
                )

                # Update waste_scans points_awarded column
                conn.execute(
                    "UPDATE waste_scans SET points_awarded = ? WHERE id = ?",
                    (points_to_award, scan_id),
                )

            # 3. Update Streaks and Green Score
            last_date = profile["last_eligible_activity_date"]
            curr_streak = profile["current_streak"]
            longest_streak = profile["longest_streak"]

            if prediction_accepted and not is_duplicate:
                streak_delta, is_new_day = calculate_streak(last_date, today_str)
                if streak_delta == 1:
                    curr_streak += 1
                elif streak_delta == -1:
                    curr_streak = 1
                # If diff == 0, curr_streak unchanged

                longest_streak = max(longest_streak, curr_streak)
                last_date = today_str

                self.user_repo.update_streak_and_score(
                    user_id=user_id,
                    green_score_delta=points_to_award,
                    current_streak=curr_streak,
                    longest_streak=longest_streak,
                    activity_date=last_date,
                    conn=conn,
                )

            # 4. Evaluate Badges
            unlocked_badges = self._evaluate_and_award_badges(
                user_id=user_id,
                current_streak=curr_streak,
                conn=conn,
            )

            # 5. Evaluate Active Challenges
            completed_challenges = self._evaluate_challenges(
                user_id=user_id,
                predicted_category=predicted_category,
                current_streak=curr_streak,
                conn=conn,
            )

            # Recalculate balance and level info
            new_balance = self.points_repo.get_user_balance(user_id, conn=conn)
            level_info = self.calculate_level_info(new_balance)

            return {
                "points_awarded": points_to_award,
                "is_first_scan_of_day": is_first_scan_of_day,
                "is_duplicate": is_duplicate,
                "reasons": reasons,
                "current_streak": curr_streak,
                "longest_streak": longest_streak,
                "balance": new_balance,
                "level_info": level_info,
                "unlocked_badges": unlocked_badges,
                "completed_challenges": completed_challenges,
            }

    def _evaluate_and_award_badges(
        self,
        user_id: int,
        current_streak: int,
        conn: sqlite3.Connection,
    ) -> List[Dict[str, Any]]:
        """Evaluates badge qualification criteria and awards badges."""
        all_badges = self.badge_repo.get_all_active_badges(conn=conn)
        already_owned_ids = {b["id"] for b in self.badge_repo.get_user_badges(user_id, conn=conn)}

        total_accepted = self.scan_repo.count_total_scans(user_id, only_accepted=True, conn=conn)
        category_counts = self.scan_repo.count_scans_by_category(user_id, only_accepted=True, conn=conn)

        unlocked = []
        for badge in all_badges:
            b_id = badge["id"]
            if b_id in already_owned_ids:
                continue

            c_type = badge["criteria_type"]
            c_val = badge["criteria_value"]
            qualified = False

            if c_type == "total_scans" and total_accepted >= c_val:
                qualified = True
            elif c_type == "streak_days" and current_streak >= c_val:
                qualified = True
            elif c_type.startswith("category_"):
                target_cat = c_type.split("category_")[1]
                if category_counts.get(target_cat, 0) >= c_val:
                    qualified = True

            if qualified:
                awarded = self.badge_repo.award_badge(user_id, b_id, conn=conn)
                if awarded:
                    unlocked.append(badge)
                    logger.info(f"Badge '{badge['name']}' awarded to user {user_id}")

        return unlocked

    def _evaluate_challenges(
        self,
        user_id: int,
        predicted_category: str,
        current_streak: int,
        conn: sqlite3.Connection,
    ) -> List[Dict[str, Any]]:
        """Evaluates active challenges, increments progress, and awards bonuses."""
        active_challenges = self.challenge_repo.get_active_challenges(conn=conn)
        completed = []

        for ch in active_challenges:
            ch_id = ch["id"]
            c_type = ch["criteria_type"]
            target_val = ch["criteria_value"]
            target_cat = ch.get("target_category")

            part = self.challenge_repo.get_user_participation(user_id, ch_id, conn=conn)
            if part and part.get("completed_at"):
                # Already finished
                continue

            curr_progress = part["progress"] if part else 0

            # Increment logic based on criteria
            should_increment = False
            if c_type == "scan_count":
                should_increment = True
            elif c_type == "category_scan" and predicted_category == target_cat:
                should_increment = True
            elif c_type == "streak_days":
                curr_progress = current_streak

            if should_increment and c_type != "streak_days":
                curr_progress += 1

            is_done = curr_progress >= target_val
            rewarded = False

            if is_done and (not part or not part.get("rewarded_at")):
                # Award bonus points
                bonus = ch["bonus_points"]
                idempotency_key = f"challenge_{ch_id}_user_{user_id}"
                if not self.points_repo.has_idempotency_key(idempotency_key, conn=conn):
                    self.points_repo.record_transaction(
                        user_id=user_id,
                        activity_type="challenge_completion",
                        points_delta=bonus,
                        reference_id=str(ch_id),
                        idempotency_key=idempotency_key,
                        conn=conn,
                    )
                    rewarded = True
                    completed.append({**ch, "bonus_awarded": bonus})
                    logger.info(f"Challenge '{ch['title']}' completed by user {user_id} (+{bonus} pts)")

            self.challenge_repo.upsert_progress(
                user_id=user_id,
                challenge_id=ch_id,
                progress=curr_progress,
                completed=is_done,
                rewarded=rewarded or bool(part and part.get("rewarded_at")),
                conn=conn,
            )

        return completed
