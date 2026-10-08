import unittest
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.dependencies import get_store

class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.store = get_store()
        self.store.reset_to_default_persona()

    def test_01_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gemini_model", data)

    def test_02_profile_flow(self):
        # GET default
        get_resp = self.client.get("/api/profile")
        self.assertEqual(get_resp.status_code, 200)

        # PUT update
        payload = {
            "name": "Alex Chen",
            "current_role": "Biology Student",
            "interests": ["Machine Learning", "Bioinformatics"],
            "weekly_hours": 8.0,
            "timeline_months": 6,
            "self_reported_skills": {"py_core": 0.8, "math_prob_stats": 0.8},
            "content_preferences": ["projects", "interactive"]
        }
        put_resp = self.client.put("/api/profile", json=payload)
        self.assertEqual(put_resp.status_code, 200)
        data = put_resp.json()
        self.assertEqual(data["name"], "Alex Chen")
        self.assertEqual(self.store.profile.name, "Alex Chen")

    def test_03_goal_flow(self):
        # Catalog
        cat_resp = self.client.get("/api/goal/catalog")
        self.assertEqual(cat_resp.status_code, 200)
        catalog = cat_resp.json()
        self.assertGreater(len(catalog), 0)

        # Extract
        extract_resp = self.client.post(
            "/api/goal/extract",
            json={"user_prompt": "I want to become a Data Scientist in 6 months with 8 hours weekly."}
        )
        self.assertEqual(extract_resp.status_code, 200)
        data = extract_resp.json()
        self.assertIn("goal_state", data)
        self.assertTrue(data["goal_state"]["active"])

    def test_04_skill_graph(self):
        resp = self.client.get("/api/skill-graph/goal_data_scientist")
        self.assertEqual(resp.status_code, 200)
        graph = resp.json()
        self.assertIn("nodes", graph)
        self.assertGreater(len(graph["nodes"]), 0)

    def test_05_assessment_and_complete(self):
        # Get items
        items_resp = self.client.get("/api/assessment")
        self.assertEqual(items_resp.status_code, 200)
        items = items_resp.json()
        self.assertGreater(len(items), 0)

        # Submit attempts and complete
        attempts = [
            {"item_id": "q_py_01", "answer": "Expression B uses lazy evaluation and produces items on-demand, consuming minimal memory, while Expression A builds the entire list in memory at once."},
            {"item_id": "q_prob_01", "answer": "Wrong Answer"}
        ]
        complete_resp = self.client.post("/api/assessment/complete", json={"attempts": attempts})
        self.assertEqual(complete_resp.status_code, 200)
        data = complete_resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("knowledge_states", data)
        self.assertIn("roadmap_v1", data)

    def test_06_gaps_and_roadmap(self):
        # Set up store with assessment
        self.test_05_assessment_and_complete()

        # Check gaps
        gap_resp = self.client.get("/api/gaps")
        self.assertEqual(gap_resp.status_code, 200)
        gaps = gap_resp.json()
        self.assertIsNotNone(gaps)

        # Check roadmap
        rd_resp = self.client.get("/api/roadmap")
        self.assertEqual(rd_resp.status_code, 200)
        roadmap = rd_resp.json()
        self.assertEqual(roadmap["version"], 1)
        self.assertGreater(len(roadmap["stages"]), 0)

    def test_07_tutor_and_adaptation(self):
        self.test_05_assessment_and_complete()

        # Regular tutor query
        tut_resp = self.client.post("/api/tutor/chat", json={"query": "Explain Bayes Theorem in ML"})
        self.assertEqual(tut_resp.status_code, 200)
        data = tut_resp.json()
        self.assertIn("reply", data)
        self.assertFalse(data["is_adaptation"])

        # Adaptation trigger query
        adapt_resp = self.client.post(
            "/api/tutor/chat",
            json={"query": "Probability is too difficult and I only have 30 minutes daily."}
        )
        self.assertEqual(adapt_resp.status_code, 200)
        adapt_data = adapt_resp.json()
        self.assertTrue(adapt_data["is_adaptation"])
        self.assertEqual(self.store.current_roadmap_version, 2)

    def test_08_dashboard(self):
        self.test_05_assessment_and_complete()
        dash_resp = self.client.get("/api/dashboard")
        self.assertEqual(dash_resp.status_code, 200)
        data = dash_resp.json()
        self.assertIn("progress_percentage", data)
        self.assertIn("knowledge_states", data)
        self.assertIn("current_roadmap", data)

    def test_09_presets(self):
        load_resp = self.client.post("/api/presets/load/kenji")
        self.assertEqual(load_resp.status_code, 200)
        data = load_resp.json()
        self.assertEqual(data["profile"]["name"], "Kenji Tanaka")

        reset_resp = self.client.post("/api/presets/reset")
        self.assertEqual(reset_resp.status_code, 200)
        self.assertEqual(self.store.profile.name, "")

if __name__ == "__main__":
    unittest.main()
