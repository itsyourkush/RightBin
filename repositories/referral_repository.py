"""
Referral and Plant-a-Tree Claims Repository.
Manages referral tracking and tree planting claim requests.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from database.connection import get_db_connection
from utils.time_utils import to_iso_string


class ReferralRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    # Referral methods
    def create_referral(
        self,
        referrer_user_id: int,
        referred_user_id: int,
        referral_code: str,
        reward_points: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        now = to_iso_string()
        query = """
            INSERT INTO referrals (referrer_user_id, referred_user_id, referral_code, status, reward_points, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
        """

        def _execute(c: sqlite3.Connection) -> Dict[str, Any]:
            cur = c.cursor()
            cur.execute(query, (referrer_user_id, referred_user_id, referral_code, reward_points, now))
            return {
                "id": cur.lastrowid,
                "referrer_user_id": referrer_user_id,
                "referred_user_id": referred_user_id,
                "referral_code": referral_code,
                "status": "pending",
                "reward_points": reward_points,
                "created_at": now,
            }

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_by_referred_id(self, referred_user_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM referrals WHERE referred_user_id = ?"

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (referred_user_id,)).fetchone()
            return dict(row) if row else None

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_user_referrals(self, referrer_user_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT r.*, u.name as referred_name, u.email as referred_email
            FROM referrals r
            JOIN users u ON r.referred_user_id = u.id
            WHERE r.referrer_user_id = ?
            ORDER BY r.id DESC
        """

        def _execute(c: sqlite3.Connection):
            return [dict(row) for row in c.execute(query, (referrer_user_id,)).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def mark_referral_rewarded(self, referral_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
        now = to_iso_string()
        query = "UPDATE referrals SET status = 'rewarded', rewarded_at = ? WHERE id = ? AND status = 'pending'"

        def _execute(c: sqlite3.Connection) -> bool:
            res = c.execute(query, (now, referral_id))
            return res.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    # Tree claims methods
    def submit_tree_claim(self, user_id: int, notes: str = "", conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        now = to_iso_string()
        query = """
            INSERT INTO tree_award_claims (user_id, status, submitted_at, notes)
            VALUES (?, 'submitted', ?, ?)
        """

        def _execute(c: sqlite3.Connection) -> Dict[str, Any]:
            cur = c.cursor()
            cur.execute(query, (user_id, now, notes))
            return {"id": cur.lastrowid, "user_id": user_id, "status": "submitted", "submitted_at": now}

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_user_tree_claims(self, user_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM tree_award_claims WHERE user_id = ? ORDER BY id DESC"

        def _execute(c: sqlite3.Connection):
            return [dict(r) for r in c.execute(query, (user_id,)).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_all_tree_claims(self, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT tc.*, u.email as user_email, u.name as user_name
            FROM tree_award_claims tc
            JOIN users u ON tc.user_id = u.id
            ORDER BY tc.id DESC
        """

        def _execute(c: sqlite3.Connection):
            return [dict(r) for r in c.execute(query).fetchall()]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def update_tree_claim_status(
        self,
        claim_id: int,
        status: str,
        reviewed_by: int,
        notes: str = "",
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        now = to_iso_string()
        query = """
            UPDATE tree_award_claims
            SET status = ?, reviewed_at = ?, reviewed_by = ?, notes = ?
            WHERE id = ?
        """

        def _execute(c: sqlite3.Connection) -> bool:
            res = c.execute(query, (status, now, reviewed_by, notes, claim_id))
            return res.rowcount > 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)
