import sqlite3
import os
import requests
import json
import time
import subprocess

print("--- FALCON-X VERIFICATION ---")

# 1. Verify Database Integrity
db_path = "backend/data/falcon.db"
print(f"Checking DB: {db_path}")
if not os.path.exists(db_path):
    print("Database file doesn't exist yet, we can create it or it will be created by FastAPI.")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode;")
    mode = cur.fetchone()[0]
    print(f"[DB] journal_mode = {mode}")
    conn.close()

# Start the server temporarily to test endpoints
print("\nStarting FastAPI server in background...")
proc = subprocess.Popen(["python", "backend/main.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Wait for server to be ready
time.sleep(5)

base_url = "http://localhost:8000/api"

def test_endpoint(name, url):
    print(f"\n--- Testing {name} ---")
    try:
        res = requests.get(url, timeout=30)
        print(f"Status: {res.status_code}")
        try:
            print("Response:", json.dumps(res.json(), indent=2)[:500] + ("..." if len(json.dumps(res.json())) > 500 else ""))
        except:
            print("Response:", res.text[:500])
    except Exception as e:
        print(f"Error: {e}")

test_endpoint("Success Rate Logic", f"{base_url}/analytics/success-rate/RELIANCE")
test_endpoint("Cluster Logic", f"{base_url}/analytics/clusters")
test_endpoint("Sentiment Tone Shift", f"{base_url}/analytics/tone-shift/TCS")
test_endpoint("Audio Script Generation", f"{base_url}/audio/market-minutes")

# Shutdown server
print("\nShutting down server...")
proc.terminate()
proc.wait()
print("Verification complete.")
