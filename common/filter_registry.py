"""
Filter Registry - Quản lý các custom spam filters cho từng brand
Dễ dàng thêm/xóa filters mà không cần sửa code chính
"""

from typing import Dict, List, Callable, Optional
import json
import os


class FilterRegistry:
    """Registry để quản lý các custom spam filters"""
    
    def __init__(self):
        self.filters: Dict[str, Callable] = {}
        self.brand_filters: Dict[str, str] = {}  # brand_id -> filter_name
        
    def register_filter(self, name: str, filter_func: Callable):
        """
        Đăng ký một filter function
        
        Args:
            name: Tên filter (vd: "vinfast", "samsung", ...)
            filter_func: Function nhận object, trả về True (spam) hoặc False (not spam)
        """
        self.filters[name] = filter_func
        print(f"✅ Registered filter: {name}")
    
    def assign_brands(self, filter_name: str, brand_ids: List[str]):
        """
        Gán một filter cho nhiều brand IDs
        
        Args:
            filter_name: Tên filter đã đăng ký
            brand_ids: List các brand IDs sử dụng filter này
        """
        if filter_name not in self.filters:
            raise ValueError(f"Filter '{filter_name}' not registered")
        
        for brand_id in brand_ids:
            self.brand_filters[brand_id] = filter_name
        
        print(f"✅ Assigned {len(brand_ids)} brands to filter '{filter_name}'")
    
    def get_filter(self, brand_id: str) -> Optional[Callable]:
        """
        Lấy filter function cho một brand ID
        
        Args:
            brand_id: Brand ID cần check
            
        Returns:
            Filter function hoặc None nếu không có custom filter
        """
        filter_name = self.brand_filters.get(brand_id)
        if filter_name:
            return self.filters.get(filter_name)
        return None
    
    def has_filter(self, brand_id: str) -> bool:
        """Check xem brand có custom filter không"""
        return brand_id in self.brand_filters
    
    def load_from_config(self, config_path: str):
        """
        Load brand-filter mapping từ config file
        
        Config format (JSON):
        {
            "filters": {
                "vinfast": ["brand_id_1", "brand_id_2", ...],
                "samsung": ["brand_id_3", ...]
            }
        }
        """
        if not os.path.exists(config_path):
            print(f"⚠️ Config file not found: {config_path}")
            return
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        filters_config = config.get('filters', {})
        for filter_name, brand_ids in filters_config.items():
            if filter_name in self.filters:
                self.assign_brands(filter_name, brand_ids)
            else:
                print(f"⚠️ Filter '{filter_name}' not registered, skipping brands")
    
    def get_stats(self) -> dict:
        """Lấy thống kê về filters"""
        return {
            "total_filters": len(self.filters),
            "total_brands_with_filter": len(self.brand_filters),
            "filters": {
                name: sum(1 for f in self.brand_filters.values() if f == name)
                for name in self.filters.keys()
            }
        }


# Global registry instance
registry = FilterRegistry()


def register_filter(name: str):
    """Decorator để đăng ký filter"""
    def decorator(func: Callable):
        registry.register_filter(name, func)
        return func
    return decorator


# =====================================================
# REGISTER BUILT-IN FILTERS
# =====================================================

@register_filter("vinfast")
def vinfast_filter(obj: dict) -> bool:
    """VinFast spam filter"""
    from common.vinfast_filter import is_spam
    return is_spam(obj)


# Thêm filters khác ở đây khi cần
# @register_filter("samsung")
# def samsung_filter(obj: dict) -> bool:
#     # Samsung-specific logic
#     return False


# =====================================================
# EXAMPLE USAGE
# =====================================================

if __name__ == '__main__':
    print("=" * 80)
    print("FILTER REGISTRY - DEMO")
    print("=" * 80)
    
    # Assign brands to filters
    vinfast_brands = [
        "6929256661fe19430ca50d22",
        "6930f94661fe19430ca51053",
        "6930f98761fe19430ca51054",
        "6930f9a561fe19430ca51055",
        "6930f9cb61fe19430ca51056",
        "6930fab361fe19430ca51057",
        "6930facd61fe19430ca51058"
    ]
    
    registry.assign_brands("vinfast", vinfast_brands)
    
    # Test
    test_brand = "6929256661fe19430ca50d22"
    print(f"\n🔍 Checking brand: {test_brand}")
    print(f"   Has custom filter: {registry.has_filter(test_brand)}")
    
    if registry.has_filter(test_brand):
        filter_func = registry.get_filter(test_brand)
        test_obj = {
            "title": "Bảo dưỡng xe VinFast",
            "content": "Đi bảo dưỡng tại xưởng",
            "description": ""
        }
        result = filter_func(test_obj)
        print(f"   Filter result: {'SPAM' if result else 'NOT SPAM'}")
    
    # Stats
    print(f"\n📊 Registry stats:")
    stats = registry.get_stats()
    print(f"   Total filters: {stats['total_filters']}")
    print(f"   Total brands with filter: {stats['total_brands_with_filter']}")
    print(f"   Brands per filter: {stats['filters']}")
