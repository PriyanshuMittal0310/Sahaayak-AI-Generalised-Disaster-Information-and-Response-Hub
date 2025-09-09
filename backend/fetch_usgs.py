import requests
from datetime import datetime

USGS_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

def fetch_usgs_quakes():
    try:
        r = requests.get(USGS_FEED, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if not data or "features" not in data:
            print("No features in USGS response")
            return []

        events = []
        for feat in data.get("features", []):
            try:
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                coords = geom.get("coordinates", [None, None, None])

                event = {
                    "id": feat.get("id"),
                    "place": props.get("place", ""),
                    "mag": props.get("mag"),
                    "time": props.get("time"),
                    "url": props.get("url"),
                    "coordinates": coords,  # [lon, lat, depth]
                    "raw": feat
                }
                events.append(event)
                
            except Exception as e:
                print(f"Error processing USGS feature: {str(e)}")
                continue
                
        return events
        
    except Exception as e:
        print(f"Error fetching USGS data: {str(e)}")
        return []
