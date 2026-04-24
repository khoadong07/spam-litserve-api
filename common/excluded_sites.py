"""
Excluded Sites Manager
Quản lý danh sách các site_id được loại trừ khỏi việc xử lý spam
"""

import os
import json
from typing import Set, List

class ExcludedSitesManager:
    def __init__(self):
        self.excluded_sites: Set[str] = set()
        self._config_loaded = False
    
    def load_from_config(self, config_path: str) -> None:
        """Load excluded sites from JSON config file only"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    sites = config.get('excluded_sites', [])
                    # Only use sites from JSON config
                    self.excluded_sites = set(sites)
                    self._config_loaded = True
                    print(f"📋 Loaded {len(sites)} excluded sites from config: {config_path}")
            else:
                print(f"⚠️ Config file not found: {config_path}, no sites will be excluded")
                self.excluded_sites = set()
                self._config_loaded = True
        except Exception as e:
            print(f"❌ Error loading excluded sites config: {e}")
            self.excluded_sites = set()
            self._config_loaded = True
    
    def load_from_list(self, sites: List[str]) -> None:
        """Load excluded sites from a list (replaces default sites)"""
        self.excluded_sites = set(sites)
        self._config_loaded = True
        print(f"📋 Loaded {len(self.excluded_sites)} excluded sites from list")
    
    def is_excluded(self, site_id: str) -> bool:
        """Check if a site_id is in the excluded list"""
        if not site_id:
            return False
        return site_id in self.excluded_sites
    
    def add_site(self, site_id: str) -> None:
        """Add a site to the excluded list"""
        if site_id:
            self.excluded_sites.add(site_id)
    
    def remove_site(self, site_id: str) -> None:
        """Remove a site from the excluded list"""
        self.excluded_sites.discard(site_id)
    
    def get_excluded_sites(self) -> List[str]:
        """Get list of all excluded sites"""
        return sorted(list(self.excluded_sites))
    
    def get_stats(self) -> dict:
        """Get statistics about excluded sites"""
        return {
            "total_excluded_sites": len(self.excluded_sites),
            "config_loaded": self._config_loaded,
            "sites": self.get_excluded_sites()
        }

# Global instance
excluded_sites_manager = ExcludedSitesManager()