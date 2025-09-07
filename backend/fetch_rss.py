import feedparser
import re
from datetime import datetime, timezone
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("rss_fetcher")

def extract_coordinates(entry):
    """Extract coordinates from GDACS entry"""
    # Try to get coordinates from georss:point
    if hasattr(entry, 'georss_point'):
        try:
            parts = entry.georss_point.strip().split()
            if len(parts) >= 2:
                lat = float(parts[0])
                lon = float(parts[1])
                # Validate coordinates
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
        except (ValueError, AttributeError, IndexError) as e:
            logger.warning(f"Error parsing georss_point: {e}")
    
    # Try to extract from georss:where/gml:Point/gml:pos
    if hasattr(entry, 'where') and hasattr(entry.where, 'Point') and hasattr(entry.where.Point, 'pos'):
        try:
            lat, lon = map(float, entry.where.Point.pos.strip().split())
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error parsing gml:pos: {e}")
    
    # Try to extract from description using more flexible patterns
    if hasattr(entry, 'description'):
        desc = entry.description
        # Look for patterns like:
        # - "Location: 10.123, 20.456"
        # - "10.123°N 20.456°E"
        # - "10.123, 20.456"
        patterns = [
            r'Location:[^\d-]*([-\d.]+)[^\d-]*([-\d.]+)',
            r'([-\d.]+)°?[NS]\s*([-\d.]+)°?[EW]',
            r'([-\d.]+)[,\s]+([-\d.]+)'
        ]
        
        for pattern in patterns:
            coord_match = re.search(pattern, desc, re.IGNORECASE)
            if coord_match:
                try:
                    lat = float(coord_match.group(1))
                    lon = float(coord_match.group(2))
                    # Convert to decimal if in DMS format
                    if '°' in coord_match.group(0):
                        lat = float(lat)
                        lon = float(lon)
                    # Validate coordinates
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return lat, lon
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing coordinates from description: {e}")
    
    # If still no coordinates, try to geocode the country name
    if hasattr(entry, 'title'):
        country_match = re.search(r'\bin\s+([A-Za-z\s]+)$', entry.title)
        if country_match:
            country = country_match.group(1).strip()
            logger.info(f"Attempting to geocode country: {country}")
            # Return a default location for the country (center point)
            # Note: In a production environment, you'd want to use a geocoding service here
            country_coords = {
                'burkina faso': (12.2383, -1.5616),
                'benin': (9.3077, 2.3158),
                'cote d\'ivoire': (7.5400, -5.5471),
                'ghana': (7.9465, -1.0232),
                'nigeria': (9.0820, 8.6753),
                'togo': (8.6195, 0.8248),
                'madagascar': (-18.7669, 46.8691),
                'bolivia': (-16.2902, -63.5887),
                'brazil': (-14.2350, -51.9253)
            }
            
            for name, coords in country_coords.items():
                if name in entry.title.lower():
                    logger.info(f"Using default coordinates for {name}: {coords}")
                    return coords
    
    return None, None

def extract_disaster_type(entry):
    """Extract disaster type from GDACS entry"""
    # Try to get from GDACS event type if available
    if hasattr(entry, 'gdacs_eventtype'):
        event_type = entry.gdacs_eventtype.lower()
        if event_type in ['eq', 'earthquake']:
            return 'earthquake'
        elif event_type in ['fl', 'flood']:
            return 'flood'
        elif event_type in ['tc', 'cyclone', 'hurricane', 'typhoon']:
            return 'cyclone'
        elif event_type in ['dr', 'drought']:
            return 'drought'
        elif event_type in ['wf', 'wildfire']:
            return 'wildfire'
        elif event_type in ['vo', 'volcano']:
            return 'volcano'
        elif event_type in ['ts', 'tsunami']:
            return 'tsunami'
    
    # Check categories/tags
    if hasattr(entry, 'tags'):
        for tag in entry.tags:
            term = tag.term.lower()
            if term in ['earthquake', 'flood', 'storm', 'drought', 'wildfire', 'cyclone', 'volcano', 'tsunami']:
                return term
    
    # Try to determine from title/description
    text = f"{entry.get('title', '')} {entry.get('summary', '')} {entry.get('description', '')}".lower()
    
    # More comprehensive disaster type detection
    disaster_keywords = {
        'earthquake': ['earthquake', 'quake', 'seismic', 'tremor'],
        'flood': ['flood', 'inundation', 'deluge', 'flash flood'],
        'cyclone': ['cyclone', 'hurricane', 'typhoon', 'tropical storm', 'tropical depression'],
        'drought': ['drought', 'dry spell', 'water shortage'],
        'wildfire': ['wildfire', 'bushfire', 'forest fire', 'brush fire'],
        'volcano': ['volcano', 'volcanic', 'eruption', 'ash cloud', 'lava'],
        'tsunami': ['tsunami', 'tidal wave', 'seismic sea wave'],
        'storm': ['storm', 'thunderstorm', 'hailstorm', 'snowstorm', 'blizzard']
    }
    
    for d_type, keywords in disaster_keywords.items():
        if any(keyword in text for keyword in keywords):
            return d_type
    
    # Default to 'unknown' if no match found
    return 'unknown'

def fetch_gdacs_feed():
    """
    Fetch disaster alerts from GDACS RSS feed.
    Returns a list of disaster events with relevant details.
    """
    GDACS_RSS_URL = "https://www.gdacs.org/xml/rss.xml"
    
    try:
        # Use requests with a timeout and user-agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(GDACS_RSS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse with feedparser
        feed = feedparser.parse(response.content)
        events = []
        
        for entry in feed.entries:
            try:
                # Extract coordinates
                lat, lon = extract_coordinates(entry)
                
                # Parse published date
                published = datetime.now(timezone.utc)
                if hasattr(entry, 'published_parsed'):
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                
                # Determine disaster type
                disaster_type = extract_disaster_type(entry)
                
                # Get description text
                description = entry.get('description', '')
                if not description and hasattr(entry, 'content'):
                    description = ' '.join([c.value for c in entry.content if hasattr(c, 'value')])
                
                event = {
                    "id": entry.get('id', entry.get('link', str(hash(entry.get('title', ''))))),
                    "title": entry.get('title', 'No title').strip(),
                    "summary": description,
                    "link": entry.get('link', ''),
                    "published": published.isoformat(),
                    "lat": lat,
                    "lon": lon,
                    "disaster_type": disaster_type,
                    "source_feed": "GDACS",
                    "raw": str(entry)  # Convert to string to avoid serialization issues
                }
                # Only add events with valid coordinates
                if lat is not None and lon is not None:
                    events.append(event)
                else:
                    logger.warning(f"Skipping entry due to missing coordinates: {event.get('title')}")
                
            except Exception as e:
                logger.error(f"Error processing GDACS entry {entry.get('id', 'unknown')}: {str(e)}")
                continue
                
        logger.info(f"Successfully fetched {len(events)} events from GDACS")
        return events
        
    except Exception as e:
        logger.error(f"Error fetching GDACS feed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def fetch_rss_items():
    """
    Main function to fetch all RSS feeds.
    Currently only fetches from GDACS but can be extended.
    """
    gdacs_events = fetch_gdacs_feed()
    return gdacs_events
