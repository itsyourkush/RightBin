"""
Weekly Eco Leaderboard Page.
Displays privacy-safe rankings, animated Top 3 podium, weekly point tallies,
and documented tie-breaking rules.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Leaderboard - RightBin", page_icon="🏆", layout="wide")

import pandas as pd

from components.navigation import render_sidebar
from services.leaderboard_service import LeaderboardService

user = st.session_state.get("user")
render_sidebar()

st.markdown(
    """
    <div style="margin-bottom: 1.2rem;">
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🏆 Weekly Community Champions
        </h1>
        <p style="font-size: 1rem; color: #64748B; margin-top: 4px;">
            Recognizing the top waste segregators in our community this week. Rank higher to earn exclusive gaming badges!
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

leaderboard_service = LeaderboardService()
current_uid = user["id"] if user else None

lb_data = leaderboard_service.get_weekly_leaderboard(current_user_id=current_uid)
rankings = lb_data["rankings"]
user_pos = lb_data["current_user_position"]

# Current User Position Highlight Banner
if user and user_pos:
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        st.markdown(
            f"""
            <div class="metric-card-interactive" style="border-top: 4px solid #F59E0B;">
                <div class="metric-header">
                    <span class="metric-label" style="color: #D97706;">Your Standing</span>
                    <div class="metric-icon-bubble bubble-gold">🎖️</div>
                </div>
                <div class="metric-value-large" style="color: #D97706;">#{user_pos['rank']}</div>
                <div class="metric-subtext">Weekly ranking position</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_u2:
        st.markdown(
            f"""
            <div class="metric-card-interactive" style="border-top: 4px solid #10B981;">
                <div class="metric-header">
                    <span class="metric-label" style="color: #059669;">Weekly Points</span>
                    <div class="metric-icon-bubble bubble-green">⚡</div>
                </div>
                <div class="metric-value-large" style="color: #059669;">+{user_pos['weekly_points']}</div>
                <div class="metric-subtext">Earned during current week</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_u3:
        st.markdown(
            f"""
            <div class="metric-card-interactive" style="border-top: 4px solid #8B5CF6;">
                <div class="metric-header">
                    <span class="metric-label" style="color: #7C3AED;">All-Time Impact</span>
                    <div class="metric-icon-bubble bubble-purple">⭐</div>
                </div>
                <div class="metric-value-large" style="color: #7C3AED;">{user_pos['green_score']:,}</div>
                <div class="metric-subtext">Cumulative Green Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

st.caption(f"🗓️ **Active Week Boundary (UTC)**: {lb_data['week_start'][:10]} to {lb_data['week_end'][:10]}")

if not rankings:
    st.info("No scans recorded yet this week. Be the first to scan and claim the #1 spot!")
else:
    # ── Top 3 Podium Cards ────────────────────────────────────────────────────
    if len(rankings) >= 1:
        st.markdown("### 👑 Top Champions")
        pod_cols = st.columns(min(len(rankings), 3))

        medals = [("🥇 1st Place", "#F59E0B", "#FFFBEB"), ("🥈 2nd Place", "#94A3B8", "#F8FAFC"), ("🥉 3rd Place", "#D97706", "#FFF7ED")]

        for i in range(min(len(rankings), 3)):
            r = rankings[i]
            label, border_c, bg_c = medals[i]
            with pod_cols[i]:
                is_curr = r.get("is_current_user", False)
                st.markdown(
                    f"""
                    <div style="background: {bg_c}; border: 2px solid {border_c}; border-radius: 16px; padding: 18px; text-align: center; box-shadow: var(--shadow-soft); position: relative; margin-bottom: 12px;">
                        <div style="font-size: 0.8rem; font-weight: 800; color: {border_c}; text-transform: uppercase; letter-spacing: 0.05em;">{label}</div>
                        <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin: 8px 0 2px 0;">
                            {r['display_name']} {'(You)' if is_curr else ''}
                        </div>
                        <div style="font-size: 1.4rem; font-weight: 900; color: #059669;">
                            +{r['weekly_points']} <span style="font-size: 0.8rem; font-weight: 600;">pts</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">
                            Total: {r['green_score']:,} pts
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── Full Table View ───────────────────────────────────────────────────────
    st.markdown("### 📋 Full Weekly Standings")

    def format_rank(r: int) -> str:
        if r == 1:
            return "🥇 1st"
        elif r == 2:
            return "🥈 2nd"
        elif r == 3:
            return "🥉 3rd"
        return f"#{r}"

    df_lb = pd.DataFrame([
        {
            "Rank": format_rank(r["rank"]),
            "Eco Member": f"🌟 {r['display_name']} (You)" if r["is_current_user"] else r["display_name"],
            "Weekly Points": f"+{r['weekly_points']} pts",
            "Total Green Score": f"{r['green_score']:,} pts",
        }
        for r in rankings
    ])

    st.dataframe(df_lb, use_container_width=True, hide_index=True)

st.divider()

with st.expander("ℹ️ How Leaderboard Points & Tie-Breaking Work", expanded=False):
    st.markdown(
        """
        - **Time Boundary**: Calculated weekly from **Monday 00:00:00 UTC** to **Sunday 23:59:59 UTC**.
        - **Eligible Points**: Includes all accepted waste scans (+10), first scan of day (+5), and challenge bonuses (+20+).
        - **Tie-Breaking Rule**:
          1. Highest weekly points.
          2. Earliest activity timestamp achieved in the current week.
          3. Higher all-time Green Score.
        - **Privacy Protection**: Only public display names are shown. Private emails are never published.
        """
    )
