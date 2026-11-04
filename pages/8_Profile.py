"""
User Profile, Refer & Earn, and Plant-a-Tree Award Claims.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Profile - RightBin", page_icon="👤", layout="wide")

import pandas as pd

from components.navigation import render_sidebar, require_auth, get_auth_service
from services.referral_service import ReferralService
from services.tree_award_service import TreeAwardService
from repositories.user_repository import UserRepository

user = require_auth()
render_sidebar()

st.title("👤 Account Profile & Eco Initiatives")
st.markdown("Manage your personal account details, invite friends, and claim Plant-a-Tree awards.")

st.divider()

auth_service = get_auth_service()
user_repo = UserRepository()
referral_service = ReferralService()
tree_service = TreeAwardService()

profile = user_repo.get_profile(user["id"])

tab_details, tab_refer, tab_tree = st.tabs(["⚙️ Profile & Security", "🤝 Refer & Earn", "🌳 Plant-a-Tree Award"])

with tab_details:
    st.markdown("### Profile Information")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Full Name:** {profile.get('name')}")
        st.write(f"**Email Address:** {profile.get('email')}")
        st.write(f"**Current Role:** `{profile.get('role')}`")
    with c2:
        st.write(f"**Display Name:** {profile.get('display_name')}")
        st.write(f"**Member Since:** {profile.get('created_at', '')[:10]}")

    st.divider()

    col_edit_name, col_edit_pwd = st.columns(2)

    with col_edit_name:
        st.markdown("#### Update Display Name")
        with st.form("edit_display_name_form"):
            new_disp_name = st.text_input("New Display Name", value=profile.get("display_name", ""))
            if st.form_submit_button("Save Display Name"):
                ok, msg = auth_service.update_profile(user["id"], new_disp_name)
                if ok:
                    st.success(msg)
                    st.session_state["user"]["display_name"] = new_disp_name
                    st.rerun()
                else:
                    st.error(msg)

    with col_edit_pwd:
        st.markdown("#### Change Password")
        with st.form("change_password_form"):
            curr_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password (min 8 chars)", type="password")
            if st.form_submit_button("Update Password"):
                ok, msg = auth_service.change_password(user["id"], curr_pwd, new_pwd)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        with st.expander("🔄 Forgot Current Password? Direct Reset"):
            with st.form("profile_forgot_password_form"):
                p_new_pwd = st.text_input("New Password (min 8 chars)", type="password", key="prof_new_pwd")
                p_confirm_pwd = st.text_input("Confirm New Password", type="password", key="prof_confirm_pwd")
                if st.form_submit_button("Reset Password Without Current"):
                    ok, msg = auth_service.reset_password_by_email(user["email"], p_new_pwd, p_confirm_pwd)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

with tab_refer:
    st.markdown("### 🤝 Refer Friends, Multiply Green Impact")
    st.write(
        "Share your unique referral code with friends and classmates. "
        "When they register and log their first valid waste scan, **you both earn +50 Green Points!**"
    )

    ref_summary = referral_service.get_user_referral_summary(user["id"])

    with st.container(border=True):
        st.markdown(f"#### Your Referral Code:")
        st.markdown(
            f"<div style='background-color: #E8F5E9; padding: 12px; border-radius: 8px; font-size: 1.5rem; font-weight: bold; text-align: center; color: #2E7D32;'>"
            f"{ref_summary['referral_code']}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption("Tell your friends to enter this code during account registration.")

    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.metric("Total Friends Invited", ref_summary["total_referred"])
    with col_r2:
        st.metric("Verified (Scanned Waste)", ref_summary["successful_referrals"])
    with col_r3:
        st.metric("Bonus Points Earned", f"+{ref_summary['points_earned']} pts")

    if ref_summary["referral_list"]:
        st.markdown("#### Referred Friends Status")
        df_ref = pd.DataFrame([
            {
                "Referred User": r.get("referred_name") or f"User #{r['referred_user_id']}",
                "Status": "✅ Verified (+50 pts)" if r["status"] == "rewarded" else "⏳ Pending First Scan",
                "Joined On": r["created_at"][:10],
            }
            for r in ref_summary["referral_list"]
        ])
        st.dataframe(df_ref, use_container_width=True, hide_index=True)

with tab_tree:
    st.markdown("### 🌳 Plant-a-Tree Milestone Award")
    st.write(
        "Reach **500 Green Score points** through regular recycling habits to sponsor planting a real sapling "
        "through verified reforestation non-profit partners."
    )

    tree_status = tree_service.get_user_tree_status(user["id"])

    with st.container(border=True):
        st.metric("Your Green Score", f"{tree_status['current_green_score']} / {tree_status['threshold']} pts")

        if tree_status["has_fulfilled_claim"]:
            st.success("🎉 **Congratulations!** Your tree has been planted! Thank you for protecting the planet.", icon="🌲")
        elif tree_status["has_pending_claim"]:
            st.info("⏳ Your Plant-a-Tree request has been submitted and is currently being verified by an eco-administrator.")
        elif tree_status["is_eligible"]:
            st.success("🌟 **You are eligible to claim a tree!**")
            with st.form("claim_tree_form"):
                notes = st.text_area("Dedication or Note (optional):", placeholder="In honor of campus earth week...")
                if st.form_submit_button("🌱 Submit Plant-a-Tree Request", type="primary"):
                    ok, msg, _ = tree_service.submit_claim(user["id"], notes)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            short = tree_status["threshold"] - tree_status["current_green_score"]
            st.warning(f"Keep recycling! You need **{short} more Green Score points** to unlock tree planting.")

    if tree_status["claims"]:
        st.markdown("#### Your Tree Planting Claims")
        df_tree = pd.DataFrame([
            {
                "Claim ID": c["id"],
                "Status": c["status"].capitalize(),
                "Submitted On": c["submitted_at"][:10],
                "Notes": c.get("notes") or "-",
            }
            for c in tree_status["claims"]
        ])
        st.dataframe(df_tree, use_container_width=True, hide_index=True)
