#!/usr/bin/env python3
"""
Bank Category Spam Classifier
Lọc các tin không thuộc ngành ngân hàng trong category "bank"
Sử dụng scoring system để giảm false positive
"""

import re


# Scoring system cho bank spam detection
BANK_SPAM_INDICATORS = {
    # High confidence non-bank indicators (3 points each)
    'high_confidence_non_bank': [
        r'bán nhà',
        r'bán đất',
        r'cho thuê phòng',
        r'phòng trọ',
        r'tìm người ở ghép',
        r'tìm roommate',
        r'sổ hồng',
        r'chính chủ bán',
        r'full nội thất',
        r'tuyển dụng',
        r'cần tuyển',
        r'việc làm',
        r'ứng tuyển',
        r'cv',
        r'resume',
    ],
    
    # Medium confidence non-bank indicators (2 points each)
    'medium_confidence_non_bank': [
        r'bán hàng',
        r'sản phẩm',
        r'khuyến mãi',
        r'giảm giá',
        r'mua ngay',
        r'đặt hàng',
        r'ship cod',
        r'freeship',
        r'donate',
        r'quyên góp',
        r'từ thiện',
        r'ủng hộ',
    ],
    
    # Property/Real estate indicators (2 points each)
    'real_estate_indicators': [
        r'căn hộ',
        r'chung cư',
        r'nhà phố',
        r'shophouse',
        r'lô đất',
        r'nền đất',
        r'mặt tiền',
        r'hẻm xe hơi',
    ],
    
    # Job/Recruitment indicators (1.5 points each)
    'job_indicators': [
        r'lương',
        r'thử việc',
        r'phỏng vấn',
        r'làm việc tại',
        r'kinh nghiệm',
        r'bằng cấp',
        r'chứng chỉ',
    ],
    
    # E-commerce indicators (1 point each)
    'ecommerce_indicators': [
        r'shop',
        r'store',
        r'bán online',
        r'order',
        r'inbox',
        r'zalo',
        r'liên hệ mua',
    ],
    
    # Suspicious bank mentions (1.5 points each)
    'suspicious_bank_mentions': [
        r'hỗ trợ vay bank',
        r'gần ngân hàng',
        r'số tài khoản',
        r'stk',
        r'chuyển khoản',
        r'banking',
    ]
}

# Legitimate bank context - decrease score
LEGITIMATE_BANK_CONTEXT = [
    r'dịch vụ ngân hàng',
    r'sản phẩm ngân hàng',
    r'lãi suất',
    r'tiền gửi',
    r'tiết kiệm',
    r'thẻ tín dụng',
    r'thẻ ghi nợ',
    r'internet banking',
    r'mobile banking',
    r'atm',
    r'chi nhánh',
    r'phòng giao dịch',
    r'tư vấn tài chính',
    r'vay vốn',
    r'thế chấp',
    r'bảo lãnh',
    r'chuyển tiền',
    r'ngoại hối',
    r'đầu tư',
    r'quỹ',
    r'bảo hiểm ngân hàng',
    # Thêm các terms banking cụ thể
    r'vay mua nhà',
    r'vay tiêu dùng',
    r'vay kinh doanh',
    r'vay thế chấp',
    r'tín dụng ngân hàng',
    r'gói sản phẩm',
    r'ưu đãi lãi suất',
    r'khách hàng ngân hàng',
    r'dịch vụ tài chính',
]

# Bank names and abbreviations
BANK_NAMES = [
    r'vietcombank',
    r'vcb',
    r'bidv',
    r'techcombank',
    r'agribank',
    r'mb bank',
    r'acb',
    r'vib',
    r'sacombank',
    r'eximbank',
    r'hdbank',
    r'tpbank',
    r'vpbank',
    r'scb',
    r'oceanbank',
    r'pgbank',
    r'vietbank',
    r'namabank',
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


def calculate_bank_spam_score(text):
    """
    Calculate bank spam score based on indicators
    
    Args:
        text (str): Text to analyze
        
    Returns:
        tuple: (score, details) where details is dict with matched patterns
    """
    text = normalize_text(text)
    score = 0
    details = {
        'high_confidence_non_bank': [],
        'medium_confidence_non_bank': [],
        'real_estate_indicators': [],
        'job_indicators': [],
        'ecommerce_indicators': [],
        'suspicious_bank_mentions': [],
        'legitimate_bank_context': [],
        'bank_names_found': [],
        'context_penalty': 0
    }
    
    # Check high confidence non-bank indicators (3 points each)
    for pattern in BANK_SPAM_INDICATORS['high_confidence_non_bank']:
        if re.search(pattern, text):
            score += 3
            details['high_confidence_non_bank'].append(pattern)
    
    # Check medium confidence non-bank indicators (2 points each)
    for pattern in BANK_SPAM_INDICATORS['medium_confidence_non_bank']:
        if re.search(pattern, text):
            score += 2
            details['medium_confidence_non_bank'].append(pattern)
    
    # Check real estate indicators (2 points each)
    for pattern in BANK_SPAM_INDICATORS['real_estate_indicators']:
        if re.search(pattern, text):
            score += 2
            details['real_estate_indicators'].append(pattern)
    
    # Check job indicators (1.5 points each)
    for pattern in BANK_SPAM_INDICATORS['job_indicators']:
        if re.search(pattern, text):
            score += 1.5
            details['job_indicators'].append(pattern)
    
    # Check e-commerce indicators (1 point each)
    for pattern in BANK_SPAM_INDICATORS['ecommerce_indicators']:
        if re.search(pattern, text):
            score += 1
            details['ecommerce_indicators'].append(pattern)
    
    # Check suspicious bank mentions (1.5 points each)
    for pattern in BANK_SPAM_INDICATORS['suspicious_bank_mentions']:
        if re.search(pattern, text):
            score += 1.5
            details['suspicious_bank_mentions'].append(pattern)
    
    # Check for legitimate bank context (penalty)
    legitimate_context_count = 0
    for pattern in LEGITIMATE_BANK_CONTEXT:
        if re.search(pattern, text):
            legitimate_context_count += 1
            details['legitimate_bank_context'].append(pattern)
    
    # Check for bank names
    bank_names_count = 0
    for pattern in BANK_NAMES:
        if re.search(pattern, text):
            bank_names_count += 1
            details['bank_names_found'].append(pattern)
    
    # Apply penalties for legitimate bank context
    if legitimate_context_count >= 3:
        # Very strong legitimate bank context - major penalty
        penalty = min(score * 0.9, 8)  # Max 90% penalty or 8 points
        score -= penalty
        details['context_penalty'] = penalty
    elif legitimate_context_count >= 2:
        # Strong legitimate bank context - significant penalty
        penalty = min(score * 0.7, 6)  # Max 70% penalty or 6 points
        score -= penalty
        details['context_penalty'] = penalty
    elif legitimate_context_count >= 1:
        # Some legitimate bank context - moderate penalty
        penalty = min(score * 0.4, 3)  # Max 40% penalty or 3 points
        score -= penalty
        details['context_penalty'] = penalty
    
    # Additional penalty if bank names are mentioned (likely legitimate)
    if bank_names_count >= 2:
        penalty = min(score * 0.6, 5)  # Max 60% penalty or 5 points
        score -= penalty
        details['context_penalty'] += penalty
    elif bank_names_count >= 1:
        penalty = min(score * 0.3, 3)  # Max 30% penalty or 3 points
        score -= penalty
        details['context_penalty'] += penalty
    
    return max(0, score), details


def is_bank_spam(text, threshold=3.0, debug=False):
    """
    Check if text is spam in bank category using scoring
    
    Args:
        text (str): Text to check
        threshold (float): Minimum score to classify as spam (default: 3.0)
        debug (bool): Print debug information
        
    Returns:
        bool: True if score >= threshold, False otherwise
    """
    score, details = calculate_bank_spam_score(text)
    
    if debug:
        print(f"Bank Spam Score: {score:.1f} (threshold: {threshold})")
        print(f"Details: {details}")
    
    return score >= threshold


def check_bank_spam(obj, category, threshold=4.0, debug=False, safe_mode=True):
    """
    Check if object is spam for bank category
    
    Args:
        obj (dict): Object with fields title, content, description
        category (str): Category name
        threshold (float): Minimum score to classify as spam (increased to 4.0 for safety)
        debug (bool): Print debug information
        safe_mode (bool): Enable conservative mode (higher threshold, more penalties)
        
    Returns:
        bool: True if spam (non-bank content in bank category), False otherwise
    """
    # Only apply to bank category
    if category != "bank":
        return False
    
    # In safe mode, use higher threshold
    if safe_mode:
        threshold = max(threshold, 4.5)
    
    # Merge text fields
    merged_text = merge_text_fields(obj)
    
    # Check if contains non-bank spam patterns
    return is_bank_spam(merged_text, threshold, debug)


# =====================================================
# EXAMPLE USAGE
# =====================================================

if __name__ == '__main__':
    test_cases = [
        {
            "obj": {
                "title": "Bán nhà gần ngân hàng VCB",
                "content": "Bán nhà 3 tầng, hỗ trợ vay bank, gần ngân hàng Vietcombank",
                "description": ""
            },
            "category": "bank",
            "expected": True  # Spam - real estate in bank category
        },
        {
            "obj": {
                "title": "Tuyển nhân viên ngân hàng",
                "content": "Cần tuyển nhân viên, yêu cầu có STK ngân hàng để nhận lương",
                "description": ""
            },
            "category": "bank",
            "expected": True  # Spam - recruitment in bank category
        },
        {
            "obj": {
                "title": "Dịch vụ ngân hàng Vietcombank",
                "content": "Vietcombank cung cấp dịch vụ thẻ tín dụng, tiền gửi tiết kiệm với lãi suất hấp dẫn",
                "description": ""
            },
            "category": "bank",
            "expected": False  # Not spam - legitimate bank content
        },
        {
            "obj": {
                "title": "Internet Banking BIDV",
                "content": "Hướng dẫn sử dụng internet banking, mobile banking, chuyển tiền online",
                "description": ""
            },
            "category": "bank",
            "expected": False  # Not spam - legitimate bank service
        },
        {
            "obj": {
                "title": "Bán hàng online",
                "content": "Shop bán quần áo, chuyển khoản qua ngân hàng, ship COD",
                "description": ""
            },
            "category": "bank",
            "expected": True  # Spam - e-commerce in bank category
        },
        {
            "obj": {
                "title": "Vay vốn ngân hàng",
                "content": "Techcombank hỗ trợ vay vốn kinh doanh, thế chấp bất động sản, lãi suất ưu đãi",
                "description": ""
            },
            "category": "bank",
            "expected": False  # Not spam - legitimate bank loan service
        },
        {
            "obj": {
                "title": "Test non-bank category",
                "content": "Bán nhà gần ngân hàng",
                "description": ""
            },
            "category": "retail",
            "expected": False  # Not spam - not bank category, filter doesn't apply
        },
        {
            "obj": {
                "title": "Vay thế chấp bất động sản BIDV",
                "content": "BIDV hỗ trợ vay thế chấp bất động sản, mua nhà, lãi suất ưu đãi từ 6%/năm",
                "description": ""
            },
            "category": "bank",
            "expected": False  # Not spam - legitimate bank loan service (RISKY CASE)
        },
        {
            "obj": {
                "title": "Ngân hàng tuyển nhân viên",
                "content": "Vietcombank tuyển nhân viên tư vấn tài chính, lương 15-20tr, yêu cầu kinh nghiệm ngân hàng",
                "description": ""
            },
            "category": "bank", 
            "expected": False  # Not spam - bank recruitment (RISKY CASE)
        }
    ]
    
    print("=" * 80)
    print("BANK SPAM CLASSIFIER - SCORING SYSTEM TEST")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result = check_bank_spam(test["obj"], test["category"], debug=True)
        expected = test["expected"]
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"\nTest {i}: {status}")
        print(f"  Category: {test['category']}")
        print(f"  Title: {test['obj']['title']}")
        print(f"  Content: {test['obj']['content'][:100]}...")
        print(f"  Result: {'SPAM' if result else 'NOT SPAM'}")
        print(f"  Expected: {'SPAM' if expected else 'NOT SPAM'}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print("-" * 40)
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)