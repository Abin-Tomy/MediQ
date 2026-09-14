import os
import firebase_admin
from firebase_admin import credentials, firestore


def _load_env(env_path: str) -> None:
    """
    Lightweight .env file parser using standard library.
    Populates os.environ without requiring third-party dotenv dependencies.
    """
    if not os.path.isfile(env_path):
        return

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            clean_value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), clean_value)


# Ensure .env is loaded from project root regardless of execution working directory
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_load_env(os.path.join(_BASE_DIR, ".env"))

# Resolve Firebase Service Account credentials
_cred_filename = os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json")
_cred_path = (
    _cred_filename
    if os.path.isabs(_cred_filename)
    else os.path.join(_BASE_DIR, _cred_filename)
)

# Initialize default Firebase Admin application if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate(_cred_path)
    firebase_admin.initialize_app(cred)

# Global Firestore client instance for database operations
db = firestore.client()

