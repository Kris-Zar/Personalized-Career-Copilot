import streamlit as st
from core.storage.store import InMemoryStore
from core.services.graph_service import GraphService
from core.services.llm_service import LLMService
from core.services.adaptation_engine import AdaptationEngine
from ui.components.skill_graph_viz import render_skill_graph
from ui.components.chat_drawer import render_chat_assistant
from ui.components.roadmap_view import render_roadmap_view

def render_dashboard_view(
    store: InMemoryStore,
    graph_service: GraphService,
    llm_service: LLMService,
    adaptation_engine: AdaptationEngine
):
    # 1. Dynamic Greeting & Goal
    learner_name = store.profile.name if (store.profile and store.profile.name) else "Learner"
    target_role = store.goal_state.target_role if store.goal_state else "Career Goal Not Activated"
    timeline_str = f"{store.goal_state.timeline_months}-Month Track" if store.goal_state else "Explore Pathways"

    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h2 style="font-family: 'Space Grotesk', sans-serif; font-weight: 800; font-size: 24px; margin: 0 0 4px 0;">Welcome back, {learner_name}</h2>
            <div style="font-size: 13px; color: var(--text-secondary);">Goal: {target_role} · {timeline_str}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Dynamic Metric Calculations
    current_roadmap = store.get_current_roadmap()
    if current_roadmap and current_roadmap.stages:
        completed_stages = sum(1 for s in current_roadmap.stages if s.completion_status == "completed" or (s.milestone and s.milestone.completed))
        progress_pct = int((completed_stages / len(current_roadmap.stages)) * 100)
    else:
        progress_pct = 0

    skills_assessed_count = len(set(att.skill_id for att in store.assessment_attempts)) if store.assessment_attempts else 0
    weak_prereq_count = len(store.gap_report.unresolved_prerequisites) if store.gap_report else 0

    st.markdown(
        f"""
        <div class="pf-metrics-grid">
            <div class="pf-metric">
                <div class="pf-metric-label">Roadmap progress</div>
                <div class="pf-metric-val">{progress_pct}%</div>
            </div>
            <div class="pf-metric success">
                <div class="pf-metric-label">Skills assessed</div>
                <div class="pf-metric-val" style="color: var(--c-jade);">{skills_assessed_count}</div>
            </div>
            <div class="pf-metric urgent">
                <div class="pf-metric-label">Weak prerequisites</div>
                <div class="pf-metric-val" style="color: var(--c-coral);">{weak_prereq_count}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. Dynamic Demonstrated vs Target Competency Panel
    skill_rows_html = []
    if store.knowledge_states:
        for ks in store.knowledge_states.values():
            pct = int(ks.demonstrated_score * 100)
            if ks.status == "adequate":
                bar_color = "var(--c-jade)"
                text_color = "var(--c-jade)"
                status_label = "strong"
            elif ks.status == "needs_improvement":
                bar_color = "var(--c-cerulean)"
                text_color = "var(--c-cerulean)"
                status_label = "building"
            elif ks.status == "weak":
                bar_color = "var(--c-coral)"
                text_color = "var(--c-coral)"
                status_label = "weak"
            else:
                bar_color = "rgba(255,255,255,0.2)"
                text_color = "var(--text-muted)"
                status_label = "unassessed"

            skill_rows_html.append(
                f"""
                <div class="skill-row">
                    <span class="skill-name">{ks.skill_name}</span>
                    <div class="skill-track"><div class="skill-fill" style="width: {max(5, pct)}%; background: {bar_color};"></div></div>
                    <span class="skill-pct" style="color: {text_color};">{pct}% · {status_label}</span>
                </div>
                """
            )
    else:
        skill_rows_html.append(
            """
            <div style="font-size: 13px; color: var(--text-muted); padding: 8px 0;">
                No demonstrated test evidence yet. Complete <b>Step 3 (Assessment)</b> to calibrate your competency baseline.
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="pf-panel">
            <div class="pf-panel-title">
                <span>Demonstrated Competency Baseline</span>
                <span class="pf-panel-tag">Evidence-Based</span>
            </div>
            {"".join(skill_rows_html)}
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Dynamic Badges Earned Panel
    badge_spans = []
    if store.knowledge_states:
        unresolved_set = set(store.gap_report.unresolved_prerequisites) if store.gap_report else set()
        for ks in store.knowledge_states.values():
            if ks.skill_id in unresolved_set:
                badge_spans.append(f'<span class="badge badge-bottleneck">🔒 {ks.skill_name} · Bottleneck</span>')
            elif ks.status == "adequate":
                badge_spans.append(f'<span class="badge badge-jade">✓ {ks.skill_name} · Mastered</span>')
            elif ks.status == "needs_improvement":
                badge_spans.append(f'<span class="badge badge-tangerine">● {ks.skill_name} · In Progress</span>')

    if not badge_spans:
        badge_content = '<span style="font-size: 12px; color: var(--text-muted);">No milestone badges unlocked yet. Complete diagnostic assessment to calibrate.</span>'
    else:
        badge_content = "".join(badge_spans)

    st.markdown(
        f"""
        <div class="pf-panel">
            <div class="pf-panel-title">Badges &amp; Status</div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                {badge_content}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 5. Two-Column Layout: Left = Roadmap & DAG, Right = AI Tutor & Adaptation
    col_left, col_right = st.columns([3, 2])

    with col_left:
        dash_tabs = st.tabs(["🗺️ Active Roadmap", "📊 Live Competency DAG", "📋 Adaptation History"])

        with dash_tabs[0]:
            if store.roadmaps:
                render_roadmap_view(
                    roadmaps=store.roadmaps,
                    current_version=store.current_roadmap_version
                )
            else:
                st.info("No roadmap generated yet. Complete Step 3 (Assessment) to generate your personalized learning path.")

        with dash_tabs[1]:
            render_skill_graph(
                graph_service=graph_service,
                goal_id=store.goal_state.goal_id if store.goal_state else "goal_ml_engineer",
                knowledge_states=store.knowledge_states
            )

        with dash_tabs[2]:
            st.markdown("#### 📜 Continuous Adaptation Event Log")
            if not store.feedback_events:
                st.info("No feedback adaptation events recorded yet. Try sending feedback in the tutor chat on the right!")
            else:
                for fb in store.feedback_events:
                    st.markdown(
                        f"""
                        <div class="pf-panel" style="padding: 14px 18px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between;">
                                <span class="badge badge-jade">{fb.source.upper()} • {fb.type.upper()}</span>
                                <span style="font-size: 11px; color: var(--text-muted);">{fb.timestamp[:19]}</span>
                            </div>
                            <div style="margin-top: 8px; font-weight: 700;">"{fb.message}"</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    with col_right:
        render_chat_assistant(
            store=store,
            llm_service=llm_service,
            adaptation_engine=adaptation_engine
        )
