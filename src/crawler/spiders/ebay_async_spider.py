
import asyncio
import json
import os
import random
import re
from datetime import datetime
from typing import Optional, List, Dict

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page

# Try to import stealth function
try:
    from playwright_stealth import stealth_async
except ImportError:
    try:
        from playwright_stealth import stealth as stealth_async
        if not callable(stealth_async):
             from playwright_stealth.stealth import stealth_async
    except ImportError:
        async def stealth_async(page): pass

from ..async_base_spider import AsyncBaseSpider

class EbayParser:
    """
    Parser encapsulating logic from user's script.
    """
    
    @staticmethod
    def extract_id(url: str) -> Optional[str]:
        if not url: return None
        # /itm/123456789...
        if "/itm/" in url:
            parts = url.split("/itm/")
            if len(parts) > 1:
                return parts[1].split("/")[0].split("?")[0]
        return None

    @staticmethod
    def normalize_price(price_str: str) -> float:
        """
        Robust price extraction handling '1,200.00' or '1.000.000'
        Returns float.
        """
        if not price_str: return 0.0
        try:
            # User logic: findall [\d\.,]+
            nums = re.findall(r'[\d\.,]+', price_str)
            if nums:
                clean_num = nums[0].replace(',', '')
                # Handle cases like 1.200.000 vs 1200.50
                # Simple logic from user: if multiple dots, assume last is decimal or standardizing
                if clean_num.count('.') > 1:
                    parts = clean_num.split('.')
                    clean_num = "".join(parts[:-1]) + "." + parts[-1]
                return float(clean_num)
        except:
            return 0.0
        return 0.0

from ...schema import ProductItem

    def parse_product(self, item_soup: BeautifulSoup, source: str, keyword: str) -> Optional[ProductItem]:
        try:
            # 1. Title
            title_el = item_soup.select_one('.s-item__title') or item_soup.select_one('.s-card__title')
            if not title_el: return None
            title = title_el.get_text(strip=True)
            if "Shop on eBay" in title: return None

            # 2. URL & ID
            link_el = item_soup.select_one('a.s-item__link') or item_soup.select_one('a.s-card__link')
            if not link_el: return None
            url = link_el.get('href', '').split('?')[0]
            
            original_id = self.extract_id(url)
            if not original_id: return None

            # 3. Price
            price_el = item_soup.select_one('.s-item__price') or item_soup.select_one('.s-card__attribute-row')
            price_text = price_el.get_text(strip=True) if price_el else "0"
            price_val = self.normalize_price(price_text)

            # 4. Rating
            rating = 0.0
            rating_el = (
                item_soup.select_one('.x-star-rating') or 
                item_soup.select_one('.s-item__stars') or
                item_soup.select_one('.s-card__stars') or
                item_soup.select_one('[class*="star-rating"]')
            )
            if rating_el:
                rating_text = rating_el.get_text(strip=True) or rating_el.get('aria-label') or ""
                r_match = re.search(r'(\d[\d\.]*)', rating_text)
                if r_match: rating = float(r_match.group(1))
            
            # Fallback text search for rating
            if rating == 0.0:
                item_text = item_soup.get_text(" ", strip=True)
                r_match = re.search(r'(\d[\d\.]*)\s*out of 5 stars', item_text, re.IGNORECASE)
                if r_match: rating = float(r_match.group(1))

            # 5. Reviews
            review_count = 0
            reviews_el = (
                item_soup.select_one('.s-item__reviews-count') or 
                item_soup.select_one('.s-item__review-count') or
                item_soup.select_one('.s-card__reviews-count') or
                item_soup.select_one('.s-item__reviews')
            )
            if reviews_el:
                rt = reviews_el.get_text(strip=True)
                rv_match = re.search(r'(\d[\d\.,]*)', rt)
                if rv_match: review_count = int(rv_match.group(1).replace(',', ''))
            
            if review_count == 0:
                item_text = item_soup.get_text(" ", strip=True)
                rv_match = re.search(r'(\d[\d\.,]*)\s*product ratings', item_text, re.IGNORECASE)
                if rv_match: review_count = int(rv_match.group(1).replace(',', ''))

            # 6. Image
            img_el = item_soup.select_one('.s-item__image-img') or item_soup.select_one('img')
            image_url = ""
            if img_el:
                image_url = img_el.get('src') or img_el.get('data-src') or ""

            # 7. Sold Count (Optional extraction if available)
            sold_count = 0
            # Basic textual search for sold count, e.g. "100+ sold"
            item_text = item_soup.get_text(" ", strip=True)
            sold_match = re.search(r'([\d,\.]+)\+?\s*sold', item_text, re.IGNORECASE)
            if sold_match:
                 try:
                     sold_count = int(sold_match.group(1).replace(',', '').replace('.', ''))
                 except: pass

            return ProductItem(
                id=f"{source}_{original_id}",
                platform=source,
                title=title,
                price=int(price_val),
                url=url,
                image_url=image_url,
                category=keyword,
                rating=rating,
                review_count=review_count,
                sold_count=sold_count,
                brand="No Brand", 
                extra_data={"original_id": original_id}
            )
        except Exception:
            return None


class EbayAsyncSpider(AsyncBaseSpider):
    source = "ebay"
    base_url = "https://www.ebay.com/sch/i.html"
    
    def __init__(self):
        super().__init__()
        self.parser = EbayParser()
        self.checkpoint_dir = "data/checkpoints"
        self.checkpoint_file = os.path.join(self.checkpoint_dir, "ebay_checkpoint.json")
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        # Tracking
        self.start_time = datetime.now()
        self.total_items_collected = 0
        
        # Load existing IDs to prevent duplicates across sessions
        self.load_existing_data()
        self.total_items_collected = len(self.seen)
        print(f"🎯 [ebay] Initialized. Loaded {self.total_items_collected} existing items.")

    def load_checkpoint(self) -> Dict:
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r") as f:
                    return json.load(f)
            except: pass
        return {}

    async def save_checkpoint(self, data: Dict):
        with open(self.checkpoint_file, "w") as f:
            json.dump(data, f, indent=4)

    async def crawl_category(self, category_id: str, max_pages: int = 5, headless: bool = False) -> None:
        """
        Main crawl loop using Playwright.
        """
        print(f"\n🚀 [ebay] Starting crawler for keyword: '{category_id}' (Max Pages: {max_pages})")
        
        checkpoint = self.load_checkpoint()
        kw_data = checkpoint.get(category_id, {})
        if kw_data.get("status") == "completed":
            print(f"✅ [ebay] Keyword '{category_id}' already completed. Skipping.")
            return

        start_page = kw_data.get("last_page", 0) + 1
        if start_page > max_pages:
             print(f"✅ [ebay] Reached max page limit ({max_pages}). Marking complete.")
             checkpoint[category_id] = {"last_page": max_pages, "status": "completed"}
             await self.save_checkpoint(checkpoint)
             return

        async with async_playwright() as p:
            print(f"   [ebay] Launching browser (Headless: {headless})...")
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            
            page = await context.new_page()
            await stealth_async(page)
            
            for pgn in range(start_page, max_pages + 1):
                url = f"{self.base_url}?_nkw={category_id.replace(' ', '+')}&_pgn={pgn}&_ipg=60"
                print(f"📄 [ebay] Page {pgn}/{max_pages}: {url}")
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    # Random sleep to mimic human
                    sleep_sec = random.uniform(3.0, 7.0)
                    await asyncio.sleep(sleep_sec)
                    
                    # Get content
                    content = await page.content()
                    
                    # CAPTCHA Check
                    # More specific check to avoid false positives
                    if "captcha-delivery" in content or "distil_captcha" in content or ("verify you are human" in content.lower() and "security check" in content.lower()):
                        print("⚠️ [ebay] CAPTCHA detected!")
                        if not headless:
                            print("   [ACTION REQUIRED] Please solve the CAPTCHA in the browser window.")
                            # Ask only ONCE when explicitly caught
                            input("   Press Enter here AFTER you have solved it...")
                            content = await page.content()
                        else:
                            print("   [ebay] Headless mode is ON. Cannot solve manually.")
                            checkpoint[category_id] = {"last_page": pgn - 1, "status": "blocked"}
                            await self.save_checkpoint(checkpoint)
                            break
                    
                    # Parse
                    soup = BeautifulSoup(content, 'html.parser')
                    items = soup.select('li.s-item') or soup.select('li.s-card') or soup.select('.s-item')
                    
                    # Filter out "Shop on eBay" pseudo-item if it's the only one
                    valid_items = []
                    for item in items:
                        if "Shop on eBay" in item.get_text():
                            continue
                        valid_items.append(item)
                    
                    if not valid_items:
                        print("⚠️ [ebay] No items found on this page.")
                        if "No matching results" in content:
                             print("   [ebay] No more results defined by page.")
                             checkpoint[category_id] = {"last_page": pgn, "status": "completed"}
                             await self.save_checkpoint(checkpoint)
                             break
                        else:
                             print("   [ebay] Possible hidden items or soft-block. Skipping page...")
                             # DO NOT PAUSE HERE, just skip to next page or break to avoid stuck loop
                             # checkpoint[category_id] = {"last_page": pgn - 1, "status": "error"}
                             # await self.save_checkpoint(checkpoint)
                             break

                    saved_count = 0
                    for item in valid_items:
                        product_data = self.parser.parse_product(item, self.source, category_id)
                        if product_data:
                            self.save_product(product_data)
                            saved_count += 1
                    
                    print(f"   ✅ [ebay] Saved {saved_count} new items from page {pgn}.")
                    
                    # Update stats
                    self.total_items_collected = len(self.seen)
                    elapsed = datetime.now() - self.start_time
                    print(f"   📊 Total Unique Data: {self.total_items_collected} | Elapsed: {str(elapsed).split('.')[0]}")
                    
                    # Checkpoint Update
                    checkpoint[category_id] = {"last_page": pgn, "status": "in_progress"}
                    await self.save_checkpoint(checkpoint)
                    
                    # Check Next Button
                    next_btn = soup.select_one('.pagination__next')
                    if not next_btn or 'disabled' in next_btn.get('class', []):
                        print("   [ebay] Reached last page.")
                        checkpoint[category_id]["status"] = "completed"
                        await self.save_checkpoint(checkpoint)
                        break

                except Exception as e:
                    print(f"❌ [ebay] Error on page {pgn}: {e}")
                    # Don't break immediately on minor errors, but maybe pause?
                    # break
            
            await browser.close()


    # Abstract methods implementation
    async def crawl_product_detail(self, session, product_id): pass
    async def get_product_ids_from_page(self, session, category_id, page): return []
    def parse_product(self, raw_data): return raw_data
