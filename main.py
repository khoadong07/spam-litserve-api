import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Any, Union
import threading
import time
from flask import Flask, request, jsonify
import json
import re
import os
import sys
import logging

# Add parent directory to path to import common modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add current directory to path for mock modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from common.filter_registry import registry
    from common.real_estate_classifier import check_real_estate_spam
    from common.phone_shopee_detector import contains_vietnam_phone_or_shopee_link
    from common.bank_spam_classifier import check_bank_spam
    from common.excluded_sites import excluded_sites_manager
    from common.cake_custom_filter import classify_row
    print("✅ Using real common modules")
except ImportError as e:
    print(f"⚠️ Common modules not available: {e}")
    print("   Using mock modules for testing...")
    try:
        from mock_common import (
            registry, 
            excluded_sites_manager, 
            check_real_estate_spam, 
            check_bank_spam, 
            contains_vietnam_phone_or_shopee_link
        )
        
        # Mock cake filter function
        def classify_row(row_dict):
            """Mock cake filter - simple logic for testing"""
            text = " ".join([
                str(row_dict.get("Title", "") or ""),
                str(row_dict.get("Content", "") or ""),
                str(row_dict.get("Description", "") or ""),
            ]).lower()
            
            # Simple mock logic
            if any(kw in text for kw in ["vpbank", "fintech", "cake app", "unicorn"]):
                return "NO", "CAKE_FINTECH"
            elif any(kw in text for kw in ["tiệm bánh", "bánh sinh nhật", "đặt bánh", "bánh kem"]):
                return "YES", "BAKERY"
            elif any(kw in text for kw in ["mỹ phẩm", "makeup", "beauty", "phấn phủ"]):
                return "YES", "UNRELATED"
            else:
                return "NO", "UNKNOWN"
            
        print("✅ Using mock common modules with mock CAKE filter")
    except ImportError as e2:
        print(f"❌ Mock modules also not available: {e2}")
        print("   Creating inline mock modules...")
        
        # Create inline mock modules as last resort
        class InlineRegistry:
            def __init__(self):
                self.filters = {}
            def load_from_config(self, path): pass
            def has_filter(self, brand_id): return False
            def get_filter(self, brand_id): return lambda x: False
            def get_stats(self): return {"total_filters": 0, "total_brands_with_filter": 0, "filters": {}}
        
        class InlineExcludedSites:
            def __init__(self):
                self.excluded_sites = set()
            def load_from_config(self, path):
                try:
                    if os.path.exists(path):
                        import json
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.excluded_sites = set(data.get("excluded_sites", []))
                except: pass
            def is_excluded(self, site_id): return site_id in self.excluded_sites
            def get_stats(self): return {"total_excluded_sites": len(self.excluded_sites), "sites": list(self.excluded_sites)}
        
        def inline_check_real_estate_spam(obj, cat): return False
        def inline_check_bank_spam(obj, cat): return False
        def inline_contains_phone_shopee(text): return False
        def inline_classify_row(row_dict):
            text = " ".join([str(row_dict.get("Title", "") or ""), str(row_dict.get("Content", "") or ""), str(row_dict.get("Description", "") or "")]).lower()
            if any(kw in text for kw in ["vpbank", "fintech", "cake app"]): return "NO", "CAKE_FINTECH"
            elif any(kw in text for kw in ["tiệm bánh", "bánh sinh nhật"]): return "YES", "BAKERY"
            elif any(kw in text for kw in ["mỹ phẩm", "makeup"]): return "YES", "UNRELATED"
            else: return "NO", "UNKNOWN"
        
        registry = InlineRegistry()
        excluded_sites_manager = InlineExcludedSites()
        check_real_estate_spam = inline_check_real_estate_spam
        check_bank_spam = inline_check_bank_spam
        contains_vietnam_phone_or_shopee_link = inline_contains_phone_shopee
        classify_row = inline_classify_row
        
        print("✅ Using inline mock modules")

MODEL_ID = "Khoa/kompa-spam-filter-hospital-update-0625"
MAX_LENGTH = 192

# ML Enable flag - set to False to disable ML inference
ML_ENABLE = os.getenv("ML_ENABLE", "true").lower() == "true"

# Brand sentiment indices - nếu index nằm trong này thì check sđt/shopee
BRAND_SENTIMENT_INDICES = {
    "69d8865a9957472efb62d227": {"name": "Panasonic Washing Machine"},
    "69d887739957472efb62d228": {"name": "Panasonic Fridge"},
    "69d8a9849957472efb62d22a": {"name": "Panasonic Air-conditioner"},
    "69d8a8c49957472efb62d229": {"name": "Panasonic Kitchenware"},
    "69dc453fc941060a5c196195": {"name": "Sanyo Air-conditioner"},
}

# Category mapping: name -> cate_name
CATEGORY_MAPPING = {
    "Consumer Discretionary": "retail",
    "Consumer Staples": "fmcg",
    "Communication Services": "electronic",
    "Finance": "bank",
    "Healthcare": "hospital",
    "Digital Payment": "ewallet",
    "Real Estate": "real_estate",
    "N/A": "corp",
    "Education Services": "education",
    "Information Tech": "software_technology",
    "Industrials": "logistics",
    "Energy": "energy_fuels",
    "Automotive": "automotive",
    "Bank": "bank",
    "Corp": "corp",
    "Ecommerce": "ecommerce",
    "Education": "education",
    "Electronic": "electronic",
    "Energy Fuels": "energy_fuels",
    "Entertianment Television": "entertainment_television",
    "Ewallet": "ewallet",
    "FMCG": "fmcg",
    "FnB": "fnb",
    "Healthcare Insurance": "healthcare_insurance",
    "Home Living": "home_living",
    "Hospital": "hospital",
    "Insurance": "insurance",
    "Investment": "investment",
    "Logistic Delivery": "logistic_delivery",
    "Logistics": "logistics",
    "Retail": "retail",
    "Software Technology": "software_technology",
    "Technology Motorbike Food": "technology_motorbike_food",
    "Telecomunication Internet": "telecomunication_internet"
}

# Regex nhận diện emoji
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE
)

def count_emoji(text: str) -> int:
    if not text:
        return 0
    return len(EMOJI_PATTERN.findall(text))

def is_only_emoji(text: str) -> bool:
    if not text:
        return False
    text = text.strip()
    cleaned = EMOJI_PATTERN.sub("", text)
    return cleaned.strip() == ""

def is_meaningful_data(obj: dict) -> bool:
    title = obj.get("title", "")
    content = obj.get("content", "")
    description = obj.get("description", "")
    
    if not content or content.strip() == "":
        return False
    
    if is_only_emoji(content):
        return False
    
    title_emoji = count_emoji(title)
    content_emoji = count_emoji(content)
    
    if title_emoji > 2 and content_emoji > 2:
        return False
    
    return True


class SpamFilterService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.setup_model()
        self.setup_filters()

    def setup_model(self):
        print(f"Loading model on device: {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            use_fast=True
        )

        self.model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_ID
        ).to(self.device)

        if self.device == "cuda":
            self.model.half()

        self.model.eval()

        print("Model loaded successfully!")
        if self.device == "cuda":
            print("GPU:", torch.cuda.get_device_name(0))

    def setup_filters(self):
        """Setup preprocessing filters"""
        try:
            # Load filter registry config
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'config',
                'brand_filters.json'
            )
            if os.path.exists(config_path):
                registry.load_from_config(config_path)
                
                # Print stats
                stats = registry.get_stats()
                print(f"📊 Filter Registry Stats:")
                print(f"   Total filters: {stats['total_filters']}")
                print(f"   Total brands with custom filter: {stats['total_brands_with_filter']}")
                for filter_name, count in stats['filters'].items():
                    print(f"   - {filter_name}: {count} brands")
            else:
                print(f"⚠️ Filter config not found: {config_path}")
            
            # Load excluded sites config
            excluded_sites_config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'config',
                'excluded_sites.json'
            )
            if os.path.exists(excluded_sites_config_path):
                excluded_sites_manager.load_from_config(excluded_sites_config_path)
                
                excluded_stats = excluded_sites_manager.get_stats()
                print(f"🚫 Excluded Sites Stats:")
                print(f"   Total excluded sites: {excluded_stats['total_excluded_sites']}")
                if excluded_stats['total_excluded_sites'] > 0:
                    sites_preview = excluded_stats['sites'][:5]
                    sites_str = ', '.join(sites_preview)
                    if len(excluded_stats['sites']) > 5:
                        sites_str += f" ... (+{len(excluded_stats['sites']) - 5} more)"
                    print(f"   Sites: {sites_str}")
                    
                    # Check if our test site is in the list
                    if "114144744928643" in excluded_stats['sites']:
                        print(f"   ✅ Test site 114144744928643 is in excluded list")
                    else:
                        print(f"   ❌ Test site 114144744928643 is NOT in excluded list")
            else:
                print(f"⚠️ Excluded sites config not found: {excluded_sites_config_path}")
                
        except Exception as e:
            print(f"❌ CRITICAL ERROR setting up filters: {e}")
            print("   Service cannot continue without filters!")
            exit(1)
        
        print(f"🤖 ML Model Status: {'ENABLED' if ML_ENABLE else 'DISABLED'}")
        if not ML_ENABLE:
            print(f"   All items passing pre-filters will be marked as spam=False")

    @torch.inference_mode()
    def predict_spam(self, texts):
        if not texts:
            return []

        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors="pt"
        ).to(self.device)

        outputs = self.model(**encoded)
        probs = torch.softmax(outputs.logits, dim=-1)
        preds = torch.argmax(probs, dim=-1)

        results = []
        for pred, prob in zip(preds.cpu().tolist(), probs.cpu().tolist()):
            label = self.model.config.id2label[pred]
            score = float(max(prob))
            is_spam = label.lower() in ["spam", "label_1", "1", "true"]
            
            results.append({
                "label": label,
                "score": score,
                "is_spam": is_spam
            })

        return results

    def apply_preprocessing_filters(self, item, mapped_category):
        """Apply preprocessing filters from ref_socket logic"""
        item_type = item.get("type", "")
        site_id = item.get("site_id", "")
        brand_id = str(item.get("index", ""))
        
        # Debug logging
        print(f"🔍 Processing item {item.get('id')}: site_id={site_id}, type={item_type}, brand_id={brand_id}")
            
        # Pre-filter 0: Excluded sites - highest priority (bỏ qua không xử lý spam)
        try:
            if excluded_sites_manager.is_excluded(site_id):
                print(f"🚫 Site {site_id} is excluded for item {item.get('id')}")
                return {
                    "spam": False, 
                    "used_custom_filter": True, 
                    "filter_reason": "excluded_site"
                }
            else:
                print(f"✅ Site {site_id} is NOT excluded for item {item.get('id')}")
        except Exception as e:
            print(f"⚠️ Error checking excluded sites for {item.get('id')}: {e}")
        
        # Pre-filter 1: CAKE Custom Filter for specific brand
        if brand_id == "61b8715499ce4372a5d739a0":
            try:
                # Prepare data for cake filter
                row_data = {
                    "Title": item.get("title", ""),
                    "Content": item.get("content", ""),
                    "Description": item.get("description", "")
                }
                
                is_spam_result, spam_reason = classify_row(row_data)
                spam_bool = is_spam_result == "YES"
                
                print(f"🍰 CAKE filter for brand {brand_id}: {item.get('id')} → spam={spam_bool} ({spam_reason})")
                return {
                    "spam": spam_bool, 
                    "used_custom_filter": True, 
                    "filter_reason": f"cake_custom_filter_{spam_reason.lower()}"
                }
            except Exception as e:
                print(f"⚠️ Error in CAKE custom filter for {item.get('id')}: {e}")
        
        # Pre-filter 2: newsTopic
        if item_type == "newsTopic":
            print(f"📰 Item {item.get('id')} is newsTopic")
            return {
                "spam": False, 
                "used_custom_filter": False, 
                "filter_reason": "news_topic"
            }
        
        # Pre-filter 3: Phone/Shopee detection
        if brand_id in BRAND_SENTIMENT_INDICES:
            title = item.get("title", "")
            content = item.get("content", "")
            description = item.get("description", "")
            text = f"{title}\n{description}\n{content}".strip()
            
            try:
                if contains_vietnam_phone_or_shopee_link(text):
                    print(f"📱 Phone/Shopee detected for brand {brand_id}: {item.get('id')}")
                    return {
                        "spam": True, 
                        "used_custom_filter": True, 
                        "filter_reason": "phone_shopee_detected"
                    }
            except Exception as e:
                print(f"⚠️ Error checking phone/shopee for {item.get('id')}: {e}")
        
        # Pre-filter 4: Custom brand filter (registry)
        try:
            if registry.has_filter(brand_id):
                custom_filter = registry.get_filter(brand_id)
                filter_obj = {
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "description": item.get("description", ""),
                    "topic": item.get("topic", ""),
                    "site_id": site_id,
                    "type": item_type,
                    "parent_id": item.get("parent_id", "")
                }
                is_spam_result = custom_filter(filter_obj)
                print(f"🎯 Custom filter for brand {brand_id}: {item.get('id')} → spam={is_spam_result}")
                return {
                    "spam": is_spam_result, 
                    "used_custom_filter": True, 
                    "filter_reason": "custom_brand_filter"
                }
        except Exception as e:
            print(f"⚠️ Error checking custom brand filter for {item.get('id')}: {e}")
        
        # Pre-filter 5: Real estate classified
        if mapped_category != "real_estate":
            filter_obj = {
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "description": item.get("description", "")
            }
            try:
                is_re_spam = check_real_estate_spam(filter_obj, mapped_category)
                
                if is_re_spam:
                    print(f"🏠 Real estate pre-filter: {item.get('id')} → spam=True (category={mapped_category})")
                    return {
                        "spam": True, 
                        "used_custom_filter": True, 
                        "filter_reason": "real_estate_classified"
                    }
            except Exception as e:
                print(f"⚠️ Error checking real estate for {item.get('id')}: {e}")
        
        # Pre-filter 6: Bank spam classifier
        if mapped_category == "bank":
            filter_obj = {
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "description": item.get("description", "")
            }
            try:
                is_bank_spam = check_bank_spam(filter_obj, mapped_category)
                if is_bank_spam:
                    print(f"🏦 Bank spam pre-filter: {item.get('id')} → spam=True (non-bank content in bank category)")
                    return {
                        "spam": True, 
                        "used_custom_filter": True, 
                        "filter_reason": "bank_spam_classified"
                    }
            except Exception as e:
                print(f"⚠️ Error checking bank spam for {item.get('id')}: {e}")
        
        print(f"➡️ No preprocessing filter applied for {item.get('id')}, proceeding to ML")
        return None  # No preprocessing filter applied, proceed to ML

    def process_infer_request(self, data):
        """Process v1/api/infer request with preprocessing filters"""
        items = data.get("data", [])
        
        results = []

        for item in items:
            # Map category
            category = item.get("category", "") or ""
            mapped_category = CATEGORY_MAPPING.get(category, category)
            mapped_category = mapped_category.lower()
            
            # Apply preprocessing filters
            preprocess_result = self.apply_preprocessing_filters(item, mapped_category)
            
            if preprocess_result is not None:
                # Preprocessing filter applied
                spam = preprocess_result["spam"]
                used_custom_filter = preprocess_result["used_custom_filter"]
                filter_reason = preprocess_result["filter_reason"]
                
                # Apply meaningful data check for spam items from non-custom filters
                if spam and not used_custom_filter:
                    is_meaningful = is_meaningful_data(item)
                    if is_meaningful:
                        spam = False
                        filter_reason = "meaningful_data_override"
                
            else:
                # No preprocessing filter, use ML model
                if ML_ENABLE:
                    # Combine title, description, and content for inference
                    text_parts = []
                    if item.get("title"):
                        text_parts.append(str(item["title"]))
                    if item.get("description"):
                        text_parts.append(str(item["description"]))
                    if item.get("content"):
                        text_parts.append(str(item["content"]))
                    
                    text = " ".join(text_parts).strip()
                    
                    if text:
                        predictions = self.predict_spam([text])
                        if predictions:
                            pred = predictions[0]
                            spam = pred["is_spam"]
                            used_custom_filter = False
                            filter_reason = f"ML model prediction: {pred['label']} (confidence: {pred['score']:.3f})"
                        else:
                            spam = None
                            used_custom_filter = False
                            filter_reason = "ml_prediction_failed"
                    else:
                        spam = False
                        used_custom_filter = False
                        filter_reason = "empty_content"
                else:
                    spam = False
                    used_custom_filter = False
                    filter_reason = "ml_disabled"

            result = {
                "id": item.get("id"),
                "index": item.get("index"),
                "category": mapped_category,
                "type": item.get("type"),
                "spam": spam,
                "used_custom_filter": used_custom_filter,
                "filter_reason": filter_reason
            }
            results.append(result)

        return {
            "status": 200,
            "data": results
        }

    def process_spam_request(self, data):
        """Process original spam API request"""
        items = data.get("items", [])
        
        texts = []
        meta_list = []

        for item in items:
            text = " ".join([
                str(item.get("title") or ""),
                str(item.get("content") or ""),
                str(item.get("description") or "")
            ]).strip()

            texts.append(text)
            meta_list.append({
                "id": item.get("id"),
                "index": item.get("index")
            })

        # Get predictions
        predictions = self.predict_spam(texts)
        
        # Format response
        results = []
        for meta, pred in zip(meta_list, predictions):
            result = {
                "id": meta["id"],
                "index": meta["index"],
                "label": pred["label"],
                "score": pred["score"],
                "is_spam": pred["is_spam"]
            }
            results.append(result)

        return {
            "results": results,
            "count": len(results)
        }


# Initialize service
spam_service = SpamFilterService()

# Create Flask app
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "device": spam_service.device,
        "model": MODEL_ID
    })

@app.route('/v1/api/infer', methods=['POST'])
def infer_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        result = spam_service.process_infer_request(data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "status": 500,
            "error": str(e)
        }), 500

@app.route('/api/spam', methods=['POST'])
def spam_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        result = spam_service.process_spam_request(data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "service": "Spam Filter API",
        "endpoints": {
            "health": "GET /health",
            "infer": "POST /v1/api/infer",
            "spam": "POST /api/spam"
        },
        "model": MODEL_ID
    })


if __name__ == "__main__":
    print("Starting Spam Filter Service...")
    print(f"Model: {MODEL_ID}")
    print(f"Device: {spam_service.device}")
    print("\nAvailable endpoints:")
    print("- GET  /health")
    print("- GET  /")
    print("- POST /v1/api/infer")
    print("- POST /api/spam")
    
    app.run(
        host="0.0.0.0",
        port=8990,
        debug=False,
        threaded=True
    )