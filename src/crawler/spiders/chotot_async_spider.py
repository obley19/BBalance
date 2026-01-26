
import aiohttp
import asyncio
import random
import json
import os
from datetime import datetime
from typing import Optional, Dict

from ..async_base_spider import AsyncBaseSpider
from ..schema import ProductItem

# Cho Tot Categories
CHOTOT_CATS = {
    # Electronics
    "laptop": "5017",
    "pc": "5018",
    "desktop": "5018",
    "gaming_pc": "5018",
    "phone": "5010",
    "tablet": "5040",
    "tv": "5020",
    "camera": "5030",
    "speakers": "5060", # Loa, Amply
    "accessories": "5050", # Phu kien
}

class ChototAsyncSpider(AsyncBaseSpider):
    """
    Async Spider for Cho Tot using Gateway API.
    """
    source = "chotot"
    base_url = "https://gateway.chotot.com/v1/public/ad-listing"
    
    def __init__(self, max_concurrent: int = 5):
        super().__init__(max_concurrent)
        # Rate limit slightly higher for API
        self.rate_limit = 0.5
        
        # Override headers for API
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.chotot.com/',
            'Origin': 'https://www.chotot.com',
        }

    async def get_product_ids_from_page(self, session: aiohttp.ClientSession, category_id: str, page: int) -> list:
        # Not used in this API-based flow where we fetch full data in one go
        return []

    async def crawl_category(self, category_key: str, max_pages: int = 50) -> None:
        """
        Crawl Cho Tot category using recursive API paging.
        """
        print(f"\n🚀 [chotot] Starting crawl for: '{category_key}'")
        
        cat_id = CHOTOT_CATS.get(category_key, category_key)
        # If user passed a raw ID, use it. If passed 'laptop', use mapped ID.
        if not cat_id or not cat_id.isdigit():
             # Try to search keyword? No, Cho Tot API needs category usually.
             # Default to checking if it looks like a keyword, maybe map generic?
             print(f"⚠️ [chotot] Unknown category '{category_key}'. Using '5000' (Electronics) as fallback.")
             cat_id = "5000"

        limit = 50 # Max limit usually 50
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for page in range(max_pages):
                offset = page * limit
                url = f"{self.base_url}?cg={cat_id}&limit={limit}&o={offset}&st=s,k"
                print(f"📄 [chotot] Page {page+1}/{max_pages} (Offset {offset}): {url}")
                
                try:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            print(f"❌ [chotot] API Error {resp.status}")
                            break
                            
                        data = await resp.json()
                        ads = data.get("ads", [])
                        
                        if not ads:
                            print("   [chotot] No more ads found.")
                            break
                        
                        saved_count = 0
                        for ad in ads:
                            product = self.parse_product(ad)
                            if product:
                                self.save_product(product)
                                saved_count += 1
                                
                        print(f"   ✅ [chotot] Saved {saved_count} items.")
                        
                        # Rate limit
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        
                except Exception as e:
                    print(f"❌ [chotot] Error: {e}")
                    break

    def parse_product(self, raw_data: dict) -> Optional[ProductItem]:
        """
        Parse Cho Tot raw ad object.
        """
        try:
            original_id = str(raw_data.get("list_id"))
            subject = raw_data.get("subject", "")
            
            # Skip invalid
            if not original_id or not subject:
                return None
                
            price_val = int(raw_data.get("price", 0) or 0)
            
            # Construct URL
            url = f"https://www.chotot.com/{original_id}.htm"
            
            # Image
            image = raw_data.get("image", "")

            # Location
            location = ""
            if "region_name" in raw_data:
                location = raw_data["region_name"]
                if "area_name" in raw_data:
                    location += f", {raw_data['area_name']}"
            
            return ProductItem(
                id=f"{self.source}_{original_id}",
                platform=self.source,
                title=subject,
                price=price_val,
                url=url,
                image_url=image,
                category=raw_data.get("category_name", ""),
                brand=raw_data.get("company_ad", "No Brand") if raw_data.get("company_ad") else "No Brand",
                location=location,
                description=raw_data.get("body", ""),
                extra_data={"original_id": original_id, "params": raw_data.get("params")}
            )
        except:
            return None

    # Implement abstract methods
    async def crawl_product_detail(self, session, product_id): pass
