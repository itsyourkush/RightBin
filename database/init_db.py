"""
Database Initialization and Seeding Script.
Executes schema.sql and seeds initial levels, badges, rewards, challenges, and admin.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Union

# Ensure parent directory is in Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config
from database.connection import get_db_connection
from utils.logging_config import logger
from utils.security import hash_password
from utils.time_utils import get_utc_now, to_iso_string


def init_database(db_path: Optional[Union[str, Path]] = None) -> None:
    """Initializes tables and seeds default records."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    now_iso = to_iso_string()

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Execute schema DDL
        cursor.executescript(schema_sql)

        # Schema migration check for waste_scans columns
        cursor.execute("PRAGMA table_info(waste_scans);")
        existing_cols = {row["name"] for row in cursor.fetchall()}

        if "sub_category" not in existing_cols:
            cursor.execute("ALTER TABLE waste_scans ADD COLUMN sub_category TEXT DEFAULT 'Standard';")
        if "latitude" not in existing_cols:
            cursor.execute("ALTER TABLE waste_scans ADD COLUMN latitude REAL;")
        if "longitude" not in existing_cols:
            cursor.execute("ALTER TABLE waste_scans ADD COLUMN longitude REAL;")
        if "location_name" not in existing_cols:
            cursor.execute("ALTER TABLE waste_scans ADD COLUMN location_name TEXT;")
        if "rejection_reason" not in existing_cols:
            cursor.execute("ALTER TABLE waste_scans ADD COLUMN rejection_reason TEXT;")
        if "is_discarded" not in existing_cols:
            cursor.execute("ALTER TABLE waste_scans ADD COLUMN is_discarded INTEGER NOT NULL DEFAULT 0;")

        # 1. Seed Levels
        for name, min_points, sort_order in config.levels:
            cursor.execute(
                """
                INSERT INTO levels (name, minimum_points, sort_order)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    minimum_points = excluded.minimum_points,
                    sort_order = excluded.sort_order;
                """,
                (name, min_points, sort_order),
            )

        # 2. Seed Badges
        default_badges = [
            ("Recycling Rookie", "Earned on your very first accepted waste scan.", "total_scans", 1, "🌱"),
            ("Plastic Detective", "Successfully classified 5 plastic items.", "category_Plastic", 5, "🧴"),
            ("Paper Saver", "Successfully classified 5 paper items.", "category_Paper", 5, "📄"),
            ("Consistency King", "Maintained an active waste scanning streak of at least 3 days.", "streak_days", 3, "🔥"),
            ("Zero Waste Hero", "Logged 25 total verified recyclable items.", "total_scans", 25, "👑"),
        ]
        for name, desc, criteria_type, criteria_val, icon in default_badges:
            cursor.execute(
                """
                INSERT INTO badges (name, description, criteria_type, criteria_value, icon, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(name) DO UPDATE SET
                    description = excluded.description,
                    criteria_type = excluded.criteria_type,
                    criteria_value = excluded.criteria_value,
                    icon = excluded.icon;
                """,
                (name, desc, criteria_type, criteria_val, icon),
            )

        # 3. Seed Rewards (Including Popular Gaming Coupons & Redeem Codes)
        default_rewards = [
            ("Puzzle Games VIP Booster Code", "Redeem code for Candy Crush, Royal Match & top puzzle games: unlimited lives, extra moves & gold booster bundle!", 100, "digital", 200),
            ("Google Play Store $5 Gift Code", "Digital gift card code redeemable on Google Play Store for in-game purchases, passes, apps & subscriptions.", 150, "digital", 150),
            ("Clash of Clans 500 Gems Voucher", "Supercell Store redeem code for 500 Gems, builder potions, or Gold Pass credit in Clash of Clans.", 200, "digital", 150),
            ("BGMI / PUBG 300 UC Digital Voucher", "Instant redeem code for 300 Unknown Cash (UC) in Battlegrounds Mobile India / PUBG Mobile.", 250, "digital", 100),
            ("Roblox 400 Robux Digital Code", "Digital gift card code to claim 400 Robux for avatar upgrades and game passes.", 300, "digital", 100),
            ("Steam / PC Games $10 Wallet Code", "Direct redeem code to add funds to your Steam wallet for games, DLCs, and community items.", 500, "digital", 75),
            ("Eco Cotton Tote Bag", "Reusable organic cotton shopping bag. Eliminates single-use plastic bags.", 500, "physical", 50),
            ("EcoStore $10 E-Voucher", "Digital shopping voucher valid at partnered zero-waste and bulk retail stores.", 1000, "voucher", 100),
            ("Premium Zero-Waste Starter Kit", "Stainless steel water bottle, bamboo cutlery set, and produce bags.", 2000, "physical", 25),
            ("Grand Reward: Electric Bike Discount", "Generous discount code applicable on certified green electric bicycles.", 5000, "discount", 10),
        ]
        for name, desc, req_points, r_type, stock in default_rewards:
            cursor.execute(
                """
                INSERT INTO rewards (name, description, required_points, reward_type, is_active, stock_quantity, created_at)
                SELECT ?, ?, ?, ?, 1, ?, ?
                WHERE NOT EXISTS (SELECT 1 FROM rewards WHERE name = ?);
                """,
                (name, desc, req_points, r_type, stock, now_iso, name),
            )

        # 4. Seed Eco Challenges
        default_challenges = [
            (
                "Plastic Detox Sprint",
                "Classify 3 plastic items this week to promote sorting and recycling awareness.",
                "category_scan",
                3,
                "Plastic",
                25,
                now_iso,
                "2030-12-31T23:59:59+00:00",
            ),
            (
                "Weekend Consistency Streak",
                "Maintain a 2-day consecutive scanning streak.",
                "streak_days",
                2,
                None,
                30,
                now_iso,
                "2030-12-31T23:59:59+00:00",
            ),
            (
                "Festival Eco Challenge",
                "Complete 5 waste scans during the community environmental festival.",
                "scan_count",
                5,
                None,
                50,
                now_iso,
                "2030-12-31T23:59:59+00:00",
            ),
        ]
        for title, desc, c_type, c_val, target_cat, bonus, start_at, end_at in default_challenges:
            cursor.execute(
                """
                INSERT INTO challenges (title, description, criteria_type, criteria_value, target_category, bonus_points, start_at, end_at, is_active)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, 1
                WHERE NOT EXISTS (SELECT 1 FROM challenges WHERE title = ?);
                """,
                (title, desc, c_type, c_val, target_cat, bonus, start_at, end_at, title),
            )

        # 5. Seed Default Admin User if not exists
        admin_email = "admin@smartwaste.org"
        cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
        if not cursor.fetchone():
            admin_pwd_hash = hash_password("AdminPassword123!")
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash, role, is_active, created_at)
                VALUES (?, ?, ?, 'admin', 1, ?)
                """,
                ("System Administrator", admin_email, admin_pwd_hash, now_iso),
            )
            admin_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id, display_name, green_score, current_streak, longest_streak, created_at, updated_at)
                VALUES (?, ?, 0, 0, 0, ?, ?)
                """,
                (admin_id, "EcoAdmin", now_iso, now_iso),
            )
            logger.info("Created default administrator account: admin@smartwaste.org")

        # 6. Seed Historical Scan Archive (Preserves previous scans across cloud redeployments)
        if db_path is None or str(db_path) == str(config.db_path):
            try:
                from database.historical_seed import seed_historical_archive
                seed_historical_archive(cursor)
            except Exception as e:
                logger.warning(f"Could not load historical scan archive: {e}")

        logger.info("Database initialized and seeded successfully.")


if __name__ == "__main__":
    init_database()
    print("Database initialization complete.")
