-- MySQL / MariaDB Schema for Smart Waste Classification System
-- Compatible with MySQL 5.7+, MySQL 8.0+, MariaDB 10.3+, AWS RDS, PlanetScale, and Cloud SQL

CREATE DATABASE IF NOT EXISTS smart_waste_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_waste_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'user',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. User Profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INT PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    green_score INT NOT NULL DEFAULT 0,
    current_streak INT NOT NULL DEFAULT 0,
    longest_streak INT NOT NULL DEFAULT 0,
    last_eligible_activity_date VARCHAR(64),
    created_at VARCHAR(64) NOT NULL,
    updated_at VARCHAR(64) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Waste Scans (includes fine-grained sub_category, area, coordinates, discarded flag)
CREATE TABLE IF NOT EXISTS waste_scans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    predicted_category VARCHAR(64) NOT NULL,
    sub_category VARCHAR(128) DEFAULT 'Standard',
    confidence DECIMAL(5, 4) NOT NULL,
    prediction_accepted TINYINT(1) NOT NULL DEFAULT 1,
    image_hash VARCHAR(128) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    points_awarded INT NOT NULL DEFAULT 0,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    location_name VARCHAR(255),
    rejection_reason TEXT,
    is_discarded TINYINT(1) NOT NULL DEFAULT 0,
    created_at VARCHAR(64) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_scans_user_time (user_id, created_at),
    INDEX idx_scans_hash (image_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Point Transactions Ledger
CREATE TABLE IF NOT EXISTS point_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_type VARCHAR(64) NOT NULL,
    reference_id VARCHAR(64),
    points_delta INT NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE,
    created_at VARCHAR(64) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_points_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Badges
CREATE TABLE IF NOT EXISTS badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    criteria_type VARCHAR(64) NOT NULL,
    criteria_value INT NOT NULL,
    icon VARCHAR(32) DEFAULT '🏅',
    is_active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. User Badges
CREATE TABLE IF NOT EXISTS user_badges (
    user_id INT NOT NULL,
    badge_id INT NOT NULL,
    awarded_at VARCHAR(64) NOT NULL,
    PRIMARY KEY (user_id, badge_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Levels
CREATE TABLE IF NOT EXISTS levels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    minimum_points INT NOT NULL,
    sort_order INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Rewards Catalog
CREATE TABLE IF NOT EXISTS rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    required_points INT NOT NULL,
    reward_type VARCHAR(64) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    stock_quantity INT,
    created_at VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Reward Redemptions
CREATE TABLE IF NOT EXISTS reward_redemptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    reward_id INT NOT NULL,
    points_cost INT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    requested_at VARCHAR(64) NOT NULL,
    reviewed_at VARCHAR(64),
    reviewed_by INT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reward_id) REFERENCES rewards(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Spin History
CREATE TABLE IF NOT EXISTS spin_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    points_awarded INT NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Referrals
CREATE TABLE IF NOT EXISTS referrals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    referrer_user_id INT NOT NULL,
    referred_user_id INT UNIQUE NOT NULL,
    referral_code VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    reward_points INT NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    rewarded_at VARCHAR(64),
    FOREIGN KEY (referrer_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (referred_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. Challenges
CREATE TABLE IF NOT EXISTS challenges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    criteria_type VARCHAR(64) NOT NULL,
    criteria_value INT NOT NULL,
    target_category VARCHAR(64),
    bonus_points INT NOT NULL,
    start_at VARCHAR(64) NOT NULL,
    end_at VARCHAR(64) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. Challenge Participation
CREATE TABLE IF NOT EXISTS challenge_participation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    challenge_id INT NOT NULL,
    progress INT NOT NULL DEFAULT 0,
    completed_at VARCHAR(64),
    rewarded_at VARCHAR(64),
    UNIQUE KEY uq_user_challenge (user_id, challenge_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. Plant-a-Tree Award Claims
CREATE TABLE IF NOT EXISTS tree_award_claims (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'submitted',
    submitted_at VARCHAR(64) NOT NULL,
    reviewed_at VARCHAR(64),
    reviewed_by INT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 15. Admin Audit Logs
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_user_id INT NOT NULL,
    action VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id INT,
    details TEXT,
    created_at VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
