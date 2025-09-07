import logging
import sys
from fetch_rss import fetch_gdacs_feed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    print("Testing GDACS feed...")
    events = fetch_gdacs_feed()
    print(f"\nFound {len(events)} events:")
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   Type: {event['disaster_type']}")
        print(f"   Location: {event.get('lat')}, {event.get('lon')}")
        print(f"   Published: {event.get('published')}")
        print(f"   Link: {event.get('link')}")

if __name__ == "__main__":
    main()
