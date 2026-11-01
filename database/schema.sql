-- SQLite Schema for Smart Waste Classification System
-- Enforces foreign keys, UTC timestamps, and unique constraints.

PRAGMA foreign_keys = ON;

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user', 'admin')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TEXT NOT NULL
);

-- 2. User Profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    green_score INTEGER NOT NULL DEFAULT 0,
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_eligible_activity_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 3. Waste Scans
CREATE TABLE IF NOT EXISTS waste_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    predicted_category TEXT NOT NULL,
    sub_category TEXT DEFAULT 'Standard',
    confidence REAL NOT NULL,
    prediction_accepted INTEGER NOT NULL CHECK(prediction_accepted IN (0, 1)),
    image_hash TEXT NOT NULL,
    model_version TEXT NOT NULL,
    points_awarded INTEGER NOT NULL DEFAULT 0,
    latitude REAL,
    longitude REAL,
    location_name TEXT,
    rejection_reason TEXT,
    is_discarded INTEGER NOT NULL DEFAULT 0 CHECK(is_discarded IN (0, 1)),
    created_at TEXT NOT NULL
);

-- 4. Point Transactions Ledger
CREATE TABLE IF NOT EXISTS point_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL,
    reference_id TEXT,
    points_delta INTEGER NOT NULL,
    idempotency_key TEXT UNIQUE,
    created_at TEXT NOT NULL
);

-- 5. Badges
CREATE TABLE IF NOT EXISTS badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    criteria_type TEXT NOT NULL,
    criteria_value INTEGER NOT NULL,
    icon TEXT DEFAULT '🏅',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1))
);

-- 6. User Badges (Many-to-Many)
CREATE TABLE IF NOT EXISTS user_badges (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    awarded_at TEXT NOT NULL,
    PRIMARY KEY (user_id, badge_id)
);

-- 7. Levels
CREATE TABLE IF NOT EXISTS levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    minimum_points INTEGER NOT NULL,
    sort_order INTEGER NOT NULL
);

-- 8. Rewards
CREATE TABLE IF NOT EXISTS rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    required_points INTEGER NOT NULL,
    reward_type TEXT NOT NULL CHECK(reward_type IN ('voucher', 'physical', 'digital', 'discount')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    stock_quantity INTEGER,
    created_at TEXT NOT NULL
);

-- 9. Reward Redemptions
CREATE TABLE IF NOT EXISTS reward_redemptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reward_id INTEGER NOT NULL REFERENCES rewards(id) ON DELETE CASCADE,
    points_cost INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
    requested_at TEXT NOT NULL,
    reviewed_at TEXT,
    reviewed_by INTEGER REFERENCES users(id),
    notes TEXT
);

-- 10. Spin History
CREATE TABLE IF NOT EXISTS spin_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    points_awarded INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    idempotency_key TEXT UNIQUE
);

-- 11. Referrals
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referred_user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referral_code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'rewarded')),
    reward_points INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    rewarded_at TEXT
);

-- 12. Challenges
CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    criteria_type TEXT NOT NULL CHECK(criteria_type IN ('scan_count', 'streak_days', 'category_scan')),
    criteria_value INTEGER NOT NULL,
    target_category TEXT,
    bonus_points INTEGER NOT NULL,
    start_at TEXT NOT NULL,
    end_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1))
);

-- 13. Challenge Participation
CREATE TABLE IF NOT EXISTS challenge_participation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    progress INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    rewarded_at TEXT,
    UNIQUE (user_id, challenge_id)
);

-- 14. Plant-a-Tree Award Claims
CREATE TABLE IF NOT EXISTS tree_award_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'submitted' CHECK(status IN ('submitted', 'verified', 'fulfilled', 'rejected')),
    submitted_at TEXT NOT NULL,
    reviewed_at TEXT,
    reviewed_by INTEGER REFERENCES users(id),
    notes TEXT
);

-- 15. Admin Audit Logs
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user_id INTEGER NOT NULL REFERENCES users(id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    details TEXT,
    created_at TEXT NOT NULL
);

-- Indexes for high-performance querying
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_scans_user_created ON waste_scans(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_scans_hash ON waste_scans(image_hash);
CREATE INDEX IF NOT EXISTS idx_points_user_created ON point_transactions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_badges_user ON user_badges(user_id);
CREATE INDEX IF NOT EXISTS idx_redemptions_user ON reward_redemptions(user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_user_id);
CREATE INDEX IF NOT EXISTS idx_challenge_user ON challenge_participation(user_id);
