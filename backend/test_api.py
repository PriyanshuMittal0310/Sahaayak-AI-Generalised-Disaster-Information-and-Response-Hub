import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_single_detection():
    """Test single disaster detection endpoint"""
    url = f"{BASE_URL}/api/disasters/detect"
    test_text = "A massive earthquake has struck Tokyo, Japan. The magnitude 7.5 quake has caused significant damage to buildings and infrastructure."
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={"text": test_text, "detect_language": True, "use_openai": False}
        )
        
        print("\nSingle Detection Test:")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))

async def test_batch_detection():
    """Test batch disaster detection endpoint"""
    url = f"{BASE_URL}/api/disasters/batch-detect"
    test_texts = [
        "Wildfires are spreading rapidly through California forests, forcing evacuations.",
        "Heavy monsoon rains cause severe flooding in Mumbai, India.",
        "A tornado touched down in Oklahoma, causing widespread damage.",
        "Chemical spill reported at industrial plant in Houston, Texas."
    ]
    
    payload = [{"text": text, "detect_language": True, "use_openai": False} 
              for text in test_texts]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        
        print("\nBatch Detection Test:")
        print(f"Status Code: {response.status_code}")
        print("Responses:")
        for i, result in enumerate(response.json(), 1):
            print(f"\n--- Item {i} ---")
            print(f"Text: {result.get('text', '')}")
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Detected Disaster: {result.get('disaster_type', 'None')}")
                print(f"Severity: {result.get('disaster_severity', 'unknown')}")
                print(f"Sentiment: {result.get('sentiment', 'neutral')}")
                
                if 'locations' in result and result['locations']:
                    print("\nLocations:")
                    for loc in result['locations']:
                        print(f"  - {loc.get('text', '')} ({loc.get('label', 'LOCATION')})")

async def main():
    print("Testing Disaster Detection API Endpoints")
    print("======================================")
    
    try:
        await test_single_detection()
        await test_batch_detection()
    except Exception as e:
        print(f"Error testing API: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
