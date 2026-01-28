import requests
import time
import random
import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from schema_shared import ProductItem

print("📂 CWD =", os.getcwd())

# ================== CONFIG ==================
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_FOLDER, "tiki_all.jsonl")

# CẤU HÌNH ĐA LUỒNG
MAX_WORKERS = 5  
MAX_PAGES = 100 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://tiki.vn/",
}

# CÁC KHÓA AN TOÀN
FILE_LOCK = threading.Lock()
SEEN = set()

# [QUAN TRỌNG] Biến toàn cục để lưu trạng thái dừng của từng Category
# Ví dụ: { 8313: False, 1951: True ... } -> True nghĩa là đã hết trang, cần dừng
STOP_FLAGS = {} 

# ================== HÀM HỖ TRỢ ==================
def load_existing_data():
    if not os.path.exists(OUTPUT_FILE):
        return
    print(f"🔄 Đang đọc dữ liệu cũ...")
    count = 0
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "id" in data:
                        SEEN.add(data["id"])
                        count += 1
                except: continue
    except: pass
    print(f"✅ Đã tải {count} sản phẩm cũ vào bộ nhớ.")

def save_items_safe(items, category_name):
    new_items_count = 0
    with FILE_LOCK:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            for item in items:
                pid = f"tiki_{item.get('id')}"
                if pid in SEEN: continue
                
                SEEN.add(pid)
                
                original_price = item.get("list_price") or item.get("price")
                product = ProductItem(
                    id=pid,
                    platform="tiki",
                    title=item.get("name", ""),
                    price=int(item.get("price", 0)),
                    original_price=int(original_price or 0),
                    url="https://tiki.vn/" + item.get("url_path", ""),
                    image_url=item.get("thumbnail_url", ""),
                    category=category_name,
                    brand=item.get("brand_name", "No Brand"),
                )
                f.write(product.to_json_line() + "\n")
                new_items_count += 1
    return new_items_count

# ================== WORKER (CÓ KIỂM TRA DỪNG) ==================
def crawl_single_page(category_name, category_id, page):
    # 1. KIỂM TRA CỜ HIỆU TRƯỚC KHI CHẠY
    # Nếu danh mục này đã bị đánh dấu là "Hết trang" (True), thì bỏ qua ngay
    if STOP_FLAGS.get(category_id) is True:
        return f"⛔ {category_name} - Page {page}: Đã dừng vì hết trang trước đó."

    url = (
        "https://tiki.vn/api/personalish/v1/blocks/listings"
        f"?limit=40&include=advertisement"
        f"&aggregations=2&version=home-persionalized"
        f"&trackity_id=123&category={category_id}&page={page}"
    )

    try:
        time.sleep(random.uniform(0.5, 1.5)) # Sleep nhẹ
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
        if resp.status_code != 200:
            return f"⚠️ {category_name} - Page {page}: Lỗi HTTP {resp.status_code}"

        items = resp.json().get("data", [])
        
        # 2. LOGIC PHÁT HIỆN HẾT TRANG
        if not items:
            # Nếu trang trả về rỗng -> Đánh dấu vào từ điển toàn cục là STOP
            STOP_FLAGS[category_id] = True
            return f"🛑 {category_name} - Page {page}: RỖNG -> Kích hoạt dừng cào category này!"

        # Lưu dữ liệu
        added = save_items_safe(items, category_name)
        return f"✅ {category_name} - Page {page}: Lấy {len(items)}, Mới {added}"

    except Exception as e:
        return f"❌ {category_name} - Page {page}: Lỗi {e}"

# ================== MAIN ==================
TIKI_CATEGORIES = [

]


if __name__ == "__main__":
    load_existing_data()
    
    # Khởi tạo cờ hiệu: Ban đầu tất cả đều chưa dừng (False)
    for cat in TIKI_CATEGORIES:
        STOP_FLAGS[cat["id"]] = False
    
    # Tạo danh sách nhiệm vụ
    all_tasks = []
    for cat in TIKI_CATEGORIES:
        for p in range(1, MAX_PAGES + 1):
            all_tasks.append((cat["name"], cat["id"], p))
            
    print(f"\n🚀 BẮT ĐẦU: {len(all_tasks)} trang dự kiến (sẽ dừng sớm nếu hết).")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {
            executor.submit(crawl_single_page, t[0], t[1], t[2]): t 
            for t in all_tasks
        }
        
        for future in as_completed(future_to_page):
            print(future.result())

    print("\n🎉 HOÀN THÀNH - Code đã tự động bỏ qua các trang thừa.")
    print("📦 Total unique items:", len(SEEN))
