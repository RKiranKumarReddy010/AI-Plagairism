import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    BASE_DIR = BASE_DIR

    # Firebase and Authentication
    FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
    CURRENT_SERVER_ID = os.getenv("CURRENT_SERVER_ID")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # Detection Thresholds
    AI_THRESHOLD_HIGH = 65    # Score >= 65: Likely AI
    AI_THRESHOLD_LOW = 40     # Score < 40: Likely Human

    # Plagiarism Thresholds
    WINNOWING_K = 5           # Shingle size (n-gram length)
    WINNOWING_W = 4           # Window size
    SEMANTIC_SIMILARITY_THRESHOLD = 0.75
    SEMANTIC_MODEL_NAME = "all-MiniLM-L6-v2"

    # Rectification settings
    RECTIFIER_MAX_PASSES = 2

    # Cashfree Payment Gateway
    CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID", "")
    CASHFREE_SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY", "")
    CASHFREE_ENV = os.getenv("CASHFREE_ENV", "production")
    CASHFREE_API_VERSION = os.getenv("CASHFREE_API_VERSION", "2023-08-01")
    PREMIUM_PRICE_INR = float(os.getenv("PREMIUM_PRICE_INR", 499))
    CASHFREE_BASE_URL = "https://api.cashfree.com/pg" if CASHFREE_ENV == "production" else "https://sandbox.cashfree.com/pg"

