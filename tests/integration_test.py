"""
Integration tests for Sahaayak Disaster Response System
"""
import pytest
import requests
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configuration
BASE_URL = "http://localhost:8000"  # Base URL without /api prefix
TEST_COORDS = {
    "hubballi": (15.3647, 75.1240),
    "bengaluru": (12.9716, 77.5946),
    "mumbai": (19.0760, 72.8777)
}

# Test data
TEST_REPORTS = [
    {"disaster_type": "flood", "severity": "high", "location": "hubballi"},
    {"disaster_type": "fire", "severity": "medium", "location": "bengaluru"},
    {"disaster_type": "earthquake", "severity": "high", "location": "mumbai"}
]

def delay(seconds: float = 0.5):
    """Add delay between API calls"""
    time.sleep(seconds)

def test_health_check():
    """Test API health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        print(f"Response: {response.text}")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "ok"
        assert "CrisisConnect API is running" in data.get("message", "")
        print("✅ Health check passed")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        print(f"Make sure the backend server is running at {BASE_URL}")
        raise

def test_database_connection():
    """Test database connection and basic query"""
    print("\n=== Testing Database Connection ===")
    try:
        response = requests.get(f"{BASE_URL}/api/items", timeout=5)
        print(f"Items endpoint status: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"Found {len(data.get('items', []))} items in the database")
        assert isinstance(data.get("items"), list)
        print("✅ Database connection test passed")
        return True
    except Exception as e:
        print(f"❌ Database connection test failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
        raise

def submit_test_report(report_data: Dict) -> Dict:
    """Helper to submit a test report"""
    try:
        location = TEST_COORDS[report_data["location"]]
        text = f"{report_data['severity'].title()} {report_data['disaster_type']} reported in {report_data['location']}"
        
        data = {
            "text": text,
            "lat": str(location[0]),
            "lon": str(location[1]),
            "disaster_type": report_data["disaster_type"],
            "source": f"test_source_{random.randint(1000, 9999)}",
            "place": report_data["location"].title(),
            "language": "en"
        }
        
        print(f"\nSubmitting report: {data}")
        response = requests.post(f"{BASE_URL}/api/ingest", data=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"Report submitted successfully. ID: {result.get('id')}")
        return result
        
    except Exception as e:
        print(f"❌ Error submitting report: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
        raise

def test_report_submission():
    """Test submitting disaster reports"""
    for report in TEST_REPORTS:
        result = submit_test_report(report)
        assert "id" in result
        assert "media_url" in result
        print(f"Submitted {report['disaster_type']} report with ID: {result['id']}")
        delay()

def test_event_clustering():
    """Test event clustering functionality"""
    print("\n=== Starting Event Clustering Test ===")
    
    # Submit multiple reports for the same location
    location = "hubballi"
    report_ids = []
    for i in range(3):
        report = {
            "disaster_type": "flood",
            "severity": "high",
            "location": location
        }
        print(f"\nSubmitting report {i+1}...")
        result = submit_test_report(report)
        report_ids.append(result.get("id"))
        print(f"  Report ID: {result.get('id')}")
        print(f"  Response: {result}")
        delay()
    
    print("\n=== Triggering Clustering ===")
    try:
        response = requests.post(f"{BASE_URL}/api/disasters/events/recluster")
        print(f"Clustering response status: {response.status_code}")
        print(f"Response content: {response.text}")
        response.raise_for_status()
        print("Clustering triggered successfully")
    except Exception as e:
        print(f"Error triggering clustering: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        raise
    
    print("\n=== Checking Events ===")
    try:
        response = requests.get(f"{BASE_URL}/api/disasters/events")
        print(f"Events response status: {response.status_code}")
        print(f"Events response content: {response.text}")
        response.raise_for_status()
        
        events_data = response.json()
        print(f"Events data: {events_data}")
        events = events_data.get("events", [])
        print(f"Found {len(events)} events")
        
        if not events:
            # Try to get all items to debug
            print("\n=== Debug: Checking All Items ===")
            items_response = requests.get(f"{BASE_URL}/api/items")
            print(f"Items response: {items_response.status_code}, {items_response.text}")
            
        assert len(events) > 0, "No events found after clustering"
        
        # Verify at least one flood event exists
        flood_events = [e for e in events if e.get("disaster_type") == "flood"]
        print(f"Found {len(flood_events)} flood events")
        assert len(flood_events) > 0, "No flood events found after clustering"
        
        # Verify event has multiple items
        for event in flood_events:
            event_id = event["id"]
            print(f"\nChecking items for event {event_id}")
            items_url = f"{BASE_URL}/api/disasters/events/{event_id}/items"
            print(f"Fetching items from: {items_url}")
            
            items_response = requests.get(items_url)
            print(f"Items response status: {items_response.status_code}")
            print(f"Items response content: {items_response.text}")
            
            # Check if response is empty or not valid JSON
            if not items_response.text.strip():
                print("Error: Empty response received from items endpoint")
                # Try to get the raw response content
                print(f"Raw response content: {items_response.content}")
                items = []
            else:
                try:
                    items_data = items_response.json()
                    print(f"Items data: {items_data}")
                    items = items_data.get("items", [])
                except ValueError as e:
                    print(f"Error parsing JSON from items response: {e}")
                    print(f"Response headers: {items_response.headers}")
                    items = []
                print(f"Found {len(items)} items in event {event_id}")
                
                if not items:
                    print("No items found in event. Checking all items in system...")
                    try:
                        all_items = requests.get(f"{BASE_URL}/api/items").json().get("items", [])
                        print(f"Total items in system: {len(all_items)}")
                        for i, item in enumerate(all_items[:5], 1):
                            print(f"  {i}. ID: {item.get('id')}, Type: {item.get('disaster_type')}, "
                                  f"Location: {item.get('lat')}, {item.get('lon')}")
                    except Exception as e:
                        print(f"Error fetching all items: {str(e)}")
                
                assert len(items) >= 3, f"Expected at least 3 items in event {event_id}, got {len(items)}"
                
                print(f"Response content: {items_response.text}")
                
    except Exception as e:
        print(f"Error in test_event_clustering: {str(e)}")
        if 'response' in locals():
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
        raise

def test_event_verification():
    """Test event verification logic"""
    # Trigger clustering
    response = requests.post(f"{BASE_URL}/api/disasters/events/recluster")
    response.raise_for_status()
    
    # Get all events
    response = requests.get(f"{BASE_URL}/api/disasters/events")
    events = response.json().get("events", [])
    
    # Find an event to verify
    for event in events:
        if event.get("item_count", 0) >= 3 and not event.get("is_verified"):
            event_id = event["id"]
            # Trigger verification
            verify_response = requests.post(
                f"{BASE_URL}/api/disasters/events/{event_id}/verify",
                json={"verify": True, "reason": "Multiple independent reports"}
            )
            verify_response.raise_for_status()
            
            # Verify status was updated
            updated_event = requests.get(f"{BASE_URL}/api/disasters/events/{event_id}").json()
            assert updated_event["is_verified"] is True
            assert "verification_reason" in updated_event
            break
    else:
        print("No suitable events found for verification test")

def test_frontend_integration():
    """Test basic frontend-backend integration"""
    # Test events endpoint used by frontend
    response = requests.get(f"{BASE_URL}/api/disasters/events")
    assert response.status_code == 200
    
    # Test event items endpoint
    events = response.json().get("events", [])
    if events:
        event_id = events[0]["id"]
        items_response = requests.get(f"{BASE_URL}/api/disasters/events/{event_id}/items")
        assert items_response.status_code == 200
        assert isinstance(items_response.json().get("items"), list)

def test_error_handling():
    """Test error cases and edge conditions"""
    # Test invalid report submission
    response = requests.post(f"{BASE_URL}/ingest", data={"text": "Invalid report"})
    assert response.status_code == 422  # Validation error
    
    # Test non-existent endpoint
    response = requests.get(f"{BASE_URL}/nonexistent")
    assert response.status_code == 404

def verify_api_endpoints():
    """Verify that all required API endpoints are accessible"""
    print("\n=== Verifying API Endpoints ===")
    endpoints = [
        ("GET", "/health"),
        ("GET", "/api/items"),
        ("POST", "/api/ingest"),
        ("GET", "/api/events"),
        ("POST", "/api/events/recluster")
    ]
    
    all_ok = True
    for method, endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            print(f"Testing {method} {url}...")
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=5)
                
            print(f"  Status: {response.status_code}")
            if response.status_code >= 400:
                print(f"  Response: {response.text}")
                all_ok = False
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            all_ok = False
    
    if all_ok:
        print("✅ All API endpoints are accessible")
    else:
        print("❌ Some API endpoints are not accessible")
    
    return all_ok

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  CrisisConnect Integration Tests")
    print("="*50)
    
    # Verify API endpoints first
    if not verify_api_endpoints():
        print("\n❌ Some API endpoints are not accessible. Please check if the backend server is running correctly.")
        print(f"   Make sure the server is running at {BASE_URL}")
        exit(1)
    
    # Run tests in order
    tests = [
        test_health_check,
        test_database_connection,
        test_report_submission,
        test_event_clustering,
        test_event_verification,
        test_frontend_integration,
        test_error_handling
    ]
    
    failed_tests = []
    for test in tests:
        print(f"\n" + "="*50)
        print(f"  RUNNING TEST: {test.__name__}")
        print("="*50)
        try:
            start_time = time.time()
            test()
            duration = time.time() - start_time
            print(f"\n✅ {test.__name__} passed in {duration:.2f} seconds")
        except Exception as e:
            print(f"\n❌ {test.__name__} failed: {str(e)}")
            import traceback
            traceback.print_exc()
            failed_tests.append(test.__name__)
    
    # Print summary
    print("\n" + "="*50)
    print("  TEST SUMMARY")
    print("="*50)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {len(tests) - len(failed_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print("\nFailed tests:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
        print("\n❌ Some tests failed. Please check the logs above for details.")
        exit(1)
    else:
        print("\n✅ All tests passed successfully!")
        exit(0)
