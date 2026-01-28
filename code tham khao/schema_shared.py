import json
import time

# --- ĐỊNH NGHĨA TÊN TRƯỜNG (CONSTANTS) ---
# Dùng hằng số để đảm bảo 3 người không ai gõ sai tên trường (VD: 'img' vs 'image')
FIELD_ID = "id"
FIELD_PLATFORM = "platform"
FIELD_TITLE = "title"
FIELD_URL = "url"
FIELD_IMAGE_URL = "image_url"
FIELD_PRICE = "price"
FIELD_ORIGINAL_PRICE = "original_price"
FIELD_CATEGORY = "category"
FIELD_BRAND = "brand"
FIELD_CRAWLED_AT = "crawled_at"

class ProductItem:
    def __init__(self, 
                 id: str, 
                 platform: str, 
                 title: str, 
                 price: int, 
                 url: str, 
                 image_url: str, 
                 category: str, 
                 brand: str = "No Brand",
                 original_price: int = None):
        
        # 1. Xử lý logic an toàn dữ liệu ngay khi khởi tạo
        
        # Nếu không có giá gốc, mặc định bằng giá bán
        if original_price is None:
            original_price = price
            
        # Xử lý Title: Xóa ký tự xuống dòng (\n) để không làm hỏng file JSONL
        clean_title = title.strip().replace('\n', ' ').replace('\r', '') if title else ""
        
        # 2. Đóng gói vào dictionary
        self.data = {
            FIELD_ID: str(id),
            FIELD_PLATFORM: str(platform),
            FIELD_TITLE: clean_title,
            FIELD_PRICE: int(price),
            FIELD_ORIGINAL_PRICE: int(original_price),
            FIELD_URL: str(url),
            FIELD_IMAGE_URL: str(image_url),
            FIELD_CATEGORY: str(category),
            FIELD_BRAND: str(brand),
            FIELD_CRAWLED_AT: int(time.time()) # Tự động lấy giờ hiện tại
        }

    def to_json_line(self):
        """Chuyển object thành chuỗi JSON trên 1 dòng (dùng cho file .jsonl)"""
        return json.dumps(self.data, ensure_ascii=False)

