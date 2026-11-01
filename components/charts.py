"""
Charts and Data Visualizations Component.
Uses Plotly to render interactive category distribution and scan activity charts.
"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render_category_donut_chart(category_distribution: Dict[str, int]) -> None:
    """Renders an interactive Donut chart showing classified waste categories."""
    df = pd.DataFrame([
        {"Category": cat, "Count": count}
        for cat, count in category_distribution.items()
        if count > 0
    ])

    if df.empty or df["Count"].sum() == 0:
        st.info("ℹ️ No accepted scans logged yet. Start scanning to view your category breakdown!")
        return

    # Eco-aligned category color palette
    color_map = {
        "Plastic": "#0284C7",
        "Paper": "#16A34A",
        "Organic": "#D97706",
        "Metal": "#9333EA",
        "Glass": "#0D9488",
    }

    fig = px.pie(
        df,
        values="Count",
        names="Category",
        hole=0.55,
        color="Category",
        color_discrete_map=color_map,
        title="Waste Classification Breakdown",
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hoverinfo="label+value+percent",
        marker=dict(line=dict(color="#FFFFFF", width=2)),
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_weekly_activity_chart(weekly_data: List[Dict[str, Any]]) -> None:
    """Renders a Bar chart showing daily scans over the past 7 days."""
    if not weekly_data:
        st.info("No activity recorded this week.")
        return

    df = pd.DataFrame(weekly_data)
    fig = px.bar(
        df,
        x="day",
        y="scans",
        title="Daily Scans (Past 7 Days)",
        labels={"day": "Day", "scans": "Verified Scans"},
        color_discrete_sequence=["#10B981"],
    )
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Scans Completed",
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
        yaxis=dict(dtick=1),
    )
    fig.update_traces(
        marker=dict(line=dict(color="#047857", width=1.5), opacity=0.85)
    )
    st.plotly_chart(fig, use_container_width=True)


def render_model_confidence_gauge(confidence: float, threshold: float = 0.60) -> None:
    """Renders a gauge chart illustrating prediction confidence vs threshold."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence * 100,
        title={'text': "Model Confidence", 'font': {'size': 18}},
        number={'suffix': "%"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': "#10B981" if confidence >= threshold else "#F59E0B"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#E5E7EB",
            'steps': [
                {'range': [0, threshold * 100], 'color': '#FEE2E2'},
                {'range': [threshold * 100, 100], 'color': '#DCFCE7'},
            ],
            'threshold': {
                'line': {'color': "#EF4444", 'width': 3},
                'thickness': 0.75,
                'value': threshold * 100,
            }
        }
    ))
    fig.update_layout(height=240, margin=dict(l=20, r=20, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)
