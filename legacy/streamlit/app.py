import streamlit as st
import os
import uuid

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# =========================================================
# Streamlit Page Configuration
# =========================================================
st.set_page_config(
    page_title="XCL PathFinder — Adaptive Career Copilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

if "current_screen" not in st.session_state:
    st.session_state["current_screen"] = "profile"

# Inject Active Theme Tokens & Stylesheet
DARK_THEME_CSS = """
:root {
    --bg-canvas: #231032;
    --bg-paper: #2C153E;
    --bg-card: #381A4E;
    --bg-card-hover: #45215F;
    --bg-rail: #190925;
    --rail-text: #FAF5FF;
    --rail-text-soft: #C6B3DA;
    --border-subtle: #532A74;
    --border-highlight: #8B4BBF;
    --text-primary: #FAF5FF;
    --text-secondary: #C6B3DA;
    --text-muted: #8E73A6;
    --c-coral: #FF4D79;
    --c-coral-soft: #FF7597;
    --c-coral-tint: rgba(255, 77, 121, 0.16);
    --c-tangerine: #FFB703;
    --c-tangerine-tint: rgba(255, 183, 3, 0.16);
    --c-jade: #59C9A5;
    --c-jade-tint: rgba(89, 201, 165, 0.16);
    --c-cerulean: #0AD3FF;
    --c-cerulean-tint: rgba(10, 211, 255, 0.16);
    --btn-gradient: linear-gradient(135deg, #FF4D79, #E02657);
    --momentum-gradient: linear-gradient(90deg, #FFB703, #FF4D79);
    --glow-coral: 0 4px 16px rgba(255, 77, 121, 0.45);
    --glow-jade: 0 4px 16px rgba(89, 201, 165, 0.35);
    --card-shadow: 0 10px 36px rgba(0, 0, 0, 0.5);
    --pill-bg: rgba(255, 77, 121, 0.16);
    --pill-color: #FF4D79;
}
"""

def apply_theme_and_styles():
    theme = st.session_state.get("theme", "light")
    css_path = "assets/style.css"
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            base_css = f.read()
        css_payload = "<style>\n" + base_css + "\n" + (DARK_THEME_CSS if theme == "dark" else "") + "\n</style>"
        st.markdown(css_payload, unsafe_allow_html=True)

apply_theme_and_styles()

# Import Core Services and Storage
from core.storage.store import InMemoryStore
from core.services.graph_service import GraphService
from core.services.assessment_service import AssessmentService
from core.services.knowledge_service import KnowledgeStateEngine
from core.services.gap_analyzer import GapAnalyzer
from core.services.recommender import RecommendationEngine
from core.services.roadmap_engine import RoadmapEngine
from core.services.adaptation_engine import AdaptationEngine
from core.services.llm_service import LLMService

# Import UI Views and Header
from ui.components.header import render_header
from ui.views.view_profile import render_profile_view
from ui.views.view_goal_discovery import render_goal_discovery_view
from ui.views.view_assessment import render_assessment_view
from ui.views.view_results_gaps import render_results_view
from ui.views.view_roadmap import render_roadmap_tab_view
from ui.views.view_dashboard import render_dashboard_view
from core.schemas.assessment import AssessmentAttempt
from core.schemas.feedback import GoalState

if "store" not in st.session_state:
    st.session_state["store"] = InMemoryStore()

store: InMemoryStore = st.session_state["store"]

@st.cache_resource
def get_services():
    graph_svc = GraphService(data_dir="data/skills")
    assess_svc = AssessmentService(data_path="data/assessment/assessment_bank.json")
    knowledge_eng = KnowledgeStateEngine(assessment_service=assess_svc)
    gap_analyzer = GapAnalyzer(graph_service=graph_svc)
    recommender = RecommendationEngine(catalog_path="data/resources/resources_catalog.json")
    roadmap_eng = RoadmapEngine(graph_service=graph_svc, recommender=recommender)
    adaptation_eng = AdaptationEngine(gap_analyzer=gap_analyzer, roadmap_engine=roadmap_eng, recommender=recommender)
    llm_svc = LLMService()
    return graph_svc, assess_svc, knowledge_eng, gap_analyzer, recommender, roadmap_eng, adaptation_eng, llm_svc

graph_svc, assess_svc, knowledge_eng, gap_analyzer, recommender, roadmap_eng, adaptation_eng, llm_svc = get_services()

# --- Optional Sidebar for Fast Demo Persona Switching & Diagnostics ---
with st.sidebar:
    st.markdown("### 🎭 Scenario Presets")

    if st.button("⚡ Alex (Bio → Data Science)", use_container_width=True):
        store.reset_to_default_persona()
        store.assessment_attempts = [
            AssessmentAttempt(attempt_id="att_alex_1", learner_id=store.profile.learner_id, goal_id=store.goal_state.goal_id, item_id="q_py_01", skill_id="py_core", answer="Expression B uses lazy evaluation and produces items on-demand, consuming minimal memory, while Expression A builds the entire list in memory at once.", correct=True),
            AssessmentAttempt(attempt_id="att_alex_2", learner_id=store.profile.learner_id, goal_id=store.goal_state.goal_id, item_id="q_py_02", skill_id="py_core", answer="O(1) average constant time using hash tables", correct=True),
            AssessmentAttempt(attempt_id="att_alex_3", learner_id=store.profile.learner_id, goal_id=store.goal_state.goal_id, item_id="q_prob_01", skill_id="math_prob_stats", answer="Approx. 95%", correct=False),
            AssessmentAttempt(attempt_id="att_alex_4", learner_id=store.profile.learner_id, goal_id=store.goal_state.goal_id, item_id="q_prob_02", skill_id="math_prob_stats", answer="Var(X - Y) = Var(X) - Var(Y)", correct=False),
            AssessmentAttempt(attempt_id="att_alex_5", learner_id=store.profile.learner_id, goal_id=store.goal_state.goal_id, item_id="q_ml_01", skill_id="ml_foundations", answer="High Variance (Overfitting); apply regularization (L1/L2), use cross-validation, reduce model capacity, or collect more data.", correct=True)
        ]
        graph = graph_svc.get_graph(store.goal_state.goal_id)
        k_states = knowledge_eng.compute_knowledge_states(graph, store.assessment_attempts, store.profile.self_reported_skills)
        store.knowledge_states = k_states
        gap_rep = gap_analyzer.analyze_gaps(store.goal_state.goal_id, k_states, store.profile.self_reported_skills)
        store.gap_report = gap_rep
        roadmap_v1 = roadmap_eng.generate_roadmap(store.goal_state.goal_id, store.profile, k_states, gap_rep, version=1)
        store.save_roadmap(roadmap_v1)
        st.session_state["current_screen"] = "dash"
        st.toast("Loaded Alex (Data Scientist Track)!", icon="🚀")
        st.rerun()

    if st.button("⚡ Kenji (Researcher → ML Ops)", use_container_width=True):
        store.reset_to_fresh_state()
        store.profile.name = "Kenji Tanaka"
        store.profile.current_role = "ML Researcher (Academia)"
        store.profile.weekly_hours = 5.0
        store.profile.timeline_months = 5
        store.profile.self_reported_skills = {"math_prob_stats": 0.95, "py_core": 0.65, "ml_foundations": 0.90, "ml_ops": 0.15}
        store.goal_state = GoalState(goal_id="goal_ml_engineer", target_role="Machine Learning Engineer", timeline_months=5, weekly_hours=5.0, target_proficiency_by_skill={"py_core": 0.85, "ml_ops": 0.75, "ml_foundations": 0.85}, active=True)
        store.assessment_attempts = [
            AssessmentAttempt(attempt_id="att_k1", learner_id="k_01", goal_id="goal_ml_engineer", item_id="q_py_01", skill_id="py_core", answer="Expression B", correct=True),
            AssessmentAttempt(attempt_id="att_k2", learner_id="k_01", goal_id="goal_ml_engineer", item_id="q_prob_01", skill_id="math_prob_stats", answer="3/8", correct=True),
            AssessmentAttempt(attempt_id="att_k3", learner_id="k_01", goal_id="goal_ml_engineer", item_id="q_ml_01", skill_id="ml_foundations", answer="High Variance", correct=True),
        ]
        graph = graph_svc.get_graph("goal_ml_engineer")
        k_states = knowledge_eng.compute_knowledge_states(graph, store.assessment_attempts, store.profile.self_reported_skills)
        store.knowledge_states = k_states
        gap_rep = gap_analyzer.analyze_gaps("goal_ml_engineer", k_states, store.profile.self_reported_skills)
        store.gap_report = gap_rep
        roadmap_v1 = roadmap_eng.generate_roadmap("goal_ml_engineer", store.profile, k_states, gap_rep, version=1)
        store.save_roadmap(roadmap_v1)
        st.session_state["current_screen"] = "dash"
        st.toast("Loaded Kenji (ML Engineer Track)!", icon="🔬")
        st.rerun()

    if st.button("⚡ Aisha (Teacher → Data Science)", use_container_width=True):
        store.reset_to_fresh_state()
        store.profile.name = "Aisha Nwosu"
        store.profile.current_role = "Maths Teacher"
        store.profile.weekly_hours = 3.0
        store.profile.timeline_months = 12
        store.profile.self_reported_skills = {"math_prob_stats": 0.85, "py_core": 0.15, "ml_foundations": 0.10}
        store.goal_state = GoalState(goal_id="goal_data_scientist", target_role="Data Scientist", timeline_months=12, weekly_hours=3.0, target_proficiency_by_skill={"py_core": 0.85, "math_prob_stats": 0.85, "ml_foundations": 0.85}, active=True)
        store.assessment_attempts = [
            AssessmentAttempt(attempt_id="att_a1", learner_id="a_01", goal_id="goal_data_scientist", item_id="q_py_01", skill_id="py_core", answer="Wrong option", correct=False),
            AssessmentAttempt(attempt_id="att_a2", learner_id="a_01", goal_id="goal_data_scientist", item_id="q_prob_01", skill_id="math_prob_stats", answer="3/8", correct=True),
            AssessmentAttempt(attempt_id="att_a3", learner_id="a_01", goal_id="goal_data_scientist", item_id="q_ml_01", skill_id="ml_foundations", answer="High Variance", correct=True),
        ]
        graph = graph_svc.get_graph("goal_data_scientist")
        k_states = knowledge_eng.compute_knowledge_states(graph, store.assessment_attempts, store.profile.self_reported_skills)
        store.knowledge_states = k_states
        gap_rep = gap_analyzer.analyze_gaps("goal_data_scientist", k_states, store.profile.self_reported_skills)
        store.gap_report = gap_rep
        roadmap_v1 = roadmap_eng.generate_roadmap("goal_data_scientist", store.profile, k_states, gap_rep, version=1)
        store.save_roadmap(roadmap_v1)
        st.session_state["current_screen"] = "dash"
        st.toast("Loaded Aisha (Teacher Track)!", icon="📚")
        st.rerun()

    st.markdown("---")
    if st.button("🔄 Reset to 100% Fresh Start", use_container_width=True):
        store.reset_to_fresh_state()
        st.session_state["current_screen"] = "profile"
        st.session_state.pop("extracted_goal", None)
        st.toast("Reset to 100% Fresh Profile!", icon="🧹")
        st.rerun()

# --- Render Top Navigation & Hero Header ---
render_header(store)

# --- Route Authoritative Screen View ---
screen = st.session_state.get("current_screen", "profile")

if screen == "profile":
    render_profile_view(store)

elif screen == "chat":
    render_goal_discovery_view(store, llm_svc, graph_svc)

elif screen == "assess":
    render_assessment_view(store, assess_svc, knowledge_eng, gap_analyzer, roadmap_eng, graph_svc)

elif screen == "results":
    render_results_view(store)

elif screen == "roadmap":
    render_roadmap_tab_view(store)

elif screen == "dash":
    render_dashboard_view(store, graph_svc, llm_svc, adaptation_eng)

else:
    render_profile_view(store)
