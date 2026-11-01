"""
Environmental Impact & Eco-Advocacy Note Component.
Provides in-depth descriptions of the harmfulness of neglected waste,
how proper segregation minimizes environmental damage, and generates a
bite-sized talking point the user can share with friends and family.
"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict


def render_environmental_impact_section(
    category: str,
    sub_category: str,
    recommendation: Dict[str, Any],
) -> None:
    """
    Renders an educational card detailing:
    1. Decomposition timeline in landfills.
    2. Environmental hazards if neglected, littered, or trashed.
    3. Concrete positive conservation benefits of proper sorting.
    4. A concise, shareable quote the user can tell other people.
    """
    decomp_time = recommendation.get("decomposition_time", "Varies by material")
    hazard = recommendation.get("hazard_if_neglected", "Accumulates in landfills and depletes raw natural resources.")
    benefits = recommendation.get("how_sorting_protects", "Recovers valuable secondary raw materials and reduces industrial pollution.")
    share_note = recommendation.get("shareable_advocacy_note", f"“Properly sorting {category} keeps our community clean and conserves energy!”")

    cat_colors = {
        "Plastic": ("#0284C7", "#E0F2FE", "🧴"),
        "Glass": ("#0D9488", "#CCFBF1", "🍾"),
        "Paper": ("#16A34A", "#DCFCE7", "📄"),
        "Metal": ("#D97706", "#FEF3C7", "🥫"),
        "Organic": ("#059669", "#ECFDF5", "🍎"),
    }
    primary_color, bg_light, cat_icon = cat_colors.get(category, ("#059669", "#ECFDF5", "♻️"))

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.5rem;">🌍</span>
                    <span style="font-size: 1.2rem; font-weight: 800; color: #0F172A;">Environmental Impact & Why Sorting Matters</span>
                </div>
                <span style="background: {bg_light}; color: {primary_color}; font-size: 0.75rem; font-weight: 800; padding: 4px 10px; border-radius: 9999px;">
                    {category} Awareness
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── 1. Key Metrics Strip ─────────────────────────────────────────────
        c_m1, c_m2 = st.columns([1, 1.8])
        with c_m1:
            st.markdown(
                f"""
                <div style="background: #FFF1F2; border: 1px solid #FECDD3; border-radius: 12px; padding: 12px; text-align: center; height: 100%;">
                    <div style="font-size: 0.75rem; font-weight: 800; color: #E11D48; text-transform: uppercase;">⏳ Landfill Lifespan</div>
                    <div style="font-size: 1.25rem; font-weight: 900; color: #9F1239; margin-top: 4px;">{decomp_time}</div>
                    <div style="font-size: 0.75rem; color: #BE123C; margin-top: 2px;">if thrown in regular trash</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_m2:
            st.markdown(
                f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 12px; height: 100%;">
                    <div style="font-size: 0.75rem; font-weight: 800; color: #059669; text-transform: uppercase;">🌱 Conservation Impact</div>
                    <div style="font-size: 0.85rem; color: #064E3B; font-weight: 600; margin-top: 4px; line-height: 1.4;">
                        {benefits}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 2. Harmfulness if neglected vs how sorting protects ──────────────
        h_col1, h_col2 = st.columns(2)

        with h_col1:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #F1F5F9; border-left: 4px solid #E11D48; border-radius: 8px; padding: 10px 14px; height: 100%;">
                    <strong style="color: #BE123C; font-size: 0.9rem;">⚠️ The Threat If Neglected / Littered:</strong>
                    <p style="font-size: 0.85rem; color: #475569; margin: 6px 0 0 0; line-height: 1.45;">
                        {hazard}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with h_col2:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #F1F5F9; border-left: 4px solid #10B981; border-radius: 8px; padding: 10px 14px; height: 100%;">
                    <strong style="color: #047857; font-size: 0.9rem;">🛡️ How Segregation Protects The Planet:</strong>
                    <p style="font-size: 0.85rem; color: #475569; margin: 6px 0 0 0; line-height: 1.45;">
                        Proper segregation guarantees this item is directed to appropriate remelting, pulping, or composting plants, cutting raw mining and factory emissions.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 3. Shareable Talking Point / Advocacy Note ───────────────────────
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FFFBEB 100%); border: 2px dashed #F59E0B; border-radius: 12px; padding: 14px 16px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-size: 0.8rem; font-weight: 800; color: #B45309; text-transform: uppercase; letter-spacing: 0.05em;">
                        🗣️ Tell Your Friends / Eco Talking Point
                    </span>
                    <span style="font-size: 0.72rem; color: #92400E; font-weight: 600;">Share this reason</span>
                </div>
                <div style="font-size: 0.95rem; font-style: italic; color: #78350F; font-weight: 600; line-height: 1.45;">
                    {share_note}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
