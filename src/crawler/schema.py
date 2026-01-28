"""
ProductItem Schema - Unified data schema for all crawler platforms.
Matches MASTER_DATA_CLEAN.jsonl format (Clean V30).
"""

import json
import time

# --- ĐỊNH NGHĨA TÊN TRƯỜNG (KHỚP 100% VỚI CODE CLEAN V30) ---
FIELD_ID = "id"
FIELD_PLATFORM = "platform"
FIELD_TITLE = "title"
FIELD_LINK = "link"              # Đã đổi từ 'url' sang 'link'
FIELD_IMAGE_URL = "image_url"
FIELD_PRICE = "price"
FIELD_ORIGINAL_PRICE = "original_price"
FIELD_SOLD_COUNT = "sold_count"  # Số lượng bán
FIELD_CATEGORY = "category"
FIELD_BRAND = "brand"

# Các trường hỗ trợ Xử lý ngôn ngữ tự nhiên (NLP) & Tracking
FIELD_TITLE_CLEAN = "title_clean"
FIELD_TITLE_SEGMENTED = "title_segmented"
FIELD_SOURCE_FILE = "source_file"


class ProductItem:
    """
    Unified Product Schema for all crawler platforms.
    Structure matches MASTER_DATA_CLEAN.jsonl format.
    """
    
    def __init__(self, 
                 id: str, 
                 platform: str, 
                 title: str, 
                 price: int, 
                 link: str,          # Thay tham số url bằng link
                 image_url: str = "", 
                 category: str = "", 
                 sold_count: int = 0, # Mặc định là 0
                 brand: str = "No Brand",
                 original_price: int = None,
                 # Các tham số mở rộng (Optional)
                 title_clean: str = "",
                 title_segmented: str = "",
                 source_file: str = ""):
        
        # 1. Xử lý logic an toàn dữ liệu
        if original_price is None or original_price <= 0:
            original_price = price
            
        # Xử lý Title: Xóa ký tự xuống dòng
        clean_title = title.strip().replace('\n', ' ').replace('\r', '') if title else ""
        
        # 2. Đóng gói vào dictionary (Cấu trúc y hệt file MASTER_DATA_CLEAN.jsonl)
        self.data = {
            FIELD_ID: str(id),
            FIELD_TITLE: clean_title,
            FIELD_PRICE: int(price),
            FIELD_ORIGINAL_PRICE: int(original_price),
            FIELD_SOLD_COUNT: int(sold_count),    # Quan trọng: Int
            FIELD_PLATFORM: str(platform).lower(), # Luôn viết thường
            FIELD_CATEGORY: str(category),
            FIELD_BRAND: str(brand),
            FIELD_LINK: str(link),                # Khớp với file Master
            FIELD_IMAGE_URL: str(image_url),
            
            # Các trường phụ (có thể rỗng ban đầu, điền sau khi clean)
            FIELD_TITLE_CLEAN: str(title_clean),
            FIELD_TITLE_SEGMENTED: str(title_segmented),
            FIELD_SOURCE_FILE: str(source_file)
        }

    def to_dict(self):
        """Convert object to dictionary for saving."""
        return self.data
    
    def to_json_line(self):
        """Chuyển object thành chuỗi JSON trên 1 dòng"""
        return json.dumps(self.data, ensure_ascii=False)
    
    def __repr__(self):
        return f"ProductItem(id={self.data[FIELD_ID]}, title={self.data[FIELD_TITLE][:30]}...)"
