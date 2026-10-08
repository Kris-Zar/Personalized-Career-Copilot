import streamlit as st
from core.storage.store import InMemoryStore
from ui.components.roadmap_view import render_roadmap_view

def render_roadmap_tab_view(store: InMemoryStore):
    st.caption("Step 5: Inspect your milestone-driven learning roadmap, sequenced to resolve prerequisites and match your available weekly hours.")

    if not store.roadmaps:
        st.info("No roadmap generated yet. Complete the assessment or click below to generate your initial plan.")
        if st.button("Generate Initial Roadmap v1"):
            st.session_state["active_tab"] = "📝 3. Assessment"
            st.rerun()
        return

    render_roadmap_view(
        roadmaps=store.roadmaps,
        current_version=store.current_roadmap_version
    )

    st.divider()
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("💬 Open AI Tutor to Ask About This Roadmap", use_container_width=True):
            st.session_state["active_tab"] = "📊 6. Master Dashboard & Tutor"
            st.rerun()
    with btn_col2:
        if st.button("🎯 Proceed to Master Dashboard", type="primary", use_container_width=True):
            st.session_state["active_tab"] = "📊 6. Master Dashboard & Tutor"
            st.rerun()
