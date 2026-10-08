import streamlit as st
import uuid
from core.storage.store import InMemoryStore
from core.services.assessment_service import AssessmentService
from core.services.knowledge_service import KnowledgeStateEngine
from core.services.gap_analyzer import GapAnalyzer
from core.services.roadmap_engine import RoadmapEngine
from core.services.graph_service import GraphService
from core.schemas.assessment import AssessmentAttempt

def render_assessment_view(
    store: InMemoryStore,
    assessment_service: AssessmentService,
    knowledge_engine: KnowledgeStateEngine,
    gap_analyzer: GapAnalyzer,
    roadmap_engine: RoadmapEngine,
    graph_service: GraphService
):
    st.subheader("📝 Diagnostic Knowledge Assessment (Signal 1)")
    st.caption("Step 3: Answer diagnostic items across key competencies to measure demonstrated proficiency against target requirements.")

    # Demo quick-fill banner
    st.markdown(
        """
        <div class="demo-bar">
            <div>
                <b>💡 1-Click Demo Persona:</b> Pre-fill assessment with Strong Python + Weak Probability responses to showcase prerequisite bottleneck detection.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_demo, _ = st.columns([2, 1])
    with col_demo:
        if st.button("⚡ Pre-fill Assessment with 'Alex' Demo Answers", use_container_width=True):
            store.assessment_attempts = [
                AssessmentAttempt(
                    attempt_id=f"att_{uuid.uuid4().hex[:6]}",
                    learner_id=store.profile.learner_id,
                    goal_id=store.goal_state.goal_id,
                    item_id="q_py_01",
                    skill_id="py_core",
                    answer="Expression B uses lazy evaluation and produces items on-demand, consuming minimal memory, while Expression A builds the entire list in memory at once.",
                    correct=True
                ),
                AssessmentAttempt(
                    attempt_id=f"att_{uuid.uuid4().hex[:6]}",
                    learner_id=store.profile.learner_id,
                    goal_id=store.goal_state.goal_id,
                    item_id="q_py_02",
                    skill_id="py_core",
                    answer="O(1) average constant time using hash tables",
                    correct=True
                ),
                AssessmentAttempt(
                    attempt_id=f"att_{uuid.uuid4().hex[:6]}",
                    learner_id=store.profile.learner_id,
                    goal_id=store.goal_state.goal_id,
                    item_id="q_prob_01",
                    skill_id="math_prob_stats",
                    answer="Approx. 95%",  # Incorrect Bayes estimate!
                    correct=False
                ),
                AssessmentAttempt(
                    attempt_id=f"att_{uuid.uuid4().hex[:6]}",
                    learner_id=store.profile.learner_id,
                    goal_id=store.goal_state.goal_id,
                    item_id="q_prob_02",
                    skill_id="math_prob_stats",
                    answer="Var(X - Y) = Var(X) - Var(Y)",  # Incorrect variance property!
                    correct=False
                ),
                AssessmentAttempt(
                    attempt_id=f"att_{uuid.uuid4().hex[:6]}",
                    learner_id=store.profile.learner_id,
                    goal_id=store.goal_state.goal_id,
                    item_id="q_ml_01",
                    skill_id="ml_foundations",
                    answer="High Variance (Overfitting); apply regularization (L1/L2), use cross-validation, reduce model capacity, or collect more data.",
                    correct=True
                )
            ]
            st.success("✅ Assessment answers loaded! Click 'Submit & Analyze Gaps' below.")

    items = assessment_service.get_all_items()
    user_answers = {}

    for idx, item in enumerate(items, start=1):
        diff_color = "badge-jade" if item.difficulty == "easy" else ("badge-tangerine" if item.difficulty == "medium" else "badge-coral")
        
        st.markdown(
            f"""
            <div class="glass-card" style="margin-top: 14px; padding: 18px 22px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="badge {diff_color}">{item.difficulty.upper()} • {item.skill_id.upper()}</span>
                    <span style="font-family: var(--font-mono); font-size: 0.8rem; opacity: 0.75;">Question {idx} of {len(items)} • Weight: {item.evidence_weight}x</span>
                </div>
                <h4 style="margin: 6px 0 10px 0;">{item.prompt}</h4>
            </div>
            """,
            unsafe_allow_html=True
        )

        if item.code_snippet:
            st.code(item.code_snippet, language="python")

        existing_ans = next((att.answer for att in store.assessment_attempts if att.item_id == item.item_id), None)
        default_index = item.options.index(existing_ans) if (existing_ans and existing_ans in item.options) else 0

        selected = st.radio(
            f"Select Answer for Question {idx}:",
            options=item.options,
            index=default_index,
            key=f"q_radio_{item.item_id}"
        )
        user_answers[item.item_id] = selected
        st.divider()

    if st.button("📊 Submit Assessment & Compute Knowledge Gaps ➔", type="primary", use_container_width=True):
        attempts = []
        for item_id, ans in user_answers.items():
            item = assessment_service.get_item(item_id)
            if not item:
                continue
            is_corr = (ans.strip() == item.correct_answer.strip())
            attempts.append(
                AssessmentAttempt(
                    attempt_id=f"att_{uuid.uuid4().hex[:6]}",
                    learner_id=store.profile.learner_id,
                    goal_id=store.goal_state.goal_id,
                    item_id=item_id,
                    skill_id=item.skill_id,
                    answer=ans,
                    correct=is_corr
                )
            )
        store.assessment_attempts = attempts

        graph = graph_service.get_graph(store.goal_state.goal_id)
        k_states = knowledge_engine.compute_knowledge_states(
            skill_graph=graph,
            attempts=attempts,
            self_reported_skills=store.profile.self_reported_skills
        )
        store.knowledge_states = k_states

        gap_rep = gap_analyzer.analyze_gaps(
            goal_id=store.goal_state.goal_id,
            knowledge_states=k_states,
            self_reported_skills=store.profile.self_reported_skills
        )
        store.gap_report = gap_rep

        roadmap = roadmap_engine.generate_roadmap(
            goal_id=store.goal_state.goal_id,
            profile=store.profile,
            knowledge_states=k_states,
            gap_report=gap_rep,
            version=1,
            generation_reason="Initial personalized roadmap generated from diagnostic assessment"
        )
        store.save_roadmap(roadmap)

        st.success("✅ Diagnostic assessment scored! Gaps identified and Roadmap v1 generated.")
        st.session_state["active_tab"] = "📊 4. Skill Gap Results"
        st.rerun()
