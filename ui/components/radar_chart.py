import streamlit as st
import plotly.graph_objects as go
from typing import List
from core.schemas.assessment import GapComparisonItem

def render_gap_charts(comparison_data: List[GapComparisonItem]):
    """
    Renders interactive Plotly charts contrasting Self-Reported vs. Demonstrated knowledge.
    """
    if not comparison_data:
        st.info("No assessment evidence available yet. Take the diagnostic test to see gap analysis.")
        return

    skills = [item.skill_name for item in comparison_data]
    self_reported = [item.self_reported * 100 for item in comparison_data]
    demonstrated = [item.demonstrated * 100 for item in comparison_data]
    targets = [item.target * 100 for item in comparison_data]

    # 1. Grouped Bar Comparison Chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Self-Reported Claim',
        x=skills,
        y=self_reported,
        marker_color='#6366f1',
        opacity=0.85
    ))

    fig.add_trace(go.Bar(
        name='Demonstrated Score (Evidence)',
        x=skills,
        y=demonstrated,
        marker_color='#06b6d4',
        opacity=0.9
    ))

    fig.add_trace(go.Scatter(
        name='Target Goal Requirement',
        x=skills,
        y=targets,
        mode='lines+markers',
        line=dict(color='#ef4444', width=2, dash='dot'),
        marker=dict(size=8, symbol='diamond')
    ))

    fig.update_layout(
        title="<b>Claimed vs. Demonstrated Knowledge vs. Goal Target</b>",
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', family='Plus Jakarta Sans'),
        yaxis=dict(title='Proficiency (%)', range=[0, 105], gridcolor='rgba(255,255,255,0.08)'),
        xaxis=dict(tickangle=-25),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=80),
        height=420
    )

    st.plotly_chart(fig, use_container_width=True)
