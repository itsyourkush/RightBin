"""
Waste Scan Repository.
Handles parameterized queries for waste scans and duplicate detection.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from database.connection import get_db_connection
from utils.location_utils import is_same_location
from utils.time_utils import to_iso_string


class ScanRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def record_scan(
        self,
        user_id: int,
        predicted_category: str,
        confidence: float,
        prediction_accepted: bool,
        image_hash: str,
        model_version: str,
        points_awarded: int,
        sub_category: str = "Standard",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_name: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        is_discarded: bool = False,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """Inserts a new waste scan entry with sub-category, location tracking, and discarded flag."""
        now = to_iso_string()
        query = """
            INSERT INTO waste_scans (
                user_id, predicted_category, sub_category, confidence, prediction_accepted,
                image_hash, model_version, points_awarded, latitude, longitude,
                location_name, rejection_reason, is_discarded, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        def _execute(c: sqlite3.Connection) -> Dict[str, Any]:
            cur = c.cursor()
            cur.execute(
                query,
                (
                    user_id,
                    predicted_category,
                    sub_category,
                    confidence,
                    1 if prediction_accepted else 0,
                    image_hash,
                    model_version,
                    points_awarded,
                    latitude,
                    longitude,
                    location_name,
                    rejection_reason,
                    1 if is_discarded else 0,
                    now,
                ),
            )
            scan_id = cur.lastrowid
            return {
                "id": scan_id,
                "user_id": user_id,
                "predicted_category": predicted_category,
                "sub_category": sub_category,
                "confidence": confidence,
                "prediction_accepted": 1 if prediction_accepted else 0,
                "image_hash": image_hash,
                "model_version": model_version,
                "points_awarded": points_awarded,
                "latitude": latitude,
                "longitude": longitude,
                "location_name": location_name,
                "rejection_reason": rejection_reason,
                "is_discarded": 1 if is_discarded else 0,
                "created_at": now,
            }

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def count_accepted_scans_in_area(
        self,
        user_id: int,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_name: Optional[str] = None,
        proximity_meters: float = 100.0,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """
        Counts how many accepted (non-discarded) scans this user has performed in this particular area.
        Uses Haversine distance if coordinates are present; otherwise matches area/location names.
        """
        if latitude is None and longitude is None and not (location_name or "").strip():
            return 0

        query = """
            SELECT latitude, longitude, location_name
            FROM waste_scans
            WHERE user_id = ? AND prediction_accepted = 1 AND (is_discarded IS NULL OR is_discarded = 0)
        """

        def _execute(c: sqlite3.Connection) -> int:
            rows = c.execute(query, (user_id,)).fetchall()
            matched = 0
            for r in rows:
                if is_same_location(
                    lat1=latitude,
                    lon1=longitude,
                    name1=location_name,
                    lat2=r["latitude"],
                    lon2=r["longitude"],
                    name2=r["location_name"],
                    proximity_threshold_m=proximity_meters,
                ):
                    matched += 1
            return matched

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    # Alias for backwards compatibility
    count_accepted_scans_at_location = count_accepted_scans_in_area

    def get_by_id(self, scan_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM waste_scans WHERE id = ?"

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (scan_id,)).fetchone()
            return dict(row) if row else None

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def get_user_scans(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves paginated scan history for a user."""
        if category:
            query = """
                SELECT * FROM waste_scans
                WHERE user_id = ? AND predicted_category = ?
                ORDER BY id DESC LIMIT ? OFFSET ?
            """
            params = (user_id, category, limit, offset)
        else:
            query = "SELECT * FROM waste_scans WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?"
            params = (user_id, limit, offset)

        def _execute(c: sqlite3.Connection):
            rows = c.execute(query, params).fetchall()
            return [dict(r) for r in rows]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def find_duplicate_scans(
        self,
        image_hash: str,
        user_id: Optional[int] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[Dict[str, Any]]:
        """Finds any prior scans matching the image SHA-256 hash."""
        if user_id:
            query = "SELECT * FROM waste_scans WHERE image_hash = ? AND user_id = ? ORDER BY id DESC"
            params = (image_hash, user_id)
        else:
            query = "SELECT * FROM waste_scans WHERE image_hash = ? ORDER BY id DESC"
            params = (image_hash,)

        def _execute(c: sqlite3.Connection):
            rows = c.execute(query, params).fetchall()
            return [dict(r) for r in rows]

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def count_scans_by_category(self, user_id: int, only_accepted: bool = True, conn: Optional[sqlite3.Connection] = None) -> Dict[str, int]:
        """Returns distribution count of scans per category."""
        if only_accepted:
            query = """
                SELECT predicted_category, COUNT(*) as count
                FROM waste_scans
                WHERE user_id = ? AND prediction_accepted = 1
                GROUP BY predicted_category
            """
        else:
            query = """
                SELECT predicted_category, COUNT(*) as count
                FROM waste_scans
                WHERE user_id = ?
                GROUP BY predicted_category
            """

        def _execute(c: sqlite3.Connection):
            rows = c.execute(query, (user_id,)).fetchall()
            return {r["predicted_category"]: r["count"] for r in rows}

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def count_accepted_scans_today(self, user_id: int, date_prefix: str, conn: Optional[sqlite3.Connection] = None) -> int:
        """Counts accepted scans for a user on a given YYYY-MM-DD date."""
        query = """
            SELECT COUNT(*) as count
            FROM waste_scans
            WHERE user_id = ? AND prediction_accepted = 1 AND created_at LIKE ?
        """

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (user_id, f"{date_prefix}%")).fetchone()
            return row["count"] if row else 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)

    def count_total_scans(self, user_id: int, only_accepted: bool = False, conn: Optional[sqlite3.Connection] = None) -> int:
        if only_accepted:
            query = "SELECT COUNT(*) as count FROM waste_scans WHERE user_id = ? AND prediction_accepted = 1"
        else:
            query = "SELECT COUNT(*) as count FROM waste_scans WHERE user_id = ?"

        def _execute(c: sqlite3.Connection):
            row = c.execute(query, (user_id,)).fetchone()
            return row["count"] if row else 0

        if conn is not None:
            return _execute(conn)
        with get_db_connection(self.db_path) as c:
            return _execute(c)
