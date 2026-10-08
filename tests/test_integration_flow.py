import unittest
import uuid
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

class TestEndToEndIntegrationFlow(unittest.TestCase):
    """
    End-to-end integration test covering the entire source-of-truth lifecycle:
    Profile -> Goal Discovery -> Assessment -> Knowledge State -> Gap Analysis ->
    Roadmap v1 -> AI Tutor -> Feedback -> Continuous Adaptation (Roadmap v2).
    """
    def setUp(self):
        self.store = InMemoryStore()
        self.graph_service = GraphService(data_dir="data/skills")
        self.assessment_service = AssessmentService(data_path="data/assessment/assessment_bank.json")
        self.knowledge_engine = KnowledgeStateEngine(assessment_service=self.assessment_service)
        self.gap_analyzer = GapAnalyzer(graph_service=self.graph_service)
        self.recommender = RecommendationEngine(catalog_path="data/resources/resources_catalog.json")
        self.roadmap_engine = RoadmapEngine(graph_service=self.graph_service, recommender=self.recommender)
        self.adaptation_engine = AdaptationEngine(
            gap_analyzer=self.gap_analyzer,
            roadmap_engine=self.roadmap_engine,
            recommender=self.recommender
        )
        self.llm_service = LLMService()

    def test_full_custom_learner_lifecycle(self):
        # 1. Profile Creation
        self.store.profile = LearnerProfile(
            learner_id="test_user_01",
            name="Test User",
            email="test.user@example.com",
            current_role="Full-Stack Developer",
            interests=["Data Analysis", "Machine Learning"],
            self_reported_skills={"math_prob_stats": 0.80, "py_core": 0.90},
            weekly_hours=5.0,
            timeline_months=6,
            content_preferences=["interactive", "projects"]
        )
        self.assertEqual(self.store.profile.name, "Test User")
        self.assertEqual(self.store.profile.weekly_hours, 5.0)

        # 2. Conversational Goal Discovery
        user_msg = "I am currently a full-stack developer and I want to become an industry-ready Data Scientist within 6 months."
        extracted = self.llm_service.extract_goal_and_constraints(user_msg)
        self.assertEqual(extracted.value["target_role"], "Data Scientist")
        self.assertEqual(extracted.value["timeline_months"], 6)

        # Activate Goal State
        self.store.goal_state = GoalState(
            goal_id="goal_data_scientist",
            target_role="Data Scientist",
            timeline_months=6,
            weekly_hours=5.0,
            target_proficiency_by_skill={"math_prob_stats": 0.85, "py_core": 0.85, "ml_foundations": 0.85},
            active=True
        )

        # 3. Assessment Delivery & Scoring
        graph = self.graph_service.get_graph(self.store.goal_state.goal_id)
        self.assertIsNotNone(graph)

        # User scores high on Python, fails Probability
        self.store.assessment_attempts = [
            AssessmentAttempt(
                attempt_id="att_01",
                learner_id="test_user_01",
                goal_id="goal_data_scientist",
                item_id="q_py_01",
                skill_id="py_core",
                answer="Expression B uses lazy evaluation and produces items on-demand, consuming minimal memory, while Expression A builds the entire list in memory at once.",
                correct=True
            ),
            AssessmentAttempt(
                attempt_id="att_02",
                learner_id="test_user_01",
                goal_id="goal_data_scientist",
                item_id="q_prob_01",
                skill_id="math_prob_stats",
                answer="Approx. 95%",  # Incorrect
                correct=False
            )
        ]

        # 4. Knowledge State Engine Execution
        k_states = self.knowledge_engine.compute_knowledge_states(
            skill_graph=graph,
            attempts=self.store.assessment_attempts,
            self_reported_skills=self.store.profile.self_reported_skills
        )
        self.store.knowledge_states = k_states
        self.assertEqual(k_states["py_core"].status, "adequate")
        self.assertEqual(k_states["math_prob_stats"].status, "weak")
        self.assertEqual(k_states["math_prob_stats"].demonstrated_score, 0.0)

        # 5. Gap Analysis Execution
        gap_rep = self.gap_analyzer.analyze_gaps(
            goal_id=self.store.goal_state.goal_id,
            knowledge_states=k_states,
            self_reported_skills=self.store.profile.self_reported_skills
        )
        self.store.gap_report = gap_rep
        self.assertIn("math_prob_stats", gap_rep.unresolved_prerequisites)
        self.assertIn("math_prob_stats", gap_rep.weak_skills)

        # 6. Roadmap v1 Generation
        roadmap_v1 = self.roadmap_engine.generate_roadmap(
            goal_id=self.store.goal_state.goal_id,
            profile=self.store.profile,
            knowledge_states=k_states,
            gap_report=gap_rep,
            version=1
        )
        self.store.save_roadmap(roadmap_v1)
        self.assertEqual(roadmap_v1.version, 1)
        self.assertTrue(len(roadmap_v1.stages) > 0)
        # Verify Probability is Stage 1 priority bottleneck
        self.assertIn("Probability", roadmap_v1.stages[0].title)

        # 7. AI Tutor Query Grounded Execution
        tutor_answer = self.llm_service.answer_tutoring_query(
            query="Why did you recommend Probability before ML?",
            profile=self.store.profile,
            current_roadmap=roadmap_v1,
            knowledge_states=k_states,
            gap_report=gap_rep,
            skill_graph=graph
        )
        self.assertIn("Probability", tutor_answer.value)
        self.assertIn(tutor_answer.source, ("gemini", "fallback"),
                      "Tutor result source must be 'gemini' or 'fallback'")

        # 8. Feedback Event & Dynamic Adaptation (Roadmap v2)
        feedback_event = FeedbackEvent(
            feedback_id="fb_01",
            learner_id="test_user_01",
            source="chat",
            type="difficulty",
            target_id="math_prob_stats",
            message="Probability is too difficult and I only have 30 minutes per day."
        )
        self.store.record_feedback(feedback_event)

        roadmap_v2, reason = self.adaptation_engine.process_feedback(
            event=feedback_event,
            profile=self.store.profile,
            knowledge_states=k_states,
            current_roadmap=roadmap_v1
        )
        self.store.save_roadmap(roadmap_v2)

        # Verify Roadmap v2 is created with updated weekly hours and diff explanation
        self.assertEqual(roadmap_v2.version, 2)
        self.assertEqual(self.store.current_roadmap_version, 2)
        self.assertIsNotNone(roadmap_v2.adaptation_diff)
        self.assertIn("v1", roadmap_v2.adaptation_diff["version_from"])
        self.assertIn("v2", roadmap_v2.adaptation_diff["version_to"])
        self.assertLess(self.store.profile.weekly_hours, 5.0)

if __name__ == "__main__":
    unittest.main()
