import asyncio
from services.nlp_service import nlp_service

async def test_disaster_detection(text: str, use_openai: bool = True):
    print(f"\nTesting disaster detection for text: '{text}'")
    print(f"Using {'OpenAI' if use_openai else 'Rule-based'} detection")
    
    try:
        # Test disaster type detection with enhanced information
        disaster_info = await nlp_service._detect_disaster_type(
            text, 
            use_openai=use_openai
        )
        print(f"Disaster Detection Results:")
        print(f"  - Type: {disaster_info['type']} (Confidence: {disaster_info['confidence']:.1f})")
        print(f"  - Severity: {disaster_info['severity']}")
        print(f"  - Sentiment: {disaster_info['sentiment']}")
        
        # Test full text processing
        print("\nFull text processing results:")
        result = await nlp_service.process_text(text)
        print(f"Language: {result.get('language')}")
        print(f"Disaster Type: {result.get('disaster_type')} (Confidence: {result.get('disaster_confidence', 0):.1f})")
        print(f"Severity: {result.get('disaster_severity', 'unknown')}")
        print(f"Sentiment: {result.get('sentiment')}")
        print("\nExtracted Entities:")
        
        # Group entities by category for better readability
        entities_by_category = {}
        for entity in result.get('entities', []):
            category = entity.get('category', 'other')
            if category not in entities_by_category:
                entities_by_category[category] = []
            entities_by_category[category].append(f"{entity['text']} ({entity['label']})")
        
        # Print entities by category
        for category, items in entities_by_category.items():
            print(f"  {category.upper()}:")
            for item in items:
                print(f"    - {item}")
        
        # Print locations separately for emphasis
        if result.get('locations'):
            print("\nLocations:")
            for loc in result['locations']:
                print(f"  - {loc['text']} ({loc['label']})")
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")

async def main():
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
        # First test with OpenAI (if available)
        if nlp_service.openai_client:
            await test_disaster_detection(text, use_openai=True)
        
        # Then test with rule-based
        await test_disaster_detection(text, use_openai=False)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())