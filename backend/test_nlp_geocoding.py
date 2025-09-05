#!/usr/bin/env python3
"""
Test script for NLP and Geocoding functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.nlp_service import nlp_service
from services.geocoding_service import geocoding_service

def test_nlp_service():
    """Test NLP service functionality"""
    print("Testing NLP Service...")
    
    test_texts = [
        "Earthquake magnitude 6.5 in California, USA",
        "Heavy flooding reported in Mumbai, India",
        "Wildfire spreading rapidly in Australia",
        "Hurricane approaching Florida coast",
        "Tsunami warning issued for Japan",
        "Terremoto de magnitud 7.2 en Chile",  # Spanish
        "Inondation grave à Paris, France",  # French
    ]
    
    for text in test_texts:
        print(f"\nText: {text}")
        result = nlp_service.process_text(text)
        print(f"Language: {result['language']}")
        print(f"Disaster Type: {result['disaster_type']}")
        print(f"Locations: {[loc['text'] for loc in result['locations']]}")

def test_geocoding_service():
    """Test Geocoding service functionality"""
    print("\n\nTesting Geocoding Service...")
    
    test_locations = [
        "California, USA",
        "Mumbai, India",
        "Paris, France",
        "Tokyo, Japan",
        "Sydney, Australia"
    ]
    
    for location in test_locations:
        print(f"\nLocation: {location}")
        result = geocoding_service.geocode_location(location)
        if result:
            print(f"Coordinates: {result['lat']}, {result['lon']}")
            print(f"Address: {result['formatted_address']}")
        else:
            print("Geocoding failed")

def test_integrated_processing():
    """Test integrated NLP + Geocoding processing"""
    print("\n\nTesting Integrated Processing...")
    
    test_texts = [
        "Major earthquake in Los Angeles, California",
        "Flooding reported in Mumbai, Maharashtra, India",
        "Wildfire spreading in Sydney, Australia"
    ]
    
    for text in test_texts:
        print(f"\nText: {text}")
        
        # Process with NLP
        nlp_result = nlp_service.process_text(text)
        print(f"NLP - Language: {nlp_result['language']}, Disaster: {nlp_result['disaster_type']}")
        
        # Extract locations and geocode
        locations = nlp_result.get('locations', [])
        if locations:
            location_texts = [loc['text'] for loc in locations]
            geocoding_result = geocoding_service.process_locations(location_texts)
            
            if geocoding_result:
                print(f"Geocoding - Coordinates: {geocoding_result['lat']}, {geocoding_result['lon']}")
                print(f"Geocoding - Address: {geocoding_result['formatted_address']}")
            else:
                print("Geocoding failed")
        else:
            print("No locations extracted")

if __name__ == "__main__":
    print("Starting NLP and Geocoding Tests...")
    print("=" * 50)
    
    try:
        print("Testing NLP Service...")
        test_nlp_service()
        print("\nTesting Geocoding Service...")
        test_geocoding_service()
        print("\nTesting Integrated Processing...")
        test_integrated_processing()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
