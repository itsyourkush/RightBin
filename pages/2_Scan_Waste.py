"""
Waste Scanning and AI Classification Page.
Features:
- Mobile-responsive layout (native camera support, touch-friendly buttons)
- Fine-grained waste sub-type identification (Resin codes, material specs, recyclability)
- Area-based scanning policy: 1 to 2 scans per particular area; otherwise discarded
"""

from __future__ import annotations

import io
from PIL import Image
import streamlit as st

st.set_page_config(page_title="Scan Waste - RightBin", page_icon="📸", layout="wide")

from components.navigation import render_sidebar, require_auth
from components.charts import render_model_confidence_gauge
from components.messages import render_gamification_celebration
from components.mobile_access import render_mobile_access_section
from components.dustbin_guide import render_dustbin_wayfinding
from components.environmental_card import render_environmental_impact_section
from components.location_picker import render_google_maps_location_section
from services.classification_service import ClassificationService
from services.gamification_service import GamificationService
from services.referral_service import ReferralService
from repositories.scan_repository import ScanRepository
from utils.location_utils import extract_exif_gps
from config import config

user = require_auth()
render_sidebar()

# ── Mobile-responsive CSS injection ──────────────────────────────────────────
st.markdown("""
<style>
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    .stRadio > div {
        gap: 0.5rem;
    }
    .stRadio label {
        padding: 0.75rem 1rem !important;
        font-size: 1.1rem !important;
    }
    [data-testid="stFileUploader"] section {
        min-height: 120px;
    }
    .stButton > button {
        min-height: 52px !important;
        font-size: 1.05rem !important;
    }
}

.camera-prompt {
    background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
    border: 2px dashed #2E7D32;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    margin: 0.5rem 0;
}

.discard-card {
    background: #FFF1F2;
    border: 2px solid #E11D48;
    border-radius: 12px;
    padding: 1.25rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

st.title("📸 Waste Image Classification")
st.markdown("Classify recyclable materials, detect specific resin types, and earn Green Points responsibly.")

# Mobile access QR code section
render_mobile_access_section()

st.divider()

# Services
classification_service = ClassificationService()
gamification_service = GamificationService()
scan_repository = ScanRepository()
referral_service = ReferralService()

# ── Step 1: Accurate Google Maps Location & Anti-Fraud Geofencing ─────────
active_lat, active_lon, active_area_name = render_google_maps_location_section()

# Query user's scan count in this particular area
scans_in_area = scan_repository.count_accepted_scans_in_area(
    user_id=user["id"],
    latitude=active_lat,
    longitude=active_lon,
    location_name=active_area_name,
    proximity_meters=config.area_proximity_threshold_meters,
)

st.markdown("#### 🛡️ Anti-Fraud Geofence Status for this Location")
if scans_in_area >= config.max_scans_per_area:
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #FFF1F2, #FFE4E6); border: 2px solid #E11D48; border-radius: 12px; padding: 12px; box-shadow: 0 4px 12px rgba(225, 29, 72, 0.15);">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-weight: 800; color: #BE123C; font-size: 0.95rem;">🚫 LIMIT REACHED ({scans_in_area}/{config.max_scans_per_area})</span>
                <span style="background: #E11D48; color: white; font-size: 0.65rem; font-weight: 800; padding: 2px 6px; border-radius: 6px;">DISCARD NEXT</span>
            </div>
            <div style="font-size: 0.8rem; color: #9F1239; margin-top: 6px; line-height: 1.3;">
                You have already used the maximum <strong>{config.max_scans_per_area} scans</strong> within 100m of this location. Further scans here will be discarded with 0 pts!
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif scans_in_area == 1:
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #FFFBEB, #FEF3C7); border: 2px solid #F59E0B; border-radius: 12px; padding: 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-weight: 800; color: #B45309; font-size: 0.95rem;">🟡 1 of 2 Scans Used</span>
                <span style="background: #F59E0B; color: white; font-size: 0.65rem; font-weight: 800; padding: 2px 6px; border-radius: 6px;">1 REMAINING</span>
            </div>
            <div style="font-size: 0.8rem; color: #92400E; margin-top: 6px;">
                You have <strong>1 more scan allowed</strong> at this location before geofence lockout.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #F0FDF4, #DCFCE7); border: 2px solid #10B981; border-radius: 12px; padding: 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-weight: 800; color: #065F46; font-size: 0.95rem;">🟢 Area Clean (0/2 Used)</span>
                <span style="background: #10B981; color: white; font-size: 0.65rem; font-weight: 800; padding: 2px 6px; border-radius: 6px;">2 AVAILABLE</span>
            </div>
            <div style="font-size: 0.8rem; color: #047857; margin-top: 6px;">
                Full eligibility active for this location. +10 Green Points awarded on valid classification!
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── Step 2: Single Waste Scanner ─────────────────────────────────────────────
st.markdown("### 📷 Step 2: Scan Waste Item")
st.caption("Snap a photo directly with your camera or select an image file to classify.")

uploaded_file = st.file_uploader(
    "📸 Tap to snap a photo with camera or choose an image:",
    type=["png", "jpg", "jpeg", "webp"],
    help="On iPhone (Safari) and Android (Chrome), tapping this directly triggers your camera to take a photo.",
)

# ── Classification & Results ─────────────────────────────────────────────────
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name if hasattr(uploaded_file, "name") else "camera_capture.png"

    # Auto-detect camera GPS from photo
    photo_gps = extract_exif_gps(file_bytes)
    if photo_gps:
        active_lat, active_lon = photo_gps
        active_area_name = f"Photo Camera GPS ({active_lat:.4f}, {active_lon:.4f})"
        st.session_state["scanner_lat"] = active_lat
        st.session_state["scanner_lon"] = active_lon
        st.session_state["scanner_gps_locked"] = True
        st.session_state["scanner_location_name"] = active_area_name
        st.info(
            f"📍 **Camera GPS Detected from Photo**: `{active_lat:.6f}, {active_lon:.6f}` "
            f"([Verified on Google Maps](https://www.google.com/maps/search/?api=1&query={active_lat},{active_lon}))",
            icon="🗺️",
        )

    col_img, col_results = st.columns([1, 1.2])

    with col_img:
        st.markdown("#### 🖼️ Captured Image")
        try:
            image_preview = Image.open(io.BytesIO(file_bytes))
            st.image(
                image_preview,
                caption=f"{file_name} ({len(file_bytes) / 1024:.1f} KB)",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Cannot render image preview: {e}")

    with col_results:
        st.markdown("#### 🤖 AI Classification Result")
        with st.spinner("Analyzing material texture, fine-grained sub-type, and area quota..."):
            result = classification_service.classify_image(
                file_name=file_name,
                image_bytes=file_bytes,
                user_id=user["id"],
                latitude=active_lat,
                longitude=active_lon,
                area_name=active_area_name,
                location_name=active_area_name,
            )

        status = result["status"]
        is_discarded = result.get("is_discarded", False)

        if status == "validation_failed":
            st.error(f"❌ **Validation Error**: {result['error_message']}")
        elif status == "model_unavailable":
            st.warning(f"⚠️ {result['error_message']}")
        else:
            category = result["predicted_category"]
            sub_category = result.get("sub_category", f"Standard {category}")
            subtype_details = result.get("subtype_details", {})
            confidence = result["confidence"]
            accepted = result["prediction_accepted"]
            rec = result["recommendation"]
            img_hash = result["image_hash"]
            rejection_reason = result.get("rejection_reason", "")

            # ── 1. If Discarded: Show Prominent Discard Notice ────────────
            cat_icons = {"Plastic": "🧴", "Paper": "📄", "Organic": "🍎", "Metal": "🥫", "Glass": "🍾"}
            c_icon = cat_icons.get(category, "♻️")

            if is_discarded:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%); border: 2px solid #E11D48; border-radius: 14px; padding: 16px; margin-bottom: 14px; box-shadow: 0 10px 25px -5px rgba(225, 29, 72, 0.25);">
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                            <span style="font-size: 2.2rem;">🚫</span>
                            <div>
                                <div style="font-size: 1.25rem; font-weight: 800; color: #9F1239;">SCAN DISCARDED — Quota Exceeded</div>
                                <div style="font-size: 0.8rem; color: #BE123C; font-weight: 700;">Particular Area: {active_area_name} • 0 Points Credited</div>
                            </div>
                        </div>
                        <div style="font-size: 0.85rem; color: #881337; line-height: 1.4;">
                            🛡️ <strong>Anti-Farming Rule</strong>: Exactly <strong>1 to 2 scans are permitted per particular area</strong>. This scan was rejected because you have already reached the quota here. Please walk to a different location or campus zone to scan new recyclables!
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif accepted:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); border: 2px solid #10B981; border-radius: 14px; padding: 14px 18px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.2);">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 2.2rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">{c_icon}</span>
                            <div>
                                <div style="font-size: 0.72rem; font-weight: 800; color: #047857; text-transform: uppercase; letter-spacing: 0.05em;">AI Verified Material</div>
                                <div style="font-size: 1.45rem; font-weight: 800; color: #064E3B; line-height: 1.1;">{category}</div>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: #10B981; color: white; font-weight: 800; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; letter-spacing: 0.03em;">
                                {confidence * 100:.1f}% ACCURACY
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.warning(f"### ⚠️ Uncertain: **{category}**")
                st.caption(result.get("uncertainty_message", ""))

            # ── 2. Specific Sub-Type Details Box ─────────────────────────
            with st.container(border=True):
                st.markdown(f"#### 🏷️ Specific Waste Type: **{sub_category}**")
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    st.write(f"**Resin / Material Code**: `{rec.get('resin_code', 'Standard')}`")
                    st.write(f"**Material Type**: {subtype_details.get('material_type', category)}")
                with c_s2:
                    st.write(f"**Recyclability**: 🌿 **{rec.get('recyclability_score', 'Widely Recyclable')}**")
                    st.markdown(f"**Disposal Location**: 📍 [{active_area_name}](https://www.google.com/maps/search/?api=1&query={active_lat},{active_lon})")

                if subtype_details.get("environmental_impact"):
                    st.caption(f"💡 **Eco Impact**: {subtype_details['environmental_impact']}")

            # ── 3. Visual Dustbin Wayfinding (Directs waste towards exact bin) ──
            render_dustbin_wayfinding(category=category, sub_category=sub_category, recommendation=rec)

            # ── 4. Environmental Harm & How Sorting Protects Our Planet ─────────
            render_environmental_impact_section(category=category, sub_category=sub_category, recommendation=rec)

            # ── 4. Confidence Gauge ──────────────────────────────────────
            render_model_confidence_gauge(
                confidence, threshold=result.get("confidence_threshold", 0.60)
            )

            # ── 4. Probability Breakdown ─────────────────────────────────
            with st.expander("📊 All Class Probabilities", expanded=False):
                probs = result.get("all_probabilities", {})
                for cat, p in sorted(probs.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"**{cat}**: {p * 100:.1f}%")
                    st.progress(float(p))

            # ── 5. QR Code / Barcode Detection Banner (if present) ───────
            if result.get("qr_code_detected"):
                st.info(f"📱 **Detected Packaging QR Code / Link:**\n\n`{result['qr_code_content']}`", icon="🔍")

            # ── 6. Disposal Recommendations ──────────────────────────────
            with st.container(border=True):
                bin_color = rec.get("bin_color", "#2E7D32")
                st.markdown(
                    f"#### 🗑️ Recommended Bin: "
                    f"<span style='color: {bin_color}; font-weight: bold;'>"
                    f"{rec.get('bin_type')}</span>",
                    unsafe_allow_html=True,
                )

                st.markdown("**How to prepare this item:**")
                for step in rec.get("preparation_steps", []):
                    st.markdown(f"✅ {step}")

                if rec.get("contamination_warnings"):
                    st.markdown("**⚠️ Watch out for:**")
                    for warn in rec.get("contamination_warnings", []):
                        st.markdown(
                            f"- <span style='color: #DC2626;'>{warn}</span>",
                            unsafe_allow_html=True,
                        )

                if rec.get("facility_note"):
                    st.caption(f"💡 *{rec['facility_note']}*")

            # ── 7. Record scan & process gamification (once per image) ───
            scan_session_key = f"processed_scan_{img_hash}"
            if scan_session_key not in st.session_state:
                # 1. Record scan into database with location, sub-category, and discarded flag
                db_scan = scan_repository.record_scan(
                    user_id=user["id"],
                    predicted_category=category,
                    sub_category=sub_category,
                    confidence=confidence,
                    prediction_accepted=accepted,
                    image_hash=img_hash,
                    model_version=result["model_version"],
                    points_awarded=0,
                    latitude=active_lat,
                    longitude=active_lon,
                    location_name=active_area_name,
                    rejection_reason=rejection_reason if not accepted else None,
                    is_discarded=is_discarded,
                )

                # 2. Gamification: points, streaks, badges, challenges
                gamification_res = gamification_service.process_scan_gamification(
                    user_id=user["id"],
                    scan_id=db_scan["id"],
                    predicted_category=category,
                    confidence=confidence,
                    prediction_accepted=accepted,
                    image_hash=img_hash,
                    rejection_reason=rejection_reason,
                )

                # 3. Check referral reward on first scan if accepted
                if accepted:
                    referral_service.check_and_reward_on_first_scan(user["id"])

                st.session_state[scan_session_key] = gamification_res

            # ── 8. Show Gamification Results ──────────────────────────────
            saved_gamification = st.session_state.get(scan_session_key)
            if saved_gamification and not is_discarded:
                render_gamification_celebration(saved_gamification)

    # ── Quick-action buttons (easy to tap on mobile) ─────────────────────────
    st.divider()
    st.markdown("#### 🔄 What's next?")
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("📸 Scan Another Item", type="primary", use_container_width=True):
            st.rerun()
    with btn_col2:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.switch_page("pages/3_Dashboard.py")
    with btn_col3:
        if st.button("🎁 Check Rewards", use_container_width=True):
            st.switch_page("pages/5_Rewards.py")
