import requests
import time
import json
import sqlite3
import os

print("\n=== VERIFYING DATABASE INTEGRITY ===")
try:
    conn = sqlite3.connect("backend/data/falcon.db")
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode;")
    mode = cur.fetchone()[0]
    print(f"[DB] PRAGMA journal_mode = {mode}")
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")

print("\n=== PINGING SERVER ===")
for _ in range(10):
    try:
        requests.get("http://127.0.0.1:8000/docs", timeout=2)
        print("Server is up!")
        break
    except:
        time.sleep(1)
else:
    print("Server failed to start.")
    exit(1)

endpoints = [
    ("Success Rate Logic", "http://127.0.0.1:8000/api/analytics/success-rate/RELIANCE"),
    ("Cluster Logic", "http://127.0.0.1:8000/api/analytics/clusters"),
    ("Sentiment Tone Shift", "http://127.0.0.1:8000/api/analytics/tone-shift/TCS"),
    ("Audio Script Generation", "http://127.0.0.1:8000/api/audio/market-minutes")
]

for name, url in endpoints:
    print(f"\n--- Testing {name} ---")
    try:
        res = requests.get(url, timeout=10)
        print(f"Status: {res.status_code}")
        try:
            print("Response:", json.dumps(res.json(), indent=2)[:300] + "...")
        except:
            print("Response:", res.text[:300])
    except Exception as e:
        print(f"Error: {e}")
