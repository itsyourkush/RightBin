"""
Badge Repository.
Handles queries for available badges and user badge awards.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from database.connection import get_db_connection
from utils.time_utils import to_iso_string


class BadgeRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_all_active_badges(self, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM badges WHERE is_active = 1 ORDER BY id ASC"

        def _execute(c: sqlite3.Connection):
            return [dict(r) for r in c.execute(query).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_user_badges(self, user_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT b.*, ub.awarded_at
            FROM badges b
            JOIN user_badges ub ON b.id = ub.badge_id
            WHERE ub.user_id = ?
            ORDER BY ub.awarded_at DESC
        """

        def _execute(c: sqlite3.Connection):
            return [dict(r) for r in c.execute(query, (user_id,)).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def has_badge(self, user_id: int, badge_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
        query = "SELECT 1 FROM user_badges WHERE user_id = ? AND badge_id = ?"

        def _execute(c: sqlite3.Connection) -> bool:
            return c.execute(query, (user_id, badge_id)).fetchone() is not None

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def award_badge(self, user_id: int, badge_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Awards a badge to a user. Returns True if awarded, False if already present."""
        now = to_iso_string()
        query = """
            INSERT INTO user_badges (user_id, badge_id, awarded_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, badge_id) DO NOTHING
        """

        def _execute(c: sqlite3.Connection) -> bool:
            cur = c.cursor()
            cur.execute(query, (user_id, badge_id, now))
            return cur.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)
