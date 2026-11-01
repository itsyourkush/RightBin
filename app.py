"""
Main Application Entrypoint for RightBin — "Wet or Dry, Always Right."
Configures global theme and multi-page routing via native st.navigation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Safe temp dirs for sandboxed environments
os.environ.setdefault("KERAS_HOME", "/tmp/keras_home")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib_cache")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
Path("/tmp/keras_home").mkdir(parents=True, exist_ok=True)
Path("/tmp/matplotlib_cache").mkdir(parents=True, exist_ok=True)

import streamlit as st
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# App Favicon
_favicon_path = PROJECT_ROOT / "assets" / "favicon.png"
_app_icon = Image.open(_favicon_path) if _favicon_path.exists() else "🏠"

# Configure Streamlit page MUST be the first Streamlit command
st.set_page_config(
    page_title="RightBin — \"Wet or Dry, Always Right.\"",
    page_icon=_app_icon,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# App Top Header Logo
_top_logo_svg = PROJECT_ROOT / "assets" / "top_nav_logo.svg"
_top_logo_png = PROJECT_ROOT / "assets" / "top_nav_logo.png"
if _top_logo_svg.exists():
    st.logo(str(_top_logo_svg), size="large")
elif _top_logo_png.exists():
    st.logo(str(_top_logo_png), size="large")

from config import config
from database.init_db import init_database
from components.navigation import apply_custom_css, init_session_state
from components.top_navbar import render_top_navbar

# Ensure database exists
if not config.db_path.exists():
    init_database(config.db_path)

# Initialize session and global styles
init_session_state()
apply_custom_css()

# ── Clean Native Top Navigation ──────────────────────────────────────────────
pages = [
    st.Page("pages/1_Home.py", title="Home", icon="🌱", default=True, url_path=""),
    st.Page("pages/2_Scan_Waste.py", title="Scan Waste", icon="📸", url_path="scan-waste"),
    st.Page("pages/3_Dashboard.py", title="Dashboard", icon="📊", url_path="dashboard"),
    st.Page("pages/5_Rewards.py", title="Rewards", icon="🎁", url_path="rewards"),
    st.Page("pages/6_Leaderboard.py", title="Leaderboard", icon="🏆", url_path="leaderboard"),
    st.Page("pages/4_Scan_History.py", title="Scan History", icon="📜", url_path="history"),
    st.Page("pages/7_Challenges.py", title="Challenges", icon="⚡", url_path="challenges"),
    st.Page("pages/8_Profile.py", title="Profile", icon="👤", url_path="profile"),
    st.Page("pages/9_Admin.py", title="Admin", icon="⚙️", url_path="admin"),
]

nav = st.navigation(pages, position="top")
render_top_navbar()
nav.run()
