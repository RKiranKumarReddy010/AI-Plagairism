import unittest
from unittest.mock import patch, MagicMock
from src.app import create_app
from src.auth.session import session_manager


class TestPaymentAndWebPages(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

        # Mock user session
        self.token = "test_pay_token_999"
        session_manager.token_cache[self.token] = {
            "user_id": "usr_pay_test",
            "email": "paytest@example.com",
            "name": "Pay Test",
            "premium": False
        }

    def test_api_root_discovery(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("service", data)
        self.assertIn("endpoints", data)

    def test_health_check(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "healthy")

    def test_get_public_config(self):
        resp = self.client.get("/api/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("cashfree", data)
        self.assertIn("firebase", data)
        self.assertIn("pricing", data)

    @patch("src.services.payment_service.requests.post")
    def test_create_payment_order_mock(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "order_id": "order_mock_123",
            "payment_session_id": "session_mock_abc",
            "order_status": "ACTIVE",
            "order_amount": 499.0
        }
        mock_post.return_value = mock_resp

        headers = {"Authorization": f"Bearer {self.token}"}
        resp = self.client.post("/api/payment/create_order", json={"amount": 499}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["order"]["payment_session_id"], "session_mock_abc")

    @patch("src.services.payment_service.requests.get")
    def test_verify_payment_order_paid(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "order_id": "order_mock_123",
            "order_status": "PAID"
        }
        mock_get.return_value = mock_resp

        headers = {"Authorization": f"Bearer {self.token}"}
        resp = self.client.post("/api/payment/verify_order", json={"order_id": "order_mock_123"}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["data"]["premium"])


if __name__ == "__main__":
    unittest.main()
