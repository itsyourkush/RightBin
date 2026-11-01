"""
User and UserProfile Repository.
Handles all parameterized database operations for accounts and profiles.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from database.connection import get_db_connection
from utils.time_utils import get_utc_now, to_iso_string


class UserRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _dict_from_row(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        return dict(row) if row is not None else None

    def create_user(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str = "user",
        display_name: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Creates a new user and an associated user_profile atomically."""
        now = to_iso_string()
        disp_name = display_name if display_name else name.split()[0]

        def _execute(c: sqlite3.Connection) -> Dict[str, Any]:
            cur = c.cursor()
            cur.execute(
                """
                INSERT INTO users (name, email, password_hash, role, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (name.strip(), email.strip().lower(), password_hash, role, now),
            )
            user_id = cur.lastrowid
            cur.execute(
                """
                INSERT INTO user_profiles (user_id, display_name, green_score, current_streak, longest_streak, created_at, updated_at)
                VALUES (?, ?, 0, 0, 0, ?, ?)
                """,
                (user_id, disp_name, now, now),
            )
            return {
                "id": user_id,
                "name": name.strip(),
                "email": email.strip().lower(),
                "role": role,
                "is_active": 1,
                "created_at": now,
            }

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_by_id(self, user_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        """Retrieves user by ID."""
        query = "SELECT id, name, email, role, is_active, created_at FROM users WHERE id = ?"

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (user_id,)).fetchone()
            return self._dict_from_row(row)

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_by_email(self, email: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        """Retrieves user with password_hash for authentication."""
        query = "SELECT id, name, email, password_hash, role, is_active, created_at FROM users WHERE email = ?"

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (email.strip().lower(),)).fetchone()
            return self._dict_from_row(row)

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_profile(self, user_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        """Retrieves profile info joined with basic user details."""
        query = """
            SELECT u.id, u.name, u.email, u.role, u.is_active,
                   p.display_name, p.green_score, p.current_streak, p.longest_streak,
                   p.last_eligible_activity_date, p.created_at, p.updated_at
            FROM users u
            JOIN user_profiles p ON u.id = p.user_id
            WHERE u.id = ?
        """

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (user_id,)).fetchone()
            return self._dict_from_row(row)

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def update_profile_display_name(self, user_id: int, display_name: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Updates user display name."""
        now = to_iso_string()
        query = "UPDATE user_profiles SET display_name = ?, updated_at = ? WHERE user_id = ?"

        def _execute(c: sqlite3.Connection) -> bool:
            res = c.execute(query, (display_name.strip(), now, user_id))
            return res.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def update_password(self, user_id: int, new_password_hash: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Updates user password hash."""
        query = "UPDATE users SET password_hash = ? WHERE id = ?"

        def _execute(c: sqlite3.Connection) -> bool:
            res = c.execute(query, (new_password_hash, user_id))
            return res.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def update_streak_and_score(
        self,
        user_id: int,
        green_score_delta: int,
        current_streak: int,
        longest_streak: int,
        activity_date: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Updates engagement metrics (green_score, streaks, last_activity_date) atomically."""
        now = to_iso_string()
        query = """
            UPDATE user_profiles
            SET green_score = green_score + ?,
                current_streak = ?,
                longest_streak = ?,
                last_eligible_activity_date = ?,
                updated_at = ?
            WHERE user_id = ?
        """

        def _execute(c: sqlite3.Connection) -> bool:
            res = c.execute(query, (green_score_delta, current_streak, longest_streak, activity_date, now, user_id))
            return res.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_all_users(self, limit: int = 100, offset: int = 0, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        """Retrieves list of users for admin management."""
        query = """
            SELECT u.id, u.name, u.email, u.role, u.is_active, u.created_at,
                   p.display_name, p.green_score, p.current_streak
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            ORDER BY u.id DESC
            LIMIT ? OFFSET ?
        """

        def _execute(c: sqlite3.Connection) -> List[Dict[str, Any]]:
            rows = c.execute(query, (limit, offset)).fetchall()
            return [dict(r) for r in rows]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def set_user_active(self, user_id: int, is_active: bool, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Enables or disables a user account."""
        query = "UPDATE users SET is_active = ? WHERE id = ?"

        def _execute(c: sqlite3.Connection) -> bool:
            res = c.execute(query, (1 if is_active else 0, user_id))
            return res.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)
