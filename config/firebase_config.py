import firebase_admin
from firebase_admin import credentials, auth, firestore

# Initialize Firebase Admin SDK (only if not already initialized)
try:
    # Try to get existing app first
    firebase_admin.get_app()
except ValueError:
    # App doesn't exist, so initialize it
    try:
        cred = credentials.Certificate('config/firebase-service-account.json')
        firebase_admin.initialize_app(cred)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: Firebase Admin SDK initialization failed: {e}")
        print("Please ensure config/firebase-service-account.json exists and is valid.")
        raise

# Initialize Firestore
db = firestore.client()

# Firebase Web Config (for frontend)
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyC9Ydvs8WhexKOZjzE0U2tTOnEM0THlIms",
    "authDomain": "foodbridge-c75de.firebaseapp.com",
    "projectId": "foodbridge-c75de",
    "storageBucket": "foodbridge-c75de.firebasestorage.app",
    "messagingSenderId": "952654772110",
    "appId": "1:952654772110:web:eca6f852147dc37ff0d6df",
    "measurementId": "G-5T24X5YH90"
}
