#!/usr/bin/env python3
"""
Test production API server
"""

import requests
import json
import time
import sys

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8990/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Device: {data.get('device')}")
            print(f"   Model: {data.get('model')}")
            print(f"   ML Enabled: {data.get('ml_enabled')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_infer_api():
    """Test infer API endpoint"""
    test_data = {
        "data": [
            {
                "id": "test_1",
                "index": "61b8715499ce4372a5d739a0",  # CAKE brand
                "category": "Finance",
                "type": "post",
                "title": "VPBank ra mắt ứng dụng CAKE mới",
                "content": "Ứng dụng CAKE của VPBank giúp bạn quản lý tài chính dễ dàng",
                "description": "Fintech app từ VPBank",
                "site_id": "123456789",
                "parent_id": "",
                "topic": "banking"
            },
            {
                "id": "test_2", 
                "index": "test_brand",
                "category": "Consumer Discretionary",
                "type": "post",
                "title": "Bán nhà đất giá rẻ",
                "content": "Cần bán gấp nhà đất tại Hà Nội, giá 2 tỷ, liên hệ 0123456789",
                "description": "Bất động sản",
                "site_id": "987654321",
                "parent_id": "",
                "topic": "real_estate"
            }
        ]
    }
    
    try:
        print("🧪 Testing /v1/api/infer endpoint...")
        start_time = time.time()
        response = requests.post(
            "http://localhost:8990/v1/api/infer",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Infer API test passed ({end_time - start_time:.2f}s)")
            print(f"   Status: {data.get('status')}")
            print(f"   Results: {len(data.get('data', []))}")
            
            for result in data.get('data', []):
                print(f"   - ID: {result.get('id')}")
                print(f"     Spam: {result.get('spam')}")
                print(f"     Custom Filter: {result.get('used_custom_filter')}")
                print(f"     Reason: {result.get('filter_reason')}")
            return True
        else:
            print(f"❌ Infer API test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Infer API test error: {e}")
        return False

def test_spam_api():
    """Test spam API endpoint"""
    test_data = {
        "items": [
            {
                "id": "spam_test_1",
                "index": "test_index",
                "title": "Khuyến mãi lớn",
                "content": "Giảm giá 50% tất cả sản phẩm, mua ngay kẻo lỡ!",
                "description": "Sale khủng"
            },
            {
                "id": "spam_test_2",
                "index": "test_index",
                "title": "Tin tức công nghệ",
                "content": "Apple ra mắt iPhone mới với nhiều tính năng đột phá",
                "description": "Tech news"
            }
        ]
    }
    
    try:
        print("🧪 Testing /api/spam endpoint...")
        start_time = time.time()
        response = requests.post(
            "http://localhost:8990/api/spam",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Spam API test passed ({end_time - start_time:.2f}s)")
            print(f"   Results: {data.get('count')}")
            
            for result in data.get('results', []):
                print(f"   - ID: {result.get('id')}")
                print(f"     Label: {result.get('label')}")
                print(f"     Score: {result.get('score'):.3f}")
                print(f"     Is Spam: {result.get('is_spam')}")
            return True
        else:
            print(f"❌ Spam API test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Spam API test error: {e}")
        return False

def test_performance():
    """Test API performance with multiple requests"""
    print("🚀 Testing API performance...")
    
    test_data = {
        "data": [
            {
                "id": f"perf_test_{i}",
                "index": "test_brand",
                "category": "Finance",
                "type": "post",
                "title": f"Test title {i}",
                "content": f"This is test content {i} for performance testing",
                "description": f"Test description {i}",
                "site_id": "123456789"
            }
            for i in range(10)  # 10 items per request
        ]
    }
    
    num_requests = 5
    total_time = 0
    successful_requests = 0
    
    for i in range(num_requests):
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:8990/v1/api/infer",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                successful_requests += 1
                request_time = end_time - start_time
                total_time += request_time
                print(f"   Request {i+1}: {request_time:.2f}s")
            else:
                print(f"   Request {i+1}: Failed ({response.status_code})")
        except Exception as e:
            print(f"   Request {i+1}: Error ({e})")
    
    if successful_requests > 0:
        avg_time = total_time / successful_requests
        throughput = (successful_requests * 10) / total_time  # items per second
        print(f"✅ Performance test completed")
        print(f"   Successful requests: {successful_requests}/{num_requests}")
        print(f"   Average response time: {avg_time:.2f}s")
        print(f"   Throughput: {throughput:.1f} items/second")
        return True
    else:
        print("❌ Performance test failed - no successful requests")
        return False

def main():
    print("🧪 Production API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Infer API", test_infer_api),
        ("Spam API", test_spam_api),
        ("Performance", test_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the API server.")
        return 1

if __name__ == "__main__":
    sys.exit(main())