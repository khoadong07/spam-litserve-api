#!/usr/bin/env python3
"""
Real Estate Classified Ads Filter
Lọc các tin rao vặt bất động sản trong các category không phải real_estate
"""

import re


# Danh sách keywords rao vặt bất động sản
REAL_ESTATE_CLASSIFIED_PATTERNS = [
    # Bán nhà/đất
    r'bán nhà',
    r'bán đất',
    r'bán gấp nhà',
    r'chủ cần bán',
    r'chính chủ bán',
    r'chủ gửi bán',
    
    # Loại hình bất động sản
    r'nhà phố',
    r'căn hộ',
    r'chung cư',
    r'shophouse',
    
    # Cho thuê
    r'cho thuê phòng',
    r'phòng trọ',
    r'thuê nhà',
    r'thuê căn hộ',
    r'thuê phòng',
    r'cho thuê/bán',
    r'cho thuê\s*bán',
    
    # Tìm người ở ghép
    r'tìm người ở ghép',
    r'tìm roommate',
    r'ở chung',
    
    # Nhượng/Pass
    r'nhượng phòng',
    r'pass phòng',
    r'nhượng căn hộ',
    
    # Đất đai
    r'lô đất',
    r'nền đất',
    r'sổ hồng',
    
    # Nội thất/Điều kiện
    r'full nội thất',
    r'không chung chủ',
    
    # Giá cả + diện tích (real estate specific)
    r'\d+\s*m2\s*-\s*giá\s*\d+',  # "50M2 - GIÁ 1TỶ830"
    r'giá\s*\d+\s*tỷ',  # "GIÁ 2TỶ"
    r'\d+\s*tr\d*\s*/\s*tháng',  # "6tr5/tháng"
    
    # Phòng ngủ/WC patterns
    r'\d+\s*pn\s+\d+\s*wc',  # "1PN 1WC"
    r'\d+\s*phòng\s+ngủ',  # "1 phòng ngủ"
    
    # Hỗ trợ vay
    r'hỗ trợ vay',
    r'hỗ trợ vay bank',
    r'vay ngân hàng',
    
    # Tiện ích/Vị trí
    r'tiện ích đầy đủ',
    r'ngay cạnh vincom',
    r'hồ bơi',
    r'khu vui chơi',
    r'thư viện',
    r'bbq',
    r'sân vườn',
    r'spa',
]


def normalize_text(text):
    """Normalize text to lowercase"""
    if text is None or text == "":
        return ""
    return str(text).lower().strip()


def merge_text_fields(obj):
    """
    Merge title, content, description into single text
    
    Args:
        obj (dict): Object with fields title, content, description
        
    Returns:
        str: Merged text in lowercase
    """
    parts = []
    for key in ['title', 'content', 'description']:
        value = obj.get(key)
        if value:
            parts.append(str(value))
    return " ".join(parts).lower()


def is_real_estate_classified(text):
    """
    Check if text contains real estate classified ad patterns
    
    Args:
        text (str): Text to check (should be merged from title/content/description)
        
    Returns:
        bool: True if contains real estate classified patterns, False otherwise
    """
    text = normalize_text(text)
    
    for pattern in REAL_ESTATE_CLASSIFIED_PATTERNS:
        if re.search(pattern, text):
            return True
    
    return False


def check_real_estate_spam(obj, category):
    """
    Check if object is real estate spam for non-real_estate categories
    
    Args:
        obj (dict): Object with fields title, content, description
        category (str): Category name
        
    Returns:
        bool: True if spam (real estate classified in non-real_estate category), False otherwise
    """
    # Skip check for real_estate category
    if category == "real_estate":
        return False
    
    # Merge text fields
    merged_text = merge_text_fields(obj)
    
    # Check if contains real estate classified patterns
    return is_real_estate_classified(merged_text)


# =====================================================
# EXAMPLE USAGE
# =====================================================

if __name__ == '__main__':
    test_cases = [
        {
            "obj": {
                "title": "Hẻm xe hơi gần BV Hoàn Mỹ",
                "content": "2 tầng 74m² Chào 11.5 Tỉ. Sổ hồng riêng, hoàn công đủ.",
                "description": ""
            },
            "category": "healthcare_insurance",
            "expected": True  # Spam - real estate in healthcare
        },
        {
            "obj": {
                "title": "Cho thuê phòng trọ giá rẻ",
                "content": "Phòng trọ full nội thất, không chung chủ",
                "description": ""
            },
            "category": "finance",
            "expected": True  # Spam - real estate in finance
        },
        {
            "obj": {
                "title": "Bán nhà phố 3 tầng",
                "content": "Nhà phố đẹp, chính chủ bán",
                "description": ""
            },
            "category": "real_estate",
            "expected": False  # Not spam - real estate in real_estate category
        },
        {
            "obj": {
                "title": "Tư vấn bảo hiểm sức khỏe",
                "content": "Chúng tôi cung cấp dịch vụ bảo hiểm y tế",
                "description": ""
            },
            "category": "healthcare_insurance",
            "expected": False  # Not spam - legitimate healthcare content
        },
        {
            "obj": {
                "title": "Tìm roommate ở chung",
                "content": "Tìm người ở ghép, căn hộ 2 phòng ngủ",
                "description": ""
            },
            "category": "software_technology",
            "expected": True  # Spam - real estate in tech category
        },
    ]
    
    print("=" * 80)
    print("REAL ESTATE CLASSIFIED FILTER - TEST CASES")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result = check_real_estate_spam(test["obj"], test["category"])
        expected = test["expected"]
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"\nTest {i}: {status}")
        print(f"  Category: {test['category']}")
        print(f"  Title: {test['obj']['title']}")
        print(f"  Result: {'SPAM' if result else 'NOT SPAM'}")
        print(f"  Expected: {'SPAM' if expected else 'NOT SPAM'}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
