import time
import requests
import os
import threading
from flask import Flask
import firebase_admin
from firebase_admin import credentials, db

# Flask app just to keep Render happy
app = Flask(__name__)

@app.route("/")
def home():
    return "Enova backend is running", 200

def worker():
    # Init Firebase
    cred = credentials.Certificate({
        "type": os.environ["FIREBASE_TYPE"],
        "project_id": os.environ["FIREBASE_PROJECT_ID"],
        "private_key_id": os.environ["FIREBASE_PRIVATE_KEY_ID"],
        "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
        "client_id": os.environ["FIREBASE_CLIENT_ID"],
        "auth_uri": os.environ["FIREBASE_AUTH_URI"],
        "token_uri": os.environ["FIREBASE_TOKEN_URI"],
        "auth_provider_x509_cert_url": os.environ["FIREBASE_AUTH_PROVIDER_X509_CERT_URL"],
        "client_x509_cert_url": os.environ["FIREBASE_CLIENT_X509_CERT_URL"]
    })
    firebase_admin.initialize_app(cred, {
        "databaseURL": os.environ["FIREBASE_DB_URL"]
    })

    ref = db.reference("requests")

    while True:
        try:
            requests_data = ref.get() or {}
            for req_id, req in requests_data.items():
                if req["status"] == "pending":
                    try:
                        resp = requests.get(req["url"], timeout=10)
                        ref.child(req_id).update({
                            "status": "done",
                            "html": resp.text[:10000]  # Limit size
                        })
                    except Exception as e:
                        ref.child(req_id).update({
                            "status": "error",
                            "html": str(e)
                        })
        except Exception as e:
            print("Worker error:", e)
        time.sleep(3)

if __name__ == "__main__":
    # Run worker in background thread
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
