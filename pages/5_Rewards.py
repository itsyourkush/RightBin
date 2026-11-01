"""
Rewards Catalogue, Game Redeem Codes, and Lucky Scan Spin.
Provides gaming vouchers (Google Play, Clash of Clans, Puzzle games, Robux),
instant redeem code generation, and daily spin rewards.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Rewards - RightBin", page_icon="🎁", layout="wide")

import pandas as pd

from components.navigation import render_sidebar, require_auth
from components.reward_cards import render_reward_catalogue
from services.rewards_service import RewardsService
from repositories.points_repository import PointsRepository
from repositories.reward_repository import RewardRepository

user = require_auth()
render_sidebar()

st.title("🎁 Rewards & Game Redeem Codes")
st.markdown("Redeem your Green Points for **Google Play credits, Clash of Clans Gems, Puzzle Game boosters**, and eco-friendly products!")

st.divider()

rewards_service = RewardsService()
points_repo = PointsRepository()
reward_repo = RewardRepository()

balance = points_repo.get_user_balance(user["id"])

# Top Balance Banner
st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 50%, #FDE68A 100%); border: 2px solid #F59E0B; border-radius: 16px; padding: 18px 24px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px; box-shadow: 0 10px 25px -5px rgba(245, 158, 11, 0.2); margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 16px;">
            <div style="width: 54px; height: 54px; border-radius: 14px; background: linear-gradient(135deg, #F59E0B, #D97706); display: flex; align-items: center; justify-content: center; font-size: 2rem; box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);">
                🪙
            </div>
            <div>
                <div style="font-size: 0.75rem; font-weight: 800; color: #92400E; text-transform: uppercase; letter-spacing: 0.05em;">Spendable Balance</div>
                <div style="font-size: 2.1rem; font-weight: 900; color: #78350F; line-height: 1.1;">{balance:,} <span style="font-size: 1.1rem; font-weight: 700;">PTS</span></div>
            </div>
        </div>
        <div style="background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(8px); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 12px; padding: 10px 16px; display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.5rem;">🎮</span>
            <div style="font-size: 0.85rem; color: #92400E; font-weight: 600;">
                Instant Gaming Codes unlocked on 1-click redemption!
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Flash latest redeemed game code if present in session
if "latest_redeemed_code" in st.session_state and st.session_state["latest_redeemed_code"]:
    code_val = st.session_state["latest_redeemed_code"]
    item_val = st.session_state.get('latest_redeemed_item', 'Reward')
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); border: 2px solid #10B981; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.25);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 1.2rem; font-weight: 800; color: #064E3B;">🎉 Redemption Successful: {item_val}</span>
                <span style="background: #10B981; color: white; font-weight: 800; font-size: 0.75rem; padding: 3px 10px; border-radius: 9999px;">INSTANT CODE READY</span>
            </div>
            <div style="font-size: 0.9rem; color: #047857; margin-bottom: 12px;">Copy and paste this voucher code into your game or store:</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(code_val, language="text")
    if st.button("Dismiss Voucher Notification", key="dismiss_code_btn"):
        st.session_state["latest_redeemed_code"] = None
        st.rerun()

st.divider()

# Tabbed layout: Catalogue, Lucky Spin, Redemption History
tab_cat, tab_spin, tab_history = st.tabs(["🛍️ Reward Catalogue", "🎡 Lucky Scan Spin", "📜 My Redemptions & Codes"])

with tab_cat:
    filter_col, _ = st.columns([1.5, 2])
    with filter_col:
        cat_filter = st.radio(
            "Filter Catalogue:",
            ["All Rewards", "🎮 Game Vouchers & Codes", "🌱 Eco-Friendly Items"],
            horizontal=True,
        )

    catalogue = rewards_service.get_catalogue(user["id"])

    # Apply filter
    if cat_filter == "🎮 Game Vouchers & Codes":
        catalogue = [
            r for r in catalogue
            if r.get("reward_type") == "digital" or any(k in r["name"].lower() for k in ("clash", "google play", "puzzle", "bgmi", "roblox", "steam", "gems"))
        ]
    elif cat_filter == "🌱 Eco-Friendly Items":
        catalogue = [
            r for r in catalogue
            if r.get("reward_type") != "digital" and not any(k in r["name"].lower() for k in ("clash", "google play", "puzzle", "bgmi", "roblox", "steam", "gems"))
        ]

    # Callback handler for redemption
    def handle_redeem(reward_id: int):
        ok, msg, red = rewards_service.request_redemption(user["id"], reward_id)
        if ok:
            st.balloons()
            if red and red.get("claim_code"):
                st.session_state["latest_redeemed_code"] = red["claim_code"]
                target_reward = next((r for r in catalogue if r["id"] == reward_id), None)
                st.session_state["latest_redeemed_item"] = target_reward["name"] if target_reward else "Game Voucher"
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    render_reward_catalogue(
        catalogue,
        user_balance=balance,
        on_redeem_callback=lambda r_id: handle_redeem(r_id),
    )

with tab_spin:
    st.markdown("### 🎡 Lucky Scan Spin")
    st.write(
        "Spin the daily mystery wheel once every 24 hours to earn bonus Green Points (5 to 25 pts)!"
    )

    col_wheel, col_info = st.columns([1.2, 1])
    with col_wheel:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%); border-radius: 20px; padding: 25px; text-align: center; color: white; box-shadow: 0 15px 30px rgba(67, 56, 202, 0.3); border: 2px solid #6366F1; position: relative; overflow: hidden;">
                <div style="font-size: 0.8rem; font-weight: 800; color: #A5B4FC; letter-spacing: 0.1em; text-transform: uppercase;">DAILY ECO ROULETTE</div>
                <div style="font-size: 4.5rem; margin: 15px 0; filter: drop-shadow(0 0 15px rgba(251, 191, 36, 0.5)); animation: float 3s ease-in-out infinite;">
                    🎡
                </div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #FDE68A;">Win +5 to +25 Green Points</div>
                <div style="font-size: 0.8rem; color: #C7D2FE; margin-top: 4px;">Free spin recharges every 24 hours</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("🎲 **Spin the Lucky Wheel!**", type="primary", use_container_width=True):
            ok, msg, spin_data = rewards_service.play_lucky_spin(user["id"])
            if ok:
                st.balloons()
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)

    with col_info:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px; box-shadow: var(--shadow-soft);">
                <h4 style="margin: 0 0 8px 0; color: #1E293B;">🎯 Rules & Fair Play</h4>
                <ul style="padding-left: 20px; color: #475569; font-size: 0.88rem; line-height: 1.6; margin-bottom: 0;">
                    <li><strong>Frequency</strong>: 1 free spin every 24 hours.</li>
                    <li><strong>Reward Range</strong>: Random bonus between 5 and 25 Green Points.</li>
                    <li><strong>Instant Credit</strong>: Points are immediately added to your spendable balance for Clash of Clans, Google Play, or eco-merch!</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        last_spin = reward_repo.get_last_spin(user["id"])
        if last_spin:
            st.caption(f"🕒 Last spin: {last_spin['created_at'][:19].replace('T', ' ')} UTC (+{last_spin['points_awarded']} pts)")

with tab_history:
    st.markdown("### 📜 My Claimed Rewards & Game Codes")
    my_redemptions = reward_repo.get_user_redemptions(user["id"])

    if not my_redemptions:
        st.info("You haven't claimed any rewards yet. Keep scanning to accumulate points!")
    else:
        for r in my_redemptions:
            r_name = r.get("reward_name", f"Reward #{r['reward_id']}")
            r_notes = r.get("notes") or ""
            cost = r["points_cost"]
            date_str = r["requested_at"][:19].replace("T", " ")

            is_game_code = "Redeem Code:" in r_notes or any(k in r_name.lower() for k in ("clash", "google play", "puzzle", "bgmi", "roblox", "steam", "gems"))

            code_part = ""
            if "Redeem Code:" in r_notes:
                code_part = r_notes.split("Redeem Code:")[1].split("|")[0].strip()

            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 2px solid {'#FED7AA' if is_game_code else '#BBF7D0'}; border-radius: 14px; padding: 16px; margin-bottom: 12px; box-shadow: var(--shadow-soft);">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <div style="font-size: 1.1rem; font-weight: 800; color: #0F172A;">
                                {'🎮 ' if is_game_code else '🌱 '}{r_name}
                            </div>
                            <div style="font-size: 0.78rem; color: #64748B;">
                                Claimed on {date_str} UTC &bull; Cost: <strong style="color: #059669;">{cost} pts</strong>
                            </div>
                        </div>
                        <span style="background: {'#FEF3C7' if is_game_code else '#DCFCE7'}; color: {'#B45309' if is_game_code else '#15803D'}; font-weight: 800; font-size: 0.72rem; padding: 4px 10px; border-radius: 9999px;">
                            {'⚡ ACTIVE VOUCHER' if is_game_code else '✅ FULFILLED'}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if code_part:
                st.code(code_part, language="text")
                st.caption("💡 Enter this code in your game settings or Google Play Store > Payments & Subscriptions > Redeem Gift Code.")
            elif r_notes:
                st.caption(f"Note: {r_notes}")
