"""
Centralized Configuration Module for Smart Waste Classification System.
Reads from environment variables with sensible defaults.
Second-year CS readable, robust, and extensible.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

# Safe temp dirs for sandboxed environments
os.environ.setdefault("KERAS_HOME", "/tmp/keras_home")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
Path("/tmp/keras_home").mkdir(parents=True, exist_ok=True)
Path("/tmp/matplotlib_cache").mkdir(parents=True, exist_ok=True)

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "waste_classification.db")))
ML_DIR = BASE_DIR / "ml"
ARTIFACTS_DIR = ML_DIR / "artifacts"
DEFAULT_MODEL_PATH = ARTIFACTS_DIR / "waste_classifier.keras"

# Create necessary directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class AppConfig:
    # Environment
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    secret_key: str = os.getenv("APP_SECRET_KEY", "default-dev-secret-key-32bytes-min")
    session_expiry_days: int = int(os.getenv("SESSION_EXPIRY_DAYS", "7"))

    # Database
    db_path: Path = DATABASE_PATH

    # Machine Learning & Classification
    model_path: Path = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))
    image_target_size: Tuple[int, int] = (224, 224)
    allowed_extensions: Tuple[str, ...] = ("png", "jpg", "jpeg", "webp")
    max_image_size_bytes: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "5")) * 1024 * 1024
    model_version: str = "v2.0.0-mobilenet"

    # Supported waste classes (authoritative single source of truth)
    categories: Tuple[str, ...] = ("Plastic", "Paper", "Organic", "Metal", "Glass")

    # Scoring & Points
    points_accepted_classification: int = int(os.getenv("POINTS_ACCEPTED_CLASSIFICATION", "10"))
    points_first_scan_of_day: int = int(os.getenv("POINTS_FIRST_SCAN_OF_DAY", "5"))
    points_daily_challenge_bonus: int = int(os.getenv("POINTS_DAILY_CHALLENGE_BONUS", "20"))
    points_referral_bonus: int = int(os.getenv("POINTS_REFERRAL_BONUS", "50"))
    points_spin_min: int = int(os.getenv("POINTS_SPIN_MIN", "5"))
    points_spin_max: int = int(os.getenv("POINTS_SPIN_MAX", "25"))
    spin_cooldown_hours: int = int(os.getenv("SPIN_COOLDOWN_HOURS", "24"))
    tree_award_points_threshold: int = int(os.getenv("TREE_AWARD_POINTS_THRESHOLD", "500"))

    # Location & Fraud Prevention: 1 to 2 scans per particular area
    max_scans_per_area: int = int(os.getenv("MAX_SCANS_PER_AREA", "2"))
    max_scans_per_location: int = max_scans_per_area
    area_proximity_threshold_meters: float = float(os.getenv("AREA_PROXIMITY_THRESHOLD_METERS", "100.0"))
    location_proximity_threshold_meters: float = area_proximity_threshold_meters

    # Level thresholds: (Name, minimum_points, sort_order)
    levels: Tuple[Tuple[str, int, int], ...] = (
        ("Green Starter", 0, 1),
        ("Eco Learner", 50, 2),
        ("Smart Recycler", 150, 3),
        ("Eco Champion", 300, 4),
        ("Planet Protector", 500, 5),
    )


# Global singleton instance
config = AppConfig()
