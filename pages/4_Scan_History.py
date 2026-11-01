"""
Scan History Page.
Provides full paginated audit trail of all waste scans with filters and CSV export.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Scan History - RightBin", page_icon="📜", layout="wide")

import pandas as pd

from components.navigation import render_sidebar, require_auth
from repositories.scan_repository import ScanRepository
from config import config

user = require_auth()
render_sidebar()

st.title("📜 Waste Scan History & Logs")
st.markdown("Review your past classifications, confidence metrics, and earned Green Points.")

st.divider()

scan_repo = ScanRepository()

# Filters
col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    selected_cat = st.selectbox("Filter by Category:", ["All Categories"] + list(config.categories))
with col_filter2:
    selected_status = st.selectbox("Filter by Status:", ["All Scans", "Accepted Only", "Discarded Only", "Low Confidence Only"])

cat_param = None if selected_cat == "All Categories" else selected_cat
scans = scan_repo.get_user_scans(user["id"], limit=100, category=cat_param)

# Filter by status in memory
if selected_status == "Accepted Only":
    scans = [s for s in scans if s["prediction_accepted"]]
elif selected_status == "Discarded Only":
    scans = [s for s in scans if s.get("is_discarded") or "discard" in (s.get("rejection_reason") or "").lower()]
elif selected_status == "Low Confidence Only":
    scans = [s for s in scans if not s["prediction_accepted"] and not s.get("is_discarded")]

if not scans:
    st.info("No scan records found matching the selected filters.")
else:
    def _format_status(s: dict) -> str:
        if s.get("is_discarded") or "discard" in (s.get("rejection_reason") or "").lower():
            return "🗑️ DISCARDED (Area Limit)"
        if s["prediction_accepted"]:
            return "✅ Accepted"
        reason = s.get("rejection_reason") or ""
        if "location" in reason.lower() or "area" in reason.lower():
            return "🗑️ DISCARDED (Area Limit)"
        elif "duplicate" in reason.lower():
            return "⚠️ Duplicate Image"
        else:
            return "⚠️ Low Confidence"

    df = pd.DataFrame([
        {
            "Scan ID": s["id"],
            "Timestamp (UTC)": s["created_at"][:19].replace("T", " "),
            "Category": s["predicted_category"],
            "Specific Sub-Type": s.get("sub_category") or f"Standard {s['predicted_category']}",
            "Confidence": f"{s['confidence'] * 100:.1f}%",
            "Particular Area": s.get("location_name") or "Unspecified",
            "Status": _format_status(s),
            "Points": f"+{s['points_awarded']}",
            "Image Hash": s["image_hash"][:12] + "...",
        }
        for s in scans
    ])

    st.dataframe(df, use_container_width=True, hide_index=True)

    # CSV Download
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Scan History (CSV)",
        data=csv_bytes,
        file_name=f"waste_scans_user_{user['id']}.csv",
        mime="text/csv",
    )
