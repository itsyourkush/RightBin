"""
Eco-Challenges and Community Sprints Page.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Challenges - RightBin", page_icon="⚡", layout="wide")

from components.navigation import render_sidebar, require_auth
from services.challenge_service import ChallengeService

user = require_auth()
render_sidebar()

st.title("🎯 Eco-Challenges & Sprints")
st.markdown("Take on environmental challenges, build sustainable habits, and claim bonus Green Points!")

st.divider()

challenge_service = ChallengeService()
challenges = challenge_service.get_challenges_for_user(user["id"])

if not challenges:
    st.info("No active challenges at this moment. Please check back soon!")
else:
    for ch in challenges:
        with st.container(border=True):
            col_info, col_status = st.columns([2, 1])

            with col_info:
                st.markdown(f"### {ch['title']}")
                st.write(ch["description"])
                st.caption(f"🗓️ Challenge Window: {ch['start_at'][:10]} to {ch['end_at'][:10]}")

            with col_status:
                bonus = ch["bonus_points"]
                target = ch["criteria_value"]
                prog = ch["user_progress"]
                is_done = ch["is_completed"]

                st.metric("Bonus Points", f"+{bonus} pts")
                st.progress(float(ch["progress_percentage"]))

                if is_done:
                    st.success("✅ **Completed & Rewarded!**", icon="🌟")
                else:
                    st.info(f"Progress: **{prog} / {target}** completed")
