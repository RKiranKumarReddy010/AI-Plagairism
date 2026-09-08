import json
import os
from flask import Blueprint, request, jsonify
from ..auth.session import session_manager
from ..services.doc_service import doc_service
from ..config import Config

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _authenticate_request(user_id: str):
    """Verifies that the request has a valid Bearer token or master API key

    and that the session corresponds to the requested user_id.
    """
    auth_header = request.headers.get("Authorization")
    session = session_manager.authenticate_header(auth_header)
    if not session:
        return None, (jsonify({"status": "error", "message": "Unauthorized."}), 401)

    is_api_key = session.get("is_api_key", False)
    if not is_api_key and session.get("user_id") != str(user_id):
        return None, (jsonify({"status": "error", "message": "Unauthorized."}), 401)

    return session, None


def _extract_raw_text() -> str:
    """Robust text extractor supporting JSON, form-data, plain text, and query parameters."""
    raw_text = None

    # Method 1: JSON body
    try:
        payload = request.get_json(silent=True) or {}
        raw_text = payload.get("text")
    except Exception:
        pass

    # Method 2: Form data
    if not raw_text:
        raw_text = request.form.get("text")

    # Method 3: Raw body (text/plain or raw JSON string)
    if not raw_text:
        try:
            raw_body = request.get_data(as_text=True)
            if raw_body:
                try:
                    data = json.loads(raw_body)
                    if isinstance(data, dict):
                        raw_text = data.get("text")
                    elif isinstance(data, str):
                        raw_text = data
                except Exception:
                    raw_text = raw_body
        except Exception:
            pass

    # Method 4: Query parameter
    if not raw_text:
        raw_text = request.args.get("text")

    return raw_text or ""


# =====================================================================
# AUTHENTICATION ROUTES
# =====================================================================

from ..services.payment_service import cashfree_service

@api_bp.route("/config", methods=["GET"])
def get_public_config():
    """Exposes public client configurations for Firebase and Cashfree."""
    return jsonify({
        "firebase": {
            "apiKey": Config.FIREBASE_API_KEY,
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "rdm-omnitensor.firebaseapp.com"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID", "rdm-omnitensor"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "rdm-omnitensor.firebasestorage.app"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "513232699098"),
            "appId": os.getenv("FIREBASE_APP_ID", "1:513232699098:web:0c5a3e28cdc75e7627efe3")
        },
        "cashfree": {
            "appId": Config.CASHFREE_APP_ID,
            "environment": Config.CASHFREE_ENV
        },
        "pricing": {
            "premium_inr": Config.PREMIUM_PRICE_INR
        }
    }), 200


@api_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    name = data.get("name", "")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required."}), 400

    success, msg, session_info = session_manager.register_user(email=email, password=password, name=name)
    if success and session_info:
        return jsonify({
            "status": "success",
            "message": msg,
            "user_id": session_info["user_id"],
            "token": session_info["token"],
            "premium": session_info["premium"],
            "email": session_info["email"],
            "name": session_info["name"]
        }), 201
    return jsonify({"status": "error", "message": msg}), 400


@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required."}), 400

    success, msg, payload = session_manager.login_user(email=email, password=password)
    if success:
        return jsonify({
            "status": "success",
            "token": payload["token"],
            "user_id": payload["user_id"],
            "premium": payload["premium"]
        }), 200
    return jsonify({"status": "error", "message": msg}), 401


@api_bp.route("/<user_id>/check", methods=["GET"])
def check_premium(user_id: str):
    session, err = _authenticate_request(user_id)
    if err:
        return err
    return jsonify({
        "status": "success",
        "user_id": user_id,
        "premium": session.get("premium", False)
    }), 200


@api_bp.route("/<user_id>/activate", methods=["POST"])
def activate_premium(user_id: str):
    session, err = _authenticate_request(user_id)
    if err:
        return err

    if session.get("premium", False) and not session.get("is_api_key"):
        return jsonify({"status": "error", "message": "Already premium."}), 400

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1] if auth_header.startswith("Bearer ") else None

    success, msg = session_manager.activate_premium(user_id=user_id, token=token)
    if success:
        return jsonify({"status": "success", "message": msg}), 200
    return jsonify({"status": "error", "message": msg}), 500


@api_bp.route("/<user_id>/call", methods=["POST", "GET"])
def handle_user_call(user_id: str):
    session, err = _authenticate_request(user_id)
    if err:
        return err
    if str(user_id) != str(Config.CURRENT_SERVER_ID):
        return jsonify({"status": "error", "message": "Forbidden: server_id mismatch."}), 403
    return jsonify({"status": "success", "message": f"Verified call processed for user {user_id}."}), 200


# =====================================================================
# AI DETECTION & RECTIFICATION ROUTES
# =====================================================================

@api_bp.route("/<user_id>/detect_ai", methods=["POST"])
def detect_ai(user_id: str):
    """Primary AI text detection endpoint.

    For premium users, returns rectified text and improvement metrics!
    """
    session, err = _authenticate_request(user_id)
    if err:
        return err

    raw_text = _extract_raw_text()
    if not raw_text.strip():
        return jsonify({"status": "error", "message": "Text field required. Send JSON with 'text' key."}), 400

    is_premium = bool(session.get("premium", False))
    result = doc_service.detect_ai(raw_text=raw_text, is_premium=is_premium)
    return jsonify(result), 200


@api_bp.route("/<user_id>/scan_document", methods=["POST"])
def scan_document(user_id: str):
    """Full-document analysis endpoint: handles multi-page long documents,

    returns hierarchical sentence heatmap, overall score, and rectified document.
    """
    session, err = _authenticate_request(user_id)
    if err:
        return err

    raw_text = _extract_raw_text()
    if not raw_text.strip():
        return jsonify({"status": "error", "message": "Document text required."}), 400

    is_premium = bool(session.get("premium", False))
    payload = request.get_json(silent=True) or {}
    check_plagiarism = payload.get("check_plagiarism", True)

    result = doc_service.scan_full_document(
        raw_text=raw_text,
        is_premium=is_premium,
        check_plagiarism=check_plagiarism
    )
    return jsonify(result), 200


@api_bp.route("/<user_id>/rectify_text", methods=["POST"])
def rectify_text(user_id: str):
    """Dedicated endpoint to humanize and rectify text for premium members."""
    session, err = _authenticate_request(user_id)
    if err:
        return err

    if not session.get("premium", False):
        return jsonify({
            "status": "error",
            "message": "Text rectification is an exclusive premium feature. Please upgrade your account."
        }), 403

    raw_text = _extract_raw_text()
    if not raw_text.strip():
        return jsonify({"status": "error", "message": "Text field required."}), 400

    rectification = doc_service.rectify_document(raw_text)
    return jsonify({
        "status": "success",
        "rectified_text": rectification["rectified_text"],
        "original_ai_score": rectification["original_ai_score"],
        "rectified_ai_score": rectification["rectified_ai_score"],
        "score_reduction": rectification["score_reduction"],
        "modifications_count": rectification["modifications_count"],
        "modifications": rectification["modifications"],
        "sentence_comparisons": rectification["sentence_comparisons"]
    }), 200


@api_bp.route("/<user_id>/index_document", methods=["POST"])
def index_document(user_id: str):
    """Indexes a reference document for plagiarism detection."""
    session, err = _authenticate_request(user_id)
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    doc_id = payload.get("doc_id")
    text = payload.get("text") or _extract_raw_text()

    if not doc_id or not text.strip():
        return jsonify({"status": "error", "message": "Both 'doc_id' and 'text' are required."}), 400

    doc_service.index_reference_document(doc_id, text)
    return jsonify({"status": "success", "message": f"Document '{doc_id}' indexed successfully."}), 200


# =====================================================================
# CASHFREE PAYMENT GATEWAY ROUTES
# =====================================================================

@api_bp.route("/payment/create_order", methods=["POST"])
def create_payment_order():
    """Creates a Cashfree payment order session for purchasing Premium access."""
    auth_header = request.headers.get("Authorization")
    session = session_manager.authenticate_header(auth_header)
    if not session:
        return jsonify({"status": "error", "message": "Unauthorized. Please log in first."}), 401

    data = request.get_json(silent=True) or {}
    user_id = session.get("user_id")
    customer_email = data.get("email") or session.get("email", "user@example.com")
    customer_phone = data.get("phone", "9876543210")
    customer_name = data.get("name") or session.get("name", "Premium Subscriber")
    amount = data.get("amount", Config.PREMIUM_PRICE_INR)

    success, msg, order_data = cashfree_service.create_order(
        user_id=user_id,
        customer_email=customer_email,
        customer_phone=customer_phone,
        customer_name=customer_name,
        amount=amount
    )

    if success and order_data:
        return jsonify({
            "status": "success",
            "message": msg,
            "order": order_data
        }), 200
    return jsonify({"status": "error", "message": msg}), 400


@api_bp.route("/payment/verify_order", methods=["POST"])
def verify_payment_order():
    """Verifies Cashfree order payment status and activates Premium tier."""
    auth_header = request.headers.get("Authorization")
    session = session_manager.authenticate_header(auth_header)
    if not session:
        return jsonify({"status": "error", "message": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    if not order_id:
        return jsonify({"status": "error", "message": "order_id is required."}), 400

    user_id = session.get("user_id")
    success, msg, verify_data = cashfree_service.verify_order(order_id=order_id, user_id=user_id)

    if success:
        return jsonify({
            "status": "success",
            "message": msg,
            "data": verify_data
        }), 200
    return jsonify({
        "status": "pending_or_failed",
        "message": msg,
        "data": verify_data
    }), 400

