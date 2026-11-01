"""
Notification and Feedback Messages Component.
Displays toasts, alerts, and gamification celebration dialogs.
"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List, Optional


def render_flash_messages() -> None:
    """Checks and renders any flash messages stored in session_state."""
    flash = st.session_state.get("flash_message")
    if flash:
        msg_type, text = flash
        if msg_type == "success":
            st.success(text)
        elif msg_type == "error":
            st.error(text)
        elif msg_type == "warning":
            st.warning(text)
        else:
            st.info(text)
        # Clear after rendering
        st.session_state["flash_message"] = None


def render_gamification_celebration(result: Dict[str, Any]) -> None:
    """Renders prominent celebration callouts for points earned, level ups, or badges."""
    points = result.get("points_awarded", 0)
    reasons = result.get("reasons", [])
    unlocked = result.get("unlocked_badges", [])
    challenges = result.get("completed_challenges", [])

    if points > 0:
        st.balloons()
        with st.container(border=True):
            st.markdown(f"### 🎉 **+{points} Green Points Earned!**")
            for reason in reasons:
                st.markdown(f"- {reason}")

            streak = result.get("current_streak", 0)
            if streak > 1:
                st.info(f"🔥 Active Streak: **{streak} Days in a row!** Keep recycling tomorrow!")

    # Badges celebration
    for badge in unlocked:
        st.success(
            f"🏆 **Achievement Unlocked**: {badge.get('icon', '🏅')} **{badge['name']}**\n\n"
            f"*{badge['description']}*",
            icon="🌟",
        )

    # Challenge completion celebration
    for ch in challenges:
        st.success(
            f"🎯 **Challenge Completed**: **{ch['title']}**! (+{ch.get('bonus_awarded', 0)} bonus points)",
            icon="🎉",
        )
