#!/usr/bin/env python3
"""
Simple test script to verify backend connectivity
"""

import requests
import json
import sys

def test_backend():
    base_url = "http://localhost:8000"
    
    print("Testing CrisisConnect Backend...")
    print("=" * 50)
    
    # Test 1: Health check
    try:
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    # Test 2: Root endpoint
    try:
        print("\n2. Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Root endpoint passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Root endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Root endpoint failed: {e}")
    
    # Test 3: Items endpoint
    try:
        print("\n3. Testing items endpoint...")
        response = requests.get(f"{base_url}/api/items", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Items endpoint passed")
            print(f"   Found {data.get('count', 0)} items")
        else:
            print(f"   ❌ Items endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Items endpoint failed: {e}")
    
    # Test 4: USGS ingestion
    try:
        print("\n4. Testing USGS ingestion...")
        response = requests.get(f"{base_url}/ingest/usgs", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ USGS ingestion passed")
            print(f"   Inserted: {data.get('inserted', 0)} new items")
            print(f"   Fetched: {data.get('fetched', 0)} total events")
        else:
            print(f"   ❌ USGS ingestion failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ USGS ingestion failed: {e}")
    
    # Test 5: Credibility stats
    try:
        print("\n5. Testing credibility stats...")
        response = requests.get(f"{base_url}/api/credibility-stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Credibility stats passed")
            print(f"   Total items: {data.get('total_items', 0)}")
            print(f"   Items with credibility: {data.get('items_with_credibility', 0)}")
        else:
            print(f"   ❌ Credibility stats failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Credibility stats failed: {e}")
    
    print("\n" + "=" * 50)
    print("Backend test completed!")
    return True

if __name__ == "__main__":
    test_backend()
