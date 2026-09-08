from flask import Flask, jsonify
from flask_cors import CORS
from .api.routes import api_bp
from .config import Config


def create_app() -> Flask:
    """Application factory for the AI Plagiarism Detection & Rectification Backend API."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable Cross-Origin Resource Sharing (CORS) for frontend React app (e.g. truth-seeker-suite on port 8080)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Register API blueprint
    app.register_blueprint(api_bp)

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "service": "AI Plagiarism Detection & Premium Text Rectification API",
            "version": "2.0.0",
            "status": "online",
            "endpoints": [
                "/api/config",
                "/api/register",
                "/api/login",
                "/api/<user_id>/check",
                "/api/<user_id>/activate",
                "/api/<user_id>/detect_ai",
                "/api/<user_id>/scan_document",
                "/api/<user_id>/rectify_text",
                "/api/<user_id>/index_document",
                "/api/payment/create_order",
                "/api/payment/verify_order",
                "/api/<user_id>/call"
            ]
        }), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "message": "API endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    return app
