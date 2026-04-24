#!/bin/bash

# Test API on localhost (run this on the server)
BASE_URL="http://localhost:8990"

echo "🚀 Testing API on localhost"
echo "Target: $BASE_URL"
echo "=================================="

# Test 1: Health check
echo ""
echo "1️⃣ Health Check"
curl -X GET "$BASE_URL/health" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\n" \
  -s

echo ""
echo "=================================="

# Test 2: Simple test
echo ""
echo "2️⃣ Simple Test"
curl -X POST "$BASE_URL/v1/api/infer" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\n" \
  -d '{
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
  }' \
  -s

echo ""
echo "=================================="

# Test 3: Excluded site
echo ""
echo "3️⃣ Excluded Site Test"
curl -X POST "$BASE_URL/v1/api/infer" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\n" \
  -d '{
    "data": [
      {
        "id": "excluded_test",
        "index": "brand_456", 
        "category": "Finance",
        "type": "article",
        "title": "Should be excluded",
        "description": "Spam content",
        "content": "This is spam but excluded",
        "topic": "test",
        "site_id": "114144744928643",
        "parent_id": "test_parent",
        "main_keywords": ["spam"]
      }
    ]
  }' \
  -s

echo ""
echo "=================================="

# Test 4: CAKE filter
echo ""
echo "4️⃣ CAKE Filter Test"
curl -X POST "$BASE_URL/v1/api/infer" \
  -H "Content-Type: application/json" \
  -w "\nStatus: %{http_code}\n" \
  -d '{
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
  }' \
  -s

echo ""
echo "=================================="
echo "✅ Tests completed!"