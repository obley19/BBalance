import requests
import json
import time
import os
import random
from datetime import datetime

# Import module Cleaner bạn vừa tạo ở bước trước
# Lưu ý: Cần đảm bảo file src/processor/__init__.py đã tồn tại
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from src.processor.cleaner import DataCleaner

class TikiSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://tiki.vn/',
        }
        self.cleaner = DataCleaner()
        self.output_file = 'data/processed/tiki_products.jsonl'
        
        # Tạo folder data/processed nếu chưa có
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

    def crawl_product_detail(self, product_id):
        """Lấy chi tiết 1 sản phẩm (như POC đã làm)"""
        try:
            url = f"https://tiki.vn/api/v2/products/{product_id}"
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None

    def parse_and_save(self, raw_data):
        """Làm sạch và lưu dữ liệu đúng chuẩn Schema"""
        if not raw_data:
            return

        # 1. Clean Data
        clean_title = self.cleaner.normalize_text(raw_data.get('name'))
        clean_desc = self.cleaner.clean_html(raw_data.get('description'))
        
        # 2. Map theo Schema (docs/data_schema.md)
        product = {
            "id": f"tiki_{raw_data.get('id')}",
            "original_id": raw_data.get('id'),
            "title": raw_data.get('name', ''),
            "price": raw_data.get('price', -1),
            "url": f"https://tiki.vn/{raw_data.get('url_path', '')}",
            "image_url": raw_data.get('thumbnail_url', ''),
            "category": raw_data.get('categories', {}).get('name', 'Unknown'),
            "source": "tiki",
            "rating": raw_data.get('rating_average', 0),
            "sold_count": raw_data.get('all_time_quantity_sold', 0),
            "description_clean": clean_desc, # Dùng cho search
            "title_clean": clean_title,      # Dùng cho search
            "crawled_at": datetime.now().isoformat()
        }

        # 3. Lưu (Append mode)
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(product, ensure_ascii=False) + '\n')
        
        print(f"✅ Saved: {product['id']} - {product['title'][:30]}...")

    def crawl_category(self, category_id, max_pages=3):
        """
        Crawl toàn bộ sản phẩm trong 1 danh mục
        API Listing: https://tiki.vn/api/personalish/v1/blocks/listings
        """
        base_url = "https://tiki.vn/api/personalish/v1/blocks/listings"
        
        for page in range(1, max_pages + 1):
            print(f"\n--- 📄 Page {page} (Category {category_id}) ---")
            params = {
                'limit': 40,            # 40 sản phẩm/trang
                'include': 'advertisement',
                'aggregations': 2,
                'trackity_id': '78d3810d-275d-8523-2868-e04732162985',
                'category': category_id,
                'page': page,
                'urlKey': 'dien-thoai-may-tinh-bang' # Chỉ là key giả để API chạy
            }
            
            try:
                resp = requests.get(base_url, headers=self.headers, params=params)
                if resp.status_code == 200:
                    items = resp.json().get('data', [])
                    if not items:
                        print("⚠️ Hết sản phẩm, dừng crawl.")
                        break
                    
                    # Lặp qua từng sản phẩm trong trang danh sách
                    for item in items:
                        pid = item.get('id')
                        # Gọi API chi tiết để lấy full description
                        detail = self.crawl_product_detail(pid)
                        self.parse_and_save(detail)
                        
                        # Sleep nhẹ để tránh bị block IP
                        time.sleep(random.uniform(0.5, 1.5))
                else:
                    print(f"❌ Lỗi trang danh mục: {resp.status_code}")
            except Exception as e:
                print(f"❌ Lỗi hệ thống: {e}")

if __name__ == "__main__":
    spider = TikiSpider()
    
    # ID 1789: Điện thoại - Máy tính bảng
    # ID 1882: Điện gia dụng
    # ID 8322: Nhà sách Tiki
    target_categories = [1789, 1882, 8322]
    
    for cat_id in target_categories:
        print(f"\n🚀 Bắt đầu crawl danh mục: {cat_id}")
        spider.crawl_category(cat_id, max_pages=1) # Test thử 1 trang mỗi loại