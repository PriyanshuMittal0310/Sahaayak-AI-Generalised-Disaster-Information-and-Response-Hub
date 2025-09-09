#!/usr/bin/env python3
"""
Test script to verify event clustering and verification logic
"""

import requests
import time
from datetime import datetime, timedelta
import random

def submit_citizen_report(lat: float, lon: float, text: str):
    """Submit a citizen report to the API"""
    url = "http://localhost:8000/api/ingest"
    data = {
        "text": text,
        "lat": lat,
        "lon": lon
    }
    response = requests.post(url, data=data)
    
    # Trigger event clustering after each submission
    requests.post("http://localhost:8000/api/disasters/events/recluster")
    
    return response.json()

def get_events():
    """Get all events from the API"""
    url = "http://localhost:8000/api/disasters/events"
    response = requests.get(url)
    return response.json()

def test_event_clustering():
    print("Testing Event Clustering and Verification...")
    print("=" * 50)
    
    # Hubballi coordinates (center point)
    hubballi_lat = 15.3647
    hubballi_lon = 75.1240
    
    # Test 1: Submit 3 reports around Hubballi
    print("\n1. Submitting 3 reports around Hubballi...")
    for i in range(3):
        # Add small random offset (less than 2km)
        offset_lat = random.uniform(-0.01, 0.01)  # ~1.1km at equator
        offset_lon = random.uniform(-0.01, 0.01)
        
        lat = hubballi_lat + offset_lat
        lon = hubballi_lon + offset_lon
        
        response = submit_citizen_report(
            lat=lat,
            lon=lon,
            text=f"Test report {i+1} - Flooding in area"
        )
        print(f"   Submitted report {i+1}: {response}")
    
    # Trigger clustering and wait
    print("   Triggering event clustering...")
    response = requests.post("http://localhost:8000/api/disasters/events/recluster")
    print(f"   Clustering response: {response.status_code} - {response.text}")
    time.sleep(2)  # Short delay for processing
    
    # Check events
    events = get_events()
    hubballi_events = [e for e in events['events'] 
                      if 'Hubballi' in e.get('title', '')]
    
    if len(hubballi_events) == 1 and hubballi_events[0]['item_count'] == 3:
        print("   ✅ Test 1 passed: 1 event created with 3 items")
    else:
        print(f"   ❌ Test 1 failed. Expected 1 event with 3 items, got {len(hubballi_events)} events")
    
    # Test 2: Submit a report far away (Bengaluru)
    print("\n2. Submitting report in Bengaluru...")
    response = submit_citizen_report(
        lat=12.9716,
        lon=77.5946,
        text="Test report - Fire in Bengaluru"
    )
    print(f"   Submitted report: {response}")
    
    # Trigger clustering and wait
    print("   Triggering event clustering...")
    response = requests.post("http://localhost:8000/api/disasters/events/recluster")
    print(f"   Clustering response: {response.status_code} - {response.text}")
    time.sleep(2)  # Short delay for processing
    
    # Check events
    events = get_events()
    if len(events['events']) >= 2:
        print("   ✅ Test 2 passed: New event created in Bengaluru")
    else:
        print(f"   ❌ Test 2 failed. Expected at least 2 events, got {len(events['events'])}")
    
    # Test 3: Check verification logic
    print("\n3. Testing verification logic...")
    # Submit 3 more reports from different sources around Hubballi
    sources = ["user1", "user2", "official_source"]
    for i, source in enumerate(sources, 1):
        offset_lat = random.uniform(-0.01, 0.01)
        offset_lon = random.uniform(-0.01, 0.01)
        
        response = submit_citizen_report(
            lat=hubballi_lat + offset_lat,
            lon=hubballi_lon + offset_lon,
            text=f"{source} report - Flooding getting worse"
        )
        print(f"   Submitted report from {source}: {response}")
    
    # Trigger clustering and wait
    print("   Triggering event clustering...")
    response = requests.post("http://localhost:8000/api/disasters/events/recluster")
    print(f"   Clustering response: {response.status_code} - {response.text}")
    time.sleep(2)  # Short delay for processing
    
    # Check if event is verified
    events = get_events()
    hubballi_event = next((e for e in events['events'] 
                          if 'Hubballi' in e.get('title', '')), None)
    
    if hubballi_event and hubballi_event.get('is_verified'):
        print("   ✅ Test 3 passed: Event verified with multiple sources")
    else:
        print("   ❌ Test 3 failed: Event not verified")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_event_clustering()
