#!/usr/bin/env python3
"""
Test script for Spam Filter API
Tests both /v1/api/infer and /api/spam endpoints
"""

import requests
import json
import time
from typing import Dict, Any

# API Base URL
BASE_URL = "http://103.232.122.6:8990"

def test_health_check():
    """Test health endpoint"""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("\n🔍 Testing Root Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_infer_api():
    """Test /v1/api/infer endpoint"""
    print("\n🔍 Testing /v1/api/infer endpoint...")
    
    # Test data with various scenarios
    test_data = {
        "data": [
            {
                "id": "test_001",
                "index": "brand_123",
                "category": "Finance",
                "type": "article",
                "title": "Vay tiền nhanh chóng",
                "description": "Vay tiền online lãi suất thấp",
                "content": "Chúng tôi cung cấp dịch vụ vay tiền nhanh chóng với lãi suất ưu đãi. Liên hệ ngay!",
                "topic": "finance",
                "site_id": "site_001",
                "parent_id": "parent_001",
                "main_keywords": ["vay tiền", "lãi suất", "online"]
            },
            {
                "id": "test_002",
                "index": "69d8865a9957472efb62d227",  # Panasonic brand - should check phone/shopee
                "category": "Consumer Discretionary",
                "type": "review",
                "title": "Máy giặt Panasonic tốt",
                "description": "Review máy giặt",
                "content": "Máy giặt này rất tốt. Liên hệ 0901234567 để mua hàng.",
                "topic": "appliance",
                "site_id": "site_002",
                "parent_id": "parent_002",
                "main_keywords": ["máy giặt", "panasonic"]
            },
            {
                "id": "test_003",
                "index": "brand_456",
                "category": "Real Estate",
                "type": "newsTopic",  # Should be marked as spam=False
                "title": "Tin tức bất động sản",
                "description": "Thông tin thị trường",
                "content": "Thị trường bất động sản đang có nhiều biến động tích cực.",
                "topic": "real_estate_news",
                "site_id": "site_003",
                "parent_id": "parent_003",
                "main_keywords": ["bất động sản", "thị trường"]
            },
            {
                "id": "test_004",
                "index": "brand_789",
                "category": "Bank",
                "type": "article",
                "title": "Dịch vụ ngân hàng",
                "description": "Thông tin tài khoản",
                "content": "Mở tài khoản ngân hàng với nhiều ưu đãi hấp dẫn.",
                "topic": "banking",
                "site_id": "site_004",
                "parent_id": "parent_004",
                "main_keywords": ["ngân hàng", "tài khoản"]
            },
            {
                "id": "test_005",
                "index": "brand_999",
                "category": "Healthcare",
                "type": "article",
                "title": "😀😀😀",  # Only emoji test
                "description": "😊😊",
                "content": "🎉🎉🎉🎉🎉",
                "topic": "health",
                "site_id": "114144744928643",
                "parent_id": "parent_005",
                "main_keywords": ["emoji"]
            }
        ]
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/api/infer",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        end_time = time.time()
        
        print(f"Status: {response.status_code}")
        print(f"Response time: {end_time - start_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Validate response format
            if "status" in result and "data" in result:
                print("✅ Response format is correct")
                
                # Check each item
                for item in result["data"]:
                    required_fields = ["id", "index", "category", "type", "spam", "used_custom_filter", "filter_reason"]
                    missing_fields = [field for field in required_fields if field not in item]
                    if missing_fields:
                        print(f"⚠️ Missing fields in item {item.get('id')}: {missing_fields}")
                    else:
                        print(f"✅ Item {item.get('id')}: spam={item.get('spam')}, filter={item.get('filter_reason')}")
                
                return True
            else:
                print("❌ Invalid response format")
                return False
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Infer API test failed: {e}")
        return False

def test_spam_api():
    """Test /api/spam endpoint (original)"""
    print("\n🔍 Testing /api/spam endpoint...")
    
    test_data = {
        "items": [
            {
                "id": "spam_test_001",
                "index": "brand_123",
                "title": "Vay tiền nhanh",
                "content": "Vay tiền online với lãi suất thấp nhất thị trường",
                "description": "Dịch vụ vay tiền uy tín"
            },
            {
                "id": "spam_test_002",
                "index": "brand_456",
                "title": "Sản phẩm chất lượng",
                "content": "Sản phẩm tốt nhất với giá cả hợp lý",
                "description": "Mô tả sản phẩm"
            }
        ]
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/spam",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        end_time = time.time()
        
        print(f"Status: {response.status_code}")
        print(f"Response time: {end_time - start_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Validate response format
            if "results" in result and "count" in result:
                print("✅ Response format is correct")
                return True
            else:
                print("❌ Invalid response format")
                return False
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Spam API test failed: {e}")
        return False

def test_error_cases():
    """Test error cases"""
    print("\n🔍 Testing Error Cases...")
    
    # Test empty data
    print("Testing empty data...")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/api/infer",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Empty data - Status: {response.status_code}")
        
        # Test invalid JSON
        print("Testing invalid content type...")
        response = requests.post(
            f"{BASE_URL}/v1/api/infer",
            data="invalid json",
            headers={"Content-Type": "text/plain"},
            timeout=10
        )
        print(f"Invalid content - Status: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Error case test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting API Tests...")
    print(f"Target URL: {BASE_URL}")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Root Endpoint", test_root_endpoint()))
    results.append(("Infer API", test_infer_api()))
    results.append(("Spam API", test_spam_api()))
    results.append(("Error Cases", test_error_cases()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed")

if __name__ == "__main__":
    run_all_tests()