import json
import time
import random
import urllib.parse
from typing import Optional

# Check if DrissionPage is installed, otherwise handle gracefully or raise error
try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    ChromiumPage = None
    ChromiumOptions = None

from ..base_spider import BaseSpider

class ShopeeSpider(BaseSpider):
    source = "shopee"
    base_url = "https://shopee.vn"
    
    def __init__(self):
        super().__init__()
        if not ChromiumPage:
            raise ImportError("DrissionPage is required for ShopeeSpider. Please install it.")
            
        self.page = None

    def _init_browser(self):
        if self.page:
            return

        co = ChromiumOptions()
        # Random port to avoid conflicts if multiple processes (though here we run single)
        port = 9330 + random.randint(0, 100) 
        co.set_local_port(port)
        
        # From reference:
        try:
            co.headless(False) 
        except AttributeError:
            co.set_argument('--headless=new')
            
        co.set_argument('--start-maximized')
        co.set_argument('--no-sandbox')
        co.set_argument('--mute-audio')
        
        # We can set user data path if needed, but for now let's keep it simple or temp
        # co.set_user_data_path(...)

        self.page = ChromiumPage(addr_or_opts=co)
        print(f"🌐 Shopee Browser initialized on port {port}")

    def crawl_category(self, category_id: str, max_pages: int = 3) -> None:
        """
        Crawl Shopee. 'category_id' is treated as a KEYWORD for search 
        because the reference code uses keyword search.
        """
        self._init_browser()
        
        keyword = category_id
        print(f"🔍 [SHOPEE] Searching for: '{keyword}'")
        
        # Open Shopee Home first
        self.page.get("https://shopee.vn")
        
        low_quality_streak = 0
        
        for page_num in range(max_pages):
            encoded_kw = urllib.parse.quote(keyword)
            # Shopee pagination is typically by offset: page 0, page 1 (which refers to index)
            # Reference uses &page={page_num}
            url = f"https://shopee.vn/search?keyword={encoded_kw}&page={page_num}"
            
            try:
                self.page.get(url)
                time.sleep(random.uniform(4, 6))
                
                # Check Login/Captcha
                if "shopee.vn/buyer/login" in self.page.url or self.page.ele('text:Đăng nhập'):
                     print(f"⚠️ Login/Captcha detected. Pausing 15s...")
                     time.sleep(15)
                     self.page.refresh()
                
                # Scroll to load lazy items
                for _ in range(4):
                    self.page.scroll.down(1200)
                    time.sleep(0.8)
                self.page.scroll.to_bottom()
                time.sleep(1)
                
                links = self.page.eles('css:a[href*="-i."]')
                if len(links) < 5:
                    low_quality_streak += 1
                    if low_quality_streak >= 3:
                        print("⚠️ Too many empty pages, stopping.")
                        break
                    continue
                else:
                    low_quality_streak = 0
                
                count = 0
                for item in links:
                    try:
                        href = item.attr('href')
                        if not href: continue
                        if "http" not in href: href = "https://shopee.vn" + href
                        
                        # Extract text lines for parsing
                        lines = [l.strip() for l in item.text.split('\n') if l.strip()]
                        if len(lines) < 2: continue
                        
                        raw_item = {
                            "link": href,
                            "lines": lines
                        }
                        
                        product = self.parse_product(raw_item)
                        if product:
                            self.save_product(product)
                            count += 1
                    except Exception as e:
                        continue
                        
                print(f"✅ [SHOPEE] Page {page_num+1}: Found {count} items.")
                
            except Exception as e:
                print(f"❌ Error on page {page_num}: {e}")
                time.sleep(5)
                
    def crawl_product_detail(self, product_id: str) -> Optional[dict]:
        return None

    def parse_product(self, raw_data: dict) -> dict:
        """
        Parse logic from reference 'run_browser_worker' function.
        raw_data expects {'link': str, 'lines': list[str]}
        """
        try:
            link = raw_data.get('link', '')
            lines = raw_data.get('lines', [])
            
            clean_link = link.split('?')[0]
            # ID extraction from link usually: ...-i.SHOPID.ITEMID
            # But BaseSpider builds its own ID usually. We can try to extract ID.
            # Example: https://shopee.vn/product-name-i.12345.67890
            try:
                # Extract the part after -i.
                id_part = clean_link.split('-i.')[-1]
                # shop_id, item_id = id_part.split('.') # Sometimes
                # Let's just use the whole tail as ID
                raw_id = id_part
            except:
                raw_id = clean_link[-15:] # Fallback
            
            product_id = self.build_product_id(raw_id)
            
            # Logic from reference
            title = lines[1] if any(x in lines[0] for x in ["Yêu thích", "Mall", "Ad"]) else lines[0]
            price = 0
            sold = "0"
            for l in lines:
                if '₫' in l:
                    p = l.replace('₫','').replace('.','').split('-')[0].strip()
                    if p.isdigit(): price = int(p)
                if 'Đã bán' in l:
                    sold = l.replace('Đã bán','').strip()

            if price > 0:
                return {
                    "id": product_id,
                    "platform": "Shopee",
                    "title": title,
                    "price": price,
                    # Reference doesn't strictly have original_price in list view usually, 
                    # unless calculated. We'll set same as price or 0.
                    "original_price": price,
                    "url": clean_link,
                    # No image url in the text parsing logic of reference (it accesses ele), 
                    # but here we only passed text lines. 
                    # To get image, we would need to pass element or image src.
                    # For now leave empty to match strict reference logic provided which used text.
                    # Wait, reference code didn't extract image in the snippet I saw?
                    # "row = {"title": title, "price": price, "sold": sold, "link": clean_link, ...}"
                    # Yes, reference output didn't have image.
                    "image_url": "", 
                    "sold_count": sold, # String in reference, maybe convert to int if possible?
                    "crawled_at": self.get_timestamp()
                }
            return {}
            
        except Exception as e:
            return {}

    def __del__(self):
        if self.page:
            try:
                self.page.quit()
            except: 
                pass
