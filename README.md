# SEG301 E-Commerce Search Engine Project

## 1. Team Information

| Name | Student ID | Role | Contribution |
|------|------------|------|--------------|
| **Trịnh Khải Nguyên** | QE190129 | Crawler Lead | Crawling Ebay & Chợ Tốt, anti-bot strategy |
| **Lê Hoàng Hữu** | QE190142 | Crawler | Crawling Tiki, Shopee, data normalization |
| **Ngô Tuấn Hoàng** | QE190076 | Crawler | Crawling Tiki, Shopee, anti-bot detection |

## 2. Project Description

This project implements an e-commerce search engine that aggregates product data from major Vietnamese e-commerce platforms. The system focuses on automated data collection, scalable indexing, and effective ranking methods.

### Key Functionalities

- **Data Collection**: Automated crawling with robust anti-bot detection handling.
- **Indexing**: Text indexing using the SPIMI algorithm.
- **Ranking**:
  - Keyword-based: BM25.
  - Semantic-based: Sentence Transformers.
- **User Interface**: Web-based search interface and real-time monitoring dashboard.

### Supported Platforms

- Shopee
- Tiki
- Chợ Tốt
- eBay

## 3. System Architecture & Technologies

The system follows a modular pipeline design:

### Tech Stack

- **Crawler**:
  - Python: `playwright` (eBay), `aiohttp` (Chợ Tốt), `DrissionPage` (Shopee).
- **Indexer**: Python (Custom SPIMI implementation).
- **Ranking**: Python (BM25 & Vector Models).
- **UI**: Streamlit (Python).
- **Database**: SQLite & JSONL files.

## 4. Installation & Environment Setup

### 4.1. Requirements

- Python (>= version 3.10)
- Git

### 4.2. Step-by-Step Setup

**Step 1: Clone the repository**

```bash
git clone <repository-url>
cd seg301-ecommerce-search
```

**Step 2: Python Environment Setup**

```bash
# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 5. Execution & Usage

### 5.1. Crawling Data

Run the crawler scripts for each platform:

**Shopee:**

```bash
# Cần cài DrissionPage & cấu hình Chrome
python code\ hoang.py
```

**eBay:**

```bash
python src/crawler/spiders/ebay_async_spider.py
```

**Chợ Tốt:**

```bash
python src/crawler/spiders/chotot_async_spider.py
```

**Tiki:**

```bash
# (Đang phát triển)
python src/crawler/spiders/tiki_spider.py
```

### 5.2. Indexing & Ranking

Once data is collected, run the following scripts:

```bash
# Build Index (SPIMI)
python src/indexer/spimi.py

# Run Ranking Algorithm (BM25)
python src/ranking/bm25.py
```

### 5.3. Search Interface

Launch the web application:

```bash
streamlit run src/ui/app.py
```

## 6. Dataset Description

### 6.1. Data Responsibilities

| Member | Platforms Assigned |
|--------|--------------------|
| Trịnh Khải Nguyên | Ebay, Chợ Tốt |
| Lê Hoàng Hữu | Tiki, Shopee |
| Ngô Tuấn Hoàng | Tiki, Shopee |

### 6.2. Sample Dataset

Located in `data_sample/`. Contains 100–200 products per platform for testing.

### 6.3. Data Schema (Unified)

All datasets follow a unified JSON structure (`ProductItem`):

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique Key: `{platform}_{original_id}` |
| `platform` | string | `shopee`, `tiki`, `chotot`, `ebay` |
| `title` | string | Product Name (cleaned) |
| `price` | int | Current Price (VND) |
| `original_price` | int | Original Price (before discount) |
| `url` | string | Product Link |
| `image_url` | string | Thumbnail Link |
| `rating` | float | Rating (0.0 - 5.0) |
| `review_count` | int | Number of reviews |
| `sold_count` | int | Number of items sold |
| `location` | string | Seller location |
| `brand` | string | Brand name |
| `crawled_at` | int | Unix Timestamp |

### 6.4. Full Dataset Access

- **Link**: [Google Drive / OneDrive Link]
- **Scale**: ~1,000,000 products
- **Format**: JSONL and SQLite

## 7. Project Structure

```
SEG301-Project/
├── .gitignore
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── ai_log.md               # AI debugging logs
├── data_sample/            # Sample data files
├── src/                    # Source code
│   ├── crawler/            # Crawling module
│   │   ├── spider.py       # Base logic
│   │   ├── async_base_spider.py # Async Base
│   │   ├── schema.py       # Unified Data Schema
│   │   └── spiders/        # Platform specific spiders
│   ├── indexer/            # SPIMI Indexing
│   ├── ranking/            # BM25 & Semantic
│   └── ui/                 # Streamlit App
└── tests/                  # Unit tests
```

## 8. Development Timeline

- **Phase 1 (Weeks 1–4)**: Setup environment, Implement crawlers, Data cleaning.
- **Phase 2 (Weeks 5–7)**: Implement SPIMI indexing, BM25 ranking.
- **Phase 3 (Weeks 8–10)**: Build Search UI, Final testing.
