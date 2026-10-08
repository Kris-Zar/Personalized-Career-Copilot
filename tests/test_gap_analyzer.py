import unittest
from core.services.graph_service import GraphService
from core.services.gap_analyzer import GapAnalyzer
from core.schemas.assessment import KnowledgeState

class TestGapAnalyzer(unittest.TestCase):
    def test_gap_analyzer_bottleneck_detection(self):
        graph_svc = GraphService("data/skills")
        gap_analyzer = GapAnalyzer(graph_svc)

        # Simulate: Strong Python, Weak Probability
        knowledge_states = {
            "py_core": KnowledgeState(skill_id="py_core", skill_name="Python", demonstrated_score=1.0, status="adequate"),
            "math_prob_stats": KnowledgeState(skill_id="math_prob_stats", skill_name="Probability", demonstrated_score=0.0, status="weak")
        }

        gap_rep = gap_analyzer.analyze_gaps("goal_ml_engineer", knowledge_states, {"math_prob_stats": 0.85})
        
        self.assertIn("math_prob_stats", gap_rep.weak_skills)
        self.assertIn("math_prob_stats", gap_rep.unresolved_prerequisites)
        self.assertEqual(gap_rep.skill_gaps["math_prob_stats"], 0.80)

if __name__ == "__main__":
    unittest.main()
