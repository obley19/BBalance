import requests
import json
import time
import random

# Headers giả lập trình duyệt thật để tránh bị block (Cực kỳ quan trọng)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://tiki.vn/',
}

# API của Tiki (Thường lấy qua API sẽ dễ hơn parse HTML)
# Bạn cần F12 -> Network -> Fetch/XHR để tìm API này
BASE_URL = "https://tiki.vn/api/v2/products"

def crawl_product_by_id(product_id):
    """
    Thử crawl 1 sản phẩm cụ thể để xem cấu trúc JSON trả về
    """
    try:
        url = f"{BASE_URL}/{product_id}"
        print(f"🔄 Đang tải: {url}")
        
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            
            # Trích xuất các trường quan trọng (Cần cho Search Engine)
            extracted_data = {
                'id': data.get('id'),
                'name': data.get('name'),
                'price': data.get('price'),
                'url_path': data.get('url_path'),
                'description': data.get('description'), # Cần clean html tags sau này
                'rating_average': data.get('rating_average'),
                'all_time_quantity_sold': data.get('all_time_quantity_sold')
            }
            return extracted_data
        else:
            print(f"❌ Lỗi {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"⚠️ Exception: {e}")
        return None

if __name__ == "__main__":
    # Test với 1 ID sản phẩm thực tế trên Tiki (Ví dụ: iPhone 15 hoặc sách)
    # Bạn lấy ID này trên thanh địa chỉ URL của sản phẩm
    test_id = 271965636  
    
    result = crawl_product_by_id(test_id)
    
    if result:
        print("\n✅ CRAWL THÀNH CÔNG (Mẫu dữ liệu):")
        print(json.dumps(result, indent=4, ensure_ascii=False))
        
        # Ghi log: Đây là bước Research, hãy ghi vào ai_log.md nếu bạn dùng AI để tìm API endpoint
    else:
        print("\n❌ Thất bại. Cần kiểm tra lại Headers hoặc IP.")