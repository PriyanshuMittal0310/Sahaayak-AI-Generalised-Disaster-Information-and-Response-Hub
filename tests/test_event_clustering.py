"""
Test event clustering functionality
"""
import pytest
import requests
from datetime import datetime, timedelta
import random
import time
from typing import Dict, List, Tuple

# Test configuration
BASE_URL = "http://localhost:8000/api/disasters"

# Test data
HUBBALLI_COORDS = (15.3647, 75.1240)  # Hubballi coordinates
BENGALURU_COORDS = (12.9716, 77.5946)  # Bengaluru coordinates

# Add a small delay between API calls to avoid rate limiting
def delay():
    time.sleep(0.5)

def submit_report(lat: float, lon: float, disaster_type: str = "flood") -> Dict:
    """Submit a test report using form data"""
    url = "http://localhost:8000/api/ingest"
    
    # Create a more descriptive text that might help with NLP
    disaster_descriptions = {
        "flood": "There is a major flood in the area with water levels rising rapidly.",
        "fire": "A large fire has broken out with heavy smoke visible for miles.",
        "earthquake": "A strong earthquake was felt in the area, causing buildings to shake.",
        "hurricane": "Hurricane conditions with strong winds and heavy rain are being reported.",
        "tornado": "A tornado was spotted touching down in the vicinity."
    }
    
    text = f"{disaster_descriptions.get(disaster_type, 'An incident has occurred')} " \
           f"at coordinates {lat:.4f}, {lon:.4f}. " \
           f"This is a test report for {disaster_type} disaster type."
    
    data = {
        "text": text,
        "lat": str(lat),  # Convert to string for form data
        "lon": str(lon),  # Convert to string for form data
        "source": f"test_source_{random.randint(1000, 9999)}",
        "disaster_type": disaster_type,
        "timestamp": datetime.now().isoformat(),
        "place": f"Test Location for {disaster_type}",
        "language": "en"  # Explicitly set language
    }
    
    print(f"  Submitting {disaster_type} report at {lat:.4f}, {lon:.4f}")
    print(f"  Text: {text}")
    
    # Convert dict to form data
    form_data = {}
    for key, value in data.items():
        if value is not None:  # Skip None values
            form_data[key] = str(value)
    
    delay()
    
    try:
        response = requests.post(url, data=form_data)
        print(f"  Response status: {response.status_code}")
        print(f"  Response content: {response.text}")
        response.raise_for_status()
        
        # Verify the item was created
        item_id = response.json().get('id')
        if item_id:
            print(f"  Successfully created item with ID: {item_id}")
            
            # Try to fetch the created item
            try:
                item_url = f"http://localhost:8000/api/items/{item_id}"
                item_response = requests.get(item_url)
                if item_response.status_code == 200:
                    item_data = item_response.json()
                    print(f"  Item details: {item_data}")
                    
                    # Verify disaster_type was saved correctly
                    saved_type = item_data.get('disaster_type')
                    if saved_type != disaster_type:
                        print(f"  WARNING: Disaster type mismatch. Expected '{disaster_type}', got '{saved_type}'")
            except Exception as e:
                print(f"  Warning: Could not verify item creation: {str(e)}")
        
        return response.json()
    except Exception as e:
        print(f"  Error submitting report: {str(e)}")
        if 'response' in locals():
            print(f"  Response content: {response.text}")
        raise

def get_events(disaster_type: str = None) -> List[Dict]:
    """Get all events with optional filtering"""
    url = f"{BASE_URL}/events"
    params = {}
    if disaster_type:
        params["disaster_type"] = disaster_type
    
    delay()
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    # Debug: Print the raw response
    data = response.json()
    print(f"  Raw events response: {data}")
    
    return data.get("events", [])

def trigger_clustering():
    """Trigger event clustering"""
    url = f"{BASE_URL}/events/recluster"
    delay()
    response = requests.post(url)
    response.raise_for_status()
    return response.json()

def get_items() -> List[Dict]:
    """Get all items for debugging"""
    url = "http://localhost:8000/api/items"
    delay()
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        print(f"  Found {len(items)} items in database")
        for item in items:
            print(f"    - ID: {item.get('id')}, Type: {item.get('disaster_type')}, "
                  f"Lat: {item.get('lat')}, Lon: {item.get('lon')}, "
                  f"Source: {item.get('source')}, Created: {item.get('created_at')}")
        return items
    except Exception as e:
        print(f"  Error getting items: {str(e)}")
        if 'response' in locals():
            print(f"  Response status: {response.status_code}")
            print(f"  Response content: {response.text}")
        return []

def test_event_clustering():
    """Test flood event clustering and verification"""
    print("\n=== Starting Flood Event Clustering Test ===")
    
    # Clear any existing data (if needed)
    print("\n=== Current items in database ===")
    get_items()
    
    # Submit 3 reports around Hubballi
    print("\nTest: Submitting 3 flood reports around Hubballi...")
    hubballi_reports = []
    for i in range(3):
        # Add small random offset (less than 2km)
        offset_lat = random.uniform(-0.01, 0.01)  # ~1.1km at equator
        offset_lon = random.uniform(-0.01, 0.01)
        lat = HUBBALLI_COORDS[0] + offset_lat
        lon = HUBBALLI_COORDS[1] + offset_lon
        
        print(f"  Submitting flood report {i+1} at {lat:.4f}, {lon:.4f}")
        report = submit_report(lat, lon, "flood")
        hubballi_reports.append(report)
    
    # Verify items were saved
    print("\nVerifying items were saved to database...")
    items = get_items()
    flood_items = [i for i in items if i.get('disaster_type') == 'flood']
    print(f"  Found {len(flood_items)} flood items in database")
    
    if not flood_items:
        print("  Error: No flood items found in database after submission")
        # Show all items for debugging
        print("\nAll items in database:")
        for i, item in enumerate(items, 1):
            print(f"  {i}. ID: {item.get('id')}, Type: {item.get('disaster_type')}, "
                  f"Lat: {item.get('lat')}, Lon: {item.get('lon')}, "
                  f"Source: {item.get('source')}")
    
    assert len(flood_items) >= 3, f"Expected at least 3 flood items, found {len(flood_items)}"
    
    # Trigger clustering
    print("\nTriggering clustering...")
    result = trigger_clustering()
    print(f"Clustering result: {result}")
    
    # Show items after clustering
    print("\nItems after clustering:")
    get_items()
    
    # Check if reports were clustered into one event
    print("\nVerifying clustering...")
    flood_events = get_events("flood")
    print(f"Found {len(flood_events)} flood events")
    
    # Print all events for debugging
    all_events = get_events()
    print(f"\nAll events in system ({len(all_events)}):")
    for i, event in enumerate(all_events, 1):
        print(f"  {i}. {event.get('disaster_type')} - {event.get('title')} "
              f"(Items: {event.get('item_count')}, Sources: {event.get('source_count')})")
    
    if flood_events:
        # Get the event with the most items (should be our Hubballi event)
        main_flood_event = max(flood_events, key=lambda x: x.get("item_count", 0))
        print(f"\nMain flood event details:")
        print(f"  - ID: {main_flood_event.get('id')}")
        print(f"  - Title: {main_flood_event.get('title')}")
        print(f"  - Items: {main_flood_event.get('item_count')}")
        print(f"  - Sources: {main_flood_event.get('source_count')}")
        print(f"  - Location: {main_flood_event.get('centroid_lat')}, {main_flood_event.get('centroid_lon')}")
        print(f"  - Verified: {main_flood_event.get('is_verified', False)}")
        
        # Get event items
        try:
            event_id = main_flood_event.get('id')
            items_url = f"{BASE_URL}/events/{event_id}/items"
            response = requests.get(items_url)
            if response.status_code == 200:
                items_data = response.json()
                print(f"\nItems in event ({items_data.get('total')}):")
                for item in items_data.get('items', [])[:10]:  # Show first 10 items
                    print(f"  - ID: {item.get('id')}, Type: {item.get('disaster_type')}")
                    print(f"    Location: {item.get('lat')}, {item.get('lon')}")
                    print(f"    Source: {item.get('source')}")
                    print(f"    Text: {item.get('text', '')[:100]}...")
        except Exception as e:
            print(f"  Error getting event items: {str(e)}")
        
        # Verify the event has the expected number of items
        assert main_flood_event.get('item_count', 0) >= 3, \
            f"Expected at least 3 items in event, got {main_flood_event.get('item_count')}"
    else:
        print("No flood events found after clustering")
        assert False, "No flood events found after clustering"
    
    print("\n=== Test completed successfully! ===")
    return True

if __name__ == "__main__":
    test_event_clustering()
    print("All tests passed!")
