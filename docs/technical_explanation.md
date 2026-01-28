# TÀI LIỆU KỸ THUẬT: GIẢI THÍCH CHI TIẾT HỆ THỐNG CRAWLER

## Đồ án: E-Commerce Search Engine (SEG301)

---

## Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Kỹ thuật Anti-Bot (Chống chặn)](#2-kỹ-thuật-anti-bot-chống-chặn)
3. [Chuẩn hóa dữ liệu (Data Schema)](#3-chuẩn-hóa-dữ-liệu-data-schema)
4. [Làm sạch văn bản (Text Cleaning)](#4-làm-sạch-văn-bản-text-cleaning)
5. [Xử lý giá tiền (Price Normalization)](#5-xử-lý-giá-tiền-price-normalization)
6. [Khử trùng lặp (De-duplication)](#6-khử-trùng-lặp-de-duplication)

---

## 1. Tổng quan kiến trúc

Hệ thống Crawler được thiết kế theo mô hình **Abstract Factory Pattern**, với một lớp cơ sở (`BaseSpider`) định nghĩa interface chung cho tất cả các spider.

### Cấu trúc thư mục

```
src/crawler/
├── base_spider.py      # Lớp cơ sở cho tất cả spider
├── async_base_spider.py # Lớp cơ sở cho spider bất đồng bộ
├── schema.py           # Định nghĩa ProductItem schema
├── parser.py           # Xử lý HTML và tách từ tiếng Việt
├── utils.py            # Các hàm tiện ích (User-Agent, config)
└── spiders/
    ├── shopee_spider.py
    ├── tiki_spider.py
    ├── chotot_async_spider.py
    └── ebay_async_spider.py
```

---

## 2. Kỹ thuật Anti-Bot (Chống chặn)

### 2.1. Xoay vòng User-Agent (User-Agent Rotation)

**File:** `src/crawler/utils.py`

```python
# Common User-Agents for rotating
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

def get_random_user_agent() -> str:
    """Return a random User-Agent string."""
    return random.choice(USER_AGENTS)
```

**Giải thích:**

- **Vấn đề:** Các sàn TMĐT kiểm tra header `User-Agent` để phát hiện bot. Nếu dùng User-Agent mặc định của thư viện (`python-requests/2.x`), sẽ bị block ngay lập tức.
- **Giải pháp:** Tạo danh sách các User-Agent phổ biến từ trình duyệt thật (Chrome, Firefox, Safari), sau đó chọn ngẫu nhiên mỗi lần gửi request.
- **Hiệu quả:** Giả lập hành vi của người dùng thực, tránh bị đánh dấu là bot.

---

### 2.2. Rate Limiting (Giới hạn tốc độ)

**File:** `src/crawler/base_spider.py`

```python
# Platform specific configurations
PLATFORM_CONFIGS = {
    "shopee": {"rate_limit": 2.0, "base_url": "https://shopee.vn"},
    "tiki":   {"rate_limit": 1.0, "base_url": "https://tiki.vn"},
    "chotot": {"rate_limit": 0.5, "base_url": "https://www.chotot.com"},
    "ebay":   {"rate_limit": 1.5, "base_url": "https://www.ebay.com"}
}

def sleep_random(self) -> None:
    """Sleep for a random duration to avoid rate limiting."""
    sleep_time = random.uniform(self.rate_limit * 0.5, self.rate_limit * 1.5)
    time.sleep(sleep_time)
```

**Giải thích:**

- **Vấn đề:** Gửi request liên tục với tốc độ cao sẽ kích hoạt hệ thống bảo vệ của sàn (ví dụ: Shopee block sau ~10 request/giây).
- **Giải pháp:**
  - Cấu hình `rate_limit` riêng cho từng sàn (Shopee: 2s, Tiki: 1s, Chợ Tốt: 0.5s, eBay: 1.5s)
  - Thêm độ ngẫu nhiên (`random.uniform`) để pattern không bị lặp lại
- **Công thức:** `sleep_time = rate_limit × (0.5 đến 1.5)`
  - Ví dụ: Shopee có rate_limit = 2.0 → sleep từ 1-3 giây giữa các request

---

### 2.3. Giả lập trình duyệt thật (Browser Automation)

**File:** `src/crawler/spiders/shopee_spider.py`

```python
from DrissionPage import ChromiumPage, ChromiumOptions

def _init_browser(self):
    co = ChromiumOptions()
    # Random port to avoid conflicts
    port = 9330 + random.randint(0, 100) 
    co.set_local_port(port)
    
    # Cấu hình trình duyệt
    co.headless(False)              # Chạy có giao diện (dễ debug)
    co.set_argument('--start-maximized')
    co.set_argument('--no-sandbox')
    co.set_argument('--mute-audio')
    
    self.page = ChromiumPage(addr_or_opts=co)
```

**Giải thích:**

- **Vấn đề:** Shopee sử dụng JavaScript rendering và anti-bot rất mạnh. Thư viện `requests` không thể xử lý được vì không chạy JavaScript.
- **Giải pháp:** Sử dụng `DrissionPage` (wrapper của Chromium) để:
  - Chạy JavaScript đầy đủ
  - Cookie và session được quản lý tự động
  - Fingerprint giống trình duyệt thật
- **Random port:** Mỗi lần khởi động dùng port khác nhau để tránh conflict khi chạy nhiều instance.

---

### 2.4. Phát hiện và xử lý CAPTCHA

**File:** `src/crawler/spiders/shopee_spider.py`

```python
# Check Login/Captcha
if "shopee.vn/buyer/login" in self.page.url or self.page.ele('text:Đăng nhập'):
    print(f"⚠️ Login/Captcha detected. Pausing 15s...")
    time.sleep(15)  # Cho người dùng tự giải captcha
    self.page.refresh()
```

**Giải thích:**

- **Nhận diện:** Kiểm tra URL có chứa `/buyer/login` hoặc có element text "Đăng nhập"
- **Xử lý:** Pause 15 giây để người dùng giải CAPTCHA thủ công (trong trường hợp chạy có giao diện)
- **Sau đó:** Refresh trang và tiếp tục crawl

---

### 2.5. Cuộn trang để load lazy-loading content

**File:** `src/crawler/spiders/shopee_spider.py`

```python
# Scroll to load lazy items
for _ in range(4):
    self.page.scroll.down(1200)  # Cuộn xuống 1200px
    time.sleep(0.8)              # Đợi JavaScript load
self.page.scroll.to_bottom()     # Cuộn tới cuối trang
time.sleep(1)
```

**Giải thích:**

- **Vấn đề:** Shopee dùng kỹ thuật Lazy Loading - chỉ load sản phẩm khi người dùng cuộn tới vùng hiển thị.
- **Giải pháp:** Mô phỏng hành vi cuộn trang:
  1. Cuộn từ từ (4 lần × 1200px = 4800px)
  2. Đợi 0.8s mỗi lần để JavaScript kịp load
  3. Cuộn tới cuối trang để đảm bảo load hết sản phẩm

---

## 3. Chuẩn hóa dữ liệu (Data Schema)

### 3.1. ProductItem Schema

**File:** `src/crawler/schema.py`

```python
# --- ĐỊNH NGHĨA TÊN TRƯỜNG (KHỚP 100% VỚI CODE CLEAN V30) ---
FIELD_ID = "id"
FIELD_PLATFORM = "platform"
FIELD_TITLE = "title"
FIELD_LINK = "link"
FIELD_IMAGE_URL = "image_url"
FIELD_PRICE = "price"
FIELD_ORIGINAL_PRICE = "original_price"
FIELD_SOLD_COUNT = "sold_count"
FIELD_CATEGORY = "category"
FIELD_BRAND = "brand"

class ProductItem:
    def __init__(self, id, platform, title, price, link, ...):
        # Xử lý logic an toàn dữ liệu
        if original_price is None or original_price <= 0:
            original_price = price  # Fallback: dùng giá hiện tại
            
        # Xử lý Title: Xóa ký tự xuống dòng
        clean_title = title.strip().replace('\n', ' ').replace('\r', '')
        
        # Đóng gói vào dictionary
        self.data = {
            FIELD_ID: str(id),
            FIELD_TITLE: clean_title,
            FIELD_PRICE: int(price),
            FIELD_PLATFORM: str(platform).lower(),  # Luôn viết thường
            # ... các field khác
        }
```

**Giải thích:**

- **Mục đích:** Đảm bảo tất cả dữ liệu từ 4 sàn khác nhau đều có cùng cấu trúc
- **Field Constants:** Dùng constants (`FIELD_ID`, `FIELD_TITLE`...) thay vì hardcode string để tránh lỗi typo
- **Validation tự động:**
  - `original_price`: Nếu null hoặc ≤ 0 → lấy giá hiện tại
  - `platform`: Luôn convert về lowercase (`Shopee` → `shopee`)
  - `title`: Xóa ký tự newline (`\n`, `\r`)

---

### 3.2. Tạo ID duy nhất

**File:** `src/crawler/base_spider.py`

```python
def build_product_id(self, original_id) -> str:
    """Build unique product ID with platform prefix."""
    return f"{self.source}_{original_id}"
```

**Giải thích:**

- **Vấn đề:** ID sản phẩm giữa các sàn có thể trùng nhau (ví dụ: Shopee và Tiki đều có product ID = `12345`)
- **Giải pháp:** Thêm prefix tên sàn vào trước ID
  - Input: `12345` (từ Shopee)
  - Output: `shopee_12345`
- **Lợi ích:** Đảm bảo ID unique trong toàn bộ hệ thống khi merge data

---

## 4. Làm sạch văn bản (Text Cleaning)

### 4.1. Loại bỏ HTML Tags

**File:** `src/crawler/parser.py`

```python
import re
import html

class DataCleaner:
    def __init__(self):
        # Regex để tìm tất cả các thẻ HTML (VD: <div>, <br>, </a>)
        self.html_tag_re = re.compile(r'<[^>]+>')
    
    def clean_html(self, raw_html: str) -> str:
        """
        Loại bỏ toàn bộ thẻ HTML và decode các ký tự entity
        VD: "&amp;" -> "&", "&nbsp;" -> " "
        """
        if not raw_html:
            return ""
        
        # 1. Unescape HTML entities
        text = html.unescape(raw_html)  # "&amp;" -> "&"
        
        # 2. Xóa thẻ HTML bằng Regex
        text = self.html_tag_re.sub(' ', text)  # "<div>text</div>" -> " text "
        
        # 3. Xóa khoảng trắng thừa
        text = ' '.join(text.split())  # "  iPhone   " -> "iPhone"
        
        return text
```

**Ví dụ thực tế:**

| Input | Output |
|-------|--------|
| `<h5>Nội dung quảng cáo</h5><p>iPhone 14 Pro Max.</p>` | `Nội dung quảng cáo iPhone 14 Pro Max.` |
| `Điện thoại &amp; Phụ kiện` | `Điện thoại & Phụ kiện` |

---

### 4.2. Tách từ tiếng Việt (Vietnamese Word Segmentation)

**File:** `src/crawler/parser.py`

```python
from pyvi import ViTokenizer

def normalize_text(self, text: str) -> str:
    """
    Chuẩn hóa văn bản để Indexing
    Input: "Điện thoại iPhone 14 Pro Max!"
    Output: "điện_thoại iphone 14 pro max"
    """
    # 1. Chuyển về chữ thường
    text = text.lower()
    
    # 2. Làm sạch HTML (đề phòng)
    text = self.clean_html(text)
    
    # 3. Tách từ tiếng Việt bằng PyVi
    # VD: "tính năng" -> "tính_năng"
    text = ViTokenizer.tokenize(text)
    
    return text
```

**Giải thích sự quan trọng của tách từ:**

| Input | Không tách từ | Có tách từ (PyVi) |
|-------|---------------|-------------------|
| "máy tính xách tay" | `["máy", "tính", "xách", "tay"]` | `["máy_tính", "xách_tay"]` |
| "điện thoại thông minh" | `["điện", "thoại", "thông", "minh"]` | `["điện_thoại", "thông_minh"]` |

**Tại sao cần tách từ?**

- Tiếng Việt là ngôn ngữ đơn lập (isolating language)
- Một từ có nghĩa thường gồm 2+ âm tiết: "máy tính" = 1 từ, không phải 2 từ
- Nếu không tách từ, search "máy tính" sẽ khớp cả "máy giặt" và "tính toán" → kết quả sai

---

## 5. Xử lý giá tiền (Price Normalization)

**File:** `src/processor/normalize_data.py`

```python
import re

def clean_price(price):
    """
    Chuyển đổi giá từ nhiều format về số nguyên
    VD: "1.200.000đ" -> 1200000
        "$99.99" -> 99
    """
    if isinstance(price, (int, float)):
        return int(price)
    
    if isinstance(price, str):
        # Xóa dấu chấm và phẩy, chỉ giữ lại số
        nums = re.findall(r'\d+', price.replace('.', '').replace(',', ''))
        if nums:
            return int(nums[0])
    
    return 0  # Default nếu không parse được
```

**Ví dụ xử lý:**

| Input | Output | Giải thích |
|-------|-------:|------------|
| `1200000` (int) | `1200000` | Đã là số nguyên |
| `1200000.0` (float) | `1200000` | Chuyển float → int |
| `"1.200.000đ"` | `1200000` | Xóa dấu chấm và ký tự đ |
| `"1,200,000 VND"` | `1200000` | Xóa dấu phẩy và VND |
| `"$99.99"` | `99` | Chỉ lấy phần số đầu tiên |
| `null` / `""` | `0` | Default value |

---

## 6. Khử trùng lặp (De-duplication)

**File:** `src/processor/deduplicate.py`

```python
def deduplicate_file(filepath: str) -> tuple[int, int]:
    """
    Khử trùng lặp file JSONL, giữ lại bản ghi mới nhất
    """
    products = {}  # id -> product (keep latest)
    original_count = 0
    
    # Đọc tất cả sản phẩm
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            product = json.loads(line)
            original_count += 1
            
            pid = product.get('id')
            if not pid:
                continue
            
            # Kiểm tra xem đã tồn tại chưa
            if pid in products:
                # So sánh timestamp, giữ bản mới hơn
                existing_time = products[pid].get('crawled_at', '')
                new_time = product.get('crawled_at', '')
                
                if new_time > existing_time:
                    products[pid] = product  # Thay thế bằng bản mới
            else:
                products[pid] = product  # Thêm mới
    
    return original_count, len(products)
```

**Logic hoạt động:**

1. Đọc từng dòng trong file JSONL
2. Với mỗi sản phẩm, kiểm tra `id` đã tồn tại trong dict chưa
3. Nếu trùng ID:
   - So sánh `crawled_at` (timestamp)
   - Giữ lại bản ghi có timestamp mới hơn
4. Ghi đè file với dữ liệu đã dedupe

**Kết quả thực tế:**

```
📊 DEDUPLICATION REPORT
==================================================
📄 shopee_products.jsonl
   Before: 850,000 | After: 800,284 | Removed: 49,716 (5.8%)
📄 tiki_products.jsonl
   Before: 440,000 | After: 435,203 | Removed: 4,797 (1.1%)
==================================================
📊 TOTAL: 1,290,000 → 1,235,487 (54,513 duplicates removed)
```

## 7. Hệ thống Checkpoint (Resume Crawling)

### 7.1. Tổng quan

**Vấn đề:** Khi crawl hàng triệu sản phẩm, quá trình có thể mất nhiều giờ/ngày. Nếu bị lỗi giữa chừng (mất điện, crash, bị block), phải crawl lại từ đầu → **lãng phí thời gian và tài nguyên**.

**Giải pháp:** Hệ thống Checkpoint lưu trạng thái crawl để có thể **resume từ chỗ dừng**.

### 7.2. Cấu trúc Checkpoint

**File:** `src/crawler/crawl_state.py`

```python
class CrawlState:
    def __init__(self, state_dir: str = "data/crawl_state"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
        
        self.checkpoint_file = os.path.join(state_dir, "checkpoint.json")
        self.crawled_ids_file = os.path.join(state_dir, "crawled_ids.txt")
        
        # Load existing state
        self.checkpoint = self._load_checkpoint()
        self.crawled_ids: Set[str] = self._load_crawled_ids()
```

**Hai file được lưu:**

| File | Nội dung | Mục đích |
|------|----------|----------|
| `checkpoint.json` | Category đang crawl, page hiện tại | Resume đúng vị trí |
| `crawled_ids.txt` | Danh sách ID đã crawl | Tránh crawl trùng |

### 7.3. Lưu trạng thái (Save Checkpoint)

```python
def save_checkpoint(self, platform: str, category: str, page: int) -> None:
    """Save current crawl progress."""
    self.checkpoint = {
        "platform": platform,
        "current_category": category,
        "last_page": page,
        "completed_categories": self.checkpoint.get("completed_categories", []),
        "timestamp": datetime.now().isoformat(),
    }
    with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(self.checkpoint, f, indent=2, ensure_ascii=False)
```

**Ví dụ nội dung `checkpoint.json`:**

```json
{
  "platform": "shopee",
  "current_category": "dien-thoai",
  "last_page": 15,
  "completed_categories": [
    "shopee:laptop",
    "shopee:may-tinh-bang"
  ],
  "timestamp": "2024-01-28T10:30:00"
}
```

### 7.4. Khôi phục (Resume)

```python
def get_resume_page(self, platform: str, category: str) -> int:
    """Get the page to resume from for a category."""
    if (self.checkpoint.get("platform") == platform and 
        self.checkpoint.get("current_category") == category):
        return self.checkpoint.get("last_page", 0)
    return 0  # Bắt đầu từ đầu nếu không match
```

**Logic hoạt động:**

1. Khi khởi động crawler, load checkpoint từ file
2. Kiểm tra category hiện tại khớp với checkpoint không
3. Nếu khớp → Resume từ `last_page`
4. Nếu không → Bắt đầu từ page 0

### 7.5. Theo dõi ID đã crawl (Duplicate Prevention)

```python
def is_crawled(self, product_id: str) -> bool:
    """Check if a product ID was already crawled."""
    return product_id in self.crawled_ids

def mark_crawled(self, product_id: str) -> None:
    """Mark a product ID as crawled."""
    if product_id not in self.crawled_ids:
        self.crawled_ids.add(product_id)
        # Append to file (atomic operation)
        with open(self.crawled_ids_file, 'a', encoding='utf-8') as f:
            f.write(product_id + '\n')
```

**Tại sao dùng Set + File?**

| Approach | Ưu điểm | Nhược điểm |
|----------|---------|------------|
| **Set (in-memory)** | Tra cứu O(1) | Mất khi restart |
| **File (disk)** | Bền vững | Tra cứu chậm |
| **Set + File** | Tra cứu nhanh + Bền vững | Tốn RAM cho set |

→ Dùng cả hai: Set để tra cứu nhanh, File để backup.

---

## 8. Câu hỏi thường gặp (FAQ - Potential Interview Questions)

### Q1: Tại sao chọn JSONL thay vì JSON hoặc CSV?

**Trả lời:**

| Format | Ưu điểm | Nhược điểm |
|--------|---------|------------|
| **JSON** | Đọc toàn bộ dễ dàng | Phải load hết vào RAM, không append được |
| **CSV** | Nhẹ, dễ đọc | Không hỗ trợ nested data, encoding issues |
| **JSONL** | Append được, memory efficient, hỗ trợ nested | Mỗi dòng phải parse riêng |

**JSONL phù hợp vì:**

- Crawler chạy liên tục, cần **append** dữ liệu
- Mỗi dòng độc lập → đọc từng dòng mà không cần load hết file
- Hỗ trợ **streaming processing** cho file lớn (1M+ dòng)

---

### Q2: Tại sao cần tách từ tiếng Việt (Word Segmentation)?

**Trả lời:**

Tiếng Việt là **ngôn ngữ đơn lập** (isolating language) - các từ không có dấu cách rõ ràng giữa các thành phần.

**Ví dụ vấn đề:**

```
Query: "máy tính"
Văn bản: "Máy giặt tính năng mới"
```

Nếu không tách từ:

- "máy" có trong văn bản ✓
- "tính" có trong văn bản ✓
- → Khớp sai!

Nếu có tách từ:

- "máy_tính" không có trong văn bản ✗
- → Không khớp (đúng!)

---

### Q3: Sync vs Async Crawler - Khi nào dùng cái nào?

**Trả lời:**

| Tiêu chí | Sync (requests) | Async (aiohttp) |
|----------|-----------------|-----------------|
| **Tốc độ** | 1 request/lần | Hàng trăm request đồng thời |
| **Phức tạp** | Đơn giản | Cần hiểu async/await |
| **Phù hợp** | API chậm, cần browser | API nhanh, nhiều endpoint |

**Trong project:**

- **Shopee:** Dùng Sync + Browser (anti-bot mạnh)
- **Chợ Tốt/eBay:** Dùng Async (API dễ, cần tốc độ)

---

### Q4: Làm sao xử lý khi bị block IP?

**Trả lời:**

1. **Rate Limiting:** Giảm tốc độ request
2. **Rotate User-Agent:** Thay đổi fingerprint
3. **Proxy Rotation:** Đổi IP (nếu có)
4. **Browser Automation:** Dùng trình duyệt thật (DrissionPage)
5. **Checkpoint:** Lưu progress để resume sau

**Trong project đã làm:**

- ✅ Rate Limiting (sleep random)
- ✅ User-Agent Rotation
- ✅ Browser Automation (Shopee)
- ✅ Checkpoint System
- ⬜ Proxy Rotation (chưa implement)

---

### Q5: Tại sao dùng DrissionPage thay vì Selenium?

**Trả lời:**

| Tiêu chí | Selenium | DrissionPage |
|----------|----------|--------------|
| **Setup** | Cần WebDriver riêng | Dùng Chrome có sẵn |
| **Anti-detection** | Dễ bị phát hiện | Fingerprint giống người thật |
| **Performance** | Chậm hơn | Nhanh hơn |
| **API** | Cũ, verbose | Modern, Pythonic |

DrissionPage wrapper Chrome DevTools Protocol (CDP) → ít bị phát hiện là bot hơn.

---

### Q6: Explain the difference between crawled_ids (Set) vs deduplicate.py

**Trả lời:**

| Component | Thời điểm | Mục đích |
|-----------|-----------|----------|
| `crawled_ids` (Set) | **Runtime** - Khi đang crawl | Tránh crawl cùng 1 product 2 lần trong session |
| `deduplicate.py` | **Post-processing** - Sau khi crawl | Xóa duplicate từ nhiều session khác nhau |

**Ví dụ:**

- Session 1: Crawl product A, B, C → `crawled_ids = {A, B, C}`
- Session 2: Crawl product B, D, E → `crawled_ids = {B, D, E}` (B trùng với session 1)
- Chạy `deduplicate.py` → Loại bỏ B trùng, giữ version mới nhất

---

### Q7: Tại sao ID sản phẩm cần prefix platform?

**Trả lời:**

**Vấn đề:** Các sàn dùng ID nội bộ khác nhau, có thể trùng.

- Shopee product ID: `12345`
- Tiki product ID: `12345` (trùng!)

**Giải pháp:** Thêm prefix platform:

- `shopee_12345`
- `tiki_12345`

→ ID unique trong toàn bộ hệ thống, không bị conflict khi merge data.

---

### Q8: Memory Management - Làm sao crawl 1M products không hết RAM?

**Trả lời:**

1. **JSONL Format:** Ghi từng dòng, không giữ trong RAM
2. **Streaming Write:** Append mode, không load toàn bộ file
3. **Set cho crawled_ids:** Chỉ lưu ID (string ngắn), không lưu toàn bộ product
4. **Garbage Collection:** Python tự động giải phóng objects không dùng

**Công thức ước tính RAM:**

```
1M IDs × ~30 bytes/ID = ~30MB cho Set
(Chấp nhận được)
```

---

### Q9: Error Handling Strategy

**Trả lời:**

```python
try:
    response = session.get(url, timeout=20)
    if response.status_code != 200:
        print(f"⚠️ HTTP {response.status_code}")
        break  # Stop category, move to next
except Exception as e:
    print(f"❌ Error: {e}")
    time.sleep(3)  # Cool down
    # Continue to next page
```

**Strategy:**

1. **Timeout:** Giới hạn 20s mỗi request
2. **HTTP Error:** Log và skip
3. **Exception:** Log, sleep, retry hoặc skip
4. **Checkpoint:** Lưu progress để resume

---

## Kết luận

Tài liệu này đã giải thích chi tiết các kỹ thuật được sử dụng trong hệ thống Crawler:

1. **Anti-Bot:** User-Agent rotation, Rate limiting, Browser automation, CAPTCHA handling
2. **Data Schema:** Unified ProductItem với field constants
3. **Text Cleaning:** HTML removal, Vietnamese word segmentation
4. **Price Normalization:** Regex-based parsing cho nhiều format tiền tệ
5. **De-duplication:** Dict-based với timestamp comparison
6. **Checkpoint System:** Resume crawling, duplicate prevention
7. **FAQ:** Các câu hỏi kỹ thuật thường gặp

Mỗi kỹ thuật đều được thiết kế để giải quyết một vấn đề cụ thể trong quá trình thu thập và xử lý dữ liệu từ các sàn TMĐT.

---

*Tài liệu kỹ thuật - SEG301 E-Commerce Search Engine*
