import streamlit as st
import json
import os
from core.storage.store import InMemoryStore
from core.services.llm_service import LLMService
from core.services.graph_service import GraphService
from core.schemas.feedback import GoalState

def render_goal_discovery_view(
    store: InMemoryStore,
    llm_service: LLMService,
    graph_service: GraphService
):
    st.subheader("🎯 Conversational Goal Discovery & Intake")
    st.caption("Step 2 of 6: State your target career role, timeline, and weekly hours in plain English. The AI engine extracts structured parameters and activates the matching competency DAG.")

    col1, col2 = st.columns([3, 2])

    with col1:
        user_prompt = st.text_area(
            "State your career learning objective:",
            value=st.session_state.get("user_goal_input", "I am currently a full-stack developer and I want to become an industry-ready Data Scientist within 6 months. I can commit around 8 hours per week and prefer hands-on projects."),
            height=110
        )

        if st.button("🤖 Extract Structured Goal & Activate Track", type="primary", use_container_width=True):
            with st.spinner("Extracting structured fields with LLM engine..."):
                extracted = llm_service.extract_goal_and_constraints(user_prompt)
                st.session_state["extracted_goal"] = extracted
                
                # Auto-match with available goals in catalog
                target = extracted.get("target_role", "").lower()
                goals_path = "data/goals/goals.json"
                matched_goal = None
                if os.path.exists(goals_path):
                    with open(goals_path, "r", encoding="utf-8") as f:
                        goals_data = json.load(f)
                        for g in goals_data:
                            if g["target_role"].lower() in target or target in g["target_role"].lower():
                                matched_goal = g
                                break
                        if not matched_goal and goals_data:
                            matched_goal = goals_data[0]

                if matched_goal:
                    store.goal_state = GoalState(
                        goal_id=matched_goal["goal_id"],
                        target_role=matched_goal["target_role"],
                        timeline_months=extracted.get("timeline_months", matched_goal["recommended_timeline_months"]),
                        weekly_hours=extracted.get("weekly_hours", matched_goal["recommended_weekly_hours"]),
                        target_proficiency_by_skill=matched_goal["target_proficiency_by_skill"],
                        active=True
                    )
                    st.toast(f"Activated {matched_goal['target_role']} Track!", icon="🎯")

    with col2:
        st.markdown("#### 📋 Validated Structured Extraction")
        extracted = st.session_state.get("extracted_goal", {
            "target_role": store.goal_state.target_role if store.goal_state else "Data Scientist",
            "timeline_months": store.goal_state.timeline_months if store.goal_state else 6,
            "weekly_hours": store.goal_state.weekly_hours if store.goal_state else 8.0,
            "interests": ["Data Analysis", "Statistics", "ML Modeling"]
        })

        st.json(extracted)

    st.divider()
    st.markdown("#### 🚀 Available Career Tracks")

    goals_data = []
    goals_path = "data/goals/goals.json"
    if os.path.exists(goals_path):
        with open(goals_path, "r", encoding="utf-8") as f:
            goals_data = json.load(f)

    goal_cols = st.columns(len(goals_data) if goals_data else 1)

    for idx, g in enumerate(goals_data):
        with goal_cols[idx]:
            is_active = (store.goal_state and store.goal_state.goal_id == g["goal_id"])
            st.markdown(
                f"""
                <div class="glass-card" style="border: 2px solid {'#EF6351' if is_active else 'rgba(255,255,255,0.08)'};">
                    <h4 style="color: {'#EF6351' if is_active else '#FFFFFF'};">{g['title']}</h4>
                    <p style="font-size: 0.85rem; color: var(--text-secondary);">{g['description']}</p>
                    <div style="font-size: 0.8rem; color: var(--c-tangerine); font-weight: 600;">
                        ⏱️ Est. Timeline: {g['recommended_timeline_months']} months • ⚡ {g['recommended_weekly_hours']}h/wk
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"{'✓ Active: ' if is_active else 'Select '} {g['target_role']}", key=f"btn_goal_{g['goal_id']}", use_container_width=True):
                store.goal_state = GoalState(
                    goal_id=g["goal_id"],
                    target_role=g["target_role"],
                    timeline_months=g["recommended_timeline_months"],
                    weekly_hours=g["recommended_weekly_hours"],
                    target_proficiency_by_skill=g["target_proficiency_by_skill"],
                    active=True
                )
                st.success(f"✅ Activated career goal: {g['target_role']}! Proceed to Diagnostic Assessment.")
                st.session_state["active_tab"] = "📝 3. Assessment"
                st.rerun()

    if store.goal_state and store.goal_state.active:
        st.markdown(
            f"""
            <div class="checkpoint-card" style="margin-top: 20px;">
                <div class="checkpoint-title">🎯 Goal Checkpoint Active: {store.goal_state.target_role}</div>
                <div style="font-size: 0.88rem;">
                    <b>Target Role:</b> {store.goal_state.target_role} • <b>Timeline:</b> {store.goal_state.timeline_months} months • <b>Pace:</b> {store.goal_state.weekly_hours} hrs/week
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("📝 Proceed to Diagnostic Assessment (Step 3) ➔", type="primary", use_container_width=True):
            st.session_state["active_tab"] = "📝 3. Assessment"
            st.rerun()
