import asyncio
import aiohttp
import json
from typing import List, Dict, Any

API_BASE = "http://localhost:8000"

async def fetch_data(session: aiohttp.ClientSession, endpoint: str) -> Dict[str, Any]:
    """Helper function to make GET requests"""
    url = f"{API_BASE}{endpoint}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            print(f"Error fetching {url}: {response.status}")
            return {}
    except Exception as e:
        print(f"Request failed for {url}: {str(e)}")
        return {}

async def load_sample_data():
    """Load sample data from various sources"""
    endpoints = [
        "/ingest/rss",
        "/ingest/usgs",
        "/ingest/seed/reddit",
        "/ingest/seed/x"
    ]
    
    async with aiohttp.ClientSession() as session:
        # First, get the current count of items
        items_data = await fetch_data(session, "/api/items")
        current_count = len(items_data.get('items', []))
        print(f"Current items in database: {current_count}")
        
        if current_count < 50:
            print("Loading sample data...")
            # Load data from all endpoints
            tasks = [fetch_data(session, endpoint) for endpoint in endpoints]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Print results
            for endpoint, result in zip(endpoints, results):
                if isinstance(result, Exception):
                    print(f"Error in {endpoint}: {str(result)}")
                else:
                    print(f"{endpoint}: {json.dumps(result, indent=2) if result else 'No data'}")
            
            # Get updated count
            items_data = await fetch_data(session, "/api/items")
            new_count = len(items_data.get('items', []))
            print(f"\nTotal items after loading: {new_count}")
            print(f"Added {new_count - current_count} new items")
        else:
            print("Already have sufficient data (50+ items). No need to load more.")

if __name__ == "__main__":
    asyncio.run(load_sample_data())
