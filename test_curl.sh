#!/bin/bash

# Test script using curl for Spam Filter API
# Usage: ./test_curl.sh

BASE_URL="http://103.232.122.6:8990"

echo "🚀 Testing Spam Filter API with curl"
echo "Target URL: $BASE_URL"
echo "=================================================="

# Test 1: Health Check
echo ""
echo "🔍 Test 1: Health Check"
echo "GET $BASE_URL/health"
curl -X GET "$BASE_URL/health" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -s

echo ""
echo "=================================================="

# Test 2: Root Endpoint
echo ""
echo "🔍 Test 2: Root Endpoint"
echo "GET $BASE_URL/"
curl -X GET "$BASE_URL/" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -s

echo ""
echo "=================================================="

# Test 3: Infer API
echo ""
echo "🔍 Test 3: Infer API (/v1/api/infer)"
echo "POST $BASE_URL/v1/api/infer"

curl -X POST "$BASE_URL/v1/api/infer" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -d '{
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
        "index": "69d8865a9957472efb62d227",
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
        "type": "newsTopic",
        "title": "Tin tức bất động sản",
        "description": "Thông tin thị trường",
        "content": "Thị trường bất động sản đang có nhiều biến động tích cực.",
        "topic": "real_estate_news",
        "site_id": "site_003",
        "parent_id": "parent_003",
        "main_keywords": ["bất động sản", "thị trường"]
      }
    ]
  }' \
  -s

echo ""
echo "=================================================="

# Test 4: Original Spam API
echo ""
echo "🔍 Test 4: Original Spam API (/api/spam)"
echo "POST $BASE_URL/api/spam"

curl -X POST "$BASE_URL/api/spam" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -d '{
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
  }' \
  -s

echo ""
echo "=================================================="

# Test 5: Error Case - Empty Data
echo ""
echo "🔍 Test 5: Error Case - Empty Data"
echo "POST $BASE_URL/v1/api/infer (empty data)"

curl -X POST "$BASE_URL/v1/api/infer" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -d '{}' \
  -s

echo ""
echo "=================================================="

# Test 6: Error Case - Invalid JSON
echo ""
echo "🔍 Test 6: Error Case - Invalid JSON"
echo "POST $BASE_URL/v1/api/infer (invalid json)"

curl -X POST "$BASE_URL/v1/api/infer" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -d 'invalid json' \
  -s

echo ""
echo "=================================================="
echo "✅ All tests completed!"