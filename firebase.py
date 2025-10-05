# firebase.py
import os
import json
import base64

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception as e:
    raise RuntimeError("firebase_admin is not installed. Add 'firebase-admin' to requirements.txt") from e

def init_firestore():
    """
    Try these in order:
    1) FIREBASE_B64 (base64 of the serviceAccountKey.json)
    2) FIREBASE_CRED (raw JSON string of serviceAccountKey.json)
    3) GOOGLE_APPLICATION_CREDENTIALS (local file path) - fallback for local dev
    """
    # 1) FIREBASE_B64
    fb_b64 = os.getenv("FIREBASE_B64")
    if fb_b64:
        try:
            cred_bytes = base64.b64decode(fb_b64)
            cred_dict = json.loads(cred_bytes)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            raise RuntimeError("Failed to decode or parse FIREBASE_B64. Make sure it's base64(serviceAccountKey.json).") from e

    # 2) FIREBASE_CRED (raw JSON)
    fb_raw = os.getenv("FIREBASE_CRED")
    if fb_raw:
        try:
            # fb_raw might already be a JSON string
            cred_dict = json.loads(fb_raw)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            raise RuntimeError("FIREBASE_CRED is set but not valid JSON of serviceAccountKey.json.") from e

    # 3) GOOGLE_APPLICATION_CREDENTIALS -> a local path to JSON file
    gac = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if gac and os.path.exists(gac):
        try:
            cred = credentials.Certificate(gac)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS points to a file but firebase failed to init.") from e

    # nothing found
    raise RuntimeError(
        "No Firebase credentials found. Set FIREBASE_B64 (preferred on Cloud), "
        "or FIREBASE_CRED (JSON string), or set GOOGLE_APPLICATION_CREDENTIALS to a local file path."
    )

# initialize DB client
db = init_firestore()
