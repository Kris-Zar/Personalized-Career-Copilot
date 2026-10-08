import unittest
from core.services.graph_service import GraphService
from core.services.recommender import RecommendationEngine
from core.services.roadmap_engine import RoadmapEngine
from core.services.gap_analyzer import GapAnalyzer
from core.services.adaptation_engine import AdaptationEngine
from core.schemas.profile import LearnerProfile
from core.schemas.assessment import KnowledgeState, GapReport
from core.schemas.feedback import FeedbackEvent

class TestAdaptationFlow(unittest.TestCase):
    def test_continuous_adaptation_cycle(self):
        graph_svc = GraphService("data/skills")
        recommender = RecommendationEngine("data/resources/resources_catalog.json")
        roadmap_eng = RoadmapEngine(graph_svc, recommender)
        gap_analyzer = GapAnalyzer(graph_svc)
        adaptation_eng = AdaptationEngine(gap_analyzer, roadmap_eng, recommender)

        profile = LearnerProfile(learner_id="u1", name="Test User", weekly_hours=8.0)
        knowledge_states = {
            "math_prob_stats": KnowledgeState(skill_id="math_prob_stats", skill_name="Probability", demonstrated_score=0.2, status="needs_improvement")
        }
        gap_rep = GapReport(
            goal_id="goal_ml_engineer",
            skill_gaps={"math_prob_stats": 0.6},
            weak_skills=["math_prob_stats"],
            unresolved_prerequisites=["math_prob_stats"]
        )

        roadmap_v1 = roadmap_eng.generate_roadmap("goal_ml_engineer", profile, knowledge_states, gap_rep, version=1)
        self.assertEqual(roadmap_v1.version, 1)

        # Ingest Feedback Event
        feedback = FeedbackEvent(
            feedback_id="fb_01",
            learner_id="u1",
            source="chat",
            type="difficulty",
            target_id="math_prob_stats",
            message="Probability is too difficult and I only have 30 minutes today."
        )

        roadmap_v2, diff_summary = adaptation_eng.process_feedback(feedback, profile, knowledge_states, roadmap_v1)

        self.assertEqual(roadmap_v2.version, 2)
        self.assertIsNotNone(roadmap_v2.adaptation_diff)
        self.assertIn("difficulty bottleneck", diff_summary.lower())
        self.assertLess(profile.weekly_hours, 8.0)  # Reduced due to time constraint signal

if __name__ == "__main__":
    unittest.main()
