# -*- coding: utf-8 -*-
"""
scripts/diagnose_gemini.py
===========================
Live Gemini API diagnostic tool for XCL PathFinder.

Run manually when GEMINI_API_KEY is configured:
    python scripts/diagnose_gemini.py

This script:
  1. Prints startup configuration (no secrets)
  2. Tests connectivity with a single minimal request
  3. Tests goal extraction and reports source
  4. Tests AI tutor and reports source
  5. Runs one full E2E scenario and shows which calls used Gemini vs fallback

Exit code: 0 = Gemini connected, 1 = Gemini unavailable (fallback active)
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Silence library noise
import logging
logging.basicConfig(level=logging.WARNING)

from core.services.llm_service import LLMService
from core.schemas.profile import LearnerProfile
from core.schemas.feedback import GoalState

# ── Formatting ────────────────────────────────────────────────────────────────
LINE = "=" * 65
SEP  = "-" * 65

def banner(title):
    print(f"\n{LINE}")
    print(f"  {title}")
    print(LINE)

def row(label, value, ok=True):
    marker = "[OK]  " if ok else "[WARN]"
    print(f"  {marker}  {label:<30} {value}")


# ── 1. Configuration Summary ──────────────────────────────────────────────────
banner("XCL PathFinder — Gemini Diagnostic")

llm = LLMService()
summary = llm.startup_summary()

print()
for k, v in summary.items():
    ok = "NO" not in v and "UNKNOWN" not in v and "FAILED" not in v
    row(k, v, ok=ok)

if not llm._configured:
    print(f"\n  [INFO] No API key configured. Only fallback mode is available.")
    print(f"         Set GEMINI_API_KEY in your .env file to enable Gemini.")
    print(f"\n  Fallback: ACTIVE\n")
    sys.exit(1)


# ── 2. Connectivity Test ──────────────────────────────────────────────────────
banner("Step 1: Gemini Connectivity Test")
conn = llm.test_gemini_connection()
print()
row("Success",         str(conn["success"]),  ok=conn["success"])
row("Model",           conn["model"],         ok=True)
row("Response preview", str(conn.get("response_preview", "N/A"))[:50], ok=conn["success"])
if conn.get("error"):
    row("Error", conn["error"], ok=False)

if not conn["success"]:
    print(f"\n  [FAIL] Gemini API is NOT reachable.")
    print(f"  Error: {conn.get('error')}")
    print(f"\n  Gemini API: FAILED")
    print(f"  Fallback:   ACTIVE")
    print(f"  Recommendation: Check your API key and model name in .env\n")
    sys.exit(1)

print(f"\n  Gemini API: CONNECTED")
print(f"  Model: {conn['model']}")


# ── 3. Goal Extraction Test ───────────────────────────────────────────────────
banner("Step 2: Goal Extraction (extract_goal_and_constraints)")

test_inputs = [
    "I am a teacher and I want to become a Data Scientist in 9 months, 6 hours per week",
    "I want to become a Full-Stack AI Developer in 4 months with 12 hours a week",
    "I want to be a Machine Learning Engineer in 6 months, 8 hours weekly",
]

all_gemini = True
for msg in test_inputs:
    result = llm.extract_goal_and_constraints(msg)
    src_label = "[GEMINI API]" if result.source == "gemini" else "[FALLBACK]  "
    role = result.value.get("target_role", "UNKNOWN")
    months = result.value.get("timeline_months", "?")
    hours = result.value.get("weekly_hours", "?")
    print(f"\n  Input:   {msg[:60]}...")
    print(f"  Source:  {src_label}")
    print(f"  Parsed:  role='{role}', months={months}, hours={hours}h/wk")
    if result.source != "gemini":
        all_gemini = False
        print(f"  Reason:  {result.error}")

print()
if all_gemini:
    print("  Goal extraction source: GEMINI")
else:
    print("  Goal extraction source: FALLBACK (see reasons above)")


# ── 4. AI Tutor Test ──────────────────────────────────────────────────────────
banner("Step 3: AI Tutor (answer_tutoring_query)")

profile = LearnerProfile(
    learner_id="diag_001",
    name="Diagnostic User",
    current_role="Software Developer",
    weekly_hours=8.0,
    timeline_months=6,
    self_reported_skills={"py_core": 0.5, "math_prob_stats": 0.3},
    content_preferences=["video", "projects"],
    interests=["Machine Learning"],
)

tutor_questions = [
    "Why is probability listed before machine learning in my roadmap?",
    "I feel the Python content is moving too fast. What should I do?",
]

tutor_all_gemini = True
for q in tutor_questions:
    result = llm.answer_tutoring_query(
        query=q,
        profile=profile,
        current_roadmap=None,
        knowledge_states={},
        gap_report=None,
        skill_graph=None,
    )
    src_label = "[GEMINI API]" if result.source == "gemini" else "[FALLBACK]  "
    print(f"\n  Question: {q[:60]}")
    print(f"  Source:   {src_label}")
    print(f"  Answer:   {result.value[:120].strip()}...")
    if result.source != "gemini":
        tutor_all_gemini = False
        print(f"  Reason:   {result.error}")

print()
if tutor_all_gemini:
    print("  AI Tutor source: GEMINI")
else:
    print("  AI Tutor source: FALLBACK (see reasons above)")


# ── 5. Final Report ───────────────────────────────────────────────────────────
banner("Diagnostic Summary")
print()
print(f"  Gemini model:         {llm.model_name}")
print(f"  Gemini API:           {'CONNECTED' if conn['success'] else 'FAILED'}")
print(f"  Goal extraction:      {'GEMINI' if all_gemini else 'FALLBACK'}")
print(f"  AI Tutor:             {'GEMINI' if tutor_all_gemini else 'FALLBACK'}")
print(f"  Fallback behavior:    ACTIVE (always available as safety net)")
print()

if conn["success"] and all_gemini and tutor_all_gemini:
    print("  STATUS: FULLY OPERATIONAL — all calls using Gemini API")
    exit_code = 0
elif conn["success"]:
    print("  STATUS: PARTIAL — Gemini connected but some calls fell back")
    exit_code = 1
else:
    print("  STATUS: FALLBACK MODE — Gemini unavailable, deterministic fallback active")
    exit_code = 1

print(f"{LINE}\n")
sys.exit(exit_code)
