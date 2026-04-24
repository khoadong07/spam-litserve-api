#!/usr/bin/env python3
"""
Test script specifically for excluded site ID: 114144744928643
"""

import requests
import json
import time

# API Base URL
BASE_URL = "http://103.232.122.6:8990"

def test_excluded_site_114144744928643():
    """Test the specific excluded site ID: 114144744928643"""
    print("🔍 Testing Excluded Site ID: 114144744928643")
    print("=" * 60)
    
    # Test data with the excluded site_id
    test_data = {
        "data": [
            {
                "id": "excluded_test_001",
                "index": "brand_123",
                "category": "Finance",
                "type": "article",
                "title": "Vay tiền nhanh chóng - SPAM CONTENT",
                "description": "Vay tiền online lãi suất thấp - SPAM",
                "content": "Chúng tôi cung cấp dịch vụ vay tiền nhanh chóng với lãi suất ưu đãi. Liên hệ ngay! Đây là nội dung spam rõ ràng.",
                "topic": "finance",
                "site_id": "114144744928643",  # This is the excluded site ID
                "parent_id": "parent_001",
                "main_keywords": ["vay tiền", "lãi suất", "spam"]
            },
            {
                "id": "normal_test_002",
                "index": "brand_456",
                "category": "Finance",
                "type": "article",
                "title": "Vay tiền nhanh chóng - SAME CONTENT",
                "description": "Vay tiền online lãi suất thấp - SAME",
                "content": "Chúng tôi cung cấp dịch vụ vay tiền nhanh chóng với lãi suất ưu đãi. Liên hệ ngay! Đây là nội dung spam rõ ràng.",
                "topic": "finance",
                "site_id": "normal_site_123",  # This is NOT excluded
                "parent_id": "parent_002",
                "main_keywords": ["vay tiền", "lãi suất", "spam"]
            }
        ]
    }
    
    try:
        print("📤 Sending request to /v1/api/infer...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/v1/api/infer",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        end_time = time.time()
        
        print(f"⏱️ Response time: {end_time - start_time:.2f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n📋 Response Analysis:")
            print("=" * 60)
            
            if "data" in result:
                for item in result["data"]:
                    site_id = item.get("site_id", "N/A")
                    spam = item.get("spam")
                    used_custom_filter = item.get("used_custom_filter")
                    filter_reason = item.get("filter_reason")
                    
                    print(f"\n🔍 Item ID: {item.get('id')}")
                    print(f"   Site ID: {site_id}")
                    print(f"   Spam: {spam}")
                    print(f"   Used Custom Filter: {used_custom_filter}")
                    print(f"   Filter Reason: {filter_reason}")
                    
                    # Check if excluded site is handled correctly
                    if site_id == "114144744928643":
                        if spam == False and used_custom_filter == True and filter_reason == "excluded_site":
                            print("   ✅ CORRECT: Excluded site properly handled")
                        else:
                            print("   ❌ ERROR: Excluded site not handled correctly")
                            print(f"      Expected: spam=False, used_custom_filter=True, filter_reason='excluded_site'")
                            print(f"      Got: spam={spam}, used_custom_filter={used_custom_filter}, filter_reason='{filter_reason}'")
                    else:
                        print(f"   ℹ️ Normal site processing")
                
                print("\n" + "=" * 60)
                print("📄 Full Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                return True
            else:
                print("❌ Invalid response format - missing 'data' field")
                print(f"Response: {response.text}")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_multiple_excluded_sites():
    """Test multiple excluded sites at once"""
    print("\n🔍 Testing Multiple Excluded Sites")
    print("=" * 60)
    
    # Test data with multiple excluded site_ids
    test_data = {
        "data": [
            {
                "id": "excluded_001",
                "index": "brand_1",
                "category": "Finance",
                "type": "article",
                "title": "Spam content 1",
                "description": "Spam description 1",
                "content": "This should be spam but site is excluded",
                "topic": "finance",
                "site_id": "114144744928643",  # Excluded
                "parent_id": "parent_001",
                "main_keywords": ["spam"]
            },
            {
                "id": "excluded_002",
                "index": "brand_2",
                "category": "Finance",
                "type": "article",
                "title": "Spam content 2",
                "description": "Spam description 2",
                "content": "This should be spam but site is excluded",
                "topic": "finance",
                "site_id": "fireant.vn",  # Also excluded (from config)
                "parent_id": "parent_002",
                "main_keywords": ["spam"]
            },
            {
                "id": "normal_001",
                "index": "brand_3",
                "category": "Finance",
                "type": "article",
                "title": "Spam content 3",
                "description": "Spam description 3",
                "content": "This should be processed normally",
                "topic": "finance",
                "site_id": "normal_site_456",  # Not excluded
                "parent_id": "parent_003",
                "main_keywords": ["spam"]
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/api/infer",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("📋 Results Summary:")
            excluded_count = 0
            normal_count = 0
            
            for item in result.get("data", []):
                site_id = item.get("site_id")
                filter_reason = item.get("filter_reason")
                
                if filter_reason == "excluded_site":
                    excluded_count += 1
                    print(f"   ✅ {item.get('id')}: Site {site_id} correctly excluded")
                else:
                    normal_count += 1
                    print(f"   ℹ️ {item.get('id')}: Site {site_id} processed normally ({filter_reason})")
            
            print(f"\n📊 Summary: {excluded_count} excluded, {normal_count} processed normally")
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def run_excluded_site_tests():
    """Run all excluded site tests"""
    print("🚀 Starting Excluded Site Tests")
    print("Target URL:", BASE_URL)
    print("Testing Site ID: 114144744928643")
    print("=" * 60)
    
    results = []
    
    # Test 1: Specific excluded site
    results.append(("Excluded Site 114144744928643", test_excluded_site_114144744928643()))
    
    # Test 2: Multiple excluded sites
    results.append(("Multiple Excluded Sites", test_multiple_excluded_sites()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All excluded site tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed")

if __name__ == "__main__":
    run_excluded_site_tests()