import unittest
from core.services.graph_service import GraphService

class TestGraphService(unittest.TestCase):
    def test_graph_loading(self):
        graph_svc = GraphService("data/skills")
        graph = graph_svc.get_graph("goal_ml_engineer")
        self.assertIsNotNone(graph)
        self.assertIn("py_core", graph.nodes)
        self.assertIn("ml_foundations", graph.nodes)

    def test_topological_ordering(self):
        graph_svc = GraphService("data/skills")
        order = graph_svc.topological_sort("goal_ml_engineer")
        self.assertEqual(len(order), 10)
        
        # Python & Math must precede ML Foundations
        self.assertLess(order.index("py_core"), order.index("py_data"))
        self.assertLess(order.index("py_data"), order.index("ml_foundations"))
        self.assertLess(order.index("math_prob_stats"), order.index("ml_foundations"))
        self.assertLess(order.index("ml_foundations"), order.index("dl_neural_nets"))

    def test_transitive_prerequisites(self):
        graph_svc = GraphService("data/skills")
        prereqs = graph_svc.get_all_prerequisites("goal_ml_engineer", "dl_neural_nets")
        self.assertIn("ml_foundations", prereqs)
        self.assertIn("math_calculus", prereqs)
        self.assertIn("py_data", prereqs)

if __name__ == "__main__":
    unittest.main()
