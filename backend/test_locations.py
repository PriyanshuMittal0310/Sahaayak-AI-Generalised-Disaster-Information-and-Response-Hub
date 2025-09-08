import asyncio
from services.nlp_service import nlp_service

async def test_location_extraction():
    test_cases = [
        "Earthquake near the city of San Francisco",
        "Flooding reported in the northern region of India",
        "Wildfire spreading rapidly through the state of California",
        "Tornado warning for areas near Oklahoma City",
        "Heavy rains cause flooding in the downtown area of Mumbai"
    ]
    
    for text in test_cases:
        print("\n" + "="*80)
        print(f"Testing: {text}")
        
        result = await nlp_service.process_text(text)
        
        print("\nDetected Locations:")
        for loc in result.get('locations', []):
            source = f" via {loc['source']}" if 'source' in loc else ""
            pattern = f" (pattern: {loc['pattern']})" if 'pattern' in loc else ""
            print(f"  - {loc['text']} ({loc['label']}{source}{pattern})")
        
        print("\nAll Entities:")
        for entity in result.get('entities', []):
            if entity['category'] != 'location':
                source = f" via {entity['source']}" if 'source' in entity else ""
                print(f"  - {entity['text']} ({entity['label']}/{entity['category']}{source})")

if __name__ == "__main__":
    asyncio.run(test_location_extraction())
