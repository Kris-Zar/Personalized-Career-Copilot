"""
tests/test_llm_service.py
=========================
Unit tests for LLMService — distinguishes real Gemini vs deterministic fallback.

TEST A: Gemini configured + successful response  → source == "gemini"
TEST B: Gemini unavailable (no key)              → source == "fallback"
TEST C: Gemini returns malformed JSON            → validation fails, safe fallback

All tests use mocking — NO live API calls in this file.
For live verification, run: python scripts/diagnose_gemini.py
"""

import unittest
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.services.llm_service import LLMService, LLMResult
from core.schemas.profile import LearnerProfile


# ── Helpers ──────────────────────────────────────────────────────────────────
def _make_profile(name="Test User", role="Student"):
    return LearnerProfile(
        learner_id="test_001",
        name=name,
        current_role=role,
        weekly_hours=8.0,
        timeline_months=6,
        self_reported_skills={},
        content_preferences=[],
        interests=[],
    )


VALID_GOAL_JSON = '{"target_role": "Data Scientist", "timeline_months": 6, "weekly_hours": 10.0, "interests": ["ML", "Stats"]}'
MALFORMED_GOAL_JSON = '{"target_role": "Data Scientist", "timeline_months": "not_a_number"}'
INCOMPLETE_GOAL_JSON = '{"target_role": "Data Scientist"}'  # missing required fields
GARBAGE_RESPONSE = "Sure! Here is your goal: blah blah blah no JSON here at all."
SHORT_TUTOR_RESPONSE = "ok"  # too short to count as real answer
VALID_TUTOR_RESPONSE = (
    "Based on your weak Python skills, I recommend starting with basic data types, "
    "then Pandas operations before tackling scikit-learn. This addresses your Stage 1 bottleneck."
)


# ════════════════════════════════════════════════════════════════════════════
# TEST A — Gemini configured + successful response
# ════════════════════════════════════════════════════════════════════════════
class TestGeminiSuccess(unittest.TestCase):
    """TEST A: When Gemini is configured and returns valid data."""

    def _make_service_with_mock_client(self, raw_response: str) -> LLMService:
        svc = LLMService.__new__(LLMService)
        svc.api_key = "fake_key_for_test"
        svc.model_name = "gemini-test-model"
        svc._configured = True
        svc._connected = False
        # Create a mock client whose models.generate_content returns the given text
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = raw_response
        mock_client.models.generate_content.return_value = mock_response
        svc.client = mock_client
        return svc

    def test_A1_goal_extraction_source_is_gemini(self):
        """Goal extraction with valid Gemini JSON → source == 'gemini'"""
        svc = self._make_service_with_mock_client(VALID_GOAL_JSON)
        result = svc.extract_goal_and_constraints("I want to become a Data Scientist in 6 months")
        self.assertIsInstance(result, LLMResult)
        self.assertEqual(result.source, "gemini",
            "Expected source='gemini' when Gemini returns valid JSON")
        self.assertIsNone(result.error)
        self.assertEqual(result.value["target_role"], "Data Scientist")
        self.assertEqual(result.value["timeline_months"], 6)
        self.assertEqual(result.value["weekly_hours"], 10.0)
        self.assertIsInstance(result.value["interests"], list)

    def test_A2_tutor_source_is_gemini(self):
        """AI Tutor with valid Gemini response → source == 'gemini'"""
        svc = self._make_service_with_mock_client(VALID_TUTOR_RESPONSE)
        profile = _make_profile()
        result = svc.answer_tutoring_query(
            query="Why is Python listed first in my roadmap?",
            profile=profile,
            current_roadmap=None,
            knowledge_states={},
            gap_report=None,
            skill_graph=None,
        )
        self.assertEqual(result.source, "gemini",
            "Expected source='gemini' when Gemini returns valid tutor text")
        self.assertIsNone(result.error)
        self.assertGreater(len(result.value), 20)

    def test_A3_gemini_result_never_empty(self):
        """Gemini result value must never be None or empty string."""
        svc = self._make_service_with_mock_client(VALID_GOAL_JSON)
        result = svc.extract_goal_and_constraints("want to be an ML Engineer in 4 months, 10h/week")
        self.assertIsNotNone(result.value)
        self.assertIn("target_role", result.value)


# ════════════════════════════════════════════════════════════════════════════
# TEST B — Gemini unavailable → fallback executes
# ════════════════════════════════════════════════════════════════════════════
class TestGeminiFallback(unittest.TestCase):
    """TEST B: When Gemini is unavailable, fallback activates and is correctly labeled."""

    def _make_no_key_service(self) -> LLMService:
        """Service with no API key — client stays None."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GEMINI_MODEL": "test-model"}):
            svc = LLMService(api_key="")
        return svc

    def test_B1_no_key_goal_extraction_source_is_fallback(self):
        """No API key → goal extraction source == 'fallback'"""
        svc = self._make_no_key_service()
        self.assertIsNone(svc.client)
        result = svc.extract_goal_and_constraints(
            "I want to become a Data Scientist in 8 months, 10 hours a week"
        )
        self.assertEqual(result.source, "fallback",
            "Must label as 'fallback' when Gemini client is None")
        self.assertIsNotNone(result.error)
        # But the value must still be usable
        self.assertIn("target_role", result.value)

    def test_B2_no_key_tutor_source_is_fallback(self):
        """No API key → AI Tutor source == 'fallback'"""
        svc = self._make_no_key_service()
        profile = _make_profile()
        result = svc.answer_tutoring_query(
            query="What should I study first?",
            profile=profile,
            current_roadmap=None,
            knowledge_states={},
            gap_report=None,
            skill_graph=None,
        )
        self.assertEqual(result.source, "fallback")
        self.assertIsNotNone(result.error)
        self.assertGreater(len(result.value), 10)

    def test_B3_api_error_triggers_fallback(self):
        """API call raises exception → source == 'fallback', not mislabeled as gemini"""
        svc = LLMService.__new__(LLMService)
        svc.api_key = "fake_key"
        svc.model_name = "test-model"
        svc._configured = True
        svc._connected = False
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("404 NOT_FOUND")
        svc.client = mock_client

        result = svc.extract_goal_and_constraints("I want to become a ML Engineer")
        self.assertEqual(result.source, "fallback",
            "API error must trigger fallback, not be reported as gemini success")
        self.assertIsNotNone(result.error)

    def test_B4_fallback_role_extraction_data_scientist(self):
        """Fallback correctly extracts Data Scientist target role."""
        svc = self._make_no_key_service()
        result = svc.extract_goal_and_constraints(
            "I am a nurse and I want to become a Data Scientist in 9 months"
        )
        self.assertIn("Data Scientist", result.value["target_role"])
        self.assertEqual(result.source, "fallback")

    def test_B5_fallback_role_extraction_fullstack(self):
        """Fallback correctly extracts Full-Stack AI Developer."""
        svc = self._make_no_key_service()
        result = svc.extract_goal_and_constraints(
            "I want to become a Full-Stack AI Developer in 4 months with 12 hours a week"
        )
        self.assertIn("Full-Stack", result.value["target_role"])
        self.assertEqual(result.value["timeline_months"], 4)
        self.assertEqual(result.value["weekly_hours"], 12.0)


# ════════════════════════════════════════════════════════════════════════════
# TEST C — Gemini returns malformed/incomplete JSON
# ════════════════════════════════════════════════════════════════════════════
class TestGeminiMalformedOutput(unittest.TestCase):
    """TEST C: Gemini returns bad structured output → safe fallback, no corruption."""

    def _make_service_with_mock_response(self, raw: str) -> LLMService:
        svc = LLMService.__new__(LLMService)
        svc.api_key = "fake_key"
        svc.model_name = "test-model"
        svc._configured = True
        svc._connected = False
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = raw
        mock_client.models.generate_content.return_value = mock_response
        svc.client = mock_client
        return svc

    def test_C1_garbage_response_triggers_fallback(self):
        """Gemini returns no JSON at all → source == 'fallback', learner state not corrupted"""
        svc = self._make_service_with_mock_response(GARBAGE_RESPONSE)
        result = svc.extract_goal_and_constraints("I want to become a Data Scientist")
        self.assertEqual(result.source, "fallback")
        self.assertIsNotNone(result.error)
        # Value must still be a valid dict with required keys
        self.assertIn("target_role", result.value)
        self.assertIn("timeline_months", result.value)
        self.assertIn("weekly_hours", result.value)
        self.assertIn("interests", result.value)
        # Types must be safe
        self.assertIsInstance(result.value["timeline_months"], int)
        self.assertIsInstance(result.value["weekly_hours"], float)

    def test_C2_incomplete_json_triggers_fallback(self):
        """Gemini returns JSON missing required fields → safe fallback"""
        svc = self._make_service_with_mock_response(INCOMPLETE_GOAL_JSON)
        result = svc.extract_goal_and_constraints("I want to become a Data Scientist")
        self.assertEqual(result.source, "fallback")
        self.assertIsNotNone(result.error)
        self.assertIn("interests", result.value)  # fallback fills all fields

    def test_C3_malformed_types_trigger_fallback(self):
        """Gemini returns wrong type for timeline_months → safe fallback"""
        svc = self._make_service_with_mock_response(MALFORMED_GOAL_JSON)
        result = svc.extract_goal_and_constraints("I want to be a Data Scientist")
        # timeline_months = "not_a_number" should fail type coercion
        self.assertEqual(result.source, "fallback")
        # Learner state must always be type-safe
        self.assertIsInstance(result.value["timeline_months"], int)
        self.assertIsInstance(result.value["weekly_hours"], float)

    def test_C4_short_tutor_response_triggers_fallback(self):
        """Tutor response too short → fallback, not a corrupt short response"""
        svc = self._make_service_with_mock_response(SHORT_TUTOR_RESPONSE)
        profile = _make_profile()
        result = svc.answer_tutoring_query(
            query="What is probability?",
            profile=profile,
            current_roadmap=None,
            knowledge_states={},
            gap_report=None,
            skill_graph=None,
        )
        self.assertEqual(result.source, "fallback")
        self.assertGreater(len(result.value), 20,
            "Fallback tutor answer must be substantive, not just the short Gemini response")


# ════════════════════════════════════════════════════════════════════════════
# Diagnostic (non-API): Startup Summary
# ════════════════════════════════════════════════════════════════════════════
class TestStartupSummary(unittest.TestCase):
    """Verify startup_summary() never exposes the API key."""

    def test_startup_summary_no_key_configured(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GEMINI_MODEL": "test"}):
            svc = LLMService(api_key="")
        summary = svc.startup_summary()
        self.assertEqual(summary["Gemini configured"], "NO")
        self.assertEqual(summary["Fallback available"], "YES")
        # Key must not appear anywhere in summary
        for v in summary.values():
            self.assertNotIn("AIza", str(v))

    def test_startup_summary_with_key(self):
        svc = LLMService.__new__(LLMService)
        svc.api_key = "AIzaFakeKey123"
        svc.model_name = "gemini-test"
        svc._configured = True
        svc._connected = False
        svc.client = MagicMock()
        summary = svc.startup_summary()
        self.assertEqual(summary["Gemini configured"], "YES")
        self.assertEqual(summary["Gemini model"], "gemini-test")
        # Key value must NOT appear in summary
        for v in summary.values():
            self.assertNotIn("AIzaFakeKey123", str(v))


if __name__ == "__main__":
    unittest.main(verbosity=2)
