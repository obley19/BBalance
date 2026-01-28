from DrissionPage import ChromiumPage, ChromiumOptions
from multiprocessing import Process, Lock, Event
import json
import time
import random
import os
import urllib.parse
import math
import shutil

# ================== CẤU HÌNH ==================
NUM_PROCESSES = 3 
PAGES_PER_KW = 100

KEYWORDS = [
    "đèn bi cầu led mini", "cảm biến áp suất lốp van trong", "tấm cách âm chống ồn ô tô", 
    "bơm lốp ô tô điện tử", "bút xóa vết xước sơn ô tô", "dung dịch tẩy ố kính xe", 
    "chống đổ xe máy", "gác chân sau nhôm đúc", "lọc gió trụ K&N", "bugi iridium", 
    "cùm tăng tốc domino", "bao tay RCB chính hãng", "nhông sên dĩa DID",
    "máy lọc nước cho mèo inox", "máy sấy lông thú cưng", "thức ăn hạt sấy khô lạnh", 
    "gel dinh dưỡng cho mèo", "thuốc trị nấm cho chó mèo", "bỉm cho chó đực", 
    "cỏ mèo tươi", "đồ chơi thông minh cho chó", "vòng cổ GPS thú cưng", 
    "thuốc xịt hướng dẫn vệ sinh đúng chỗ", "pate tươi handmade cho thú cưng",
    "sách artbook game anime", "sách triết học nhập môn", "vở viết calligraphy", 
    "bút thư pháp Nhật Bản", "mực viết máy cao cấp Iroshizuku", "con dấu sáp seal wax", 
    "giấy vẽ watercolor 300gsm", "kệ sách gỗ thông mini", "đèn đọc sách chống cận", 
    "túi tote vải canvas đựng sách", "bàn phím cơ custom", "keycap resin thủ công", 
    "chuột gaming không dây siêu nhẹ", "lót chuột khổ lớn 90x40", "đèn led treo màn hình", 
    "mô hình nhân vật tỷ lệ 1/12", "bộ kit thêu chữ thập", "len sợi milk cotton", 
    "máy in ảnh lấy liền", "bộ màu marker 80 màu", "con quay giảm stress metal",
    "cây thủy tùng để bàn", "sen đá kim cương", "cây nắp ấm bắt mồi", 
    "hệ thống tưới nhỏ giọt tự động", "đèn led quang phổ cho cây", "đất nung Akadama", 
    "phân bón tan chậm Nhật Bản", "kéo tỉa cành bonsai", "máy đo độ ẩm đất",
    "bàn xếp nhôm dã ngoại", "ghế xếp thư giãn Naturehike", "ly giữ nhiệt quân đội", 
    "túi ngủ chịu nhiệt âm độ", "bếp củi camping gấp gọn", "thùng giữ nhiệt có bánh xe", 
    "máy lọc nước cầm tay du lịch", "dây thun ràng đồ siêu bền", "móc khóa đa năng 10 trong 1",
    "module camera ESP32", "màn hình OLED 0.96 inch", "cảm biến vân tay Arduino", 
    "bộ kit xe tự hành robot", "pin LiPo 3.7V", "trạm hàn thiếc điều chỉnh nhiệt", 
    "nguồn tổ ong 12v 20a", "dây cáp jumper đực cái", "vỏ case Raspberry Pi 4",
    "viên uống bổ mắt chống ánh sáng xanh", "kẹo dẻo giúp ngủ ngon melatonin", 
    "bột protein thực vật", "máy massage cổ vai gáy cầm tay", "máy tăm nước cầm tay", 
    "miếng dán mụn hydrocolloid", "xịt khoáng làm dịu da", "thanh lăn massage mặt đá cẩm thạch"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_shopee")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, "shopee_tong_hop.jsonl") 

file_lock = Lock()

def load_existing_links():
    seen = set()
    if not os.path.exists(OUTPUT_FILE): return seen
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    link = data.get("link", "")
                    if link: seen.add(link.split('?')[0])
                except: continue
    except: pass
    return seen

def run_browser_worker(worker_id, keywords_chunk, start_event):
    print(f"🤖 Worker {worker_id}: Đang khởi tạo môi trường...")
    local_seen = load_existing_links()
    
    co = ChromiumOptions()
    port = 9330 + worker_id 
    co.set_local_port(port)
    
    # --- SỬA LỖI TẠI ĐÂY ---
    try:
        co.headless(False) # Cú pháp đúng cho bản mới
    except AttributeError:
        co.set_argument('--headless=new') if False else None # Dự phòng cho bản rất cũ
        
    co.set_argument('--start-maximized')
    co.set_argument('--no-sandbox')
    co.set_argument('--mute-audio')
    
    user_data_path = os.path.abspath(os.path.join(BASE_DIR, f"UserData_W{worker_id}"))
    co.set_user_data_path(user_data_path)

    try:
        page = ChromiumPage(addr_or_opts=co)
        print(f"🌐 Worker {worker_id}: Đang mở Shopee tại Port {port}...")
        page.get("https://shopee.vn")
        
        start_event.wait() 
        
        for kw in keywords_chunk:
            print(f"🔍 Worker {worker_id}: Tìm kiếm '{kw}'")
            low_quality_streak = 0
            
            for page_num in range(PAGES_PER_KW):
                encoded_kw = urllib.parse.quote(kw)
                url = f"https://shopee.vn/search?keyword={encoded_kw}&page={page_num}"
                
                try:
                    page.get(url)
                    time.sleep(random.uniform(4, 6))
                    
                    if "shopee.vn/buyer/login" in page.url or page.ele('text:Đăng nhập'):
                        print(f"⚠️ Worker {worker_id}: Cần xử lý Captcha/Login. Đang tạm dừng...")
                        time.sleep(15)
                        page.refresh()

                    for _ in range(4):
                        page.scroll.down(1200)
                        time.sleep(0.8)
                    page.scroll.to_bottom()
                    time.sleep(1)

                    links = page.eles('css:a[href*="-i."]')
                    if len(links) < 5:
                        low_quality_streak += 1
                        if low_quality_streak >= 3: break
                        continue
                    else: low_quality_streak = 0

                    buffer = []
                    count = 0
                    for item in links:
                        try:
                            href = item.attr('href')
                            if not href: continue
                            if "http" not in href: href = "https://shopee.vn" + href
                            clean_link = href.split('?')[0]
                            if clean_link in local_seen: continue
                            
                            lines = [l.strip() for l in item.text.split('\n') if l.strip()]
                            if len(lines) < 2: continue
                            
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
                                row = {"title": title, "price": price, "sold": sold, "link": clean_link, "keyword": kw, "platform": "Shopee"}
                                buffer.append(json.dumps(row, ensure_ascii=False))
                                local_seen.add(clean_link)
                                count += 1
                        except: continue
                    
                    if buffer:
                        with file_lock:
                            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                                f.write("\n".join(buffer) + "\n")
                    
                    print(f"✅ W{worker_id} | {kw} (P{page_num+1}): Lấy được {count} món.")
                except Exception as e:
                    print(f"❌ W{worker_id} lỗi: {e}")
                    time.sleep(5)
            
    except Exception as e:
        print(f"❌ Worker {worker_id} chết: {e}")
    finally:
        try: page.quit()
        except: pass

if __name__ == "__main__":
    chunk_size = math.ceil(len(KEYWORDS) / NUM_PROCESSES)
    keyword_chunks = [KEYWORDS[i:i + chunk_size] for i in range(0, len(KEYWORDS), chunk_size)]
    start_event = Event()
    
    print("="*60)
    print(f"🔥 KHỞI CHẠY HỆ THỐNG CÀO SHOPEE - 3 TRÌNH DUYỆT")
    print("="*60)
    
    processes = []
    for i in range(NUM_PROCESSES):
        if i < len(keyword_chunks):
            p = Process(target=run_browser_worker, args=(i+1, keyword_chunks[i], start_event))
            processes.append(p)
            p.start()
            time.sleep(3) 
            
    print("\n👉 ĐANG MỞ TRÌNH DUYỆT... VUI LÒNG ĐỢI.")
    input("👉 SAU KHI CÁC CỬA SỔ ĐÃ HIỆN LÊN, NHẤN [ENTER] ĐỂ CHẠY...")
    
    start_event.set()
    for p in processes:
        p.join()
    print("\n🏆 HOÀN THÀNH.")