# Common Modules

Thư mục này chứa các module dùng chung cho hệ thống spam detection.

## Excluded Sites (`excluded_sites.py`)

### Mô tả
Module quản lý danh sách các site_id được loại trừ khỏi việc xử lý spam. Các site từ danh sách này sẽ được gán `spam=false` ngay lập tức mà không cần qua bất kỳ bước xử lý nào khác.

**Lưu ý quan trọng**: Danh sách excluded sites chỉ được load từ file JSON config, không có default sites.

### Cách sử dụng

#### 1. Import module
```python
from common.excluded_sites import excluded_sites_manager
```

#### 2. Kiểm tra site có bị loại trừ không
```python
if excluded_sites_manager.is_excluded("vnexpress.net"):
    print("Site này được loại trừ")
```

#### 3. Load từ file config (bắt buộc)
```python
excluded_sites_manager.load_from_config("config/excluded_sites.json")
```

#### 4. Thêm/xóa site
```python
# Thêm site
excluded_sites_manager.add_site("new-site.com")

# Xóa site
excluded_sites_manager.remove_site("old-site.com")
```

#### 5. Xem thống kê
```python
stats = excluded_sites_manager.get_stats()
print(f"Total excluded sites: {stats['total_excluded_sites']}")
```

### Config File (Bắt buộc)
Tất cả excluded sites phải được định nghĩa trong file `config/excluded_sites.json`:
```json
{
  "excluded_sites": [
    "vnexpress.net",
    "tuoitre.vn",
    "thanhnien.vn",
    "fireant.vn",
    "google.com",
    "137952892978533",
    "UCmHyuC-eNeCGn7bf64Nt66Q"
  ]
}
```

### Behavior
- **Nếu file config tồn tại**: Load tất cả sites từ JSON
- **Nếu file config không tồn tại**: Không có site nào bị exclude
- **Nếu file config lỗi**: Không có site nào bị exclude và log error

### Thứ tự ưu tiên trong Socket Server
1. **Excluded Sites** → `spam=false` (ưu tiên cao nhất)
2. newsTopic/Trusted sites → `spam=false`
3. Phone/Shopee detection → `spam=true` nếu phát hiện
4. Custom brand filters → Theo logic custom
5. Real estate classifier → `spam=true` nếu là real estate spam
6. Bank spam classifier → `spam=true` nếu là bank spam
7. ML inference → Theo model ML

### Logging
Khi site bị loại trừ:
```
🚫 Excluded site vnexpress.net: item_123 → spam=False (excluded)
```

### API Methods

#### `is_excluded(site_id: str) -> bool`
Kiểm tra site_id có trong danh sách loại trừ không.

#### `load_from_config(config_path: str) -> None`
Load danh sách từ file JSON config (merge với default sites).

#### `load_from_list(sites: List[str]) -> None`
Load danh sách từ list (thay thế default sites).

#### `add_site(site_id: str) -> None`
Thêm site vào danh sách loại trừ.

#### `remove_site(site_id: str) -> None`
Xóa site khỏi danh sách loại trừ.

#### `get_excluded_sites() -> List[str]`
Lấy danh sách tất cả sites bị loại trừ (đã sort).

#### `get_stats() -> dict`
Lấy thống kê về excluded sites.