"""
Badge Cards UI Component.
Displays achievements and milestones in an animated, interactive visual card grid.
"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List


def render_badges_grid(all_badges: List[Dict[str, Any]], earned_badges: List[Dict[str, Any]]) -> None:
    """Renders badges grid showing unlocked achievements and locked milestones with animations."""
    earned_dict = {b["id"]: b for b in earned_badges}

    st.markdown("### 🏅 Achievements & Milestone Badges")
    cols = st.columns(3)

    for idx, badge in enumerate(all_badges):
        col = cols[idx % 3]
        badge_id = badge["id"]
        is_earned = badge_id in earned_dict

        with col:
            icon = badge.get("icon", "🏅")
            name = badge["name"]
            desc = badge["description"]

            if is_earned:
                earned_record = earned_dict[badge_id]
                awarded_at = earned_record.get("awarded_at", "")[:10]
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); border: 2px solid #10B981; border-radius: 16px; padding: 16px; box-shadow: 0 10px 20px -5px rgba(16, 185, 129, 0.2); position: relative; overflow: hidden; margin-bottom: 12px; transition: transform 0.2s ease;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <span style="font-size: 2.2rem; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));">{icon}</span>
                            <span style="background: #10B981; color: white; font-size: 0.7rem; font-weight: 800; padding: 3px 8px; border-radius: 9999px; letter-spacing: 0.05em;">UNLOCKED 🎉</span>
                        </div>
                        <div style="font-size: 1.1rem; font-weight: 800; color: #064E3B; margin-bottom: 4px;">{name}</div>
                        <div style="font-size: 0.82rem; color: #047857; margin-bottom: 8px; line-height: 1.4;">{desc}</div>
                        <div style="font-size: 0.72rem; color: #059669; font-weight: 600;">Unlocked: {awarded_at}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                crit_type = badge.get('criteria_type', 'Scans')
                crit_val = badge.get('criteria_value', 1)
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 2px dashed #CBD5E1; border-radius: 16px; padding: 16px; position: relative; margin-bottom: 12px; opacity: 0.85; transition: transform 0.2s ease;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <span style="font-size: 2rem; opacity: 0.5;">🔒</span>
                            <span style="background: #F1F5F9; color: #64748B; font-size: 0.7rem; font-weight: 700; padding: 3px 8px; border-radius: 9999px;">LOCKED</span>
                        </div>
                        <div style="font-size: 1.05rem; font-weight: 700; color: #334155; margin-bottom: 4px;">{name}</div>
                        <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 8px; line-height: 1.4;">{desc}</div>
                        <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 600;">Goal: Reach {crit_val} {crit_type}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
