# BÁO CÁO MILESTONE 3

## Hệ Thống Tìm Kiếm Thương Mại Điện Tử Tích Hợp Trí Tuệ Nhân Tạo

**Môn học:** SEG301 — Search Engine  
**Nhóm thực hiện:** Trịnh Khải Nguyên (QE190129), Lê Hoàng Hữu (QE190142), Ngô Tuấn Hoàng (QE190076)

---

## 1. TỔNG QUAN

### 1.1. Bối cảnh

Milestone 3 là giai đoạn cuối cùng của dự án, nâng cấp hệ thống từ một công cụ tìm kiếm dựa trên từ khóa (BM25) thành một nền tảng tìm kiếm tích hợp trí tuệ nhân tạo (AI-Powered Search Engine) có giao diện Web hoàn chỉnh.

### 1.2. Quy mô dữ liệu

| Nền tảng | Số lượng sản phẩm | Tỷ trọng |
| :--- | ---: | ---: |
| Shopee | 800,284 | 55.0% |
| Tiki | 435,203 | 29.9% |
| Chợ Tốt | 114,370 | 7.9% |
| eBay | 104,742 | 7.2% |
| **Tổng cộng** | **1,454,599** | **100%** |

### 1.3. Các mục tiêu Milestone 3

1. Xây dựng hệ thống đánh giá chất lượng tìm kiếm (Evaluation Framework).
2. Tích hợp tìm kiếm ngữ nghĩa bằng AI (Vector Search với PhoBERT + FAISS).
3. Thiết kế cơ chế kết hợp xếp hạng (Hybrid Ranking với RRF + Dynamic Weighting).
4. Phát triển giao diện người dùng trực quan (Web UI với Streamlit).

---

## 2. KIẾN TRÚC HỆ THỐNG

```
┌────────────────────────────────────────────────────────┐
│                    Web UI (Streamlit)                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │
│  │ Search   │  │ Filters  │  │ Product Grid (4 cột)  │ │
│  │ Bar      │  │ Sidebar  │  │ Card + Badge + Score  │ │
│  └──────────┘  └──────────┘  └───────────────────────┘ │
└────────────────────┬───────────────────────────────────┘
                     │
           ┌─────────▼─────────┐
           │   SearchEngine    │  ← src/search/engine.py
           │  (Query Pipeline) │
           │  expand_query()   │
           │  segment_query()  │
           └───────┬───────────┘
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
 ┌─────────┐ ┌──────────┐ ┌──────────────┐
 │  BM25   │ │  Vector  │ │   Hybrid     │
 │ Ranker  │ │ Searcher │ │  Searcher    │
 │         │ │ (PhoBERT │ │ (RRF Fusion  │
 │         │ │ + FAISS) │ │ + Dynamic W) │
 └─────────┘ └──────────┘ └──────────────┘
```

---

## 3. CHI TIẾT TRIỂN KHAI

### 3.1. Hệ thống Đánh giá Chất lượng (Evaluation Framework)

**Mã nguồn:** `src/evaluation/metrics.py`, `evaluate.py`, `evaluation/ground_truth.json`

#### 3.1.1. Bộ dữ liệu kiểm thử (Ground Truth)

Xây dựng tập dữ liệu tiêu chuẩn gồm **15 truy vấn** đại diện cho các kịch bản tìm kiếm phổ biến trên sàn TMĐT. Mỗi truy vấn được gán nhãn thủ công (manual annotation) với danh sách Document ID liên quan.

#### 3.1.2. Các thang đo (IR Metrics)

Triển khai đầy đủ **5 thang đo** chuẩn ngành Information Retrieval:

| Thang đo | Công thức | Ý nghĩa |
| :--- | :--- | :--- |
| **Precision@K** | `P@K = \|retrieved ∩ relevant\| / K` | Tỷ lệ kết quả đúng trong top K |
| **Recall@K** | `R@K = \|retrieved ∩ relevant\| / \|relevant\|` | Tỷ lệ bao phủ kết quả đúng |
| **nDCG@K** | `DCG / IDCG` với `DCG = Σ(rel_i / log₂(i+2))` | Chất lượng xếp hạng có trọng số vị trí |
| **MRR** | `Mean(1/rank of first relevant)` | Vị trí trung bình của kết quả đúng đầu tiên |
| **F1@K** | `2·P·R / (P + R)` | Trung bình điều hòa Precision và Recall |

#### 3.1.3. Pipeline đánh giá tự động

Hàm `evaluate_search_engine()` trong `metrics.py` tự động:

1. Chạy từng truy vấn trong Ground Truth qua Search Engine.
2. Tính `P@5`, `P@10`, `R@10`, `nDCG@10`, `F1@10` cho mỗi truy vấn.
3. Tính `MRR` trên toàn bộ tập truy vấn.
4. Xuất báo cáo so sánh giữa chế độ BM25 và Hybrid.

---

### 3.2. Tìm kiếm Ngữ nghĩa (Vector / Semantic Search)

**Mã nguồn:** `src/ranking/vector.py` (class `VectorSearcher`), `build_vector_index.py`

#### 3.2.1. Mô hình nhúng ngôn ngữ (Embedding Model)

- **Model:** `VoVanPhuc/sup-SimCSE-VietNamese-phobert-base` — mô hình PhoBERT được fine-tune cho bài toán Semantic Textual Similarity trên tiếng Việt.
- **Chiều vector:** 768 chiều (normalized L2).
- **Khả năng:** Hiểu được quan hệ ngữ nghĩa giữa các từ/cụm từ (ví dụ: "áo lạnh" ↔ "áo ấm mùa đông", "điện thoại" ↔ "smartphone").

#### 3.2.2. Vector Index (FAISS)

- **Thư viện:** FAISS (Facebook AI Similarity Search) — CPU mode.
- **Loại Index:** `IndexFlatIP` (Inner Product / Cosine Similarity cho vector đã chuẩn hóa).
- **Quy trình xây dựng:** Đọc `MASTER_DATA_CLEAN.jsonl` → Batch embedding toàn bộ title sản phẩm → Lưu index FAISS + mapping `doc_ids` ra đĩa.
- **Tốc độ truy vấn:** Dưới **30ms** cho mỗi truy vấn trên tập 1.45 triệu sản phẩm.

#### 3.2.3. Các phương thức chính

| Phương thức | Chức năng |
| :--- | :--- |
| `load_model()` | Nạp model PhoBERT từ HuggingFace (cache sau lần đầu, ~500MB) |
| `embed_text(text)` | Mã hóa 1 đoạn text → vector 768 chiều đã chuẩn hóa |
| `embed_batch(texts)` | Mã hóa hàng loạt (batch processing) cho tốc độ tối ưu |
| `build_index(docs_path)` | Xây dựng FAISS index từ file JSONL |
| `search(query, top_k)` | Nhúng query → tìm top_k vector gần nhất → trả `[(doc_id, score)]` |

---

### 3.3. Xếp hạng Kết hợp (Hybrid Search & Ranking)

**Mã nguồn:** `src/ranking/vector.py` (class `HybridSearcher`)

#### 3.3.1. Thuật toán Reciprocal Rank Fusion (RRF)

**Vấn đề:** Điểm số BM25 (thang `15.0 – 100.0+`) và Vector Cosine Similarity (thang `0.0 – 1.0`) nằm trên hai phân phối hoàn toàn khác nhau. Chuẩn hóa Min-Max không hiệu quả do outlier ở BM25.

**Giải pháp:** Áp dụng thuật toán RRF — chỉ sử dụng **thứ hạng (rank)** thay vì điểm số gốc.

**Công thức:**

```
Score_RRF(doc) = w_bm25 × 1/(60 + rank_bm25) + w_vector × 1/(60 + rank_vector)
```

Trong đó:

- `60` là hằng số chuẩn hóa RRF (giá trị chuẩn công nghiệp).
- `w_bm25`, `w_vector` là trọng số được điều chỉnh động.

#### 3.3.2. Trọng số Động (Dynamic Weighting)

Hàm `_analyze_query_weights()` tự động phân tích cấu trúc truy vấn bằng biểu thức chính quy (Regex) để quyết định tỷ lệ trọng số:

| Loại truy vấn | Ví dụ | tech_ratio | BM25 | Vector |
| :--- | :--- | :---: | :---: | :---: |
| Kỹ thuật/Mã máy | "iphone 15 pro max 256gb" | ≥ 0.5 | **0.8** | 0.2 |
| Hỗn hợp | "samsung điện thoại chụp ảnh" | > 0 | **0.6** | 0.4 |
| Ngôn ngữ tự nhiên | "điện thoại thông minh chụp ảnh ban đêm đẹp" | ≤ 0.2 | 0.2 | **0.8** |
| Mặc định | "tai nghe" | = 0 | 0.5 | 0.5 |

**Pattern kỹ thuật được nhận dạng:** các cụm chứa số (`15`, `256`), hậu tố kỹ thuật (`gb`, `tb`, `mah`), mã phiên bản (`pro`, `max`, `ultra`, `plus`, `mini`).

#### 3.3.3. Bộ lọc chất lượng

Kết quả Vector Search có Cosine Similarity dưới ngưỡng `0.55` sẽ bị loại bỏ tự động, ngăn chặn "rác" ngữ nghĩa khi người dùng nhập các truy vấn vô nghĩa hoặc ký tự đặc biệt.

---

### 3.4. Giao diện Web (Streamlit UI)

**Mã nguồn:** `src/ui/app.py` (341 dòng)

#### 3.4.1. Thiết kế giao diện

- **Framework:** Streamlit — chuyển đổi Python thành ứng dụng Web tương tác.
- **Phong cách:** Thiết kế sạch, hiện đại với CSS tùy chỉnh (font Manrope, card hover animation, platform badges theo màu riêng cho từng sàn).
- **Layout:** Product Grid 4 cột, CSS Flexbox đồng nhất chiều cao. Line-clamp (`-webkit-line-clamp: 2`) ngắt gọn title và category dài, tránh vỡ giao diện.

#### 3.4.2. Tính năng vận hành

| Tính năng | Mô tả |
| :--- | :--- |
| **3 chế độ tìm kiếm** | BM25 (Từ khóa) · Vector (Ngữ nghĩa) · Hybrid (Kết hợp) — chuyển đổi real-time |
| **Bộ lọc nâng cao** | Thanh kéo giá tiền Min–Max, Chọn lọc sàn (Shopee/Tiki/Chotot/eBay) |
| **Phân trang** | Pagination tối ưu hiển thị kết quả theo trang |
| **Lịch sử tìm kiếm** | Lưu các truy vấn đã thực hiện trong phiên làm việc |
| **Sắp xếp** | Mặc định (theo điểm Engine) hoặc theo Giá tăng/giảm dần |

#### 3.4.3. Tối ưu hiệu năng

- **`@st.cache_resource`:** Mô hình AI PhoBERT (~500MB) và toàn bộ Document Store (1.45 triệu sản phẩm) chỉ được nạp vào RAM **duy nhất một lần** khi khởi động. Các lần tìm kiếm tiếp theo truy xuất trực tiếp từ bộ nhớ (Hot-loading), đạt tốc độ **dưới 120ms/truy vấn**.
- **`sys.path.append`:** Giải quyết vấn đề import module `src` khi chạy Streamlit từ thư mục gốc dự án.

---

### 3.5. Tích hợp SearchEngine

**Mã nguồn:** `src/search/engine.py` (class `SearchEngine`, 354 dòng)

SearchEngine là lớp điều phối trung tâm, tích hợp toàn bộ pipeline:

1. **Mở rộng truy vấn (Query Expansion):** Bảng `SYNONYM_MAP` tự động chuyển đổi viết tắt thông dụng (ví dụ: `ip` → `iphone`, `ss` → `samsung`, `prm` → `pro max`).
2. **Tách từ tiếng Việt (Segmentation):** Sử dụng thư viện `pyvi.ViTokenizer` để phân đoạn từ tiếng Việt cho BM25.
3. **Điều phối chế độ tìm kiếm:** Hỗ trợ chuyển đổi linh hoạt giữa `bm25`, `vector`, và `hybrid` qua phương thức `set_search_mode()`.
4. **Nâng hạng tiêu đề (Title Boost):** Kết quả có từ khóa xuất hiện trong tiêu đề sản phẩm được tăng điểm ưu tiên.
5. **Đa dạng hóa sàn (Platform Diversification):** Đảm bảo kết quả trả về không bị chiếm lĩnh bởi một sàn duy nhất.

---

## 4. KIỂM THỬ VÀ ĐẢM BẢO CHẤT LƯỢNG

### 4.1. Unit Testing

| Bộ test | File | Số ca kiểm thử | Nội dung |
| :--- | :--- | :---: | :--- |
| Evaluation Metrics | `tests/test_metrics.py` | 18 | Kiểm thử P@K, R@K, nDCG@K, MRR, F1@K |
| Index Compression | `tests/test_compression_integration.py` | 15 | Kiểm thử VB/Delta encode-decode |
| Vector Search | `tests/test_vector.py` | 10 | Kiểm thử embed, search, semantic similarity |
| Hybrid Search | `tests/test_hybrid.py` | 7 | Kiểm thử RRF fusion, dynamic weighting |
| BM25 + Engine | `tests/test_*.py` (khác) | 10 | Kiểm thử BM25 ranker, query expansion |
| **Tổng cộng** | | **60/60 ✅** | **100% Pass Rate — 0 Regression** |

### 4.2. Hiệu năng hệ thống

| Chỉ số | Giá trị |
| :--- | :--- |
| Thời gian khởi động (Cold start) | ~10–15 giây (nạp index + model) |
| Thời gian truy vấn (Warm, BM25) | 80–120ms |
| Thời gian truy vấn (Warm, Vector) | < 30ms |
| Thời gian truy vấn (Warm, Hybrid) | 100–150ms |
| Số lượng sản phẩm được index | 1,454,599 |
| Số lượng term trong Inverted Index | 381,391 |

---

## 5. CẤU TRÚC THƯ MỤC DỰ ÁN

```
seg301-ecommerce-search/
├── src/
│   ├── crawler/                 # Spiders thu thập dữ liệu (Milestone 1)
│   ├── indexer/                 # SPIMI Indexer + Compression (Milestone 2)
│   ├── ranking/
│   │   ├── bm25.py              # BM25 Ranker (Milestone 2)
│   │   └── vector.py            # VectorSearcher + HybridSearcher ★
│   ├── search/
│   │   └── engine.py            # SearchEngine — lớp điều phối trung tâm ★
│   ├── evaluation/
│   │   └── metrics.py           # 5 IR Metrics + evaluate pipeline ★
│   └── ui/
│       └── app.py               # Streamlit Web UI ★
├── tests/                       # 60 unit tests
├── evaluate.py                  # Script chạy evaluation tự động ★
├── build_vector_index.py        # Script build FAISS index ★
├── data_sample/                 # Dữ liệu mẫu JSONL
├── docs/                        # Tài liệu và báo cáo
└── requirements.txt
```

> Các file đánh dấu ★ là thành quả mới của Milestone 3.

---

## 6. KẾT LUẬN

Milestone 3 đã hoàn thành đầy đủ và vượt mức yêu cầu đề ra. Hệ thống đã chuyển từ một công cụ tìm kiếm từ khóa đơn thuần thành một nền tảng tìm kiếm AI tích hợp, với:

- **Tìm kiếm ngữ nghĩa** giúp hiểu ý định người dùng vượt xa giới hạn khớp từ khóa.
- **Xếp hạng kết hợp** với trọng số tự động thích ứng theo từng truy vấn.
- **Hệ thống đánh giá định lượng** cung cấp bằng chứng thực nghiệm về chất lượng.
- **Giao diện Web chuyên nghiệp** biến đồ án thành một sản phẩm hoàn chỉnh.
