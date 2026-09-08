import time
import uuid
import re
import requests
from typing import Dict, Any, Tuple, Optional
from ..config import Config
from ..auth.session import session_manager


class CashfreePaymentService:
    """Cashfree Payment Gateway Integration for Subscription Orders & Verification."""

    def __init__(self):
        self.app_id = Config.CASHFREE_APP_ID
        self.secret_key = Config.CASHFREE_SECRET_KEY
        self.base_url = Config.CASHFREE_BASE_URL
        self.api_version = Config.CASHFREE_API_VERSION

    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-client-id": self.app_id,
            "x-client-secret": self.secret_key,
            "x-api-version": self.api_version,
            "Content-Type": "application/json"
        }

    def create_order(
        self,
        user_id: str,
        customer_email: str,
        customer_phone: Optional[str] = None,
        customer_name: Optional[str] = None,
        amount: Optional[float] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Creates a payment order with Cashfree and returns a payment_session_id."""
        if not self.app_id or not self.secret_key:
            return False, "Cashfree payment credentials missing.", None

        # Cashfree customer_id must be alphanumeric and between 3-50 chars
        clean_cust_id = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)[:45] or f"cust_{int(time.time())}"
        order_id = f"order_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        order_amount = amount or Config.PREMIUM_PRICE_INR

        # Default fallback phone if not provided
        clean_phone = re.sub(r'[^0-9]', '', customer_phone or "")
        if len(clean_phone) != 10:
            clean_phone = "9876543210"

        order_payload = {
            "order_id": order_id,
            "order_amount": round(order_amount, 2),
            "order_currency": "INR",
            "customer_details": {
                "customer_id": clean_cust_id,
                "customer_email": customer_email or "user@example.com",
                "customer_phone": clean_phone,
                "customer_name": customer_name or "Premium User"
            },
            "order_meta": {
                "return_url": f"http://127.0.0.1:5000/playground?order_id={order_id}"
            },
            "order_note": "AI Plagiarism & Text Rectifier Lifetime Premium Access"
        }

        url = f"{self.base_url}/orders"
        try:
            resp = requests.post(url, json=order_payload, headers=self._get_headers(), timeout=10)
            data = resp.json()

            if resp.status_code in (200, 201) and "payment_session_id" in data:
                return True, "Order created successfully.", {
                    "order_id": data["order_id"],
                    "payment_session_id": data["payment_session_id"],
                    "order_status": data.get("order_status", "ACTIVE"),
                    "order_amount": data.get("order_amount", order_amount),
                    "order_currency": data.get("order_currency", "INR"),
                    "environment": Config.CASHFREE_ENV
                }
            err_msg = data.get("message", f"Cashfree HTTP {resp.status_code}")
            return False, f"Cashfree error: {err_msg}", None
        except Exception as e:
            return False, f"Network error contacting Cashfree: {str(e)}", None

    def verify_order(self, order_id: str, user_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Queries Cashfree to verify payment status and activates premium if paid."""
        if not self.app_id or not self.secret_key:
            return False, "Cashfree payment credentials missing.", {}

        url = f"{self.base_url}/orders/{order_id}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            data = resp.json()

            if resp.status_code == 200:
                order_status = data.get("order_status")
                if order_status == "PAID":
                    # Activate premium for user
                    success, act_msg = session_manager.activate_premium(user_id=user_id)
                    return True, "Payment verified! Premium activated successfully.", {
                        "order_id": order_id,
                        "order_status": order_status,
                        "premium": True,
                        "activated": success
                    }
                else:
                    return False, f"Payment pending or not completed. Current status: {order_status}", {
                        "order_id": order_id,
                        "order_status": order_status,
                        "premium": False
                    }
            return False, f"Failed to fetch order details from Cashfree: {data.get('message')}", {}
        except Exception as e:
            return False, f"Error verifying order: {str(e)}", {}


cashfree_service = CashfreePaymentService()
