import os
import time
import json
import random
import urllib.parse
import math
import shutil
import requests
import threading
from multiprocessing import Process, Lock, Event
from concurrent.futures import ThreadPoolExecutor, as_completed
from DrissionPage import ChromiumPage, ChromiumOptions

# ================== CẤU HÌNH CHUNG ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_crawled")
os.makedirs(DATA_DIR, exist_ok=True)

SHOPEE_FILE = os.path.join(DATA_DIR, "shopee_data.jsonl")
TIKI_FILE = os.path.join(DATA_DIR, "tiki_data.jsonl")

# Cấu hình Shopee
SHOPEE_PROCESSES = 3
SHOPEE_PAGES = 50

# Cấu hình Tiki
TIKI_WORKERS = 5
TIKI_PAGES = 50

# Khóa an toàn cho ghi file đa tiến trình
file_lock = Lock()

# ==============================================================================
#                                PHẦN 1: TIKI CRAWLER (API)
# ==============================================================================
TIKI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://tiki.vn/",
}

TIKI_CATEGORIES = [
    {"id": 8322, "name": "Nhà Sách Tiki"},
    {"id": 1815, "name": "Thiết Bị Số"},
    {"id": 1846, "name": "Laptop"},
    {"id": 1801, "name": "Máy Ảnh"},
    {"id": 1789, "name": "Điện Thoại"},
    {"id": 4221, "name": "Điện Tử"},
    {"id": 1882, "name": "Gia Dụng"},
    {"id": 1883, "name": "Nhà Cửa"},
    {"id": 931, "name": "Thời Trang Nam"},
    {"id": 915, "name": "Thời Trang Nữ"},
    {"id": 1703, "name": "Giày Dép Nam"},
    {"id": 1686, "name": "Giày Dép Nữ"},
    {"id": 976, "name": "Túi Thời Trang Nữ"},
    {"id": 27616, "name": "Túi Thời Trang Nam"},
    {"id": 8594, "name": "Xe Máy"},
    {"id": 8595, "name": "Phụ Kiện Xe"},
    {"id": 1975, "name": "Thể Thao"},
    {"id": 11312, "name": "Dã Ngoại"},
]

STOP_FLAGS = {} # Cờ hiệu dừng Tiki
SEEN_TIKI = set()

def load_tiki_data():
    if not os.path.exists(TIKI_FILE): return
    try:
        with open(TIKI_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if "id" in d: SEEN_TIKI.add(d["id"])
                except: continue
    except: pass
    print(f"📘 [TIKI] Đã nhớ {len(SEEN_TIKI)} sản phẩm cũ.")

def crawl_tiki_worker(cat_name, cat_id, page):
    if STOP_FLAGS.get(cat_id) is True: return # Dừng nếu đã hết trang
    
    url = f"https://tiki.vn/api/personalish/v1/blocks/listings?limit=40&include=advertisement&aggregations=2&version=home-persionalized&trackity_id=123&category={cat_id}&page={page}"
    try:
        time.sleep(random.uniform(0.5, 1.0))
        resp = requests.get(url, headers=TIKI_HEADERS, timeout=10)
        if resp.status_code != 200: return
        
        items = resp.json().get("data", [])
        if not items:
            STOP_FLAGS[cat_id] = True # Kích hoạt cờ dừng
            return
        
        new_count = 0
        with open(TIKI_FILE, "a", encoding="utf-8") as f:
            for item in items:
                pid = str(item.get("id"))
                if pid in SEEN_TIKI: continue
                SEEN_TIKI.add(pid)
                
                row = {
                    "id": pid, "platform": "tiki",
                    "title": item.get("name"),
                    "price": int(item.get("price") or 0),
                    "original_price": int(item.get("list_price") or 0),
                    "sold": str(item.get("quantity_sold", {}).get("value", 0)),
                    "category": cat_name,
                    "url": "https://tiki.vn/" + item.get("url_path", ""),
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                new_count += 1
        print(f"   🔹 [TIKI] {cat_name} (P{page}): +{new_count} món")
    except: pass

def run_tiki_crawler():
    print("\n" + "="*40)
    print("🚀 ĐANG KHỞI ĐỘNG TIKI CRAWLER...")
    print("="*40)
    load_tiki_data()
    
    # Reset cờ dừng
    for c in TIKI_CATEGORIES: STOP_FLAGS[c["id"]] = False
    
    tasks = []
    for c in TIKI_CATEGORIES:
        for p in range(1, TIKI_PAGES + 1):
            tasks.append((c["name"], c["id"], p))
            
    with ThreadPoolExecutor(max_workers=TIKI_WORKERS) as exe:
        futures = {exe.submit(crawl_tiki_worker, t[0], t[1], t[2]): t for t in tasks}
        for _ in as_completed(futures): pass
        
    print("\n✅ TIKI DONE! Data saved to:", TIKI_FILE)


# ==============================================================================
#                                PHẦN 2: SHOPEE CRAWLER (BROWSER)
# ==============================================================================
SHOPEE_KEYWORDS = [
    # Thêm list keyword dài ngoằng của bạn vào đây
    "nồi chiên không dầu", "son môi", "tai nghe bluetooth", 
    "mũ bảo hiểm 3/4", "thức ăn cho mèo", "sách đắc nhân tâm",
    "rubik 3x3", "hạt giống rau", "cần câu máy", "mỏ hàn thiếc",
    "vitamin c dhc", "bao lì xì tết", "bánh pía sóc trăng",
    "khẩu trang y tế", "sơn xịt atm", "wig cosplay anime"
]

def load_shopee_links():
    seen = set()
    if not os.path.exists(SHOPEE_FILE): return seen
    try:
        with open(SHOPEE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if "link" in d: seen.add(d["link"].split('?')[0])
                except: continue
    except: pass
    return seen

def run_shopee_worker(worker_id, keywords, start_event):
    print(f"🤖 [SHOPEE] Worker {worker_id} Ready...")
    local_seen = load_shopee_links()
    
    co = ChromiumOptions()
    co.set_local_port(9220 + worker_id) # Cổng riêng
    co.set_argument('--mute-audio')
    user_data = os.path.join(BASE_DIR, f"User_Shopee_{worker_id}")
    co.set_user_data_path(user_data)
    
    try:
        page = ChromiumPage(addr_or_opts=co)
        page.get("https://shopee.vn")
        
        print(f"⏳ [SHOPEE W{worker_id}] Đợi lệnh kích hoạt...")
        start_event.wait() # Chờ tín hiệu
        
        print(f"🚀 [SHOPEE W{worker_id}] GO!")
        
        for kw in keywords:
            print(f"   🔥 [SHOPEE W{worker_id}] Tìm: {kw}")
            bad_streak = 0
            
            for p_num in range(SHOPEE_PAGES):
                encoded = urllib.parse.quote(kw)
                url = f"https://shopee.vn/search?keyword={encoded}&page={p_num}"
                
                # Retry loop
                retry = 0
                while retry < 3:
                    try:
                        page.get(url)
                        time.sleep(4)
                        
                        # Check Captcha
                        if "verify/captcha" in page.url or page.ele("text:Xác nhận để tiếp tục"):
                            print(f"   🚨 [W{worker_id}] DÍNH CAPTCHA! Hãy xử lý thủ công...")
                            while "verify" in page.url: time.sleep(2)
                            print(f"   ✅ [W{worker_id}] Đã qua ải!")
                        
                        # Scroll
                        for _ in range(5):
                            page.scroll.down(1500)
                            time.sleep(0.5)
                        page.scroll.to_bottom()
                        time.sleep(1)
                        
                        links = page.eles('css:a[href*="-i."]')
                        if not links:
                            page.refresh()
                            retry += 1
                            time.sleep(3)
                            continue
                        else: break
                    except: 
                        retry += 1
                        time.sleep(2)
                
                # Stop Logic
                if len(links) < 5:
                    bad_streak += 1
                    if bad_streak >= 2: break
                else: bad_streak = 0
                
                # Save
                buffer = []
                c = 0
                for item in links:
                    try:
                        href = item.attr('href')
                        if not href: continue
                        if "http" not in href: href = "https://shopee.vn" + href
                        clean = href.split('?')[0]
                        if clean in local_seen: continue
                        
                        raw = item.text.split('\n')
                        lines = [x for x in raw if x.strip()]
                        if len(lines) < 2: continue
                        
                        title = lines[0]
                        if any(x in title for x in ["Yêu thích", "Mall", "Ad"]):
                            title = lines[1] if len(lines) > 1 else title
                            
                        price = 0
                        sold = "0"
                        for l in lines:
                            if '₫' in l or 'đ' in l:
                                p = l.replace('₫','').replace('đ','').replace('.','').strip()
                                if '-' in p: p = p.split('-')[0]
                                if p.isdigit(): price = int(p)
                            if 'Đã bán' in l or 'k' in l:
                                sold = l.replace('Đã bán','').strip()
                        
                        if price > 1000:
                            row = {"title": title, "price": price, "sold": sold, "platform": "shopee", "link": clean, "keyword": kw}
                            buffer.append(json.dumps(row, ensure_ascii=False))
                            local_seen.add(clean)
                            c += 1
                    except: continue
                
                if buffer:
                    with file_lock:
                        with open(SHOPEE_FILE, "a", encoding="utf-8") as f:
                            f.write("\n".join(buffer) + "\n")
                print(f"      ✅ [SHOPEE W{worker_id}] {kw} (P{p_num}): +{c} món")
                time.sleep(1)
            
            time.sleep(2)
        
        page.quit()
        try: shutil.rmtree(user_data, ignore_errors=True)
        except: pass
        
    except Exception as e:
        print(f"❌ [SHOPEE W{worker_id}] Error: {e}")

def run_shopee_crawler():
    print("\n" + "="*40)
    print("🚀 ĐANG KHỞI ĐỘNG SHOPEE CRAWLER...")
    print("="*40)
    
    chunk_size = math.ceil(len(SHOPEE_KEYWORDS) / SHOPEE_PROCESSES)
    chunks = [SHOPEE_KEYWORDS[i:i + chunk_size] for i in range(0, len(SHOPEE_KEYWORDS), chunk_size)]
    
    evt = Event()
    procs = []
    
    for i in range(SHOPEE_PROCESSES):
        if i < len(chunks):
            p = Process(target=run_shopee_worker, args=(i+1, chunks[i], evt))
            procs.append(p)
            p.start()
            time.sleep(3)
            
    print("\n📢 [SHOPEE] 3 Trình duyệt đang mở. Hãy đăng nhập nếu cần.")
    input("👉 BẤM [ENTER] ĐỂ BẮT ĐẦU CHẠY SHOPEE...")
    evt.set()
    
    for p in procs: p.join()
    print("\n✅ SHOPEE DONE! Data saved to:", SHOPEE_FILE)

# ==============================================================================
#                                PHẦN 3: MAIN CONTROLLER
# ==============================================================================
if __name__ == "__main__":
    while True:
        print("\n" + "█"*40)
        print("   🔥 SUPER CRAWLER V24 (GỘP ALL) 🔥")
        print("█"*40)
        print("1. Chạy TIKI (Nhanh, API, Nhẹ máy)")
        print("2. Chạy SHOPEE (Chậm, Browser, Cần login)")
        print("3. Chạy CẢ HAI (Hardcore mode)")
        print("4. Thoát")
        
        choice = input("👉 Chọn chế độ (1-4): ")
        
        if choice == "1":
            run_tiki_crawler()
        elif choice == "2":
            run_shopee_crawler()
        elif choice == "3":
            # Chạy song song cả hai bằng 2 tiến trình lớn
            p_tiki = Process(target=run_tiki_crawler)
            p_shopee = Process(target=run_shopee_crawler)
            
            p_tiki.start()
            p_shopee.start()
            
            p_tiki.join()
            p_shopee.join()
        elif choice == "4":
            print("👋 Bye bye!")
            break
        else:
            print("❌ Chọn sai rồi đại ca!")