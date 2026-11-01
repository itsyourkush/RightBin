"""
Dustbin Wayfinding and Disposal Direction Component.
Provides visual mapping showing users exactly which color and type of dustbin
to throw their scanned waste item into, complete with drop-path wayfinding.
"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict


# Municipal station dustbin definitions
STANDARD_DUSTBINS = [
    {
        "id": "blue_bin",
        "name": "BLUE DUSTBIN",
        "label": "Dry Recyclables",
        "color": "#1E88E5",
        "bg_light": "#E3F2FD",
        "icon": "🔵",
        "accepted_items": "Plastics (PET, HDPE, PP), Paper, Cardboard boxes, Clean cartons",
        "matched_categories": ["Plastic", "Paper"],
    },
    {
        "id": "green_bin",
        "name": "GREEN DUSTBIN",
        "label": "Wet & Organic Waste",
        "color": "#2E7D32",
        "bg_light": "#E8F5E9",
        "icon": "🟢",
        "accepted_items": "Fruit peels, food scraps, coffee grounds, garden waste, bakery leftovers",
        "matched_categories": ["Organic"],
    },
    {
        "id": "yellow_bin",
        "name": "YELLOW DUSTBIN",
        "label": "Metals & Glass Containers",
        "color": "#F57C00",
        "bg_light": "#FFF3E0",
        "icon": "🟡",
        "accepted_items": "Aluminum beverage cans, tin food cans, glass jars & bottles",
        "matched_categories": ["Metal", "Glass"],
    },
    {
        "id": "black_bin",
        "name": "BLACK DUSTBIN",
        "label": "General Refuse / Landfill",
        "color": "#424242",
        "bg_light": "#EEEEEE",
        "icon": "⚫",
        "accepted_items": "Greasy soiled paper, sanitary waste, broken ceramic, non-recyclable multi-films",
        "matched_categories": [],
    },
]


def render_dustbin_wayfinding(
    category: str,
    sub_category: str,
    recommendation: Dict[str, Any],
) -> None:
    """
    Renders an interactive, visual dustbin wayfinding guide:
    1. Shows a direct graphic arrow: [Item] -> [Target Dustbin]
    2. Highlights the exact matching dustbin among all station bins
    3. Step-by-step action guide for dropping the item into the bin
    """
    # Find matching target bin
    target_bin = next(
        (b for b in STANDARD_DUSTBINS if category in b["matched_categories"]),
        STANDARD_DUSTBINS[0],
    )

    bin_name = target_bin["name"]
    bin_color = target_bin["color"]
    bin_icon = target_bin["icon"]
    bin_label = target_bin["label"]

    st.markdown("""
    <style>
    .wayfinding-hero {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
        border: 2px solid #3B82F6;
        border-radius: 14px;
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
    }
    .arrow-flow {
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        color: #2563EB;
        font-weight: bold;
    }
    .bin-choice-card {
        border-radius: 12px;
        padding: 0.85rem;
        text-align: center;
        transition: transform 0.2s ease;
        height: 100%;
    }
    .bin-selected {
        border: 3px solid #2E7D32 !important;
        background: #F0FDF4 !important;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.3) !important;
        transform: scale(1.03);
    }
    .bin-dimmed {
        opacity: 0.55;
        border: 1px solid #CBD5E1;
        background: #F8FAFC;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"### 🎯 Step-by-Step Wayfinding to Dustbin")
        st.caption(f"Follow this path to safely segregate **{sub_category}** at the disposal station:")

        # ── 1. The Path: Scanned Item -> Throw Direction -> Target Bin ──────
        col_item, col_arrow, col_target = st.columns([1.2, 0.6, 1.4])

        with col_item:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 2px dashed #94A3B8; border-radius: 10px; padding: 1rem; text-align: center;">
                    <div style="font-size: 2rem;">📸</div>
                    <strong style="color: #1E293B;">Scanned Item:</strong><br>
                    <span style="font-size: 1.05rem; font-weight: bold; color: #2563EB;">{sub_category}</span><br>
                    <small style="color: #64748B;">Category: {category}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_arrow:
            st.markdown(
                """
                <div class="arrow-flow" style="padding-top: 2rem; text-align: center;">
                    ════▶<br>
                    <span style="font-size: 0.8rem; text-transform: uppercase;">THROW INTO</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_target:
            st.markdown(
                f"""
                <div style="background: {target_bin['bg_light']}; border: 3px solid {bin_color}; border-radius: 10px; padding: 1rem; text-align: center;">
                    <div style="font-size: 2.2rem;">{bin_icon} 🗑️</div>
                    <strong style="color: {bin_color}; font-size: 1.15rem;">{bin_name}</strong><br>
                    <span style="color: #1E293B; font-weight: 600;">{bin_label}</span><br>
                    <span style="background: {bin_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold;">
                        ✓ TARGET BIN
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 2. Station Bin Comparison: Which Bin at the Station? ────────────
        st.markdown("#### 🏢 Disposal Station Bins Layout")
        st.caption("Look at the physical dustbins in front of you and match the highlighted color:")

        cols_bins = st.columns(4)
        for idx, b in enumerate(STANDARD_DUSTBINS):
            with cols_bins[idx]:
                is_target = (b["id"] == target_bin["id"])
                border_style = f"3px solid {b['color']}" if is_target else "1px solid #E2E8F0"
                bg_style = b["bg_light"] if is_target else "#FAFAFA"
                badge = f"<div style='background: {b['color']}; color: white; border-radius: 6px; font-size: 0.75rem; font-weight: bold; margin-top: 4px; padding: 2px 4px;'>🎯 THROW HERE</div>" if is_target else "<div style='color: #94A3B8; font-size: 0.75rem; margin-top: 4px;'>—</div>"

                st.markdown(
                    f"""
                    <div style="border: {border_style}; background: {bg_style}; border-radius: 10px; padding: 0.75rem; text-align: center; min-height: 140px;">
                        <div style="font-size: 1.8rem;">{b['icon']} 🗑️</div>
                        <strong style="color: {b['color']}; font-size: 0.85rem;">{b['name']}</strong><br>
                        <small style="color: #475569; font-weight: 500;">{b['label']}</small>
                        {badge}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # ── 3. Quick 3-Step Drop Protocol ────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 📋 3-Step Waste Segregation Action:")
        step1 = recommendation.get("preparation_steps", ["Empty residual contents."])[0]
        st.markdown(
            f"1. **Prepare Item**: {step1}\n"
            f"2. **Navigate**: Walk to the **{bin_name}** ({bin_label}).\n"
            f"3. **Drop Waste**: Deposit the item inside. Do not mix with non-recyclable bags!"
        )
