# SEG301 - E-commerce Search Engine

Hệ thống tìm kiếm sản phẩm từ các trang thương mại điện tử Việt Nam (Shopee, Tiki).

## Yêu cầu

- Python 3.10+

## Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd seg301-ecommerce-search
```

### 2. Tạo môi trường ảo (Virtual Environment)

```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

> **Lưu ý**: Thư mục `venv/` đã được thêm vào `.gitignore` và sẽ không được upload lên GitHub.

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình environment variables

Tạo file `.env` từ template (nếu có):

```bash
cp .env.example .env
```

## Cấu trúc thư mục

```
SEG301-Project/
├── .gitignore               # File cấu hình git ignore
├── README.md                # Hướng dẫn cài đặt, chạy dự án & Link tải Full Dataset
├── ai_log.md                # Nhật ký sử dụng AI (Cập nhật liên tục theo ngày)
├── requirements.txt         # Danh sách các thư viện cần thiết
├── docs/                    # Thư mục chứa báo cáo (PDF/Markdown)
│   ├── Milestone1_Report.pdf
│   ├── Milestone2_Report.pdf
│   └── Milestone3_Presentation.pdf
├── data_sample/             # Chỉ chứa 100-500 docs mẫu (KHÔNG UP 1 TRIỆU DOCS)
│   └── sample.jsonl
├── src/                     # Source code chính
│   ├── __init__.py
│   ├── crawler/             # Milestone 1: Code thu thập dữ liệu
│   │   ├── spider.py        # Logic crawl chính
│   │   ├── parser.py        # Xử lý HTML, tách từ
│   │   └── utils.py         # Hàm phụ trợ (Proxy, User-agent)
│   ├── indexer/             # Milestone 2: Code tạo chỉ mục
│   │   ├── spimi.py         # Thuật toán SPIMI
│   │   ├── merging.py       # Logic merge block
│   │   └── compression.py   # Nén dữ liệu (nếu có)
│   ├── ranking/             # Milestone 2 & 3: Code xếp hạng
│   │   ├── bm25.py          # Thuật toán BM25 (Code tay)
│   │   └── vector.py        # Semantic Search (Dùng thư viện cho M3)
│   └── ui/                  # Milestone 3: Giao diện người dùng
│       └── app.py           # Streamlit/Flask app
└── tests/                   # Unit tests cho các thuật toán core
    ├── test_spimi.py
    └── test_bm25.py
```

## Full Dataset

> Link tải dữ liệu đầy đủ (1 triệu docs): [Google Drive / OneDrive Link]

## Chạy tests

```bash
pytest
```

## License

MIT License
