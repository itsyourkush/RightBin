"""
Time and Date utility functions.
Enforces UTC storage and standard calendar calculations for streaks and weekly leaderboards.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional


def get_utc_now() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def to_iso_string(dt: Optional[datetime] = None) -> str:
    """Converts a datetime to an ISO 8601 string. Defaults to now UTC."""
    if dt is None:
        dt = get_utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def from_iso_string(s: str) -> datetime:
    """Parses an ISO 8601 string into a timezone-aware UTC datetime."""
    # Replace trailing 'Z' if present
    clean_s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def get_date_string(dt: Optional[datetime] = None) -> str:
    """Returns YYYY-MM-DD date string for streak calculation."""
    if dt is None:
        dt = get_utc_now()
    return dt.strftime("%Y-%m-%d")


def get_start_of_week_utc(dt: Optional[datetime] = None) -> datetime:
    """
    Returns Monday 00:00:00 UTC for the given datetime or current week.
    Standardized boundary for weekly leaderboard.
    """
    if dt is None:
        dt = get_utc_now()
    # weekday(): Monday is 0 and Sunday is 6
    start = dt - timedelta(days=dt.weekday(), hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)
    return start.replace(tzinfo=timezone.utc)


def get_end_of_week_utc(dt: Optional[datetime] = None) -> datetime:
    """Returns Sunday 23:59:59.999999 UTC for the given datetime."""
    start = get_start_of_week_utc(dt)
    return start + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)


def calculate_streak(last_activity_date_str: Optional[str], current_date_str: Optional[str] = None) -> Tuple[int, bool]:
    """
    Given the last eligible activity date (YYYY-MM-DD),
    determines if today is a continuation (+1), already counted today (+0), or broken (reset to 1).
    Returns (streak_delta, is_new_day_activity)
    """
    if current_date_str is None:
        current_date_str = get_date_string()

    if not last_activity_date_str:
        # First activity ever
        return 1, True

    d_last = datetime.strptime(last_activity_date_str, "%Y-%m-%d").date()
    d_curr = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    diff = (d_curr - d_last).days

    if diff == 0:
        # Already logged today
        return 0, False
    elif diff == 1:
        # Consecutive day!
        return 1, True
    else:
        # Streak broken, reset to 1
        return -1, True
