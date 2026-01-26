# SEG301 E-Commerce Search Engine Project

## 1. Team Information

| Name | Student ID | Role | Contribution |
|------|------------|------|--------------|
| **Trịnh Khải Nguyên** | QE190129 | Crawler Lead | Crawler (Ebay, Chợ Tốt), Anti-bot strategy |
| **Lê Hoàng Hữu** | QE190142 | Crawler Dev | Crawler (Tiki, Shopee), Data normalization |
| **Ngô Tuấn Hoàng** | QE190076 | Crawler Dev | Crawler (Tiki, Shopee), Performance optimization |

## 2. Project Description

This project implements an e-commerce search engine aggregating product data from major Vietnamese platforms (Shopee, Tiki, Chợ Tốt, eBay). The system focuses on automated data collection, scalable indexing (SPIMI), and effective ranking (BM25 + Semantic).

### Key Features

- **Data Collection**: Async crawlers with anti-bot handling (IP rotation, Browser Automation).
- **Indexing**: Custom SPIMI implementation for large-scale indexing.
- **Ranking**: Hybrid ranking using BM25 and Vector Search.
- **Unified Schema**: Standardized `ProductItem` structure across all platforms.

## 3. Dataset Statistics (Milestone 1)

**Total Collected:** **1,454,599 products**

| Platform | Documents | Share | Status |
| :--- | :--- | :--- | :--- |
| **Shopee** | 800,284 | 55.0% | Included |
| **Tiki** | 435,203 | 29.9% | Included |
| **Chợ Tốt** | 114,370 | 7.9% | Included |
| **eBay** | 104,742 | 7.2% | Included |

**Data Location:**

- **Full Dataset**: [Link to Google Drive/OneDrive]
- **Sample Data**: `data_sample/` (for testing)

## 4. Setup & Usage

### 4.1. Installation

```bash
# Python >= 3.10 required
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 4.2. Running Crawlers

```bash
# Shopee (Requires DrissionPage)
python src/crawler/spiders/shopee_spider.py

# Tiki / Chợ Tốt / eBay (Async)
python src/crawler/spiders/tiki_spider.py
python src/crawler/spiders/chotot_async_spider.py
```

### 4.3. Indexing & Search (Upcoming)

```bash
# Build Index
python src/indexer/spimi.py
# Start Web UI
streamlit run src/ui/app.py
```

## 5. Project Structure

```
SEG301-Project/
├── docs/                   # Documentation & Reports
├── data_sample/            # Sample JSONL files
├── src/                    # Source Code
│   ├── crawler/            # Spiders & verification scripts
│   ├── indexer/            # SPIMI Algorithm
│   ├── ranking/            # Ranking Logic
│   └── ui/                 # Web Interface
├── requirements.txt
└── README.md
```
