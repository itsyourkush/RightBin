"""
Home Page: System Mission, Interactive Workflow, Category Explorer, and Mobile Gateway.
Full rich landing page for RightBin — "Wet or Dry, Always Right."
"""

from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="RightBin — \"Wet or Dry, Always Right.\"",
    page_icon="🏠",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.navigation import render_sidebar, get_app_icon_base64
from components.messages import render_flash_messages
from components.mobile_access import render_mobile_access_section
from ml.model_loader import is_model_available

# Render sidebar & flash messages
user = render_sidebar()
render_flash_messages()

model_ready = is_model_available()

# ── 1. Animated Hero Banner ───────────────────────────────────────────────────
app_icon_b64 = get_app_icon_base64()
hero_badge_html = (
    f'<img src="data:image/png;base64,{app_icon_b64}" style="width: 64px; height: 64px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); animation: float 4s ease-in-out infinite; flex-shrink: 0;" alt="RightBin Icon" />'
    if app_icon_b64
    else '<span style="font-size: 2.6rem;">🌐</span>'
)

st.markdown(
    f"""
    <div class="eco-hero">
        <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 8px;">
            {hero_badge_html}
            <div>
                <div class="eco-hero-title">RightBin • AI Waste Vision & Rewards</div>
                <div style="font-size: 1.05rem; color: #6EE7B7; font-weight: 700; margin-top: 4px;">🌱 "Wet or Dry, Always Right."</div>
            </div>
        </div>
        <div class="eco-hero-subtitle">
            Harness deep learning computer vision to instantly classify recyclables, follow direct dustbin wayfinding,
            and earn real redeem codes for <strong>Clash of Clans, Google Play, and Puzzle Games</strong>.
        </div>
        <div class="eco-hero-badges">
            <span class="hero-pill hero-pill-online">
                <span class="status-dot"></span>
                <span>{"AI Vision Online (MobileNetV2)" if model_ready else "AI Model Offline"}</span>
            </span>
            <span class="hero-pill">
                <span>🛡️ Anti-Fraud Geofencing Active (Max 1–2 scans/area)</span>
            </span>
            <span class="hero-pill">
                <span>🎮 Instant Game Redeem Codes</span>
            </span>
            <span class="hero-pill">
                <span>🗑️ Color-Coded Municipal Wayfinding</span>
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 2. Quick Action Launchpad ─────────────────────────────────────────────────
st.markdown("### ⚡ Quick Launchpad")
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("📸 **Scan Waste Now**", type="primary", use_container_width=True, key="hp_launch_scan"):
        st.switch_page("pages/2_Scan_Waste.py")

with c2:
    if st.button("📊 **Eco Dashboard**", use_container_width=True, key="hp_launch_dash"):
        st.switch_page("pages/3_Dashboard.py")

with c3:
    if st.button("🎁 **Gaming Rewards**", use_container_width=True, key="hp_launch_rew"):
        st.switch_page("pages/5_Rewards.py")

with c4:
    if st.button("🏆 **Leaderboard**", use_container_width=True, key="hp_launch_lead"):
        st.switch_page("pages/6_Leaderboard.py")

st.divider()

# ── 3. 4-Step Interactive Workflow ───────────────────────────────────────────
st.markdown("### 🧭 How It Works")
step1, step2, step3, step4 = st.columns(4)

with step1:
    st.markdown(
        """
        <div class="metric-card-interactive" style="border-top: 4px solid #0284C7; min-height: 190px;">
            <div class="metric-header">
                <span class="metric-label" style="color: #0284C7;">Step 01</span>
                <div class="metric-icon-bubble bubble-blue">📸</div>
            </div>
            <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin-bottom: 6px;">1. Capture Waste</div>
            <div style="font-size: 0.85rem; color: #64748B; line-height: 1.4;">
                Snap an image with your smartphone camera or upload any JPG/PNG item.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with step2:
    st.markdown(
        """
        <div class="metric-card-interactive" style="border-top: 4px solid #10B981; min-height: 190px;">
            <div class="metric-header">
                <span class="metric-label" style="color: #059669;">Step 02</span>
                <div class="metric-icon-bubble bubble-green">🧠</div>
            </div>
            <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin-bottom: 6px;">2. AI Classification</div>
            <div style="font-size: 0.85rem; color: #64748B; line-height: 1.4;">
                MobileNetV2 neural vision extracts textures & resin codes with 98.89% verified accuracy.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with step3:
    st.markdown(
        """
        <div class="metric-card-interactive" style="border-top: 4px solid #F59E0B; min-height: 190px;">
            <div class="metric-header">
                <span class="metric-label" style="color: #D97706;">Step 03</span>
                <div class="metric-icon-bubble bubble-gold">🗑️</div>
            </div>
            <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin-bottom: 6px;">3. Direct Wayfinding</div>
            <div style="font-size: 0.85rem; color: #64748B; line-height: 1.4;">
                Follow the visual drop-path to deposit into the correct Blue, Green, or Yellow dustbin.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with step4:
    st.markdown(
        """
        <div class="metric-card-interactive" style="border-top: 4px solid #FF6B00; min-height: 190px;">
            <div class="metric-header">
                <span class="metric-label" style="color: #EA580C;">Step 04</span>
                <div class="metric-icon-bubble bubble-orange">🎮</div>
            </div>
            <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin-bottom: 6px;">4. Gaming Rewards</div>
            <div style="font-size: 0.85rem; color: #64748B; line-height: 1.4;">
                Earn Green Points, maintain daily streaks, and claim Clash of Clans & Play Store codes.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── 4. Interactive Category Explorer & Municipal Wayfinding ───────────────────
st.markdown("### 🗂️ Interactive Waste Category Explorer & Wayfinding")
st.caption("Hover or tap each category to see material details, target dustbins, and municipal segregation protocols:")

cat1, cat2, cat3, cat4, cat5 = st.columns(5)

with cat1:
    st.markdown(
        """
        <div class="category-card cat-plastic">
            <div class="cat-icon-container" style="background: linear-gradient(135deg, #E0F2FE, #BAE6FD); color: #0284C7;">🧴</div>
            <h4 style="color: #0369A1; margin: 0 0 4px 0;">Plastic</h4>
            <div style="font-size: 0.75rem; font-weight: 700; color: #0284C7; margin-bottom: 6px;">♳ PET • ♴ HDPE • ♷ PP</div>
            <p style="font-size: 0.8rem; color: #475569; margin: 0 0 8px 0;">Bottles, containers, caps</p>
            <div style="background: #0284C7; color: white; border-radius: 6px; padding: 3px 6px; font-size: 0.72rem; font-weight: 700;">
                🔵 BLUE DUSTBIN
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with cat2:
    st.markdown(
        """
        <div class="category-card cat-paper">
            <div class="cat-icon-container" style="background: linear-gradient(135deg, #DCFCE7, #BBF7D0); color: #16A34A;">📄</div>
            <h4 style="color: #15803D; margin: 0 0 4px 0;">Paper</h4>
            <div style="font-size: 0.75rem; font-weight: 700; color: #16A34A; margin-bottom: 6px;">PAP-20 • PAP-21</div>
            <p style="font-size: 0.8rem; color: #475569; margin: 0 0 8px 0;">Cartons, books, clean sheets</p>
            <div style="background: #16A34A; color: white; border-radius: 6px; padding: 3px 6px; font-size: 0.72rem; font-weight: 700;">
                🔵 BLUE DUSTBIN
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with cat3:
    st.markdown(
        """
        <div class="category-card cat-organic">
            <div class="cat-icon-container" style="background: linear-gradient(135deg, #FEF3C7, #FDE68A); color: #D97706;">🍎</div>
            <h4 style="color: #B45309; margin: 0 0 4px 0;">Organic</h4>
            <div style="font-size: 0.75rem; font-weight: 700; color: #D97706; margin-bottom: 6px;">FOR-50 • Compostable</div>
            <p style="font-size: 0.8rem; color: #475569; margin: 0 0 8px 0;">Fruit peels, leftovers, greens</p>
            <div style="background: #15803D; color: white; border-radius: 6px; padding: 3px 6px; font-size: 0.72rem; font-weight: 700;">
                🟢 GREEN DUSTBIN
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with cat4:
    st.markdown(
        """
        <div class="category-card cat-metal">
            <div class="cat-icon-container" style="background: linear-gradient(135deg, #F3E8FF, #E9D5FF); color: #9333EA;">🥫</div>
            <h4 style="color: #7E22CE; margin: 0 0 4px 0;">Metal</h4>
            <div style="font-size: 0.75rem; font-weight: 700; color: #9333EA; margin-bottom: 6px;">ALU-41 • FE-40</div>
            <p style="font-size: 0.8rem; color: #475569; margin: 0 0 8px 0;">Beverage cans, tin food cans</p>
            <div style="background: #F59E0B; color: white; border-radius: 6px; padding: 3px 6px; font-size: 0.72rem; font-weight: 700;">
                🟡 YELLOW DUSTBIN
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with cat5:
    st.markdown(
        """
        <div class="category-card cat-glass">
            <div class="cat-icon-container" style="background: linear-gradient(135deg, #CCFBF1, #99F6E4); color: #0D9488;">🍾</div>
            <h4 style="color: #0F766E; margin: 0 0 4px 0;">Glass</h4>
            <div style="font-size: 0.75rem; font-weight: 700; color: #0D9488; margin-bottom: 6px;">GL-70 Clear • GL-71 Green</div>
            <p style="font-size: 0.8rem; color: #475569; margin: 0 0 8px 0;">Jars, glass drink bottles</p>
            <div style="background: #F59E0B; color: white; border-radius: 6px; padding: 3px 6px; font-size: 0.72rem; font-weight: 700;">
                🟡 YELLOW DUSTBIN
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── 5. System Highlights ──────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="metric-card-interactive" style="border-top: 4px solid #0284C7;">
            <div class="metric-header">
                <span class="metric-label" style="color: #0284C7;">MobileNetV2 Vision</span>
                <div class="metric-icon-bubble bubble-blue">🧠</div>
            </div>
            <div class="metric-value-large" style="font-size: 1.5rem;">98.89% Accuracy</div>
            <div class="metric-subtext">Zero Plastic vs. Glass confusion. Advanced 7-stage pre-processing with aspect letterboxing.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="metric-card-interactive" style="border-top: 4px solid #10B981;">
            <div class="metric-header">
                <span class="metric-label" style="color: #059669;">Anti-Fraud Geofencing</span>
                <div class="metric-icon-bubble bubble-green">📍</div>
            </div>
            <div class="metric-value-large" style="font-size: 1.5rem;">1–2 Scans / Area</div>
            <div class="metric-subtext">Haversine GPS boundary enforcement prevents reward farming of duplicate items at disposal stations.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="metric-card-interactive" style="border-top: 4px solid #FF6B00;">
            <div class="metric-header">
                <span class="metric-label" style="color: #EA580C;">Gaming Rewards</span>
                <div class="metric-icon-bubble bubble-orange">🎮</div>
            </div>
            <div class="metric-value-large" style="font-size: 1.5rem;">Instant Game Codes</div>
            <div class="metric-subtext">Clash of Clans Gems, Google Play gift cards, and Puzzle VIP passes delivered immediately upon claim.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── 6. Mobile Access QR Gateway ───────────────────────────────────────────────
render_mobile_access_section()

st.divider()

# ── 7. Educational Viva & Technical Details ───────────────────────────────────
with st.expander("🎓 **Technical Architecture & Defense Overview**", expanded=False):
    st.markdown(
        """
        #### 1. Machine Learning Pipeline:
        - **Model Architecture**: MobileNetV2 Transfer Learning with GlobalAveragePooling2D, Dense(128, ReLU), and Dropout(0.25).
        - **Target Categories**: `Plastic`, `Paper`, `Organic`, `Metal`, `Glass`.
        - **Preprocessing**: 7-stage pipeline with EXIF orientation auto-transpose, Lanczos letterboxing ($224 \\times 224$), and normalization.
        - **Confidence Policy**: Rejects predictions under 60% confidence to prevent municipal contamination.

        #### 2. Anti-Fraud & Gamification Architecture:
        - **Area Policy**: Exactly 1 to 2 scans allowed per 100m geofenced radius. 3rd+ scan is discarded with 0 points.
        - **Database**: Dual SQLite local edge engine + PyMySQL background cloud synchronizer.
        - **Security**: PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations and cryptographic salts.
        """
    )
