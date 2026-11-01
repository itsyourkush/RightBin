"""
Reward Cards UI Component.
Presents the reward catalogue with gaming vouchers, Clash of Clans codes,
Google Play cards, puzzle boosters, eligibility status, and handles redemption interactions
with modern vibrant visual cards and animations.
"""

from __future__ import annotations

import streamlit as st
from typing import Any, Callable, Dict, List, Optional


def _get_reward_icon(name: str) -> str:
    """Returns a matching icon for the reward item."""
    n = name.lower()
    if "clash" in n or "gems" in n:
        return "⚔️"
    if "google play" in n:
        return "🕹️"
    if "puzzle" in n or "booster" in n:
        return "🧩"
    if "bgmi" in n or "pubg" in n or "uc" in n:
        return "🎯"
    if "roblox" in n or "robux" in n:
        return "💎"
    if "steam" in n:
        return "🎮"
    if "tree" in n:
        return "🌳"
    if "bottle" in n:
        return "🍶"
    if "tote" in n or "bag" in n:
        return "🛍️"
    if "bamboo" in n:
        return "🎋"
    return "🎁"


def render_reward_catalogue(
    rewards: List[Dict[str, Any]],
    user_balance: int,
    on_redeem_callback: Optional[Callable[[int], None]] = None,
) -> None:
    """Renders the grid of rewards with vibrant cards and interactive redemption triggers."""
    if not rewards:
        st.info("No rewards currently listed in the catalogue.")
        return

    cols = st.columns(2)
    for idx, r in enumerate(rewards):
        col = cols[idx % 2]
        with col:
            r_id = r["id"]
            name = r["name"]
            desc = r["description"]
            cost = r["required_points"]
            stock = r.get("stock_quantity")
            r_type = r.get("reward_type", "voucher").capitalize()
            is_eligible = r.get("is_eligible", False)
            has_pending = r.get("has_pending_request", False)
            in_stock = r.get("in_stock", True)

            # Gaming badge detection
            is_gaming = any(
                k in name.lower()
                for k in ("clash", "google play", "puzzle", "bgmi", "pubg", "roblox", "steam", "gems")
            ) or r_type == "Digital"

            reward_icon = _get_reward_icon(name)

            if is_gaming:
                border_color = "#FFD7AA"
                tag_bg = "linear-gradient(135deg, #FF6B00, #FF2A6D)"
                tag_label = "🎮 INSTANT GAMING CODE"
                card_class = "gaming-voucher-card"
            else:
                border_color = "#BBF7D0"
                tag_bg = "linear-gradient(135deg, #10B981, #059669)"
                tag_label = "🌱 ECO REWARD"
                card_class = "category-card cat-paper"

            st.markdown(
                f"""
                <div class="{card_class}" style="margin-bottom: 12px; text-align: left;">
                    <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 8px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 2.2rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">{reward_icon}</span>
                            <div>
                                <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; line-height: 1.2;">{name}</div>
                                <div style="font-size: 0.75rem; color: #64748B; margin-top: 2px;">
                                    {"⚡ Instant Digital Delivery" if is_gaming else "📦 Physical Eco Merch"}
                                </div>
                            </div>
                        </div>
                        <span style="background: {tag_bg}; color: #FFFFFF; font-size: 0.65rem; font-weight: 800; padding: 4px 8px; border-radius: 9999px; letter-spacing: 0.05em; white-space: nowrap;">
                            {tag_label}
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; margin: 10px 0 12px 0; line-height: 1.4;">
                        {desc}
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 8px; border-top: 1px dashed {border_color}; margin-bottom: 8px;">
                        <span style="font-size: 0.85rem; font-weight: 700; color: #064E3B;">
                            Required: <strong style="color: {'#C2410C' if is_gaming else '#059669'}; font-size: 1.1rem;">{cost:,}</strong> pts
                        </span>
                        <span style="font-size: 0.75rem; color: #64748B;">
                            {"📦 Unlimited Stock" if stock is None else f"📦 {stock} left"}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Action button
            if has_pending:
                st.info("⏳ **Pending Fulfillment**: Request under review by admin.", icon="ℹ️")
            elif not in_stock:
                st.button("Sold Out", disabled=True, key=f"btn_sold_out_{r_id}", use_container_width=True)
            elif is_eligible:
                if st.button(
                    f"✨ Redeem Voucher ({cost:,} pts)",
                    key=f"btn_redeem_{r_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    if on_redeem_callback:
                        on_redeem_callback(r_id)
            else:
                short = r.get("points_short", cost - user_balance)
                st.button(
                    f"🔒 Locked ({short:,} more points needed)",
                    disabled=True,
                    key=f"btn_locked_{r_id}",
                    use_container_width=True,
                )
