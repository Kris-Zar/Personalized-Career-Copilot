"""
core/services/llm_service.py
=============================
Centralized LLM adapter for XCL PathFinder.

Provider:  Google Gemini via the `google-genai` SDK (google.genai)
Fallback:  Deterministic regex/template engine (always available)

Every public method returns a LLMResult namedtuple that includes:
  - value     : the actual structured/text result
  - source    : "gemini" | "fallback"
  - error     : None or exception string (only when source == "fallback" due to API error)

Rule: a fallback response is NEVER labeled as a Gemini response.
"""

import os
import json
import re
import logging
from typing import Dict, List, Optional, Any, NamedTuple

from core.schemas.roadmap import Roadmap
from core.schemas.assessment import KnowledgeState, GapReport
from core.schemas.profile import LearnerProfile
from core.schemas.skill_graph import SkillGraph

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
# Single canonical default — overridden by GEMINI_MODEL env var.
# Must match an ID from the ListModels response (without 'models/' prefix).
DEFAULT_MODEL = "gemini-3.6-flash"

# ── Result container ─────────────────────────────────────────────────────────
class LLMResult(NamedTuple):
    value: Any          # the structured/text result
    source: str         # "gemini" | "fallback"
    error: Optional[str]  # None for success; error description when fallback triggered by API failure


# ── Service ──────────────────────────────────────────────────────────────────
class LLMService:
    """
    Centralized LLM adapter using the google-genai SDK (google.genai >= 1.0).

    Initialization is silent about the API key value — it only logs
    whether Gemini is configured (YES/NO) and which model will be used.

    Call test_gemini_connection() once at startup to verify live connectivity.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv("GEMINI_MODEL", model_name or DEFAULT_MODEL)
        self.client = None
        self._configured = False   # key present + non-placeholder
        self._connected = False    # live API call succeeded at least once
        self._init_client()

    # ── Initialization ────────────────────────────────────────────────────
    def _init_client(self) -> None:
        placeholder = {"", "your_gemini_api_key_here"}
        if not self.api_key or self.api_key in placeholder:
            logger.info("[LLMService] Gemini configured: NO  (no API key)  |  Fallback: ACTIVE")
            return

        self._configured = True
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info(
                "[LLMService] Gemini configured: YES  |  Model: %s  |  Fallback: ACTIVE",
                self.model_name,
            )
        except Exception as exc:
            logger.warning(
                "[LLMService] Gemini client init failed: %s  |  Fallback: ACTIVE", exc
            )
            self.client = None

    # ── Startup config summary ────────────────────────────────────────────
    def startup_summary(self) -> Dict[str, str]:
        """Return a dict suitable for printing at app startup (no secrets)."""
        return {
            "Gemini configured": "YES" if self._configured else "NO",
            "Gemini model":      self.model_name if self._configured else "N/A",
            "Gemini connected":  "YES" if self._connected else "UNKNOWN (not tested yet)",
            "Fallback available": "YES",
        }

    # ── Connection diagnostic ─────────────────────────────────────────────
    def test_gemini_connection(self) -> Dict[str, Any]:
        """
        Make ONE minimal Gemini request to verify live connectivity.
        Returns a dict with: success, model, response_preview, error.
        Safe to call once at startup; do NOT call in a loop.
        """
        if not self.client:
            return {
                "success": False,
                "model": self.model_name,
                "response_preview": None,
                "error": "Gemini client not initialized (no valid API key or import failed)",
            }
        try:
            raw = self._raw_generate("Reply with exactly: PATHFINDER_OK")
            if raw and "PATHFINDER_OK" in raw:
                self._connected = True
                return {
                    "success": True,
                    "model": self.model_name,
                    "response_preview": raw[:80],
                    "error": None,
                }
            self._connected = True  # got a response, even if not exact
            return {
                "success": True,
                "model": self.model_name,
                "response_preview": (raw or "")[:80],
                "error": None,
            }
        except Exception as exc:
            return {
                "success": False,
                "model": self.model_name,
                "response_preview": None,
                "error": str(exc),
            }

    # ── Internal raw generate ─────────────────────────────────────────────
    def _raw_generate(self, prompt: str) -> Optional[str]:
        """Call Gemini and return raw text. Returns None on any failure."""
        if not self.client:
            return None
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text
        except Exception as exc:
            logger.error("[LLMService] Gemini API error (%s): %s", self.model_name, exc)
            return None

    # ── Public: Goal Extraction ───────────────────────────────────────────
    def extract_goal_and_constraints(self, user_message: str) -> LLMResult:
        """
        Extract structured goal JSON from conversational user input.

        Returns LLMResult:
          source = "gemini"   → real Gemini response, validated
          source = "fallback" → deterministic extraction; error describes reason
        """
        prompt = f"""Extract the following JSON fields from the user's career learning goal:
- target_role: string (e.g. "Data Scientist", "Machine Learning Engineer", "Full-Stack AI Developer")
- timeline_months: integer (e.g. 6)
- weekly_hours: float (e.g. 8.0)
- interests: list of strings

CRITICAL: If the user mentions a CURRENT role AND a TARGET desire, extract only the TARGET role.

User input: "{user_message}"
Output ONLY valid JSON — no markdown, no explanation."""

        raw = self._raw_generate(prompt)
        if raw:
            parsed, parse_error = self._parse_goal_json(raw)
            if parsed:
                self._connected = True
                logger.info("[LLMService] Goal extraction: GEMINI_SUCCESS (model=%s)", self.model_name)
                return LLMResult(value=parsed, source="gemini", error=None)
            else:
                logger.warning(
                    "[LLMService] Gemini returned unparseable goal JSON: %s | falling back", parse_error
                )
                fallback_val = self._fallback_extract_goal(user_message)
                return LLMResult(
                    value=fallback_val,
                    source="fallback",
                    error=f"Gemini JSON parse failed: {parse_error}",
                )

        # Gemini unavailable or returned None
        reason = "Gemini client not available" if not self.client else "Gemini returned empty response"
        logger.warning("[LLMService] Goal extraction: GEMINI_FAILURE — %s — using fallback", reason)
        return LLMResult(
            value=self._fallback_extract_goal(user_message),
            source="fallback",
            error=reason,
        )

    def _parse_goal_json(self, raw: str) -> tuple:
        """Try to parse Gemini goal JSON. Returns (dict, None) or (None, error_str)."""
        # Strip markdown fences if present
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return None, "no JSON object found in response"
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            return None, f"JSONDecodeError: {e}"
        # Validate required fields
        required = {"target_role", "timeline_months", "weekly_hours", "interests"}
        missing = required - data.keys()
        if missing:
            return None, f"missing fields: {missing}"
        # Type coercion / sanity
        try:
            data["timeline_months"] = int(data["timeline_months"])
            data["weekly_hours"] = float(data["weekly_hours"])
            if not isinstance(data["interests"], list):
                data["interests"] = [str(data["interests"])]
        except (ValueError, TypeError) as e:
            return None, f"type coercion failed: {e}"
        return data, None

    def _fallback_extract_goal(self, user_message: str) -> Dict[str, Any]:
        """Deterministic regex-based goal extraction — always returns a valid dict."""
        msg = user_message.lower()
        result = {
            "target_role": "Machine Learning Engineer",
            "timeline_months": 6,
            "weekly_hours": 8.0,
            "interests": ["Machine Learning", "Applied AI"],
        }

        # Extract target intent clause
        target_clause = msg
        for pattern in [
            r"(?:want to become|want to be|become|transition to|goal is|aiming to be|aspire to be|moving into)\s+(?:a\s+|an\s+)?([a-z\s\-\/]+?)(?:\s+(?:specialising|focusing|working|and|with|in\s+\d)|$)",
        ]:
            m = re.search(pattern, msg)
            if m:
                target_clause = m.group(1).strip()
                break

        if "data scien" in target_clause or "data analyst" in target_clause:
            result["target_role"] = "Data Scientist"
            result["interests"] = ["Data Analysis", "Statistics", "ML Modeling", "Pandas"]
        elif ("full" in target_clause and "stack" in target_clause) or "fullstack" in target_clause:
            result["target_role"] = "Full-Stack AI Developer"
            result["interests"] = ["Web Dev", "FastAPI", "LLMs", "RAG"]
        elif "machine learning" in target_clause or "ml engineer" in target_clause:
            result["target_role"] = "Machine Learning Engineer"
            result["interests"] = ["Machine Learning", "Neural Networks", "Deep Learning"]

        # Also scan full message for role keywords if target clause didn't match
        if "data scien" in msg and result["target_role"] == "Machine Learning Engineer":
            result["target_role"] = "Data Scientist"
            result["interests"] = ["Data Analysis", "Statistics", "ML Modeling"]
        elif "full-stack ai" in msg or "fullstack ai" in msg:
            result["target_role"] = "Full-Stack AI Developer"

        tm = re.search(r"(\d+)\s*(month|year)", msg)
        if tm:
            val, unit = int(tm.group(1)), tm.group(2)
            result["timeline_months"] = val * 12 if "year" in unit else val

        hm = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:a\s+week|per\s+week|weekly|week)?", msg)
        if hm:
            result["weekly_hours"] = float(hm.group(1))

        return result

    # ── Public: AI Tutor ──────────────────────────────────────────────────
    def answer_tutoring_query(
        self,
        query: str,
        profile: LearnerProfile,
        current_roadmap: Optional[Roadmap],
        knowledge_states: Dict[str, KnowledgeState],
        gap_report: Optional[GapReport],
        skill_graph: Optional[SkillGraph],
    ) -> LLMResult:
        """
        Answer a learner question grounded in their actual learner model.

        Returns LLMResult:
          source = "gemini"   → real Gemini tutor response
          source = "fallback" → pattern-matched deterministic answer
        """
        weak_skills = [
            ks.skill_name for ks in knowledge_states.values()
            if ks.status in ["weak", "needs_improvement"]
        ]
        bottlenecks = [
            skill_graph.nodes[sid].name
            for sid in (gap_report.unresolved_prerequisites if gap_report else [])
            if skill_graph and sid in skill_graph.nodes
        ]
        current_stage = (
            current_roadmap.stages[0].title
            if current_roadmap and current_roadmap.stages
            else "Prerequisite Foundations"
        )
        roadmap_version = current_roadmap.version if current_roadmap else 1

        prompt = f"""You are the XCL PathFinder AI Tutor. Be concise, specific, and encouraging.
Answer based ONLY on the learner's actual state below — never invent URLs or scores.

LEARNER STATE:
- Name: {profile.name}
- Current Role: {profile.current_role}
- Weekly Hours: {profile.weekly_hours}h/week | Timeline: {profile.timeline_months} months
- Roadmap Version: v{roadmap_version} | Current Stage: {current_stage}
- Weak Skills: {', '.join(weak_skills) if weak_skills else 'None detected'}
- Bottlenecks: {', '.join(bottlenecks) if bottlenecks else 'None'}

QUESTION: {query}

ANSWER (2-4 sentences, grounded in learner state):"""

        raw = self._raw_generate(prompt)
        if raw and len(raw.strip()) > 20:
            self._connected = True
            logger.info("[LLMService] AI Tutor: GEMINI_SUCCESS (model=%s)", self.model_name)
            return LLMResult(value=raw.strip(), source="gemini", error=None)

        reason = "Gemini client not available" if not self.client else "Gemini returned empty/short response"
        logger.warning("[LLMService] AI Tutor: GEMINI_FAILURE — %s — using fallback", reason)
        return LLMResult(
            value=self._fallback_tutor(query, profile, current_roadmap),
            source="fallback",
            error=reason,
        )

    def _fallback_tutor(
        self,
        query: str,
        profile: LearnerProfile,
        current_roadmap: Optional[Roadmap],
    ) -> str:
        """Deterministic pattern-matched tutor responses."""
        q = query.lower()
        name = profile.name or "Learner"
        stage = (
            current_roadmap.stages[0].title
            if current_roadmap and current_roadmap.stages
            else "Prerequisite Foundations"
        )
        version = current_roadmap.version if current_roadmap else 1

        if "why" in q and ("probability" in q or "prereq" in q or "before" in q or "recommend" in q):
            return (
                f"Great question, {name}! Probability & Statistics is a strict prerequisite for "
                f"Classical ML algorithms (Naive Bayes, Logistic Regression, MLE). Your diagnostic "
                f"score showed a gap here, so the roadmap places it first to prevent you getting "
                f"stuck on mathematical derivations later."
            )
        if "bayes" in q or ("probability" in q and "ml" in q):
            return (
                "Bayes' Theorem: P(A|B) = P(B|A)*P(A)/P(B). In ML it powers Naive Bayes classifiers, "
                "Bayesian hyperparameter optimisation, and MAP estimation — foundational before probabilistic models."
            )
        if "overfit" in q or "variance" in q or "bias" in q:
            return (
                "Overfitting (high variance) = model memorises training noise. "
                "Fixes: L1/L2 regularisation, Dropout, K-Fold CV, more data, or reduced model complexity."
            )
        if "skip" in q or "fast track" in q or "already know" in q:
            return (
                f"You can request a checkpoint re-test in the Assessment tab at any time, {name}. "
                f"If you demonstrate proficiency above the target threshold, that stage is automatically "
                f"marked adequate and the roadmap skips it."
            )
        if "sql" in q or "excel" in q or "existing" in q or "transfer" in q:
            return (
                f"Your existing skills are a genuine advantage, {name}! SQL maps directly to Pandas "
                f"DataFrames; Excel formulas map to NumPy arrays. Start with Python data manipulation "
                f"before ML — your analytical mindset will accelerate this phase significantly."
            )
        if "mlops" in q or "docker" in q or "deploy" in q or "kubernetes" in q:
            return (
                f"MLOps is the bridge between your DevOps background and ML Engineering, {name}. "
                f"Docker, CI/CD, and Kubernetes transfer directly to ML serving, experiment tracking "
                f"(MLflow), and model monitoring — your background makes the MLOps stage your fastest."
            )
        if "vector" in q or "rag" in q or ("rest" in q and "api" in q):
            return (
                "A REST API (e.g. FastAPI) serves your AI logic over HTTP. A Vector Database "
                "(e.g. Pinecone, Chroma) stores text embeddings for semantic retrieval. "
                "Together they form a RAG (Retrieval-Augmented Generation) system."
            )
        if "maths" in q or ("math" in q and "teacher" in q) or "statistics" in q:
            return (
                f"As a maths teacher, {name}, you already have the hardest prerequisite covered! "
                f"Your probability/statistics knowledge means you can move through that stage quickly. "
                f"Expect to reach your first real ML models within 6-8 weeks of starting Python."
            )
        if "phd" in q or "researcher" in q or "theory" in q:
            return (
                f"Your theoretical depth is a major asset, {name}. Focus your energy on the "
                f"engineering stages: MLOps, model serving (FastAPI + Docker), and experiment tracking. "
                f"You can fast-track the foundational math and classical ML stages via checkpoint tests."
            )
        return (
            f"I have reviewed your current roadmap (v{version}). "
            f"Your immediate focus is {stage}. "
            f"Mark milestones complete or give me feedback (e.g. 'this is too difficult') "
            f"and I will adapt your roadmap in real-time!"
        )
