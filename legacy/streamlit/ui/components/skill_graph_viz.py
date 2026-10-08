import streamlit as st
from typing import Dict, Any, Optional
from core.services.graph_service import GraphService

def render_skill_graph(graph_service: GraphService, goal_id: str, knowledge_states: Optional[Dict[str, Any]] = None):
    """
    Renders an interactive DAG visualization showing competencies,
    prerequisites, and color-coded mastery statuses.
    """
    st.markdown("### 🗺️ Competency & Prerequisite Graph")
    st.caption("Visual DAG showing dependency chains and diagnostic assessment evidence.")

    # Legend
    st.markdown(
        """
        <div style="display: flex; gap: 12px; margin-bottom: 12px; font-size: 0.8rem;">
            <span class="badge badge-adequate">● Demonstrated Adequate (>= Target)</span>
            <span class="badge badge-warning">● Needs Improvement</span>
            <span class="badge badge-bottleneck">● Weak Prerequisite Bottleneck</span>
            <span style="color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 999px;">○ Not Assessed</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    dot_code = graph_service.generate_dot_graph(goal_id, knowledge_states)
    st.graphviz_chart(dot_code, use_container_width=True)
