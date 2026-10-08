import unittest
from core.services.assessment_service import AssessmentService
from core.services.knowledge_service import KnowledgeStateEngine
from core.services.graph_service import GraphService
from core.schemas.assessment import AssessmentAttempt

class TestAssessmentScoring(unittest.TestCase):
    def test_assessment_scoring_and_evidence(self):
        graph_svc = GraphService("data/skills")
        graph = graph_svc.get_graph("goal_ml_engineer")
        assess_svc = AssessmentService("data/assessment/assessment_bank.json")
        knowledge_eng = KnowledgeStateEngine(assess_svc)

        attempts = [
            AssessmentAttempt(
                attempt_id="att_1",
                learner_id="test_user",
                goal_id="goal_ml_engineer",
                item_id="q_py_01",
                skill_id="py_core",
                answer="Expression B uses lazy evaluation and produces items on-demand, consuming minimal memory, while Expression A builds the entire list in memory at once.",
                correct=True
            ),
            AssessmentAttempt(
                attempt_id="att_2",
                learner_id="test_user",
                goal_id="goal_ml_engineer",
                item_id="q_py_02",
                skill_id="py_core",
                answer="O(1) average constant time using hash tables",
                correct=True
            ),
            AssessmentAttempt(
                attempt_id="att_3",
                learner_id="test_user",
                goal_id="goal_ml_engineer",
                item_id="q_prob_01",
                skill_id="math_prob_stats",
                answer="Approx. 95%",  # Incorrect
                correct=False
            )
        ]

        states = knowledge_eng.compute_knowledge_states(graph, attempts, {"py_core": 0.8, "math_prob_stats": 0.9})
        
        # Python demonstrated score should be 1.0 (adequate)
        self.assertEqual(states["py_core"].demonstrated_score, 1.0)
        self.assertEqual(states["py_core"].status, "adequate")

        # Probability demonstrated score should be 0.0 (weak) despite high self-report (0.9)
        self.assertEqual(states["math_prob_stats"].demonstrated_score, 0.0)
        self.assertEqual(states["math_prob_stats"].status, "weak")

if __name__ == "__main__":
    unittest.main()
