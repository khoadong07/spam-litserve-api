#!/usr/bin/env python3
"""
VinFast Social Listening - Spam Filter
Lọc data theo Rule lọc data từ Monitoring Plan.

Usage:
    from common.vinfast_filter import is_spam
    
    item = {
        "title": "...",
        "content": "...",
        "description": "...",
        "topic": "...",  # optional
        "site_id": "...",  # optional
        "type": "...",  # optional
        "parent_id": "..."  # optional
    }
    
    result = is_spam(item)  # True = spam, False = not spam
"""

import re


# =====================================================
# KEYWORD DEFINITIONS
# =====================================================

# Core service keywords - content MUST match at least one to be KEPT
SERVICE_KEYWORDS = [
    # Xưởng dịch vụ (workshop) - including common typos
    r'xưởng', r'xưỡng', r'sưởng', r'\bxdv\b',
    # Bảo hành (warranty)
    r'bảo hành', r'bão hành',
    # Bảo dưỡng (maintenance)
    r'bảo dưỡng', r'bão dưỡng', r'bảo trì',
    # Sửa chữa (repair)
    r'sửa chữa', r'sửa xe', r'đi sửa', r'mang.*sửa', r'đem.*sửa',
    r'ra sửa', r'vào sửa',
    # Hậu mãi (after-sales)
    r'hậu mãi', r'sau bán hàng',
    # CSKH (customer service)
    r'\bcskh\b', r'chăm sóc khách hàng', r'chăm sóc kh\b',
    r'tổng đài', r'hotline', r'đường dây nóng', r'dây nóng',
    # Dịch vụ in service context
    r'dịch vụ bảo', r'dịch vụ sửa', r'dịch vụ hậu', r'dịch vụ sau',
    # Chi phí service
    r'chi phí bảo dưỡng', r'chi phí sửa', r'giá bảo dưỡng',
    r'phí bảo hành', r'báo giá.*bảo', r'báo giá.*sửa',
    # Phụ tùng (parts at workshop)
    r'phụ tùng',
    # Cứu hộ (emergency/towing)
    r'cứu hộ', r'hỗ trợ khẩn cấp',
    # Service staff
    r'kỹ thuật viên', r'thợ sửa',
    r'nhân viên.*xưởng', r'nhân viên.*bảo dưỡng',
    # Quy trình (process)
    r'book lịch', r'đặt lịch.*bảo', r'lịch bảo dưỡng',
    # Chính sách (policy about service)
    r'chính sách bảo hành', r'chính sách.*hậu mãi', r'chính sách.*bảo dưỡng',
    # Triệu hồi (recall)
    r'triệu hồi', r'recall',
    # Maintenance actions
    r'thay nhớt', r'thay lốp', r'thay phanh', r'thay kính',
    r'thay.*ắc quy', r'thay acquy', r'thay.*bình ắc',
    # Khắc phục (fix/remedy)
    r'khắc phục',
    # FOTA / Software updates
    r'\bfota\b', r'cập nhật.*phần mềm', r'update.*phần mềm',
    # Resale value opinions
    r'mất giá', r'giữ giá', r'bán lỗ', r'giá trị.*bán lại',
    # Đại lý in service context
    r'đại lý.*bảo', r'đại lý.*sửa', r'đại lý.*dịch vụ',
]

# Strict subset used for spam-override checks
STRICT_SERVICE = [
    r'xưởng', r'xưỡng', r'sưởng', r'\bxdv\b',
    r'bảo hành', r'bão hành',
    r'bảo dưỡng', r'bão dưỡng', r'bảo trì',
    r'sửa chữa', r'sửa xe', r'đi sửa',
    r'hậu mãi', r'sau bán hàng',
    r'\bcskh\b', r'chăm sóc khách', r'tổng đài', r'hotline',
    r'cứu hộ', r'triệu hồi',
]

# --- SPAM PATTERNS ---

# Rule 1-2: Trạm sạc / V-GREEN
SPAM_CHARGING = [
    r'trạm sạc', r'cột sạc', r'sạc ngoài', r'sạc công cộng',
    r'chính sách sạc', r'giá sạc', r'phí sạc', r'hạ tầng sạc',
    r'v[\-\.]?green', r'\bvgreen\b',
]

# Rule 3: XanhSM
SPAM_XANHSM = [r'xanhsm', r'xanh\s*sm']

# Rule 4-5: Rao vặt / Classified ads
SPAM_CLASSIFIED = [
    r'cho thuê xe tự lái', r'thuê xe ô tô tự lái', r'cho thuê.*tự lái',
    r'trả trước.*triệu', r'trả góp.*tháng',
    r'xả kho', r'siêu deal', r'giá lăn bánh',
    r'dịch vụ tài chính', r'xuất xưởng.*chiếc',
    r'giá tốt.*liên hệ', r'ốp chìa khóa',
    r'hoàng dũ car', r'vintech.*phụ kiện',
    r'phụ kiện.*chính hãng.*nâng cấp',
    r'độ xe.*chuyên nghiệp', r'nâng cấp option',
]

# Rule 7: Green Future / NVBH
SPAM_GREEN_FUTURE = [
    r'green\s*future', r'greenfuture',
    r'\bgf\b.*lướt', r'lướt.*\bgf\b', r'chuẩn gf\b',
]

# Rule 9: Bán xe cũ
SPAM_SELLING = [
    r'cần bán.*xe', r'bán gấp.*xe',
    r'xe lướt.*bán', r'rao bán.*xe',
]

# Rule 10: Pin / V-GREEN
SPAM_BATTERY = [r'chính sách pin', r'thuê pin']

# Misc
SPAM_MISC = [r'chào mừng các thành viên mới']

# Third-party shop posts with service keywords
SPAM_THIRD_PARTY_SHOP = [
    r'(shopee|lazada|tiki).*bảo hành',
    r'bảo hành.*(shopee|lazada|tiki)',
    r'(ship toàn quốc|giao hàng toàn quốc).*bảo hành',
    r'bảo hành.*(ship toàn quốc|giao hàng toàn quốc)',
    r'(decal|ppf|dán phim|phủ ceramic|dán keo).*bảo hành',
    r'bảo hành.*(decal|ppf|dán phim|phủ ceramic|dán keo)',
    r'(đặt hàng|order).*bảo hành',
    r'inbox.*bảo hành', r'bảo hành.*inbox',
    r'\bib\b.*bảo hành', r'bảo hành.*\bib\b',
]

# Used car dealer patterns
SPAM_DEALER = [
    r'xe lướt.*triệu', r'odo.*vạn.*triệu',
    r'(xe đẹp|xe zin|xe nguyên).*liên hệ',
    r'lăn bánh.*triệu.*liên hệ',
]

# Excluded sources
EXCLUDED_SOURCES = ['101832179297964']


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def normalize_text(text):
    """Normalize text to lowercase and strip whitespace"""
    if text is None or text == "":
        return ""
    return str(text).lower().strip()


def combine_text(obj):
    """Combine title, content, description into single text"""
    parts = []
    for key in ['title', 'content', 'description']:
        value = obj.get(key)
        if value:
            parts.append(str(value))
    return " ".join(parts).lower()


def has_match(text, patterns):
    """Check if text matches any pattern in the list"""
    for p in patterns:
        if re.search(p, text):
            return True
    return False


def is_spam(obj):
    """
    Check if an object is spam based on VinFast monitoring rules.
    
    Args:
        obj (dict): Object with fields:
            - title (str): Title text
            - content (str): Content text
            - description (str): Description text
            - topic (str, optional): Topic name
            - site_id (str, optional): Site ID
            - type (str, optional): Content type
            - parent_id (str, optional): Parent post ID
    
    Returns:
        bool: True if spam, False if not spam
    """
    # Combine all text fields
    text = combine_text(obj)
    
    # Get optional fields
    topic = normalize_text(obj.get('topic', ''))
    site_id = str(obj.get('site_id', ''))
    
    # --- SPAM CHECKS (always spam) ---
    
    # Excluded source
    if site_id in EXCLUDED_SOURCES:
        return True
    
    # Always spam patterns
    if has_match(text, SPAM_CLASSIFIED):
        return True
    if has_match(text, SPAM_MISC):
        return True
    if has_match(text, SPAM_THIRD_PARTY_SHOP):
        return True
    if has_match(text, SPAM_DEALER):
        return True
    
    # --- SPAM CHECKS (service keywords can override) ---
    
    if has_match(text, SPAM_XANHSM) and not has_match(text, STRICT_SERVICE):
        return True
    if has_match(text, SPAM_GREEN_FUTURE) and not has_match(text, STRICT_SERVICE):
        return True
    if has_match(text, SPAM_CHARGING) and not has_match(text, STRICT_SERVICE):
        return True
    if has_match(text, SPAM_BATTERY) and not has_match(text, STRICT_SERVICE):
        return True
    if has_match(text, SPAM_SELLING) and not has_match(text, STRICT_SERVICE):
        return True
    
    # --- COMPETITOR TOPICS ---
    
    if 'vinfast' not in topic:
        vinfast_re = r'vinfast|vin\s*fast|xe vin|vin fat|\bvf\d|\bvf\s'
        if not re.search(vinfast_re, text):
            return True
        if not has_match(text, STRICT_SERVICE):
            return True
    
    # --- SERVICE KEYWORD CHECK ---
    
    if has_match(text, SERVICE_KEYWORDS):
        return False  # Has service keywords → NOT spam
    
    # No service signal → SPAM (Rule 6)
    return True


# =====================================================
# EXAMPLE USAGE
# =====================================================

if __name__ == '__main__':
    # Test cases
    test_cases = [
        {
            "title": "Bảo dưỡng xe VinFast tại xưởng",
            "content": "Hôm nay mình đi bảo dưỡng xe tại xưởng dịch vụ VinFast",
            "description": "",
            "expected": False  # Not spam - has service keywords
        },
        {
            "title": "Cho thuê xe VinFast tự lái",
            "content": "Cho thuê xe VinFast VF8 giá tốt, liên hệ ngay",
            "description": "",
            "expected": True  # Spam - classified ad
        },
        {
            "title": "Trạm sạc V-GREEN",
            "content": "Giới thiệu về trạm sạc V-GREEN mới",
            "description": "",
            "expected": True  # Spam - charging station without service context
        },
        {
            "title": "Sửa chữa xe VinFast",
            "content": "Xe bị hỏng, mang vào xưởng sửa chữa",
            "description": "Dịch vụ sửa chữa tốt",
            "expected": False  # Not spam - has service keywords
        },
        {
            "title": "XanhSM ra mắt",
            "content": "Ứng dụng XanhSM mới ra mắt",
            "description": "",
            "expected": True  # Spam - XanhSM without service context
        }
    ]
    
    print("=" * 80)
    print("VINFAST SPAM FILTER - TEST CASES")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result = is_spam(test)
        expected = test["expected"]
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"\nTest {i}: {status}")
        print(f"  Title: {test['title']}")
        print(f"  Result: {'SPAM' if result else 'NOT SPAM'}")
        print(f"  Expected: {'SPAM' if expected else 'NOT SPAM'}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
