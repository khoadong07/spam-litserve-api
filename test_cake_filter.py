#!/usr/bin/env python3
"""
Test script specifically for CAKE custom filter with index: 61b8715499ce4372a5d739a0
"""

import requests
import json
import time

BASE_URL = "http://103.232.122.6:8990"

def test_cake_custom_filter():
    """Test the CAKE custom filter for specific brand index"""
    print("🍰 Testing CAKE Custom Filter")
    print("Brand Index: 61b8715499ce4372a5d739a0")
    print("=" * 60)
    
    # Test data with different CAKE scenarios
    test_data = {
        "data": [
            {
                "id": "cake_fintech_001",
                "index": "61b8715499ce4372a5d739a0",  # CAKE brand
                "category": "Finance",
                "type": "article",
                "title": "CAKE by VPBank ra mắt tính năng mới",
                "description": "Ứng dụng fintech hàng đầu",
                "content": "CAKE by VPBank vừa công bố đạt 15.000 tỷ huy động từ triệu user. Team CAKE rất tự hào về sản phẩm fintech này.",
                "topic": "fintech",
                "site_id": "cake_site_001",
                "parent_id": "parent_001",
                "main_keywords": ["cake", "vpbank", "fintech"]
            },
            {
                "id": "cake_bakery_002",
                "index": "61b8715499ce4372a5d739a0",  # CAKE brand
                "category": "Food",
                "type": "article",
                "title": "Tiệm bánh CAKE mới mở",
                "description": "Đặt bánh sinh nhật",
                "content": "Tiệm bánh CAKE nhận đặt bánh sinh nhật, bánh kem, giao bánh tận nơi. Order bánh ngay hôm nay!",
                "topic": "bakery",
                "site_id": "cake_site_002",
                "parent_id": "parent_002",
                "main_keywords": ["cake", "bánh", "tiệm bánh"]
            },
            {
                "id": "cake_unrelated_003",
                "index": "61b8715499ce4372a5d739a0",  # CAKE brand
                "category": "Beauty",
                "type": "article",
                "title": "CAKE makeup tutorial",
                "description": "Hướng dẫn trang điểm",
                "content": "Hướng dẫn sử dụng phấn phủ CAKE, mỹ phẩm HUDA Beauty cho làn da hoàn hảo.",
                "topic": "beauty",
                "site_id": "cake_site_003",
                "parent_id": "parent_003",
                "main_keywords": ["cake", "makeup", "beauty"]
            },
            {
                "id": "normal_brand_004",
                "index": "other_brand_123",  # Different brand - should not use CAKE filter
                "category": "Finance",
                "type": "article",
                "title": "CAKE by VPBank content",
                "description": "Same content but different brand",
                "content": "CAKE by VPBank vừa công bố đạt 15.000 tỷ huy động từ triệu user.",
                "topic": "fintech",
                "site_id": "other_site_004",
                "parent_id": "parent_004",
                "main_keywords": ["cake", "vpbank"]
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
                    item_id = item.get("id")
                    index = item.get("index")
                    spam = item.get("spam")
                    used_custom_filter = item.get("used_custom_filter")
                    filter_reason = item.get("filter_reason")
                    
                    print(f"\n🔍 Item: {item_id}")
                    print(f"   Index: {index}")
                    print(f"   Spam: {spam}")
                    print(f"   Used Custom Filter: {used_custom_filter}")
                    print(f"   Filter Reason: {filter_reason}")
                    
                    # Analyze CAKE filter results
                    if index == "61b8715499ce4372a5d739a0":
                        if "cake_custom_filter" in filter_reason:
                            print(f"   ✅ CAKE filter applied correctly")
                            
                            # Check specific scenarios
                            if "cake_fintech" in item_id and spam == False:
                                print(f"   ✅ FINTECH content correctly marked as NOT spam")
                            elif "cake_bakery" in item_id and spam == True:
                                print(f"   ✅ BAKERY content correctly marked as spam")
                            elif "cake_unrelated" in item_id and spam == True:
                                print(f"   ✅ UNRELATED content correctly marked as spam")
                            else:
                                print(f"   ⚠️ Unexpected result for CAKE filter")
                        else:
                            print(f"   ❌ CAKE filter NOT applied for CAKE brand")
                    else:
                        if "cake_custom_filter" not in filter_reason:
                            print(f"   ✅ CAKE filter correctly NOT applied for non-CAKE brand")
                        else:
                            print(f"   ❌ CAKE filter incorrectly applied for non-CAKE brand")
                
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

def test_cake_filter_scenarios():
    """Test different CAKE filter scenarios individually"""
    print("\n🍰 Testing Individual CAKE Filter Scenarios")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "FINTECH (should be NOT spam)",
            "data": {
                "id": "fintech_test",
                "index": "61b8715499ce4372a5d739a0",
                "category": "Finance",
                "type": "article",
                "title": "VPBank CAKE fintech unicorn",
                "description": "Kỳ lân fintech Việt Nam",
                "content": "CAKE by VPBank đạt 15.000 tỷ huy động với triệu user, trở thành unicorn fintech hàng đầu.",
                "topic": "fintech",
                "site_id": "test_site",
                "parent_id": "test_parent",
                "main_keywords": ["cake", "vpbank", "fintech"]
            },
            "expected_spam": False
        },
        {
            "name": "BAKERY (should be spam)",
            "data": {
                "id": "bakery_test",
                "index": "61b8715499ce4372a5d739a0",
                "category": "Food",
                "type": "article",
                "title": "Đặt bánh sinh nhật CAKE",
                "description": "Tiệm bánh CAKE",
                "content": "Tiệm bánh CAKE nhận đặt bánh sinh nhật, bánh kem, ship bánh tận nơi. Bánh mousse, cheesecake đặc biệt.",
                "topic": "food",
                "site_id": "test_site",
                "parent_id": "test_parent",
                "main_keywords": ["cake", "bánh", "sinh nhật"]
            },
            "expected_spam": True
        },
        {
            "name": "UNRELATED (should be spam)",
            "data": {
                "id": "unrelated_test",
                "index": "61b8715499ce4372a5d739a0",
                "category": "Beauty",
                "type": "article",
                "title": "CAKE makeup collection",
                "description": "Bộ sưu tập mỹ phẩm",
                "content": "Bộ sưu tập mỹ phẩm CAKE với phấn phủ, HUDA Beauty, yến sào cao cấp.",
                "topic": "beauty",
                "site_id": "test_site",
                "parent_id": "test_parent",
                "main_keywords": ["cake", "makeup", "beauty"]
            },
            "expected_spam": True
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        
        test_data = {"data": [scenario["data"]]}
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/api/infer",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    item = result["data"][0]
                    actual_spam = item.get("spam")
                    filter_reason = item.get("filter_reason")
                    
                    expected = scenario["expected_spam"]
                    status = "✅ PASS" if actual_spam == expected else "❌ FAIL"
                    
                    print(f"   Expected spam: {expected}")
                    print(f"   Actual spam: {actual_spam}")
                    print(f"   Filter reason: {filter_reason}")
                    print(f"   Result: {status}")
                else:
                    print("   ❌ Invalid response format")
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def run_cake_filter_tests():
    """Run all CAKE filter tests"""
    print("🚀 Starting CAKE Custom Filter Tests")
    print("Target URL:", BASE_URL)
    print("CAKE Brand Index: 61b8715499ce4372a5d739a0")
    print("=" * 60)
    
    results = []
    
    # Test 1: Multiple scenarios
    results.append(("CAKE Filter Multiple Scenarios", test_cake_custom_filter()))
    
    # Test 2: Individual scenarios
    test_cake_filter_scenarios()
    
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
    
    print(f"\nTotal: {passed}/{total} main tests passed")
    
    if passed == total:
        print("🎉 All CAKE filter tests completed!")
    else:
        print(f"⚠️ {total - passed} tests failed")

if __name__ == "__main__":
    run_cake_filter_tests()