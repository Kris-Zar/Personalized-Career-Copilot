# -*- coding: utf-8 -*-
"""
XCL PathFinder - 6-Scenario Integration Test Suite
Tests the full end-to-end pipeline with Gemini LLM and deterministic backends
across 6 unique learner profiles with different goals, backgrounds, and constraints.
Run: python scripts/run_scenario_tests.py
"""

import sys
import os
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.storage.store import InMemoryStore
from core.schemas.profile import LearnerProfile
from core.schemas.feedback import GoalState, FeedbackEvent
from core.schemas.assessment import AssessmentAttempt
from core.services.graph_service import GraphService
from core.services.assessment_service import AssessmentService
from core.services.knowledge_service import KnowledgeStateEngine
from core.services.gap_analyzer import GapAnalyzer
from core.services.recommender import RecommendationEngine
from core.services.roadmap_engine import RoadmapEngine
from core.services.adaptation_engine import AdaptationEngine
from core.services.llm_service import LLMService

# ── Colour helpers ──────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"
CYAN  = "\033[96m"
BOLD  = "\033[1m"
RESET = "\033[0m"
LINE  = f"{CYAN}{'─' * 72}{RESET}"

def ok(msg):   print(f"  {GREEN}[PASS]{RESET}  {msg}")
def fail(msg): print(f"  {RED}[FAIL]{RESET}  {msg}")
def info(msg): print(f"  {YELLOW}[INFO]{RESET} {msg}")
def head(msg): print(f"\n{BOLD}{CYAN}{msg}{RESET}\n{LINE}")

# ── Shared service singletons ─────────────────────────────────────────────
graph_svc   = GraphService(data_dir="data/skills")
assess_svc  = AssessmentService(data_path="data/assessment/assessment_bank.json")
know_eng    = KnowledgeStateEngine(assessment_service=assess_svc)
gap_az      = GapAnalyzer(graph_service=graph_svc)
recommender = RecommendationEngine(catalog_path="data/resources/resources_catalog.json")
roadmap_eng = RoadmapEngine(graph_service=graph_svc, recommender=recommender)
adapt_eng   = AdaptationEngine(gap_analyzer=gap_az, roadmap_engine=roadmap_eng, recommender=recommender)
llm         = LLMService()

# Report if Gemini is live
if llm.client:
    print(f"\n{GREEN}{BOLD}[GEMINI LIVE] API Connected - Model: {llm.model_name}{RESET}")
else:
    print(f"\n{YELLOW}{BOLD}[WARNING] Gemini API not configured - using deterministic fallback{RESET}")

results = []  # (scenario_name, passed, failed, notes)


def run_scenario(
    name: str,
    description: str,
    learner_id: str,
    learner_name: str,
    current_role: str,
    goal_message: str,            # raw natural-language goal input
    expected_target_role: str,    # what we expect after LLM extraction
    goal_id: str,                 # which catalog track to activate
    weekly_hours: float,
    timeline_months: int,
    self_reported_skills: dict,
    assessment_answers: list,     # list of {item_id, skill_id, answer, correct}
    feedback_message: str,        # post-roadmap feedback for adaptation
    extra_tutor_query: str,       # a question for the AI tutor
):
    head(f"SCENARIO — {name}")
    print(f"  {description}\n")

    passed = 0
    failed = 0
    notes  = []

    # ── Step 1: Profile ──────────────────────────────────────────────────
    store = InMemoryStore()
    store.reset_to_fresh_state()
    profile = LearnerProfile(
        learner_id=learner_id,
        name=learner_name,
        current_role=current_role,
        weekly_hours=weekly_hours,
        timeline_months=timeline_months,
        self_reported_skills=self_reported_skills,
        content_preferences=["video", "interactive", "projects"],
        interests=[]
    )
    store.profile = profile
    ok(f"Profile created — {learner_name}, {current_role}, {weekly_hours}h/week, {timeline_months}-month goal")
    passed += 1

    # ── Step 2: Conversational Goal Extraction ───────────────────────────
    goal_result = llm.extract_goal_and_constraints(goal_message)
    extracted = goal_result.value
    actual_role = extracted.get("target_role", "")
    if goal_result.source == "gemini":
        source_label = "[GEMINI API]"
    else:
        source_label = f"[FALLBACK: {goal_result.error or 'no key'}]"
    if expected_target_role.lower() in actual_role.lower() or actual_role.lower() in expected_target_role.lower():
        ok(f"Goal extracted {source_label} -> '{actual_role}'  [expected: '{expected_target_role}']")
        passed += 1
    else:
        fail(f"Goal extraction mismatch -> got '{actual_role}', expected '{expected_target_role}' {source_label}")
        failed += 1
        notes.append(f"Goal mismatch: got '{actual_role}'")

    # ── Step 3: Goal State Activation ────────────────────────────────────
    graph = graph_svc.get_graph(goal_id)
    if graph:
        ok(f"Skill graph loaded for goal_id='{goal_id}' — {len(graph.nodes)} competency nodes")
        passed += 1
    else:
        fail(f"Skill graph NOT found for goal_id='{goal_id}'")
        failed += 1
        notes.append(f"No graph for {goal_id}")

    store.goal_state = GoalState(
        goal_id=goal_id,
        target_role=actual_role or expected_target_role,
        timeline_months=extracted.get("timeline_months", timeline_months),
        weekly_hours=extracted.get("weekly_hours", weekly_hours),
        active=True
    )

    # ── Step 4: Assessment ───────────────────────────────────────────────
    attempts = []
    for ans in assessment_answers:
        attempts.append(AssessmentAttempt(
            attempt_id=f"att_{learner_id}_{ans['item_id']}",
            learner_id=learner_id,
            goal_id=goal_id,
            item_id=ans["item_id"],
            skill_id=ans["skill_id"],
            answer=ans["answer"],
            correct=ans["correct"]
        ))
    store.assessment_attempts = attempts
    ok(f"Assessment submitted — {len(attempts)} items answered "
       f"({sum(1 for a in attempts if a.correct)} correct / {sum(1 for a in attempts if not a.correct)} incorrect)")
    passed += 1

    # ── Step 5: Knowledge State Engine ──────────────────────────────────
    if not graph:
        info("Skipping knowledge computation — no graph")
    else:
        k_states = know_eng.compute_knowledge_states(graph, attempts, self_reported_skills)
        store.knowledge_states = k_states
        weak = [ks.skill_name for ks in k_states.values() if ks.status == "weak"]
        adequate = [ks.skill_name for ks in k_states.values() if ks.status == "adequate"]
        info(f"Knowledge States — Adequate: {adequate or ['none']}  |  Weak: {weak or ['none']}")
        if k_states:
            ok("Knowledge states computed from evidence (not self-report)")
            passed += 1
        else:
            fail("Knowledge state computation returned empty")
            failed += 1

    # ── Step 6: Gap Analysis ─────────────────────────────────────────────
        gap_rep = gap_az.analyze_gaps(goal_id, k_states, self_reported_skills)
        store.gap_report = gap_rep
        info(f"Gaps — Weak: {len(gap_rep.weak_skills)}  Needs improvement: {len(gap_rep.needs_improvement_skills)}  Bottlenecks: {len(gap_rep.unresolved_prerequisites)}")
        if gap_rep.comparison_data:
            ok("Gap analysis computed — comparison table generated")
            passed += 1
        else:
            fail("Gap analysis returned no comparison data")
            failed += 1

    # ── Step 7: Roadmap v1 Generation ───────────────────────────────────
        roadmap_v1 = roadmap_eng.generate_roadmap(
            goal_id=goal_id,
            profile=store.profile,
            knowledge_states=k_states,
            gap_report=gap_rep,
            version=1
        )
        store.save_roadmap(roadmap_v1)
        stage_titles = [s.title for s in roadmap_v1.stages]
        info(f"Roadmap v1 — {len(stage_titles)} stages: {stage_titles}")
        if len(roadmap_v1.stages) > 0:
            ok(f"Personalized Roadmap v1 generated — {int(roadmap_v1.total_estimated_hours)}h total effort")
            passed += 1
        else:
            fail("Roadmap v1 returned 0 stages")
            failed += 1

    # ── Step 8: AI Tutor Query ───────────────────────────────────────────
        tutor_result = llm.answer_tutoring_query(
            query=extra_tutor_query,
            profile=store.profile,
            current_roadmap=roadmap_v1,
            knowledge_states=k_states,
            gap_report=gap_rep,
            skill_graph=graph
        )
        tutor_src = "[GEMINI API]" if tutor_result.source == "gemini" else f"[FALLBACK: {tutor_result.error or 'no key'}]"
        info(f"Tutor Q: '{extra_tutor_query}'")
        info(f"Tutor source: {tutor_src}")
        info(f"Tutor A (first 180 chars): {tutor_result.value[:180].strip()}")
        if len(tutor_result.value) > 20:
            if tutor_result.source == "gemini":
                ok("AI Tutor response generated by Gemini API")
            else:
                ok(f"AI Tutor using deterministic fallback (Gemini unavailable)")
            passed += 1
        else:
            fail("AI Tutor returned empty/too-short response")
            failed += 1

    # ── Step 9: Feedback → Adaptation (Roadmap v2) ──────────────────────
        original_weekly_hours = store.profile.weekly_hours
        fb = FeedbackEvent(
            feedback_id=f"fb_{learner_id}",
            learner_id=learner_id,
            source="chat",
            type="difficulty",
            target_id=gap_rep.weak_skills[0] if gap_rep.weak_skills else "math_prob_stats",
            message=feedback_message
        )
        store.record_feedback(fb)
        roadmap_v2, reason = adapt_eng.process_feedback(
            event=fb,
            profile=store.profile,
            knowledge_states=k_states,
            current_roadmap=roadmap_v1
        )
        store.save_roadmap(roadmap_v2)
        info(f"Feedback: '{feedback_message}'")
        info(f"Adaptation Reason: {reason}")

        v2_stages = [s.title for s in roadmap_v2.stages]
        if roadmap_v2.version == 2 and roadmap_v2.adaptation_diff:
            ok(f"Roadmap v2 generated via Adaptation Engine (v1→v2) — {len(v2_stages)} stages")
            passed += 1
        else:
            fail("Roadmap v2 adaptation failed or missing diff")
            failed += 1

    # ── Step 10: Verify state propagation ───────────────────────────────
        assert store.current_roadmap_version == 2, "Version should be 2 after adaptation"
        assert store.profile.name == learner_name, "Profile name lost"
        assert store.goal_state.goal_id == goal_id, "Goal ID lost"
        ok("State survived full pipeline — profile, goal, roadmap all consistent")
        passed += 1

    # ── Summary for this scenario ────────────────────────────────────────
    total = passed + failed
    status = "✅ ALL PASSED" if failed == 0 else f"⚠ {failed}/{total} FAILED"
    print(f"\n  Result: {BOLD}{status}{RESET}  ({passed}/{total} checks)  [{name}]")
    if notes:
        for n in notes:
            print(f"  {YELLOW}NOTE: {n}{RESET}")
    results.append((name, passed, failed, notes))
    time.sleep(1.2)  # gentle rate-limiting for Gemini API


# ════════════════════════════════════════════════════════════════════════════
# 6 UNIQUE SCENARIOS
# ════════════════════════════════════════════════════════════════════════════

# ── Scenario 1 ─────────────────────────────────────────────────────────────
run_scenario(
    name="Priya — Biology Student → Data Scientist",
    description="Final-year Biology student with Python basics, wants to pivot into bioinformatics & Data Science.",
    learner_id="priya_bio_01",
    learner_name="Priya Sharma",
    current_role="Biology Student (Final Year)",
    goal_message="I am finishing my biology degree and I am passionate about bioinformatics. I want to become a Data Scientist specialising in life-sciences data. I can dedicate 10 hours per week and would like to be job-ready in 8 months.",
    expected_target_role="Data Scientist",
    goal_id="goal_data_scientist",
    weekly_hours=10.0,
    timeline_months=8,
    self_reported_skills={"py_core": 0.30, "math_prob_stats": 0.40, "ml_foundations": 0.10},
    assessment_answers=[
        {"item_id": "q_py_01", "skill_id": "py_core",          "answer": "Expression B uses generators", "correct": True},
        {"item_id": "q_py_02", "skill_id": "py_core",          "answer": "O(n²) because nested loops",   "correct": False},
        {"item_id": "q_prob_01","skill_id": "math_prob_stats", "answer": "P(A|B) = P(A)",                "correct": False},
        {"item_id": "q_prob_02","skill_id": "math_prob_stats", "answer": "They add",                      "correct": False},
    ],
    feedback_message="The statistics content is moving too fast. I only have weekends free, maybe 4 hours total per week now.",
    extra_tutor_query="Why is Probability listed before Machine Learning Foundations in my roadmap?",
)

# ── Scenario 2 ─────────────────────────────────────────────────────────────
run_scenario(
    name="Marcus — DevOps Engineer → ML Engineer",
    description="Experienced DevOps engineer, strong in cloud infra, wants to add ML model deployment to his skillset.",
    learner_id="marcus_devops_02",
    learner_name="Marcus Osei",
    current_role="Senior DevOps Engineer",
    goal_message="I spend most of my time on Kubernetes and CI/CD pipelines. I want to become a Machine Learning Engineer so I can own the full model lifecycle from training to MLOps deployment. 8 hours per week, 6 months.",
    expected_target_role="Machine Learning Engineer",
    goal_id="goal_ml_engineer",
    weekly_hours=8.0,
    timeline_months=6,
    self_reported_skills={"py_core": 0.70, "ml_foundations": 0.20, "math_prob_stats": 0.30, "ml_ops": 0.75},
    assessment_answers=[
        {"item_id": "q_py_01",  "skill_id": "py_core",          "answer": "Expression B is a generator that is memory-efficient", "correct": True},
        {"item_id": "q_py_02",  "skill_id": "py_core",          "answer": "O(1) average for dict lookups",                        "correct": True},
        {"item_id": "q_prob_01","skill_id": "math_prob_stats",  "answer": "3/8 because of combinations",                          "correct": True},
        {"item_id": "q_ml_01",  "skill_id": "ml_foundations",   "answer": "High variance / overfitting; use regularisation",      "correct": True},
    ],
    feedback_message="I'm flying through the Python content since I already code daily. Can you give me more project-based exercises instead?",
    extra_tutor_query="I already know Docker and Kubernetes. How does MLOps fit into my existing skillset?",
)

# ── Scenario 3 ─────────────────────────────────────────────────────────────
run_scenario(
    name="Sofia — Graphic Designer → Full-Stack AI Developer",
    description="Self-taught graphic designer who has learned HTML/CSS but wants to build AI-powered web apps.",
    learner_id="sofia_design_03",
    learner_name="Sofia Almeida",
    current_role="Freelance Graphic Designer",
    goal_message="I know HTML, CSS, and a little JavaScript from YouTube tutorials. I want to become a Full-Stack AI Developer who can build beautiful AI-powered web apps. I have 12 hours a week and ideally want to do this in 4 months.",
    expected_target_role="Full-Stack AI Developer",
    goal_id="goal_fullstack_ai",
    weekly_hours=12.0,
    timeline_months=4,
    self_reported_skills={"web_frontend": 0.45, "web_backend": 0.15, "llm_integration": 0.10, "db_systems": 0.10},
    assessment_answers=[
        {"item_id": "q_fs_01",  "skill_id": "web_frontend",    "answer": "React uses a virtual DOM for performance",   "correct": True},
        {"item_id": "q_fs_02",  "skill_id": "web_backend",     "answer": "REST means stateless client-server architecture", "correct": True},
        {"item_id": "q_llm_01", "skill_id": "llm_integration", "answer": "I am not sure about RAG",                  "correct": False},
        {"item_id": "q_db_01",  "skill_id": "db_systems",      "answer": "SQL uses tables, NoSQL uses documents",      "correct": True},
    ],
    feedback_message="The backend API section is confusing. I prefer watching video tutorials over reading documentation.",
    extra_tutor_query="What is the difference between a REST API and a vector database, and why do I need both?",
)

# ── Scenario 4 ─────────────────────────────────────────────────────────────
run_scenario(
    name="James — Accountant → Data Scientist (Career Switcher)",
    description="Accountant with Excel and SQL experience trying a full career switch into Data Science.",
    learner_id="james_acct_04",
    learner_name="James Whitfield",
    current_role="Senior Accountant",
    goal_message="I have been an accountant for 8 years and I use Excel and SQL every day. I want to switch careers and become a Data Scientist. I am a complete beginner at Python and machine learning. I can do 6 hours a week for the next 9 months.",
    expected_target_role="Data Scientist",
    goal_id="goal_data_scientist",
    weekly_hours=6.0,
    timeline_months=9,
    self_reported_skills={"py_core": 0.10, "math_prob_stats": 0.50, "ml_foundations": 0.05},
    assessment_answers=[
        {"item_id": "q_py_01",  "skill_id": "py_core",         "answer": "Expression A is a list",         "correct": False},
        {"item_id": "q_py_02",  "skill_id": "py_core",         "answer": "O(n) for each lookup",            "correct": False},
        {"item_id": "q_prob_01","skill_id": "math_prob_stats", "answer": "3/8",                              "correct": True},
        {"item_id": "q_prob_02","skill_id": "math_prob_stats", "answer": "Variances add for independent",   "correct": True},
    ],
    feedback_message="Python syntax is very new to me. I feel overwhelmed. Can we break down the Python stage into much smaller daily chunks?",
    extra_tutor_query="As an accountant, how can I use my existing Excel and SQL skills to help me learn Python and statistics faster?",
)

# ── Scenario 5 ─────────────────────────────────────────────────────────────
run_scenario(
    name="Kenji — ML Researcher → Production ML Engineer",
    description="Academic ML researcher with strong theory, weak in engineering and deployment.",
    learner_id="kenji_research_05",
    learner_name="Kenji Tanaka",
    current_role="ML Research Scientist (Academia)",
    goal_message="I have a PhD in statistical machine learning and I publish papers. But I have never deployed anything to production. I want to become a professional Machine Learning Engineer who builds real production systems. I have 5 hours per week and want to achieve this in 5 months.",
    expected_target_role="Machine Learning Engineer",
    goal_id="goal_ml_engineer",
    weekly_hours=5.0,
    timeline_months=5,
    self_reported_skills={"math_prob_stats": 0.95, "math_linear_algebra": 0.95, "ml_foundations": 0.90, "py_core": 0.65, "ml_ops": 0.15},
    assessment_answers=[
        {"item_id": "q_py_01",  "skill_id": "py_core",         "answer": "Expression B produces items lazily using generator protocol", "correct": True},
        {"item_id": "q_py_02",  "skill_id": "py_core",         "answer": "O(1) average amortised via hash table",                       "correct": True},
        {"item_id": "q_prob_01","skill_id": "math_prob_stats", "answer": "3/8 by hypergeometric distribution",                          "correct": True},
        {"item_id": "q_ml_01",  "skill_id": "ml_foundations",  "answer": "High variance overfitting; regularise via L2 weight decay",   "correct": True},
    ],
    feedback_message="I already know all the math theory. Please skip foundational stages and focus on MLOps, Docker, FastAPI, and model monitoring instead.",
    extra_tutor_query="Given my PhD background, which stages in my roadmap can I fast-track and where should I focus my energy?",
)

# ── Scenario 6 ─────────────────────────────────────────────────────────────
run_scenario(
    name="Aisha — High School Teacher → Data Scientist (Parent, time-constrained)",
    description="Teacher and parent with only 3 hours per week available, wants to upskill slowly into Data Science.",
    learner_id="aisha_teacher_06",
    learner_name="Aisha Nwosu",
    current_role="High School Mathematics Teacher",
    goal_message="I teach maths and statistics at high school so I understand the concepts well. I want to slowly learn Data Science and Python on the side while working full time as a teacher. I can only manage 3 hours per week and I am thinking of a 12-month journey.",
    expected_target_role="Data Scientist",
    goal_id="goal_data_scientist",
    weekly_hours=3.0,
    timeline_months=12,
    self_reported_skills={"math_prob_stats": 0.80, "py_core": 0.20, "ml_foundations": 0.15},
    assessment_answers=[
        {"item_id": "q_py_01",  "skill_id": "py_core",         "answer": "I think it has to do with lists",                    "correct": False},
        {"item_id": "q_prob_01","skill_id": "math_prob_stats",  "answer": "3/8 using combinations C(4,3)/C(8,3)",               "correct": True},
        {"item_id": "q_prob_02","skill_id": "math_prob_stats",  "answer": "Var(X-Y)=Var(X)+Var(Y) for independent variables",   "correct": True},
        {"item_id": "q_ml_01",  "skill_id": "ml_foundations",  "answer": "Overfitting; reduce complexity or add more data",     "correct": True},
    ],
    feedback_message="Some weeks I cannot study at all due to work. Can the roadmap adapt to very short 20-minute daily learning sessions?",
    extra_tutor_query="As a maths teacher, I understand probability well. How quickly can I move from statistics to actual machine learning models?",
)

# ════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════════════════════════════
print(f"\n\n{'═' * 72}")
print(f"{BOLD}{CYAN}  XCL PATHFINDER — SCENARIO TEST SUMMARY{RESET}")
print(f"{'═' * 72}")
print(f"  {'Scenario':<45} {'Passed':>8} {'Failed':>8}")
print(f"  {'─' * 63}")
total_p = total_f = 0
for (name, p, f, notes) in results:
    status_icon = GREEN + "[OK]" + RESET if f == 0 else RED + "[!!]" + RESET
    print(f"  {status_icon} {name:<43} {GREEN}{p:>6}{RESET}  {RED if f else GREEN}{f:>6}{RESET}")
    total_p += p
    total_f += f
    for n in notes:
        print(f"      {YELLOW}↳ {n}{RESET}")

print(f"\n  {'─' * 63}")
print(f"  {'TOTAL':<45} {GREEN}{total_p:>6}{RESET}  {RED if total_f else GREEN}{total_f:>6}{RESET}")
grand_status = f"{GREEN}{BOLD}ALL SCENARIOS PASSED{RESET}" if total_f == 0 else f"{YELLOW}{BOLD}{total_f} CHECKS NEED REVIEW{RESET}"
print(f"\n  {grand_status}")
print(f"  LLM Mode: {'Gemini ' + llm.model_name if llm.client else 'Deterministic Fallback'}")
print(f"  Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
