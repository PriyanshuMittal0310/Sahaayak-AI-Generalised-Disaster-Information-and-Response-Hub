"""
Seed demo events for QA and demo runs.
"""
import requests
import time

API_URL = "http://localhost:8000/api/disasters/detect"

demo_events = [
    {
        "text": "Flood reported in Bengaluru, verified by local authorities.",
        "detect_language": True,
        "use_openai": True,
        "lat": 12.9716,
        "lon": 77.5946
    },
    {
        "text": "Rumor: Fire in Mumbai mall, unverified sources.",
        "detect_language": True,
        "use_openai": True,
        "lat": 19.0760,
        "lon": 72.8777
    },
    {
        "text": "Conflicting posts: Earthquake felt in Delhi, some deny.",
        "detect_language": True,
        "use_openai": True,
        "lat": 28.6139,
        "lon": 77.2090
    },
    {
        "text": "Voice intake: Cyclone warning issued for Chennai coast.",
        "detect_language": True,
        "use_openai": True,
        "lat": 13.0827,
        "lon": 80.2707
    },
    {
        "text": "Flooding in Assam, shelter available at local school.",
        "detect_language": True,
        "use_openai": True,
        "lat": 26.2006,
        "lon": 92.9376
    }
]

def seed_events():
    for i, event in enumerate(demo_events):
        print(f"Seeding event {i+1}: {event['text']}")
        r = requests.post(API_URL, json=event)
        print(f"Status: {r.status_code}, Response: {r.text}")
        time.sleep(1)

if __name__ == "__main__":
    seed_events()
