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
seg301-ecommerce-search/
├── src/                    # Source code chính
│   ├── crawlers/          # Các crawler cho từng platform
│   └── utils/             # Các tiện ích
├── data/                   # Dữ liệu (không upload lên git)
│   ├── raw/               # Dữ liệu thô từ crawler
│   ├── processed/         # Dữ liệu đã xử lý
│   └── indices/           # Search indices
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
└── .gitignore             # File cấu hình git ignore
```

## Chạy tests

```bash
pytest
```

## License

MIT License
