import asyncio
from services.nlp_service import nlp_service

async def test_disaster_detection():
    test_cases = [
        # Geological
        "Major earthquake hits Tokyo with magnitude 6.5 - buildings collapsed",
        "Volcanic eruption in Iceland forces mass evacuation",
        "Massive landslide blocks major highway in the mountains",
        "Sinkhole swallows car in downtown area",
        
        # Hydrological
        "Severe flooding reported in Mumbai after heavy monsoon rains",
        "Tsunami warning issued after 7.8 magnitude earthquake near coast",
        "Drought conditions worsen in the region, water rationing begins",
        
        # Meteorological
        "Tornado warning issued for Oklahoma county - take shelter immediately",
        "Record-breaking heatwave grips Europe, temperatures soar to 45°C",
        "Blizzard conditions paralyze transportation in northern states",
        
        # Climatological
        "Wildfire spreads rapidly through California forests, thousands evacuated",
        "Massive industrial fire engulfs chemical plant, toxic smoke spreads",
        
        # Biological
        "New virus outbreak reported in Asia, WHO issues pandemic alert",
        "Locust swarm destroys crops across East Africa",
        
        # Technological
        "Chemical spill at factory prompts evacuation of nearby residents",
        "Train derailment causes major disruption to commuter services",
        "Major power outage leaves millions without electricity",
        
        # Human-made
        "Suicide bombing at market kills dozens, terrorist group claims responsibility",
        "Nationwide protests turn violent as police clash with demonstrators",
        "Airstrikes target capital city as conflict escalates"
    ]
    
    for text in test_cases:
        print("\n" + "="*80)
        print(f"Testing: {text}")
        
        # Get disaster detection results
        disaster_info = await nlp_service._detect_disaster_type(text, use_openai=False)
        
        # Print results
        print("\nDisaster Detection Results:")
        print(f"  - Type: {disaster_info['type']}")
        print(f"  - Severity: {disaster_info['severity']}")
        print(f"  - Sentiment: {disaster_info['sentiment']}")
        print(f"  - Confidence: {disaster_info['confidence']:.1f}")
        
        # Process full text to show entity extraction
        result = await nlp_service.process_text(text)
        if result.get('locations'):
            print("\nDetected Locations:")
            for loc in result['locations']:
                source = f" via {loc['source']}" if 'source' in loc else ""
                pattern = f" (pattern: {loc['pattern']})" if 'pattern' in loc else ""
                print(f"  - {loc['text']} ({loc['label']}{source}{pattern})")
        
        # Show all entities if any
        if result.get('entities'):
            print("\nAll Entities:")
            for entity in result['entities']:
                if entity['category'] != 'location':  # Skip locations already shown
                    source = f" via {entity['source']}" if 'source' in entity else ""
                    print(f"  - {entity['text']} ({entity['label']}/{entity['category']}{source})")

if __name__ == "__main__":
    asyncio.run(test_disaster_detection())
