"""
CLI utility to create or update an administrator account.
Usage:
    python scripts/create_admin.py [name] [email] [password]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import config
from database.connection import get_db_connection
from database.init_db import init_database
from utils.security import hash_password
from utils.time_utils import to_iso_string


def create_or_update_admin(name: str, email: str, password: str) -> None:
    # Ensure database is initialized
    init_database()

    now = to_iso_string()
    pwd_hash = hash_password(password)
    clean_email = email.strip().lower()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (clean_email,))
        existing = cursor.fetchone()

        if existing:
            user_id = existing["id"]
            cursor.execute(
                """
                UPDATE users
                SET name = ?, password_hash = ?, role = 'admin', is_active = 1
                WHERE id = ?
                """,
                (name, pwd_hash, user_id),
            )
            print(f"✅ Existing user '{clean_email}' (ID: {user_id}) updated to Administrator.")
        else:
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash, role, is_active, created_at)
                VALUES (?, ?, ?, 'admin', 1, ?)
                """,
                (name, clean_email, pwd_hash, now),
            )
            user_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id, display_name, green_score, current_streak, longest_streak, created_at, updated_at)
                VALUES (?, ?, 0, 0, 0, ?, ?)
                """,
                (user_id, name.split()[0], now, now),
            )
            print(f"✅ New Administrator '{clean_email}' (ID: {user_id}) created successfully.")


if __name__ == "__main__":
    if len(sys.argv) == 4:
        name_arg, email_arg, pwd_arg = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        name_arg = "System Administrator"
        email_arg = "admin@smartwaste.org"
        pwd_arg = "AdminPassword123!"
        print(f"No arguments provided. Using defaults: {email_arg} / {pwd_arg}")

    create_or_update_admin(name_arg, email_arg, pwd_arg)
