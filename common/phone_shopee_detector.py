import re

def contains_vietnam_phone_or_shopee_link(text: str) -> bool:
    """
    Kiểm tra xem text có chứa số điện thoại Việt Nam hoặc link Shopee hay không.
    
    Args:
        text: Chuỗi text cần kiểm tra
        
    Returns:
        True nếu text chứa số điện thoại VN hoặc link Shopee, False nếu không
    """
    if not text:
        return False
    
    # Pattern cho số điện thoại Việt Nam
    # Hỗ trợ các định dạng với dấu phân cách (dấu chấm, khoảng trắng, gạch ngang)
    # Đầu số: 03, 05, 07, 08, 09
    phone_patterns = [
        # 10 số với dấu phân cách tùy ý giữa các chữ số
        r'0[3|5|7|8|9][\d\s.\-]{8,}',
        # 11 số bắt đầu bằng 84
        r'84[3|5|7|8|9][\d\s.\-]{8,}',
        # Có dấu +84
        r'\+84[3|5|7|8|9][\d\s.\-]{8,}',
    ]
    
    # Pattern cho link Shopee
    shopee_patterns = [
        r'shopee\.vn',
        r'shope\.ee',
        r'shopee\.com',
    ]
    
    text_lower = text.lower()
    
    # Kiểm tra số điện thoại
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Đếm số chữ số trong match
            digits = re.findall(r'\d', match)
            # Số điện thoại VN có 10 số (bắt đầu 0) hoặc 11 số (bắt đầu 84)
            if len(digits) >= 10:
                return True
    
    # Kiểm tra link Shopee
    for pattern in shopee_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False
