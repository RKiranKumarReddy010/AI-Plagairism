import unittest
import json
from src.app import create_app
from src.config import Config
from src.auth.session import session_manager


class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

        # Set up a test token in session_manager
        self.test_token_free = "test_free_token_123"
        session_manager.token_cache[self.test_token_free] = {
            "user_id": "usr_test_free",
            "premium": False
        }

        self.test_token_premium = "test_premium_token_456"
        session_manager.token_cache[self.test_token_premium] = {
            "user_id": "usr_test_premium",
            "premium": True
        }

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "healthy")

    def test_unauthorized_detect(self):
        resp = self.client.post("/api/usr_test_free/detect_ai", json={"text": "Hello world."})
        self.assertEqual(resp.status_code, 401)

    def test_detect_ai_free_user(self):
        headers = {"Authorization": f"Bearer {self.test_token_free}"}
        payload = {"text": "Furthermore, it is important to delve into the multifaceted framework of modern paradigm."}
        resp = self.client.post("/api/usr_test_free/detect_ai", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["is_premium"], False)
        self.assertIn("ai_score", data)
        self.assertIn("premium_upgrade_hint", data)

    def test_detect_ai_premium_user_returns_rectified_text(self):
        headers = {"Authorization": f"Bearer {self.test_token_premium}"}
        payload = {"text": "Furthermore, it is important to delve into the multifaceted framework of modern paradigm."}
        resp = self.client.post("/api/usr_test_premium/detect_ai", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["is_premium"], True)
        self.assertIn("rectified_text", data)
        self.assertIsNotNone(data["rectified_text"])
        self.assertIn("rectification_details", data)

    def test_scan_document_heatmap(self):
        headers = {"Authorization": Config.FIREBASE_API_KEY}
        doc_text = (
            "Paragraph one is written by a human. We tested the system yesterday and it worked.\n\n"
            "Furthermore, it is important to delve into the comprehensive framework of this phenomenon. "
            "Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems."
        )
        resp = self.client.post(
            f"/api/{Config.CURRENT_SERVER_ID}/scan_document",
            json={"text": doc_text},
            headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("sentence_heatmap", data)
        self.assertIn("rectified_text", data)  # API key gives premium access

    def test_rectify_text_endpoint(self):
        headers = {"Authorization": f"Bearer {self.test_token_premium}"}
        payload = {
            "text": (
                "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon. "
                "Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems."
            )
        }
        resp = self.client.post("/api/usr_test_premium/rectify_text", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("rectified_text", data)
        self.assertGreater(data["score_reduction"], 0)


if __name__ == "__main__":
    unittest.main()
