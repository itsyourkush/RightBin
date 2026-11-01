"""
Administrative Control Center.
Protected dashboard for reviewing redemptions, auditing tree claims,
monitoring ML metrics, managing users, and publishing eco-challenges.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Admin - RightBin", page_icon="⚙️", layout="wide")

import json
import os
from pathlib import Path
import pandas as pd

from components.navigation import render_sidebar, require_admin
from config import config
from services.analytics_service import AnalyticsService
from services.rewards_service import RewardsService
from services.tree_award_service import TreeAwardService
from services.challenge_service import ChallengeService
from repositories.reward_repository import RewardRepository
from repositories.user_repository import UserRepository
from repositories.referral_repository import ReferralRepository

admin_user = require_admin()
render_sidebar()

st.title("👑 Administrator Control Center")
st.markdown("System overview, reward fulfillment, machine learning audit, and user management.")

st.divider()

analytics_service = AnalyticsService()
rewards_service = RewardsService()
tree_service = TreeAwardService()
challenge_service = ChallengeService()
reward_repo = RewardRepository()
user_repo = UserRepository()
referral_repo = ReferralRepository()

# System Metrics Overview
stats = analytics_service.get_system_analytics()

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("Total Users", f"{stats['total_users']:,}")
with m2:
    st.metric("Scans Logged", f"{stats['total_scans']:,}")
with m3:
    st.metric("Accepted Scans", f"{stats['accepted_scans']:,}")
with m4:
    st.metric("Points Issued", f"{stats['total_points_distributed']:,}")
with m5:
    st.metric("Pending Redemptions", f"{stats['pending_redemptions']:,}")

st.divider()

tab_ml, tab_redemptions, tab_trees, tab_users, tab_new_ch, tab_mysql = st.tabs([
    "🧠 ML Model & Audit",
    "🎁 Review Redemptions",
    "🌳 Tree Award Claims",
    "👥 User Accounts",
    "🎯 Create Challenge",
    "🔗 MySQL Server Sync",
])

# 1. Machine Learning Model Audit
with tab_ml:
    st.markdown("### 🧠 Keras CNN Model Audit & Evaluation")
    st.caption("Inspecting genuine model performance metrics and confusion matrix artifacts.")

    metadata_path = config.model_path.parent / "model_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        col_m1, col_m2 = st.columns([1, 1.2])
        with col_m1:
            st.markdown("#### Model Specification")
            st.write(f"**Version**: `{meta.get('model_version')}`")
            st.write(f"**Test Set Accuracy**: `{meta.get('overall_test_accuracy') * 100:.2f}%`")
            st.write(f"**Confidence Threshold**: `{meta.get('confidence_threshold') * 100:.0f}%`")
            st.write(f"**Evaluated At**: `{meta.get('evaluated_at')[:19].replace('T', ' ')} UTC`")

            # Per class metrics table
            st.markdown("#### Per-Class Metrics")
            pcm = meta.get("per_class_metrics", {})
            if pcm:
                df_pcm = pd.DataFrame([
                    {
                        "Class": cat,
                        "Precision": f"{vals['precision'] * 100:.1f}%",
                        "Recall": f"{vals['recall'] * 100:.1f}%",
                        "F1-Score": f"{vals['f1_score']:.2f}",
                        "Test Support": vals["support"],
                    }
                    for cat, vals in pcm.items()
                ])
                st.dataframe(df_pcm, use_container_width=True, hide_index=True)

        with col_m2:
            st.markdown("#### Confusion Matrix & Training Curves")
            cm_img = config.model_path.parent / "confusion_matrix.png"
            history_img = config.model_path.parent / "training_history.png"

            if cm_img.exists():
                st.image(str(cm_img), caption="Test Split Confusion Matrix", use_container_width=True)
            if history_img.exists():
                st.image(str(history_img), caption="Training & Validation Accuracy/Loss Curves", use_container_width=True)
    else:
        st.warning("Model metadata artifact not found. Please run evaluate_model.py.")

# 2. Review Redemptions
with tab_redemptions:
    st.markdown("### 🎁 Pending Reward Redemptions")
    pending = reward_repo.get_all_redemptions(status="pending")

    if not pending:
        st.success("No pending redemptions requiring review!")
    else:
        for r in pending:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.markdown(f"**Request #{r['id']}**: {r['reward_name']}")
                    st.caption(f"Requested by: {r.get('user_name')} ({r.get('user_email')}) • Cost: {r['points_cost']} pts")
                    st.write(f"User Notes: {r.get('notes') or 'None'}")
                with c2:
                    if st.button(f"✅ Approve #{r['id']}", key=f"app_red_{r['id']}", type="primary"):
                        ok, msg = rewards_service.review_redemption(r["id"], "approved", admin_user["id"], "Approved by Admin")
                        if ok:
                            st.success(msg)
                            st.rerun()
                with c3:
                    if st.button(f"❌ Reject & Refund #{r['id']}", key=f"rej_red_{r['id']}"):
                        ok, msg = rewards_service.review_redemption(r["id"], "rejected", admin_user["id"], "Refunded by Admin")
                        if ok:
                            st.warning(msg)
                            st.rerun()

    # All Redemptions History
    with st.expander("View Full Redemptions Audit Log", expanded=False):
        all_reds = reward_repo.get_all_redemptions()
        if all_reds:
            df_all_reds = pd.DataFrame([
                {
                    "ID": r["id"],
                    "User": r.get("user_email"),
                    "Reward": r["reward_name"],
                    "Cost": f"-{r['points_cost']} pts",
                    "Status": r["status"].capitalize(),
                    "Requested At": r["requested_at"][:16].replace("T", " "),
                    "Notes": r.get("notes") or "-",
                }
                for r in all_reds
            ])
            st.dataframe(df_all_reds, use_container_width=True, hide_index=True)

# 3. Tree Award Claims
with tab_trees:
    st.markdown("### 🌳 Plant-a-Tree Award Claims")
    tree_claims = referral_repo.get_all_tree_claims()

    if not tree_claims:
        st.info("No tree award claims submitted yet.")
    else:
        for tc in tree_claims:
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**Claim #{tc['id']}** by {tc.get('user_name')} ({tc.get('user_email')})")
                    st.caption(f"Status: **{tc['status'].upper()}** • Submitted: {tc['submitted_at'][:10]}")
                    st.write(f"Dedication: {tc.get('notes') or 'None'}")
                with c2:
                    if tc["status"] in ("submitted", "verified"):
                        action = st.selectbox(
                            f"Update Status #{tc['id']}",
                            ["verified", "fulfilled", "rejected"],
                            key=f"tc_status_{tc['id']}",
                        )
                        if st.button(f"Save Status #{tc['id']}", key=f"save_tc_{tc['id']}"):
                            ok, msg = tree_service.review_claim(tc["id"], action, admin_user["id"], "Reviewed by admin")
                            if ok:
                                st.success(msg)
                                st.rerun()

# 4. User Accounts
with tab_users:
    st.markdown("### 👥 User Account Management")
    users_list = user_repo.get_all_users()
    if users_list:
        df_users = pd.DataFrame([
            {
                "User ID": u["id"],
                "Name": u["name"],
                "Email": u["email"],
                "Display Name": u.get("display_name"),
                "Role": u["role"],
                "Green Score": u.get("green_score", 0),
                "Streak": f"{u.get('current_streak', 0)}d",
                "Status": "Active" if u["is_active"] else "Deactivated",
                "Joined": u["created_at"][:10],
            }
            for u in users_list
        ])
        st.dataframe(df_users, use_container_width=True, hide_index=True)

# 5. Create Challenge
with tab_new_ch:
    st.markdown("### 🎯 Publish New Eco-Challenge")
    with st.form("create_challenge_form"):
        title = st.text_input("Challenge Title", placeholder="e.g. Glass Recycling Drive")
        desc = st.text_area("Description", placeholder="Classify 4 glass items this week...")
        c_type = st.selectbox("Criteria Type", ["scan_count", "category_scan", "streak_days"])
        c_val = st.number_input("Target Goal Value", min_value=1, value=3)
        target_cat = st.selectbox("Target Category (if applicable)", ["None"] + list(config.categories))
        bonus = st.number_input("Bonus Green Points", min_value=5, value=25, step=5)

        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

        submitted = st.form_submit_button("Publish Challenge", type="primary")
        if submitted:
            start_iso = f"{start_date.isoformat()}T00:00:00+00:00"
            end_iso = f"{end_date.isoformat()}T23:59:59+00:00"
            chosen_cat = None if target_cat == "None" else target_cat

            res = challenge_service.create_challenge(
                title=title,
                description=desc,
                criteria_type=c_type,
                criteria_value=int(c_val),
                target_category=chosen_cat,
                bonus_points=int(bonus),
                start_at=start_iso,
                end_at=end_iso,
            )
            st.success(f"Challenge '{title}' created successfully! (ID: {res['id']})")

# 6. MySQL Server Sync
with tab_mysql:
    st.markdown("### 🔗 External MySQL / MariaDB Server Sync")
    st.caption("Link your external MySQL database to sync local SQLite scans, points, and user accounts.")

    from database.mysql_sync import MySQLSyncManager

    with st.expander("⚙️ MySQL Server Connection Settings", expanded=True):
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            my_host = st.text_input("MySQL Host", value=os.getenv("MYSQL_HOST", "localhost"))
            my_port = st.number_input("MySQL Port", value=int(os.getenv("MYSQL_PORT", "3306")), min_value=1, max_value=65535)
            my_db = st.text_input("Database Name", value=os.getenv("MYSQL_DATABASE", "smart_waste_db"))
        with m_col2:
            my_user = st.text_input("MySQL Username", value=os.getenv("MYSQL_USER", "root"))
            my_pwd = st.text_input("MySQL Password", value=os.getenv("MYSQL_PASSWORD", ""), type="password")
            my_ssl = st.checkbox("Enable SSL / TLS", value=os.getenv("MYSQL_SSL", "False").lower() in ("true", "1", "yes"))

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔌 Test MySQL Connection", use_container_width=True):
            mgr = MySQLSyncManager(host=my_host, port=my_port, user=my_user, password=my_pwd, database=my_db, ssl=my_ssl)
            with st.spinner("Connecting to MySQL server..."):
                t_res = mgr.test_connection()
            if t_res["success"]:
                st.success(f"✅ {t_res['message']}")
            else:
                st.error(f"❌ {t_res['message']}")

    with col_btn2:
        if st.button("🚀 Sync SQLite Data to MySQL", type="primary", use_container_width=True):
            mgr = MySQLSyncManager(host=my_host, port=my_port, user=my_user, password=my_pwd, database=my_db, ssl=my_ssl)
            with st.spinner("Initializing schema and synchronizing tables to MySQL..."):
                s_res = mgr.sync_from_sqlite()
            if s_res["success"]:
                st.success(f"✅ {s_res['message']}")
                if "summary" in s_res:
                    st.json(s_res["summary"])
            else:
                st.error(f"❌ {s_res['message']}")

