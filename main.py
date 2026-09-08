"""Main entry point for AI Plagiarism Detection and Text Rectification Server."""
import os
from src.app import create_app
from src.config import Config
from src.core.preprocessor import preprocessor
from src.detector.ai_detector import AITextDetector
from src.services.doc_service import doc_service
from src.auth.session import session_manager

# Application instance
app = create_app()

# Backward compatibility exports
detector = doc_service.detector
TOKEN_CACHE = session_manager.token_cache
FIREBASE_DB_URL = Config.FIREBASE_DB_URL
FIREBASE_API_KEY = Config.FIREBASE_API_KEY
CURRENT_SERVER_ID = Config.CURRENT_SERVER_ID

def _build_report(analysis):
    return doc_service.build_report(analysis)

def _build_fix(analysis, raw_text):
    return doc_service.build_fix_tips(analysis, raw_text)

if __name__ == "__main__":
    port = Config.FLASK_PORT
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
