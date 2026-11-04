"""
Export historical database records into a clean python seed module.
"""

import sqlite3
import pprint
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
db_path = BASE_DIR / "data" / "waste_classification.db"

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT * FROM users WHERE id IN (1, 3, 4, 5, 6)")
users = [dict(r) for r in c.fetchall()]

c.execute("SELECT * FROM user_profiles WHERE user_id IN (1, 3, 4, 5, 6)")
profiles = [dict(r) for r in c.fetchall()]

c.execute("SELECT * FROM waste_scans ORDER BY id")
scans = [dict(r) for r in c.fetchall()]

c.execute("SELECT * FROM point_transactions ORDER BY id")
raw_txs = [dict(r) for r in c.fetchall()]
txs = []
for t in raw_txs:
    t_copy = dict(t)
    if t_copy.get("idempotency_key"):
        t_copy["idempotency_key"] = "hist_" + t_copy["idempotency_key"]
    txs.append(t_copy)

content = [
    '"""',
    "Historical Scan Data & User Archive Seeder.",
    "Ensures past scan records, user profiles, and point ledger entries",
    "persist across cloud container redeployments and fresh database instantiations.",
    '"""',
    "",
    "from __future__ import annotations",
    "import sqlite3",
    "",
    f"USERS_DATA = {pprint.pformat(users, width=120)}",
    "",
    f"PROFILES_DATA = {pprint.pformat(profiles, width=120)}",
    "",
    f"SCANS_DATA = {pprint.pformat(scans, width=120)}",
    "",
    f"TRANSACTIONS_DATA = {pprint.pformat(txs, width=120)}",
    "",
    """
def seed_historical_archive(cursor: sqlite3.Cursor) -> None:
    \"\"\"Seeds historical user accounts, profiles, scans, and transactions if empty.\"\"\"
    cursor.execute("SELECT COUNT(*) FROM waste_scans")
    if cursor.fetchone()[0] == 0:
        for u in USERS_DATA:
            cursor.execute(
                \"\"\"
                INSERT INTO users (id, name, email, password_hash, role, is_active, created_at)
                VALUES (:id, :name, :email, :password_hash, :role, :is_active, :created_at)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    email = excluded.email,
                    password_hash = excluded.password_hash;
                \"\"\",
                u,
            )

        for p in PROFILES_DATA:
            cursor.execute(
                \"\"\"
                INSERT INTO user_profiles (user_id, display_name, green_score, current_streak, longest_streak, last_eligible_activity_date, created_at, updated_at)
                VALUES (:user_id, :display_name, :green_score, :current_streak, :longest_streak, :last_eligible_activity_date, :created_at, :updated_at)
                ON CONFLICT(user_id) DO UPDATE SET
                    green_score = excluded.green_score,
                    current_streak = excluded.current_streak,
                    longest_streak = excluded.longest_streak,
                    last_eligible_activity_date = excluded.last_eligible_activity_date;
                \"\"\",
                p,
            )

        for s in SCANS_DATA:
            cursor.execute(
                \"\"\"
                INSERT INTO waste_scans (id, user_id, predicted_category, sub_category, confidence, prediction_accepted, image_hash, model_version, points_awarded, latitude, longitude, location_name, rejection_reason, is_discarded, created_at)
                VALUES (:id, :user_id, :predicted_category, :sub_category, :confidence, :prediction_accepted, :image_hash, :model_version, :points_awarded, :latitude, :longitude, :location_name, :rejection_reason, :is_discarded, :created_at)
                ON CONFLICT(id) DO NOTHING;
                \"\"\",
                s,
            )

        for t in TRANSACTIONS_DATA:
            cursor.execute(
                \"\"\"
                INSERT INTO point_transactions (id, user_id, activity_type, reference_id, points_delta, idempotency_key, created_at)
                VALUES (:id, :user_id, :activity_type, :reference_id, :points_delta, :idempotency_key, :created_at)
                ON CONFLICT(id) DO NOTHING;
                \"\"\",
                t,
            )
""",
]

out_file = BASE_DIR / "database" / "historical_seed.py"
out_file.write_text("\n".join(content), encoding="utf-8")
print(f"Generated {out_file} with {len(scans)} scans and {len(txs)} transactions!")
