import requests
import time
import random
from typing import Optional

from ..base_spider import BaseSpider

class TikiSpider(BaseSpider):
    source = "tiki"
    base_url = "https://tiki.vn"
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # Tiki specific headers from reference
        self.session.headers.update({
            "Referer": "https://tiki.vn/",
            "Accept-Language": "vi-VN,vi;q=0.9",
        })

    def crawl_category(self, category_id: str, max_pages: int = 3) -> None:
        """
        Crawl Tiki category by ID.
        In Reference cr2.py: query param `category={cid}`
        """
        print(f"🚀 [TIKI] START Crawling Category: {category_id}")
        
        for page in range(1, max_pages + 1):
            print(f"[{self.source}] Page {page}/{max_pages}")
            
            # API from cr2.py
            url = (
                "https://tiki.vn/api/personalish/v1/blocks/listings"
                f"?limit=40&include=advertisement"
                f"&aggregations=2&version=home-persionalized"
                f"&trackity_id=123&category={category_id}&page={page}"
            )
            
            try:
                resp = self.session.get(url, timeout=20)
                if resp.status_code != 200:
                    print(f"⚠️ HTTP {resp.status_code}")
                    break
                
                data = resp.json()
                items = data.get("data", [])
                
                if not items:
                    print("⚠️ No items found or end of pages.")
                    break
                
                for item in items:
                    product = self.parse_product(item)
                    if product:
                        self.save_product(product)
                
                self.sleep_random()
                
            except Exception as e:
                print(f"❌ Error crawling page {page}: {e}")
                time.sleep(3)
        
        print(f"✅ [TIKI] FINISH Category: {category_id}")

    def crawl_product_detail(self, product_id: str) -> Optional[dict]:
        # Not implemented in reference, returning None implies using data from listing
        return None

    def parse_product(self, raw_data: dict) -> dict:
        """
        Parse Tiki API product data.
        """
        try:
            raw_id = raw_data.get('id')
            if not raw_id:
                return {}
                
            product_id = self.build_product_id(raw_id)
            
            # Pricing logic from cr2.py
            price = int(raw_data.get("price", 0))
            original_price = raw_data.get("list_price") or raw_data.get("price")
            original_price = int(original_price or 0)
            
            return {
                "id": product_id,
                "platform": "tiki",  # Luôn viết thường
                "title": raw_data.get("name", ""),
                "price": price,
                "original_price": original_price,
                "sold_count": raw_data.get('quantity_sold', {}).get('value', 0) if isinstance(raw_data.get('quantity_sold'), dict) else 0,
                "link": "https://tiki.vn/" + raw_data.get("url_path", ""),  # Đổi từ 'url' sang 'link'
                "image_url": raw_data.get("thumbnail_url", ""),
                "category": str(raw_data.get('primary_category_path', '')),
                "brand": raw_data.get("brand_name", "No Brand") or "No Brand",
                "title_clean": "",
                "title_segmented": "",
                "source_file": ""
            }
        except Exception as e:
            print(f"❌ Parse Error: {e}")
            return {}
