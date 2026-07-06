import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv
import os

load_dotenv()

cred_path = os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()
