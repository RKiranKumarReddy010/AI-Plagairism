import time
import requests
from typing import Optional, Dict, Any, Tuple
from ..config import Config


class SessionManager:
    """Manages user authentication with Google Firebase Authentication (Identity Toolkit)

    and user metadata / premium status in Firebase Realtime Database.
    """

    def __init__(self):
        self.token_cache: Dict[str, Dict[str, Any]] = {}

    def authenticate_header(self, auth_header: Optional[str]) -> Optional[Dict[str, Any]]:
        """Validates Bearer Firebase ID token or master API key."""
        if not auth_header:
            return None

        # Master Firebase API Key (admin/system access)
        if auth_header == Config.FIREBASE_API_KEY:
            return {"user_id": Config.CURRENT_SERVER_ID, "premium": True, "is_api_key": True}

        # Check Bearer token
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

            # 1. Fast path: check memory cache
            cached = self.token_cache.get(token)
            if cached:
                # Optionally sync latest premium status from Realtime DB
                user_id = cached.get("user_id")
                if user_id and Config.FIREBASE_DB_URL:
                    try:
                        db_url = f"{Config.FIREBASE_DB_URL}/users/{user_id}/premium.json?auth={Config.FIREBASE_API_KEY}"
                        resp = requests.get(db_url, timeout=3)
                        if resp.status_code == 200 and resp.json() is not None:
                            cached["premium"] = bool(resp.json())
                    except Exception:
                        pass
                return cached

            # 2. Verify with Firebase Auth Identity Toolkit REST API
            if Config.FIREBASE_API_KEY:
                lookup_url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={Config.FIREBASE_API_KEY}"
                try:
                    resp = requests.post(lookup_url, json={"idToken": token}, timeout=5)
                    if resp.status_code == 200 and resp.json().get("users"):
                        user_info = resp.json()["users"][0]
                        user_id = user_info.get("localId")
                        email = user_info.get("email")

                        # Fetch premium status from Realtime DB
                        premium = False
                        if Config.FIREBASE_DB_URL:
                            db_url = f"{Config.FIREBASE_DB_URL}/users/{user_id}/premium.json?auth={Config.FIREBASE_API_KEY}"
                            r_db = requests.get(db_url, timeout=3)
                            if r_db.status_code == 200 and r_db.json() is not None:
                                premium = bool(r_db.json())

                        session_payload = {
                            "user_id": user_id,
                            "email": email,
                            "premium": premium
                        }
                        self.token_cache[token] = session_payload
                        return session_payload
                except Exception:
                    pass

        return None

    def register_user(self, email: str, password: str, name: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Registers a new user in Firebase Authentication and creates profile in Realtime DB."""
        if not Config.FIREBASE_API_KEY:
            return False, "Firebase API Key is missing.", None

        # Call Firebase Identity Toolkit SignUp API
        signup_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={Config.FIREBASE_API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            resp = requests.post(signup_url, json=payload, timeout=8)
            data = resp.json()

            if resp.status_code != 200 or "idToken" not in data:
                err_msg = data.get("error", {}).get("message", "Registration failed.")
                if "EMAIL_EXISTS" in err_msg:
                    return False, "This email is already registered. Please log in.", None
                if "WEAK_PASSWORD" in err_msg:
                    return False, "Password should be at least 6 characters.", None
                return False, f"Firebase Auth error: {err_msg}", None

            user_id = data["localId"]
            id_token = data["idToken"]
            refresh_token = data.get("refreshToken", "")

            # Create / sync initial user metadata in Firebase Realtime DB
            if Config.FIREBASE_DB_URL:
                db_url = f"{Config.FIREBASE_DB_URL}/users/{user_id}.json?auth={Config.FIREBASE_API_KEY}"
                user_data = {
                    "email": email,
                    "name": name,
                    "premium": False,
                    "created_at": int(time.time())
                }
                try:
                    requests.put(db_url, json=user_data, timeout=5)
                except Exception:
                    pass

            session_info = {
                "token": id_token,
                "user_id": user_id,
                "email": email,
                "name": name,
                "premium": False,
                "refreshToken": refresh_token
            }
            self.token_cache[id_token] = session_info

            return True, "User registered successfully with Firebase Authentication.", session_info

        except Exception as e:
            return False, f"Connection error contacting Firebase: {str(e)}", None

    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Authenticates user against Firebase Authentication and fetches subscription tier."""
        if not Config.FIREBASE_API_KEY:
            return False, "Firebase API Key is missing.", None

        signin_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={Config.FIREBASE_API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            resp = requests.post(signin_url, json=payload, timeout=8)
            data = resp.json()

            if resp.status_code != 200 or "idToken" not in data:
                err_msg = data.get("error", {}).get("message", "Invalid credentials.")
                if "EMAIL_NOT_FOUND" in err_msg or "INVALID_PASSWORD" in err_msg or "INVALID_LOGIN_CREDENTIALS" in err_msg:
                    return False, "Invalid email or password.", None
                return False, f"Authentication error: {err_msg}", None

            user_id = data["localId"]
            id_token = data["idToken"]
            refresh_token = data.get("refreshToken", "")

            # Query Realtime DB for subscription status & profile
            premium = False
            name = ""
            if Config.FIREBASE_DB_URL:
                db_url = f"{Config.FIREBASE_DB_URL}/users/{user_id}.json?auth={Config.FIREBASE_API_KEY}"
                try:
                    r_db = requests.get(db_url, timeout=5)
                    if r_db.status_code == 200 and r_db.json():
                        db_user = r_db.json()
                        premium = bool(db_user.get("premium", False))
                        name = db_user.get("name", "")
                except Exception:
                    pass

            session_info = {
                "token": id_token,
                "user_id": user_id,
                "email": email,
                "name": name,
                "premium": premium,
                "refreshToken": refresh_token
            }
            self.token_cache[id_token] = session_info

            return True, "Login successful.", session_info

        except Exception as e:
            return False, f"Connection error contacting Firebase: {str(e)}", None

    def activate_premium(self, user_id: str, token: Optional[str] = None) -> Tuple[bool, str]:
        """Marks user as Premium in Firebase Realtime DB and updates active session cache."""
        if not Config.FIREBASE_DB_URL or not Config.FIREBASE_API_KEY:
            return False, "Firebase configuration missing."

        url = f"{Config.FIREBASE_DB_URL}/users/{user_id}.json?auth={Config.FIREBASE_API_KEY}"
        try:
            resp = requests.patch(url, json={"premium": True, "premium_activated_at": int(time.time())}, timeout=5)
            if resp.status_code == 200:
                # Update in-memory session cache
                if token and token in self.token_cache:
                    self.token_cache[token]["premium"] = True
                for s in self.token_cache.values():
                    if s.get("user_id") == user_id:
                        s["premium"] = True
                return True, f"Premium activated for {user_id}."
            return False, "Failed to update subscription in Firebase database."
        except Exception as e:
            return False, f"Error updating subscription: {str(e)}"


session_manager = SessionManager()
