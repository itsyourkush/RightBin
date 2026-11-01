"""
Personal Sustainability Dashboard.
Displays authoritative metrics, category breakdown charts, streaks, and badges.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Dashboard - RightBin", page_icon="📊", layout="wide")

import pandas as pd

from components.navigation import render_sidebar, require_auth
from components.metric_cards import render_metric_cards
from components.charts import render_category_donut_chart, render_weekly_activity_chart
from components.badge_cards import render_badges_grid
from services.analytics_service import AnalyticsService
from repositories.badge_repository import BadgeRepository

user = require_auth()
render_sidebar()

st.title(f"📊 {user.get('display_name') or user.get('name')}'s Eco Dashboard")
st.markdown("Monitor your recycling impact, active streaks, points, and category distribution.")

st.divider()

analytics_service = AnalyticsService()
badge_repo = BadgeRepository()

try:
    summary = analytics_service.get_dashboard_summary(user["id"])
except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.stop()

# 1. Top Metric Cards
render_metric_cards(
    green_score=summary["green_score"],
    points_balance=summary["points_balance"],
    current_streak=summary["current_streak"],
    level_info=summary["level_info"],
)

st.divider()

# 2. Charts Section
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    with st.container(border=True):
        render_category_donut_chart(summary["category_distribution"])

with col_chart2:
    with st.container(border=True):
        render_weekly_activity_chart(summary["weekly_trend"])

st.divider()

# 3. Active Challenges & Recent Scans
col_chal, col_recent = st.columns([1, 1.2])

with col_chal:
    st.markdown("### 🎯 Active Eco Challenges")
    challenges = summary.get("challenges_progress", [])
    if challenges:
        for ch in challenges:
            with st.container(border=True):
                title = ch["title"]
                prog = ch["progress"]
                target = ch["target"]
                done = ch["is_completed"]

                st.markdown(f"**{title}**")
                pct = min(prog / target, 1.0) if target > 0 else 1.0
                st.progress(float(pct))
                if done:
                    st.caption(f"✅ Completed ({prog}/{target})")
                else:
                    st.caption(f"In progress: {prog} of {target} completed")
    else:
        st.info("No active challenges right now.")

with col_recent:
    st.markdown("### 🕒 Recent Activity")
    recent = summary.get("recent_scans", [])
    if recent:
        df_recent = pd.DataFrame([
            {
                "Time": r["created_at"][:16].replace("T", " "),
                "Category": r["predicted_category"],
                "Sub-Type": r.get("sub_category") or f"Standard {r['predicted_category']}",
                "Location": r.get("location_name") or "—",
                "Status": "✅ Accepted" if r["prediction_accepted"] else "⚠️ Rejected",
                "Points": f"+{r['points_awarded']}",
            }
            for r in recent
        ])
        st.dataframe(df_recent, use_container_width=True, hide_index=True)
    else:
        st.info("No waste items scanned yet. Head over to Scan Waste to get started!")

st.divider()

# 4. Badges & Milestones
all_badges = badge_repo.get_all_active_badges()
render_badges_grid(all_badges, summary["earned_badges"])
