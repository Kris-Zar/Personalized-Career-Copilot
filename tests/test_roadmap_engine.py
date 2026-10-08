import unittest
from core.services.graph_service import GraphService
from core.services.recommender import RecommendationEngine
from core.services.roadmap_engine import RoadmapEngine
from core.schemas.profile import LearnerProfile
from core.schemas.assessment import KnowledgeState, GapReport

class TestRoadmapEngine(unittest.TestCase):
    def test_roadmap_engine_generation(self):
        graph_svc = GraphService("data/skills")
        recommender = RecommendationEngine("data/resources/resources_catalog.json")
        roadmap_eng = RoadmapEngine(graph_svc, recommender)

        profile = LearnerProfile(learner_id="u1", name="Test User", weekly_hours=8.0)
        knowledge_states = {
            "math_prob_stats": KnowledgeState(skill_id="math_prob_stats", skill_name="Probability", demonstrated_score=0.0, status="weak")
        }
        gap_rep = GapReport(
            goal_id="goal_ml_engineer",
            skill_gaps={"math_prob_stats": 0.8},
            weak_skills=["math_prob_stats"],
            unresolved_prerequisites=["math_prob_stats"]
        )

        roadmap = roadmap_eng.generate_roadmap("goal_ml_engineer", profile, knowledge_states, gap_rep, version=1)

        self.assertEqual(roadmap.version, 1)
        self.assertGreater(len(roadmap.stages), 0)
        self.assertEqual(roadmap.stages[0].skill_targets, ["math_prob_stats"])
        self.assertIn("prerequisite bottleneck", roadmap.stages[0].rationale.lower())
        self.assertGreater(len(roadmap.stages[0].resources), 0)

if __name__ == "__main__":
    unittest.main()
