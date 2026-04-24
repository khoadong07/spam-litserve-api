#!/usr/bin/env python3
"""
Test script to run directly on the server (localhost)
"""

import requests
import json
import time

# Use localhost since we're running on the same server
BASE_URL = "http://localhost:8990"

def test_local_api():
    """Test API on localhost"""
    print("🚀 Testing API on localhost")
    print(f"Target: {BASE_URL}")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1️⃣ Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test 2: Simple infer test
    print("\n2️⃣ Simple Infer Test")
    test_data = {
        "data": [
            {
                "id": "test_001",
                "index": "brand_123",
                "category": "Finance",
                "type": "article",
                "title": "Test content",
                "description": "Test description",
                "content": "This is test content",
                "topic": "test",
                "site_id": "test_site",
                "parent_id": "test_parent",
                "main_keywords": ["test"]
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/api/infer",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
    
    # Test 3: Excluded site test
    print("\n3️⃣ Excluded Site Test (114144744928643)")
    excluded_test_data = {
        "data": [
            {
                "id": "excluded_test",
                "index": "brand_456",
                "category": "Finance",
                "type": "article",
                "title": "This should be excluded",
                "description": "Spam content",
                "content": "This is spam content but site is excluded",
                "topic": "test",
                "site_id": "114144744928643",
                "parent_id": "test_parent",
                "main_keywords": ["spam"]
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/api/infer",
            json=excluded_test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Check if excluded site works
            if "data" in result and len(result["data"]) > 0:
                item = result["data"][0]
                if item.get("filter_reason") == "excluded_site":
                    print("✅ Excluded site filter working correctly!")
                else:
                    print(f"⚠️ Expected excluded_site, got: {item.get('filter_reason')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Excluded site test failed: {e}")
    
    # Test 4: CAKE filter test
    print("\n4️⃣ CAKE Filter Test (61b8715499ce4372a5d739a0)")
    cake_test_data = {
        "data": [
            {
                "id": "cake_test",
                "index": "61b8715499ce4372a5d739a0",
                "category": "Finance",
                "type": "article",
                "title": "CAKE by VPBank fintech",
                "description": "Fintech unicorn",
                "content": "CAKE by VPBank là ứng dụng fintech hàng đầu với triệu user",
                "topic": "fintech",
                "site_id": "cake_site",
                "parent_id": "cake_parent",
                "main_keywords": ["cake", "vpbank", "fintech"]
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/api/infer",
            json=cake_test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Check if CAKE filter works
            if "data" in result and len(result["data"]) > 0:
                item = result["data"][0]
                filter_reason = item.get("filter_reason", "")
                if "cake_custom_filter" in filter_reason:
                    print("✅ CAKE custom filter working correctly!")
                else:
                    print(f"⚠️ Expected cake_custom_filter, got: {filter_reason}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ CAKE filter test failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    test_local_api()