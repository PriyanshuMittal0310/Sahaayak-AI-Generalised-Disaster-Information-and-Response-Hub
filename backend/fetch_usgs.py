import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# USGS earthquake feed URL
USGS_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

def fetch_usgs_quakes() -> List[Dict]:
    """
    Fetch and parse real-time earthquake data from USGS feed
    
    Returns:
        List of earthquake events with relevant data
    """
    try:
        logger.info(f"Fetching earthquake data from: {USGS_FEED}")
        
        # Make request to USGS API
        response = requests.get(USGS_FEED, timeout=30)
        response.raise_for_status()
        
        # Parse JSON response
        earthquake_data = response.json()
        features = earthquake_data.get('features', [])
        
        # Parse and format the data
        events = []
        for feature in features:
            try:
                props = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                coords = geometry.get('coordinates', [])
                
                if not coords or len(coords) < 2:
                    continue
                    
                event = {
                    'id': feature.get('id'),
                    'magnitude': props.get('mag'),
                    'place': props.get('place', 'Unknown location'),
                    'time_utc': datetime.utcfromtimestamp(props.get('time') / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'coordinates': coords[:2],  # [longitude, latitude]
                    'depth': coords[2] if len(coords) > 2 else None,
                    'url': props.get('url', '')
                }
                events.append(event)
                
            except Exception as e:
                logger.error(f"Error processing earthquake feature: {e}")
                continue
        
        logger.info(f"Successfully processed {len(events)} earthquake records")
        return events
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching USGS data: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching USGS data: {e}")
        return None

def parse_earthquake_features(earthquake_data: Dict) -> List[Dict]:
    """
    Parse earthquake features from USGS data
    
    Args:
        earthquake_data: Raw earthquake data from USGS API
        
    Returns:
        List of parsed earthquake records
    """
    if not earthquake_data or 'features' not in earthquake_data:
        return []
    
    parsed_earthquakes = []
    
    for feature in earthquake_data['features']:
        try:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('coordinates', [])
            
            # Extract relevant earthquake information
            earthquake = {
                'id': feature.get('id'),
                'magnitude': properties.get('mag'),
                'place': properties.get('place'),
                'time': datetime.fromtimestamp(properties.get('time', 0) / 1000).isoformat() if properties.get('time') else None,
                'updated': datetime.fromtimestamp(properties.get('updated', 0) / 1000).isoformat() if properties.get('updated') else None,
                'url': properties.get('url'),
                'detail': properties.get('detail'),
                'felt': properties.get('felt'),
                'cdi': properties.get('cdi'),
                'mmi': properties.get('mmi'),
                'alert': properties.get('alert'),
                'status': properties.get('status'),
                'tsunami': properties.get('tsunami'),
                'sig': properties.get('sig'),
                'net': properties.get('net'),
                'code': properties.get('code'),
                'ids': properties.get('ids'),
                'sources': properties.get('sources'),
                'types': properties.get('types'),
                'nst': properties.get('nst'),
                'dmin': properties.get('dmin'),
                'rms': properties.get('rms'),
                'gap': properties.get('gap'),
                'magType': properties.get('magType'),
                'type': properties.get('type'),
                'title': properties.get('title'),
                'longitude': coordinates[0] if len(coordinates) > 0 else None,
                'latitude': coordinates[1] if len(coordinates) > 1 else None,
                'depth': coordinates[2] if len(coordinates) > 2 else None
            }
            
            parsed_earthquakes.append(earthquake)
            
        except Exception as e:
            logger.warning(f"Error parsing earthquake feature: {e}")
            continue
    
    return parsed_earthquakes

def get_recent_earthquakes(min_magnitude: float = 0.0) -> List[Dict]:
    """
    Get recent earthquakes with optional magnitude filter
    
    Args:
        min_magnitude: Minimum magnitude threshold (default: 0.0)
        
    Returns:
        List of filtered earthquake records
    """
    # Fetch raw data
    raw_data = fetch_usgs_quakes()
    if not raw_data:
        return []
    
    # Parse earthquake features
    earthquakes = parse_earthquake_features(raw_data)
    
    # Filter by magnitude if specified
    if min_magnitude > 0.0:
        earthquakes = [
            eq for eq in earthquakes 
            if eq.get('magnitude') is not None and eq['magnitude'] >= min_magnitude
        ]
    
    # Sort by magnitude (descending)
    earthquakes.sort(key=lambda x: x.get('magnitude', 0), reverse=True)
    
    logger.info(f"Returning {len(earthquakes)} earthquakes (min magnitude: {min_magnitude})")
    
    return earthquakes

if __name__ == "__main__":
    # Test the functions
    print("Testing USGS earthquake data fetcher...")
    
    # Fetch and display recent earthquakes
    earthquakes = get_recent_earthquakes(min_magnitude=2.0)
    
    if earthquakes:
        print(f"\nFound {len(earthquakes)} earthquakes with magnitude >= 2.0:")
        for eq in earthquakes[:5]:  # Show top 5
            print(f"- {eq['title']} (Magnitude: {eq['magnitude']})")
    else:
        print("No earthquake data available")
