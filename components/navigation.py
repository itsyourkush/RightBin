"""
Navigation and Session State Management Component.
Provides user authentication state, sidebar status, login/register forms,
and server-side authorization guards.
"""

from __future__ import annotations

import streamlit as st
from typing import Optional, Dict, Any

from config import config
from services.auth_service import AuthService


def get_auth_service() -> AuthService:
    """Returns an AuthService instance."""
    return AuthService()


import base64
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def get_app_icon_base64() -> str:
    """Returns base64 string of the custom modern app icon."""
    icon_file = Path(__file__).resolve().parent.parent / "assets" / "app_icon.png"
    if icon_file.exists():
        try:
            return base64.b64encode(icon_file.read_bytes()).decode("utf-8")
        except Exception:
            pass
    return ""

def apply_custom_css() -> None:
    """Injects global CSS styles and animations across all Streamlit pages."""
    css_path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def init_session_state() -> None:
    """Initializes standard session state keys if not already set."""
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "flash_message" not in st.session_state:
        st.session_state["flash_message"] = None


def render_sidebar() -> Optional[Dict[str, Any]]:
    """
    Renders sidebar brand, navigation helper, and user account status.
    Returns the current authenticated user dictionary or None.
    """
    apply_custom_css()
    init_session_state()
    auth_service = get_auth_service()
    user = st.session_state.get("user")

    icon_b64 = get_app_icon_base64()
    icon_markup = (
        f'<img src="data:image/png;base64,{icon_b64}" class="sidebar-brand-icon-img" alt="Smart Waste Icon" />'
        if icon_b64
        else '<span style="font-size: 1.4rem;">🌐</span>'
    )

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-brand-box">
                <div class="sidebar-brand-icon-wrapper">
                    {icon_markup}
                </div>
                <div>
                    <div style="font-size: 1.35rem; font-weight: 800; background: linear-gradient(135deg, #10B981, #059669); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.02em; line-height: 1.2;">RightBin</div>
                    <div style="font-size: 0.74rem; color: #64748B; font-weight: 600; margin-top: 2px;">"Wet or Dry, Always Right."</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        if user:
            # Authenticated user view with colorful avatar
            role_badge = "👑 Admin" if user.get("role") == "admin" else "🌱 Eco Member"
            display_name = user.get('display_name') or user.get('name') or "Eco Recycler"
            initial = display_name[0].upper()

            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #F0FDF4, #DCFCE7); border: 1px solid #BBF7D0; border-radius: 12px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; gap: 12px;">
                    <div style="width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, #10B981, #059669); color: white; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);">
                        {initial}
                    </div>
                    <div style="overflow: hidden;">
                        <div style="font-weight: 700; color: #064E3B; font-size: 0.95rem; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{display_name}</div>
                        <div style="font-size: 0.75rem; color: #047857; font-weight: 600;">{role_badge}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("🚪 Log Out", use_container_width=True, key="sidebar_logout_btn"):
                st.session_state["user"] = None
                st.session_state["flash_message"] = ("info", "You have been logged out.")
                st.rerun()

            st.divider()
        else:
            # Guest / Login options
            st.info("👋 Log in to save scans, earn Green Points, and unlock gaming vouchers.")
            with st.expander("🔐 Quick Login", expanded=False):
                with st.form("sidebar_login_form"):
                    email = st.text_input("Email", placeholder="you@university.edu").strip()
                    password = st.text_input("Password", type="password")
                    submit = st.form_submit_button("Sign In", use_container_width=True)
                    if submit:
                        ok, msg, profile = auth_service.authenticate(email, password)
                        if ok:
                            st.session_state["user"] = profile
                            st.success("Signed in successfully!")
                            st.rerun()
                        else:
                            st.error(msg)

            st.divider()

        # Helpful quick links & viva details
        with st.expander("ℹ️ About System", expanded=False):
            st.markdown(
                """
                **Architecture:**
                - Model: Keras CNN (5 classes)
                - Database: SQLite (Atomic Ledger)
                - Preprocessing: 180x180 RGB Normalized
                - Model Version: `v1.0.0-cnn`
                """
            )

    return user


def require_auth() -> Optional[Dict[str, Any]]:
    """
    Halts execution and prompts for login if user is not authenticated.
    Used on protected pages (Scan Waste, Dashboard, Profile, etc.).
    """
    init_session_state()
    user = st.session_state.get("user")
    if not user:
        st.warning("🔒 **Authentication Required** — Please sign in or create an account to access this page.")
        tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])
        auth_svc = get_auth_service()

        with tab_login:
            with st.form("page_require_login_form"):
                email = st.text_input("Email Address", key="req_login_email")
                password = st.text_input("Password", type="password", key="req_login_pwd")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                if submitted:
                    ok, msg, profile = auth_svc.authenticate(email, password)
                    if ok:
                        st.session_state["user"] = profile
                        st.success("Signed in successfully!")
                        st.rerun()
                    else:
                        st.error(msg)

        with tab_register:
            with st.form("page_require_register_form"):
                name = st.text_input("Full Name", placeholder="e.g. Alex Rivera")
                reg_email = st.text_input("Email Address", placeholder="alex@university.edu")
                reg_pwd = st.text_input("Password (min 8 chars)", type="password")
                disp_name = st.text_input("Display Name (optional)", placeholder="EcoAlex")
                ref_code = st.text_input("Referral Code (optional)", placeholder="ECO-USER0001")
                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)
                if reg_submitted:
                    ok, msg, new_user = auth_svc.register_user(name, reg_email, reg_pwd, disp_name, ref_code)
                    if ok:
                        st.success(msg)
                        # Auto-login
                        _, _, profile = auth_svc.authenticate(reg_email, reg_pwd)
                        st.session_state["user"] = profile
                        st.rerun()
                    else:
                        st.error(msg)

        st.stop()
    return user


def require_admin() -> Dict[str, Any]:
    """Guards admin pages against regular user or unauthenticated access."""
    user = require_auth()
    if not AuthService.is_admin(user):
        st.error("⛔ **Access Denied**: Administrator privileges are required to view this page.")
        st.stop()
    return user
