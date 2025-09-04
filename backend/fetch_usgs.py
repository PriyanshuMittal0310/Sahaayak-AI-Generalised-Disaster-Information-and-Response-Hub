import requests
from datetime import datetime

USGS_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

def fetch_usgs_quakes():
    r = requests.get(USGS_FEED, timeout=10)
    r.raise_for_status()
    data = r.json()

    events = []
    for feat in data.get("features", []):
        props = feat["properties"]
        geom = feat["geometry"] or {}
        coords = (geom.get("coordinates") or [None, None, None])

        events.append({
            "id": feat.get("id"),
            "place": props.get("place"),
            "magnitude": props.get("mag"),
            "time_utc": datetime.utcfromtimestamp(props["time"]/1000).isoformat() if props.get("time") else None,
            "url": props.get("url"),
            "coordinates": coords,  # [lon, lat, depth]
            "raw": feat
        })
    return events
