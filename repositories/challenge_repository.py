"""
Challenge Repository.
Manages active challenges and user progress tracking.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from database.connection import get_db_connection
from utils.time_utils import to_iso_string


class ChallengeRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_active_challenges(self, now_iso: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        if now_iso is None:
            now_iso = to_iso_string()
        query = """
            SELECT * FROM challenges
            WHERE is_active = 1 AND start_at <= ? AND end_at >= ?
            ORDER BY id ASC
        """

        def _execute(c: sqlite3.Connection):
            return [dict(r) for r in c.execute(query, (now_iso, now_iso)).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_by_id(self, challenge_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM challenges WHERE id = ?"

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (challenge_id,)).fetchone()
            return dict(row) if row else None

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_user_participation(self, user_id: int, challenge_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM challenge_participation WHERE user_id = ? AND challenge_id = ?"

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (user_id, challenge_id)).fetchone()
            return dict(row) if row else None

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_user_all_participations(self, user_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT cp.*, c.title, c.description, c.criteria_type, c.criteria_value,
                   c.target_category, c.bonus_points, c.start_at, c.end_at
            FROM challenge_participation cp
            JOIN challenges c ON cp.challenge_id = c.id
            WHERE cp.user_id = ?
            ORDER BY cp.id DESC
        """

        def _execute(c: sqlite3.Connection):
            return [dict(r) for r in c.execute(query, (user_id,)).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def upsert_progress(
        self,
        user_id: int,
        challenge_id: int,
        progress: int,
        completed: bool = False,
        rewarded: bool = False,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        """Upserts challenge progress for a user."""
        now = to_iso_string()
        completed_at = now if completed else None
        rewarded_at = now if rewarded else None

        query = """
            INSERT INTO challenge_participation (user_id, challenge_id, progress, completed_at, rewarded_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, challenge_id) DO UPDATE SET
                progress = excluded.progress,
                completed_at = COALESCE(challenge_participation.completed_at, excluded.completed_at),
                rewarded_at = COALESCE(challenge_participation.rewarded_at, excluded.rewarded_at);
        """

        def _execute(c: sqlite3.Connection) -> bool:
            c.execute(query, (user_id, challenge_id, progress, completed_at, rewarded_at))
            return True

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)
