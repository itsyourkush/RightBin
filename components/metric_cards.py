"""
Metric Cards UI Component.
Displays high-level user engagement, balances, levels, and streak counters
using modern interactive glassmorphic cards with animated colorful icon bubbles.
"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict


def render_metric_cards(
    green_score: int,
    points_balance: int,
    current_streak: int,
    level_info: Dict[str, Any],
) -> None:
    """Renders a responsive 4-column interactive metrics dashboard."""
    col1, col2, col3, col4 = st.columns(4)

    cur_level = level_info.get("current_level", "Green Starter")
    next_lvl = level_info.get("next_level")
    progress_val = level_info.get("progress", 0.0)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card-interactive">
                <div class="metric-header">
                    <span class="metric-label">Green Score</span>
                    <div class="metric-icon-bubble bubble-green">🌿</div>
                </div>
                <div class="metric-value-large">{green_score:,}</div>
                <div class="metric-subtext">Lifetime recycling impact</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card-interactive">
                <div class="metric-header">
                    <span class="metric-label">Spendable Points</span>
                    <div class="metric-icon-bubble bubble-gold">💰</div>
                </div>
                <div class="metric-value-large" style="color: #D97706;">{points_balance:,}</div>
                <div class="metric-subtext">Redeemable for gaming codes</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        streak_text = f"{current_streak} Day{'s' if current_streak != 1 else ''}"
        st.markdown(
            f"""
            <div class="metric-card-interactive">
                <div class="metric-header">
                    <span class="metric-label">Daily Streak</span>
                    <div class="metric-icon-bubble bubble-orange">🔥</div>
                </div>
                <div class="metric-value-large" style="color: #EA580C;">{streak_text}</div>
                <div class="metric-subtext">Consecutive active sorting</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card-interactive">
                <div class="metric-header">
                    <span class="metric-label">Current Tier</span>
                    <div class="metric-icon-bubble bubble-purple">⭐</div>
                </div>
                <div class="metric-value-large" style="font-size: 1.45rem; color: #7C3AED;">{cur_level}</div>
                <div class="metric-subtext">Next: {next_lvl or 'Max Tier Achieved'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    # Level progress bar with customized visual styling
    if next_lvl:
        pts_needed = level_info.get("points_needed", 0)
        st.markdown(
            f"""
            <div style="background: #F1F5F9; border-radius: 9999px; padding: 3px; border: 1px solid #CBD5E1; margin: 10px 0 4px 0;">
                <div style="background: linear-gradient(90deg, #10B981, #059669); height: 10px; width: {int(progress_val * 100)}%; border-radius: 9999px; transition: width 0.6s ease;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748B;">
                <span>Current: <strong>{cur_level}</strong></span>
                <span><strong>{pts_needed}</strong> more pts to <strong>{next_lvl}</strong></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: #FEF3C7; border-radius: 9999px; padding: 3px; border: 1px solid #FCD34D; margin: 10px 0 4px 0;">
                <div style="background: linear-gradient(90deg, #F59E0B, #D97706); height: 10px; width: 100%; border-radius: 9999px;"></div>
            </div>
            <div style="text-align: center; font-size: 0.85rem; color: #92400E; font-weight: 700; margin-top: 4px;">
                🏆 Highest Tier Achieved! You are an official Planet Protector.
            </div>
            """,
            unsafe_allow_html=True,
        )
