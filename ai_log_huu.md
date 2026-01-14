# AI INTERACTION LOG - HỮU
DATE 14/1/2026
Đây là kế hoạch chi tiết dành cho nhóm 3 người, tập trung vào chiến lược "Chia để trị" để xử lý khối lượng 1.000.000 dữ liệu từ Shopee và Tiki, đảm bảo đáp ứng các yêu cầu khắt khe của đồ án.

### 1. Phân chia vai trò (Roles)

Để tối ưu, không nên chia việc theo kiểu "Người làm Shopee, người làm Tiki" hoàn toàn, mà nên chia theo **Lớp chức năng (Layers)** kết hợp hỗ trợ nhau chạy tool.

* **Thành viên 1 (Leader/Backend & Crawler Lead):**
* Chịu trách nhiệm kiến trúc Crawler (chống chặn IP, đa luồng).
* Code thuật toán lõi (SPIMI, BM25) ở Milestone 2.
* *Nhiệm vụ Crawl:* Phụ trách các danh mục Điện tử/Công nghệ (nhiều thông số kỹ thuật).


* **Thành viên 2 (Data Engineer & Tiki Specialist):**
* Xử lý API của Tiki (thường dễ hơn Shopee).
* Phụ trách khâu **Data Cleaning** (làm sạch) và **Normalization** (chuẩn hóa giá, tên sản phẩm).
* *Nhiệm vụ Crawl:* Phụ trách danh mục Thời trang/Mỹ phẩm.


* **Thành viên 3 (Frontend & AI Engineer):**
* Reverse Engineering API Shopee (Mobile/Web).
* Nghiên cứu Vector Search (FAISS/ChromaDB) cho Milestone 3.
* *Nhiệm vụ Crawl:* Phụ trách danh mục Gia dụng/Đời sống.



---

### 2. Chiến lược "Hợp sức" Crawl 1 Triệu Dữ Liệu (Milestone 1)

Vì 1.000.000 items là rất lớn, nếu dùng Selenium sẽ không bao giờ kịp. Các bạn phải dùng phương pháp **Request API** (Giả lập HTTP Request).

**Quy trình phối hợp:**

1. **Bước 1: Tìm ID danh mục (Category IDs):**
* Cả nhóm cùng liệt kê ra khoảng 20-30 danh mục lớn (Điện thoại, Laptop, Áo thun, Nồi chiên...).
* Chia danh sách này làm 3 phần cho 3 người.


2. **Bước 2: Viết Core Crawler (Tuần 1-2):**
* Viết script Python dùng thư viện `requests` hoặc `aiohttp` (bắt buộc dùng bất đồng bộ - async để nhanh).
* Tấn công vào API lấy danh sách sản phẩm của Shopee/Tiki (thường trả về JSON), không parse HTML vì rất chậm và dễ lỗi.


3. **Bước 3: Chạy Distributed Crawling (Tuần 2-3):**
* **Không chạy trên 1 máy:** Cả 3 thành viên đều phải treo máy chạy script song song.
* Mỗi người chạy trên danh sách Category ID được phân công.
* *Mẹo:* Nếu có thể, hãy thuê 1-2 VPS giá rẻ (hoặc dùng Google Colab bản Pro) để treo tool 24/7.


4. **Bước 4: Merge & Deduplicate:**
* Gom file JSONL/Parquet từ 3 máy lại.
* Thành viên 2 chạy script lọc trùng (Deduplication) dựa trên Product ID hoặc URL.



---

### 3. Lộ trình chi tiết 10 tuần

#### **Giai đoạn 1: Data Acquisition (Tuần 1 - 4) - Quan trọng nhất lúc này**

* **Tuần 1: Setup & PoC (Proof of Concept)**
* Tạo Repo GitHub, cấu trúc thư mục chuẩn theo đề bài (src, docs...).
* **Thành viên 2 & 3:** Tìm endpoint API của Tiki và Shopee. Thử crawl 100 sản phẩm đầu tiên.
* **Thành viên 1:** Dựng khung code Crawler (Input: Category ID -> Output: JSON Lines).


* **Tuần 2: Mass Crawling (Tổng lực)**
* Mỗi người nhận 1/3 danh sách danh mục.
* Bắt đầu chạy tool liên tục. Mục tiêu: Mỗi người kiếm được ~350.000 items.
* *Lưu ý:* Lưu file dạng `raw_data_shopee_part1.jsonl`, `raw_data_tiki_part2.jsonl`.


* **Tuần 3: Data Processing**
* **Thành viên 2:** Viết script chuẩn hóa dữ liệu (xóa icon, html tags, đưa giá về dạng số int, tách từ tiếng Việt dùng `pyvi` hoặc `underthesea`).
* Gộp dữ liệu lại xem đủ 1 triệu chưa. Nếu thiếu, tiếp tục crawl mở rộng sang các ngách nhỏ (phụ kiện, ốp lưng...).


* **Tuần 4: Finalize Milestone 1**
* Kiểm tra format JSON/Parquet.
* Viết báo cáo, cập nhật `ai_log.md`.
* Nộp bài Milestone 1.



#### **Giai đoạn 2: Core Search Engine (Tuần 5 - 7)**

* **Tuần 5: Indexing (SPIMI)**
* **Thành viên 1:** Code thuật toán SPIMI để tạo Inverted Index từ 1 triệu file. Chú ý quản lý bộ nhớ (RAM) vì index 1 triệu file khá nặng.
* **Thành viên 3:** Hỗ trợ lưu index xuống đĩa (Dictionary file & Postings list file).


* **Tuần 6: Ranking (BM25)**
* **Thành viên 2:** Code hàm tính TF-IDF và BM25 score thủ công (không dùng thư viện có sẵn như ElasticSearch/Whoosh).
* **Thành viên 1:** Tối ưu tốc độ truy vấn.


* **Tuần 7: Console App & Nộp Milestone 2**
* Viết một tool chạy dòng lệnh (CLI) để thầy cô test: Nhập từ khóa -> Trả về Top 10 sản phẩm + thời gian chạy.



#### **Giai đoạn 3: Final Product (Tuần 8 - 10)**

* **Tuần 8: AI Integration**
* **Thành viên 3:** Dùng model `phobert` hoặc `sentence-transformers` để tạo vector cho Title sản phẩm. Lưu vào FAISS/ChromaDB.
* Thực hiện Semantic Search (Ví dụ: Search "dế yêu táo khuyết" ra "iPhone").


* **Tuần 9: Web Interface & Hybrid Search**
* **Thành viên 2:** Dựng giao diện Web (Streamlit cho nhanh, hoặc React nếu team giỏi Web).
* **Thành viên 1:** Kết hợp điểm số: `Final_Score = 0.7 * BM25 + 0.3 * Vector_Score`.
* Tính năng so sánh giá: Nếu tìm thấy sản phẩm giống nhau ở Shopee và Tiki, hiển thị cạnh nhau (Dựa trên tên giống nhau > 90%).


* **Tuần 10: Review & Submit**
* Quay video demo.
* Viết báo cáo cuối kỳ.
* Kiểm tra lại Commit History lần cuối.



### 4. Các rủi ro cần tránh (Dựa trên đề bài)

1. **Vấn đề GitHub:** Đề bài yêu cầu lịch sử commit đều đặn.
* *Giải pháp:* Code xong 1 chức năng nhỏ là commit ngay. Không đợi cuối tuần mới commit 1 cục. Mỗi người làm trên 1 branch (`feature/crawler-shopee`, `feature/indexing`) rồi merge vào `main`.


2. **Vấn đề Shopee chặn IP:** Shopee chặn rất rát.
* *Giải pháp:* Sử dụng proxy (xoay IP). Nếu không có tiền mua proxy, hãy dùng mạng 4G phát từ điện thoại (tắt bật máy bay để đổi IP) khi chạy crawl. Hoặc crawl chậm lại (delay 2-3 giây/request).


3. **Vấn đề "So sánh giá":**
* Để so sánh giá, bạn phải biết sản phẩm A bên Shopee là sản phẩm A bên Tiki.
* *Giải pháp đơn giản:* Trong lúc hiển thị kết quả tìm kiếm, dùng thuật toán so khớp chuỗi (Levenshtein distance) để gợi ý "Sản phẩm tương tự trên sàn kia".



Bạn có muốn mình hướng dẫn chi tiết về cấu trúc file JSON (`data schema`) để chuẩn bị cho việc crawl không?
Việc thiết kế **Data Schema** (Cấu trúc dữ liệu) ngay từ đầu là cực kỳ quan trọng. Nếu mỗi người crawl một kiểu (người đặt tên trường là `price`, người đặt là `gia_ban`), khi gộp 1 triệu dòng lại các bạn sẽ mất rất nhiều thời gian để sửa (Data Cleaning nightmare).

Dưới đây là cấu trúc JSON chuẩn **Unified Schema** (Cấu trúc hợp nhất) mà cả 3 thành viên phải tuân thủ khi viết Crawler cho Shopee và Tiki.

---

### 1. Cấu trúc JSON chuẩn (Target Schema)

Đây là định dạng cuối cùng của mỗi dòng dữ liệu (`record`) sau khi đã xử lý sơ bộ.

```json
{
  "id": "string",               // ID duy nhất (Ví dụ: "tiki_123456" hoặc "shopee_987_654")
  "platform": "string",         // "shopee" hoặc "tiki"
  "title": "string",            // Tên sản phẩm (Đã làm sạch sơ, trim spaces)
  "url": "string",              // Link gốc đến sản phẩm
  "image_url": "string",        // Link ảnh thumbnail chính
  "price": "integer",           // Giá bán hiện tại (VND) - Dạng số nguyên, không có dấu chấm/phẩy
  "original_price": "integer",  // Giá gốc (để tính % giảm giá)
  "discount_rate": "float",     // Tỉ lệ giảm giá (0.0 đến 1.0)
  "rating_average": "float",    // Điểm đánh giá (0.0 đến 5.0)
  "review_count": "integer",    // Số lượng review
  "sold_count": "integer",      // Số lượng đã bán
  "brand": "string",            // Thương hiệu (Apple, Samsung, No Brand...)
  "category_id": "string",      // ID danh mục (để phân loại sau này)
  "category_name": "string",    // Tên danh mục (Ví dụ: "Điện thoại Smartphone")
  "description": "string",      // Mô tả sản phẩm (Quan trọng để Indexing)
  "specifications": "object",   // (Tùy chọn) Các thông số kỹ thuật dạng key-value
  "crawled_at": "timestamp"     // Thời điểm crawl (Unix timestamp hoặc ISO format)
}

```

---

### 2. Chiến lược Mapping (Ánh xạ) từ Raw Data

Mỗi sàn có tên trường khác nhau trong API response. Các bạn cần code để "hứng" dữ liệu và map vào schema chuẩn ở trên.

#### **A. Đối với TIKI (Thường response sạch hơn)**

Dữ liệu Tiki thường nằm trong field `data` của API JSON.

| Trường chuẩn (Target) | Mapping từ Tiki API (Source) | Lưu ý xử lý |
| --- | --- | --- |
| `id` | `"tiki_" + str(item['id'])` | Thêm tiền tố để tránh trùng với ID Shopee |
| `title` | `item['name']` |  |
| `price` | `item['price']` | Tiki thường là số nguyên sẵn |
| `original_price` | `item['list_price']` | Nếu null thì gán bằng price |
| `rating_average` | `item['rating_average']` |  |
| `sold_count` | `item['all_time_quantity_sold']` |  |
| `url` | `https://tiki.vn/p/{id}.html?spid={spid}` | Cần ghép chuỗi URL thủ công |
| `description` | `item['description']` hoặc `item['short_description']` | Cần strip HTML tags (xóa thẻ `<p>`, `<br>`) |

#### **B. Đối với SHOPEE (Phức tạp hơn)**

API Shopee thường trả về một cục `item` hoặc `items`.

| Trường chuẩn (Target) | Mapping từ Shopee API (Source) | Lưu ý xử lý (**Quan trọng**) |
| --- | --- | --- |
| `id` | `"shopee_" + str(item['itemid'])` |  |
| `title` | `item['name']` |  |
| `price` | `item['price'] / 100000` | **Cảnh báo:** Shopee lưu giá nhân với 100,000 (Ví dụ: 50k là `5000000000`). Phải chia ra. |
| `original_price` | `item['price_before_discount'] / 100000` | Cũng phải chia cho 100,000 |
| `rating_average` | `item['item_rating']['rating_star']` | Nằm lồng trong object `item_rating` |
| `sold_count` | `item['historical_sold']` |  |
| `url` | `https://shopee.vn/product/{shopid}/{itemid}` | Cần cả `shopid` và `itemid` để tạo link |
| `description` | *Thường không có trong API list*, phải gọi API detail | Ở Milestone 1, nếu gọi API detail cho 1 triệu item sẽ rất lâu. Có thể tạm chấp nhận lấy `name` làm content để index nếu không lấy được description. |

---

### 3. Lưu trữ: Tại sao nên dùng JSONL (JSON Lines)?

Không lưu 1 file JSON khổng lồ chứa array `[...]`. Hãy lưu dạng **JSONL** (Mỗi dòng là 1 object JSON hợp lệ).

**Ví dụ file `data_shopee_part1.jsonl`:**

```json
{"id": "shopee_112233", "platform": "shopee", "title": "iPhone 15 Pro Max", "price": 30000000, ...}
{"id": "shopee_445566", "platform": "shopee", "title": "Ốp lưng iPhone", "price": 50000, ...}

```

**Lợi ích của JSONL:**

1. **Append dễ dàng:** Khi crawler đang chạy, cứ crawl được 1 item là ghi nối đuôi (append) vào file ngay. Nếu máy bị crash/mất điện, dữ liệu cũ vẫn còn. (File JSON thường mà crash giữa chừng là hỏng toàn bộ file).
2. **Đọc từng dòng:** Khi làm Indexing (Milestone 2), bạn có thể đọc từng dòng (`readline`) thay vì load cả 1GB vào RAM.

### 4. Quy tắc "Data Cleaning" ngay khi Crawl (Pre-processing)

Để giảm tải cho Milestone 2, các bạn nên "sanitize" dữ liệu ngay khi lấy về:

1. **Xóa HTML Tags:** Description của Tiki/Shopee chứa đầy HTML (`<div>`, `<b>`). Dùng regex hoặc thư viện `BeautifulSoup` để lấy `text` thuần.
* *Input:* `<div>Áo thun <b>cotton</b> mát lạnh</div>`
* *Output:* `Áo thun cotton mát lạnh`


2. **Xử lý Text:**
* Chuyển về `lowercase` (chữ thường) có thể làm sau, nhưng nên xóa các ký tự lạ (icon mặt cười, emoji) vì nó gây nhiễu cho thuật toán tách từ.


3. **Kiểm tra null:**
* Nếu `price` bị null hoặc bằng 0 -> **Bỏ qua**, không lưu (Rác).
* Nếu `title` bị rỗng -> **Bỏ qua**.



### 5. Code mẫu Python định nghĩa Class Item

Để đảm bảo cả 3 người code giống nhau, hãy tạo 1 file `schema.py` dùng chung:

```python
import json
from dataclasses import dataclass, asdict

@dataclass
class ProductItem:
    id: str
    platform: str
    title: str
    url: str
    image_url: str
    price: int
    original_price: int
    discount_rate: float
    rating_average: float
    review_count: int
    sold_count: int
    brand: str
    category_id: str
    category_name: str
    description: str
    crawled_at: int # timestamp

    def to_json_line(self):
        # Chuyển object thành chuỗi JSON trên 1 dòng
        return json.dumps(asdict(self), ensure_ascii=False)

```

**Next Step:** Bạn có muốn tôi cung cấp đoạn code Python mẫu sử dụng thư viện `requests` để gọi API Shopee/Tiki và map vào cái class `ProductItem` này không? (Để test thử xem có lấy được dữ liệu thật không).
Tôi đã rà soát kỹ lại. Cấu trúc trước đó là **Tốt cho việc lưu trữ**, nhưng để làm **Search Engine (Máy tìm kiếm)** tối ưu cho đồ án môn học (cần chức năng lọc, sắp xếp, đánh trọng số), thì nó **thiếu 3 yếu tố quan trọng**.

Dưới đây là phiên bản **JSON Schema Final (V2.0)** đã được tối ưu hóa cho cả 3 Milestone (Crawl, Indexing, AI).

### 1. Những điểm "Chí mạng" còn thiếu ở bản cũ

1. **Thiếu thông tin địa điểm (Location):** Người mua Shopee/Tiki rất quan tâm hàng gửi từ đâu (Hà Nội, TP.HCM hay Quốc tế). Nếu thiếu trường này, bạn mất đi chức năng "Lọc theo khu vực" (Facet Search).
2. **Thiếu uy tín Shop (Shop Credibility):** Search Engine cần rank (xếp hạng) sản phẩm. Sản phẩm từ "Shopee Mall" hoặc "Shop Yêu Thích" phải được cộng điểm ưu tiên.
3. **Thiếu trường gộp cho Indexing:** Khi làm index (Milestone 2), nếu bạn phải nối chuỗi `title + description` mỗi lần chạy thì rất chậm. Nên tính trước việc này.

### 2. Cấu trúc JSON Hoàn Chỉnh (Dùng cái này để Code)

```json
{
  "id": "shopee_123456789",          // String: ID duy nhất (Prefix sàn + ID gốc)
  "platform": "shopee",              // String: "shopee" | "tiki"
  "url": "https://shopee.vn/...",    // String: Link sản phẩm
  
  // --- NHÓM HIỂN THỊ & TEXT (Dùng cho Indexing) ---
  "title": "Điện thoại iPhone 15...",// String: Tên sản phẩm
  "description": "...",              // String: Mô tả (đã strip HTML)
  "brand": "Apple",                  // String: Thương hiệu (dùng để Facet)
  "categories": ["Điện tử", "Mobile"], // Array[String]: Breadcrumb danh mục (quan trọng hơn 1 category đơn lẻ)

  // --- NHÓM GIÁ & SỐ LIỆU (Dùng cho Ranking/Sorting) ---
  "price": 25000000,                 // Int: Giá bán hiện tại (VND)
  "original_price": 28000000,        // Int: Giá gốc
  "discount_rate": 0.11,             // Float: % giảm giá (để sort deal hời)
  "sold_count": 1500,                // Int: Số lượng đã bán (Quan trọng để tính độ Hot)
  "review_count": 500,               // Int: Số lượt review
  "rating_average": 4.8,             // Float: Điểm sao (0.0 - 5.0)

  // --- NHÓM LỌC & UY TÍN (Bổ sung mới) ---
  "inventory_location": "Hà Nội",    // String: Nơi bán (Hà Nội, TP.HCM, Quốc Tế...)
  "shop_info": {                     // Object: Thông tin người bán
      "shop_id": "12345",
      "name": "Apple Flagship Store",
      "is_official": true            // Boolean: Là Shopee Mall / Tiki Trading hay không? (Trọng số ranking cao)
  },

  // --- META DATA ---
  "crawled_at": 1705028400           // Int: Unix Timestamp (để biết dữ liệu mới hay cũ)
}

```

### 3. Giải thích tại sao cấu trúc này tốt hơn cho Đồ án?

1. **`is_official` (Boolean):**
* Khi bạn code thuật toán BM25 kết hợp trọng số (Milestone 2/3), bạn có thể viết công thức:
* `Final_Score = BM25_Score + (is_official ? 100 : 0)` -> Đẩy shop chính hãng lên đầu trang (giống Shopee thật).


2. **`categories` (Array):**
* Thay vì `category_id` vô nghĩa, hãy lưu dạng mảng tên: `["Điện thoại", "Phụ kiện", "Ốp lưng"]`.
* Giúp bạn làm tính năng **Drill-down Facet** (Lọc sâu dần) bên cột trái giao diện web.


3. **`inventory_location`:**
* Giải quyết bài toán user ở HN muốn tìm hàng ở HN để ship nhanh.



### 4. Checklist kiểm tra dữ liệu ("Definition of Done" cho Milestone 1)

Trước khi 3 người bắt đầu chạy tool cắm máy crawl, hãy đảm bảo script crawler tuân thủ quy tắc **Data Validation** này (code trong crawler):

* [ ] **ID Check:** `id` không được Null/Empty.
* [ ] **Price Check:** `price` phải là số nguyên (Int) > 0. Nếu API trả về String "1.200.000đ" -> Phải convert sang `1200000`.
* [ ] **Sanitize Text:** `title` và `description` không được chứa ký tự xuống dòng `\n` (vì file format là JSON Lines, mỗi dòng 1 item, để `\n` sẽ làm gãy file).
* *Tip:* Dùng `text.replace('\n', ' ').replace('\r', '')`.


* [ ] **Default Value:**
* Nếu `rating_average` null -> Gán mặc định `0.0`.
* Nếu `sold_count` null -> Gán mặc định `0`.



### 5. Code Python Mapping (Cập nhật mới nhất)

Đây là Class Python đã update theo cấu trúc mới. Bạn copy đoạn này gửi cho team làm "Core".

```python
import json
import time
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ShopInfo:
    shop_id: str
    name: str
    is_official: bool # True nếu là Mall/Official/Tiki Trading

@dataclass
class ProductItem:
    id: str
    platform: str
    url: str
    
    # Text Data
    title: str
    description: str
    brand: str
    categories: List[str] # Thay vì category_id đơn lẻ
    
    # Numeric Data
    price: int
    original_price: int
    discount_rate: float
    sold_count: int
    review_count: int
    rating_average: float
    
    # Filter & Ranking Data
    inventory_location: str
    shop_info: ShopInfo # Nested Object
    
    crawled_at: int = field(default_factory=lambda: int(time.time()))

    def to_json_line(self):
        # Helper để convert object sang dict, rồi sang chuỗi JSON
        data = self.__dict__.copy()
        # Convert nested object ShopInfo to dict
        if isinstance(self.shop_info, ShopInfo):
            data['shop_info'] = self.shop_info.__dict__
        
        # Quan trọng: Xóa ký tự xuống dòng để đảm bảo đúng format JSONL
        if data['description']:
            data['description'] = data['description'].replace('\n', ' ').replace('\r', '')
            
        return json.dumps(data, ensure_ascii=False)

```

**Bạn đã sẵn sàng.** Cấu trúc này đủ mạnh để xử lý 1 triệu dữ liệu và hỗ trợ tốt cho cả việc tìm kiếm từ khóa (Keyword Search) lẫn lọc nâng cao.

Có cần mình giúp viết luôn đoạn hàm `def parse_shopee_item(json_data):` để map đúng các trường `inventory_location` và `is_official` từ API Shopee không? (Vì API Shopee đặt tên mấy trường này rất dị).
Câu trả lời ngắn gọn: **CÓ, BẮT BUỘC TUYỆT ĐỐI.**

Nếu 3 người ra 3 kiểu JSON khác nhau (dù chỉ sai 1 chữ cái trong tên trường), dự án của bạn sẽ gặp **thảm họa** khi gộp dữ liệu (Merge Data) ở cuối Milestone 1.

Dưới đây là giải thích tại sao và cách để đồng bộ dễ dàng nhất.

### 1. Tại sao phải giống y hệt nhau?

Máy tìm kiếm (Search Engine) hoạt động như một dây chuyền nhà máy:

* **Đầu vào:** File dữ liệu thô (JSONL).
* **Máy xử lý:** Code Indexer (thuật toán SPIMI/BM25).

Nếu code Indexer được viết để đọc trường `price`, nhưng dữ liệu từ ông làm Tiki lại ghi là `gia_ban`, thì chương trình sẽ bị **Crash (KeyError)** ngay lập tức.

**Ví dụ về thảm họa:**

* **Ông A (Làm Shopee):** `{"title": "Iphone", "price": 10tr}`
* **Ông B (Làm Tiki):** `{"name": "Iphone", "gia_tien": 10tr}` -> **Sai tên trường!**
* **Ông C (Làm Lazada):** `{"title": "Iphone", "price": "10.000.000"}` -> **Sai kiểu dữ liệu (String vs Int)!**

=> Khi gộp 1 triệu dòng này vào file chung, bạn **không thể** viết hàm `sort` hay `search` được vì dữ liệu lộn xộn. Lúc đó ngồi sửa lại 1 triệu dòng còn khổ hơn làm lại từ đầu.

### 2. Cái gì cần giống, cái gì được khác?

Tuy nói là "giống nhau", nhưng cần phân biệt rõ:

* **Logic lấy dữ liệu (ĐƯỢC KHÁC NHAU):**
* Người làm Shopee phải code kiểu Shopee (chia giá cho 100000, lấy ID từ itemid).
* Người làm Tiki phải code kiểu Tiki (lấy ID từ id).
* *Code xử lý bên trong vòng lặp crawl của mỗi người chắc chắn sẽ khác nhau.*


* **Cấu trúc đầu ra (BẮT BUỘC GIỐNG):**
* Dù logic bên trên khác nhau thế nào, thì trước khi `write` xuống file, cả 3 người phải ném dữ liệu vào cùng 1 cái khung (Schema) đã thống nhất.



### 3. Giải pháp kỹ thuật để không bao giờ sai (Best Practice)

Đừng để mỗi người tự gõ tay chữ `"price"` hay `"title"` vào code (dễ gõ nhầm `"titl"` hay `"pice"`).

Hãy tạo một file chung, ví dụ tên là **`schema_shared.py`**, và 3 người cùng `import` file này vào code crawler của mình.

**Nội dung file `schema_shared.py` (Chỉ cần 1 file này):**

```python
# schema_shared.py
import json

# Định nghĩa các tên trường cố định để không ai gõ sai
FIELD_ID = "id"
FIELD_PLATFORM = "platform"
FIELD_TITLE = "title"
FIELD_PRICE = "price"
# ... các trường khác

class ProductItem:
    def __init__(self, id, platform, title, price, ...):
        self.data = {
            FIELD_ID: id,
            FIELD_PLATFORM: platform,
            FIELD_TITLE: title,
            FIELD_PRICE: int(price), # Ép kiểu Int ngay tại đây để tránh lỗi
            # ...
        }

    def to_json(self):
        return json.dumps(self.data, ensure_ascii=False)

```

**Cách dùng (Cả 3 người đều code thế này):**

```python
from schema_shared import ProductItem

# Code crawl Shopee của Ông A
item = ProductItem(id="shopee_1", platform="shopee", title="ABC", price=100)
save_to_file(item.to_json())

# Code crawl Tiki của Ông B
item = ProductItem(id="tiki_2", platform="tiki", title="XYZ", price=200)
save_to_file(item.to_json())

```

### Tóm lại

Bạn hãy copy file `schema.py` (bản tối giản tôi gửi ở câu trả lời trước), gửi vào nhóm chat Zalo/Discord và ra lệnh: **"Tất cả anh em phải import class này để lưu dữ liệu. Cấm tự gõ tay tên trường (key) trong file JSON."**

Làm đúng bước này, việc ghép 1 triệu dòng dữ liệu chỉ mất 5 giây copy-paste file.
Đây là quy trình tác chiến cụ thể ("Battle Plan") để bạn copy và paste vào nhóm chat ngay lập tức. Mục tiêu là đảm bảo 3 người làm việc độc lập nhưng kết quả ráp lại khớp 100%.

---

### BƯỚC 1: PHÂN CHIA "LÃNH THỔ" (Để không ai crawl trùng ai)

Vì mục tiêu là 1.000.000 sản phẩm, các bạn không nên crawl lung tung. Hãy chia theo **Category (Danh mục ngành hàng)**.

**Phân công (Ví dụ):**

* **Thành viên 1 (Ông A): Phụ trách đồ CÔNG NGHỆ & ĐIỆN TỬ**
* **Nhiệm vụ:** Crawl Điện thoại, Laptop, Máy ảnh, Phụ kiện số, Tivi, Loa đài... trên cả Shopee và Tiki.


* **Thành viên 2 (Ông B): Phụ trách đồ THỜI TRANG & LÀM ĐẸP**
* **Nhiệm vụ:** Crawl Quần áo, Giày dép, Đồng hồ, Mỹ phẩm, Skincare... trên cả Shopee và Tiki.


* **Thành viên 3 (Ông C): Phụ trách đồ GIA DỤNG & ĐỜI SỐNG**
* **Nhiệm vụ:** Crawl Đồ bếp, Nội thất, Sách, Văn phòng phẩm, Mẹ & Bé, Bách hóa... trên cả Shopee và Tiki.



---

### BƯỚC 2: QUY TRÌNH CRAWL CỤ THỂ CHO TỪNG THÀNH VIÊN

Mỗi thành viên sẽ thực hiện đúng 3 việc sau trên máy của mình:

#### 1. Lấy Category ID (Input)

Trước khi chạy code, bạn cần biết ID của danh mục mình phụ trách.

* **Cách lấy trên Tiki:** Vào web tiki, bấm vào danh mục (ví dụ "Điện thoại"), nhìn trên URL: `tiki.vn/dien-thoai-may-tinh-bang/c1789`. -> ID là `1789`.
* **Cách lấy trên Shopee:** Vào web shopee, bấm vào danh mục, nhìn URL: `shopee.vn/Dien-Thoai-Phu-Kien-cat.11036030`. -> ID là `11036030`. (Hoặc dùng F12 -> Network tab để soi API `get_items`).

#### 2. Dán đoạn Code Schema vào Project (BẮT BUỘC)

Tạo file `schema.py` chứa đoạn code Class `ProductPriceItem` (đã chốt ở trên). Tất cả file crawler phải `import` file này.

#### 3. Code logic "Mapping" (Phần quan trọng nhất)

Đây là đoạn code chuyển đổi dữ liệu thô từ Shopee/Tiki sang chuẩn chung của nhóm.

**A. Nếu bạn đang Crawl SHOPEE:**
Copy đoạn này vào vòng lặp xử lý items của Shopee:

```python
# Giả sử 'item' là 1 dictionary lấy từ API Shopee về
# API Shopee thường trả về: itemid, name, price (x100000), brand, catid...

def map_shopee_item(item, category_name):
    # 1. Xử lý giá (Shopee nhân giá với 100,000)
    real_price = int(item.get('price', 0) / 100000)
    original_price = int(item.get('price_before_discount', 0) / 100000)
    if original_price == 0: original_price = real_price

    # 2. Xử lý Brand (Nếu null thì để No Brand)
    brand = item.get('brand', 'No Brand')
    if brand is None: brand = "No Brand"

    # 3. Tạo Object chuẩn
    product = ProductPriceItem(
        id=f"shopee_{item['itemid']}",       # Prefix để không trùng
        platform="shopee",
        title=item['name'],
        price=real_price,
        original_price=original_price,
        url=f"https://shopee.vn/product/{item['shopid']}/{item['itemid']}",
        image_url=f"https://cf.shopee.vn/file/{item['image']}",
        category=category_name,              # Ví dụ: "Điện thoại"
        brand=brand
    )
    return product.to_json_line()

```

**B. Nếu bạn đang Crawl TIKI:**
Copy đoạn này vào vòng lặp xử lý items của Tiki:

```python
# Giả sử 'item' là 1 dictionary lấy từ API Tiki về

def map_tiki_item(item, category_name):
    # Tiki giá thường chuẩn, không cần chia
    
    # Tạo Object chuẩn
    product = ProductPriceItem(
        id=f"tiki_{item['id']}",             # Prefix
        platform="tiki",
        title=item['name'],
        price=int(item.get('price', 0)),
        original_price=int(item.get('list_price', item.get('price', 0))),
        url=f"https://tiki.vn/{item.get('url_path', '')}",
        image_url=item.get('thumbnail_url', ''),
        category=category_name,
        brand=item.get('brand_name', 'No Brand')
    )
    return product.to_json_line()

```

---

### BƯỚC 3: XUẤT FILE & GỘP DỮ LIỆU

Sau khi chạy xong, mỗi người sẽ có các file riêng lẻ. Hãy đặt tên file theo quy tắc:
`data_{TÊN_NGƯỜI}_{SÀN}_{DANH_MỤC}.jsonl`

**Ví dụ:**

* `data_Huy_Shopee_Dienthoai.jsonl`
* `data_Huy_Tiki_Laptop.jsonl`
* `data_Tuan_Shopee_Thoitrang.jsonl`

**Cuối tuần:**

1. Cả 3 người upload file lên Google Drive chung.
2. Trưởng nhóm tải hết về.
3. Chạy lệnh gộp (trên Windows CMD):
`type *.jsonl > all_data_merged.jsonl`
4. Lúc này các bạn sẽ có file `all_data_merged.jsonl` chứa 1 triệu dòng với **cấu trúc y hệt nhau**, sẵn sàng để làm Search Engine.

**Tóm lại:** Bạn chỉ cần gửi file `schema.py` và cái hướng dẫn "Mapping" ở Bước 2 cho 2 bạn kia là xong. Code crawl (request gửi đi) thì mỗi người tự lo, nhưng dữ liệu đầu ra phải đi qua cái phễu Mapping này.
