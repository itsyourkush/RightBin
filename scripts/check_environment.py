"""
Environment and System Health Verification Script.
Checks Python version, package imports, database tables, and ML model artifacts.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import config
from database.connection import get_db_connection


def check_environment() -> bool:
    print("=" * 60)
    print("SMART WASTE CLASSIFICATION SYSTEM - HEALTH CHECK")
    print("=" * 60)
    all_ok = True

    # 1. Python Version
    py_ver = sys.version.split()[0]
    print(f"[*] Python Version: {py_ver}")

    # 2. Package Imports
    packages = [
        ("Streamlit", "streamlit"),
        ("TensorFlow", "tensorflow"),
        ("Keras", "keras"),
        ("NumPy", "numpy"),
        ("Pandas", "pandas"),
        ("Pillow", "PIL"),
        ("Plotly", "plotly"),
        ("Pytest", "pytest"),
        ("Scikit-Learn", "sklearn"),
        ("Matplotlib", "matplotlib"),
    ]

    print("\n[*] Checking Dependencies:")
    for name, module in packages:
        try:
            mod = __import__(module)
            ver = getattr(mod, "__version__", "installed")
            print(f"  [+] {name:<15}: OK ({ver})")
        except ImportError as e:
            print(f"  [-] {name:<15}: FAILED ({e})")
            all_ok = False

    # 3. Database Check
    print(f"\n[*] Checking Database at: {config.db_path}")
    if not config.db_path.exists():
        print(f"  [-] Database file does not exist yet.")
        all_ok = False
    else:
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                tables = [
                    r[0]
                    for r in cur.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                ]
                required_tables = [
                    "users",
                    "user_profiles",
                    "waste_scans",
                    "point_transactions",
                    "badges",
                    "user_badges",
                    "levels",
                    "rewards",
                    "reward_redemptions",
                    "challenges",
                    "referrals",
                    "tree_award_claims",
                ]
                missing = [t for t in required_tables if t not in tables]
                if missing:
                    print(f"  [-] Missing database tables: {missing}")
                    all_ok = False
                else:
                    print(f"  [+] All {len(required_tables)} core schema tables verified!")
        except Exception as e:
            print(f"  [-] Database connection error: {e}")
            all_ok = False

    # 4. ML Model Artifacts
    print(f"\n[*] Checking Model Artifacts:")
    model_path = config.model_path
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"  [+] Model Artifact  : OK ({model_path.name}, {size_mb:.2f} MB)")
    else:
        print(f"  [-] Model Artifact  : MISSING ({model_path})")
        all_ok = False

    metadata_path = model_path.parent / "model_metadata.json"
    if metadata_path.exists():
        print(f"  [+] Model Metadata  : OK")
    else:
        print(f"  [-] Model Metadata  : MISSING")

    cm_path = model_path.parent / "confusion_matrix.png"
    if cm_path.exists():
        print(f"  [+] Confusion Matrix: OK")
    else:
        print(f"  [-] Confusion Matrix: MISSING")

    print("\n" + "=" * 60)
    if all_ok:
        print("🎉 ALL SYSTEM CHECKS PASSED! The environment is ready.")
    else:
        print("⚠️ Some checks failed. Review warnings above.")
    print("=" * 60)
    return all_ok


if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
