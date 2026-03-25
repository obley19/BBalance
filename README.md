# SEG301 E-Commerce Search Engine Project

## 1. Team Information

| Name | Student ID | Role | Contribution |
|------|------------|------|--------------|
| **Trịnh Khải Nguyên** | QE190129 | Crawler Lead | Crawler (Ebay, Chợ Tốt), Anti-bot strategy |
| **Lê Hoàng Hữu** | QE190142 | Crawler Dev | Crawler (Tiki, Shopee), Data normalization |
| **Ngô Tuấn Hoàng** | QE190076 | Crawler Dev | Crawler (Tiki, Shopee), Performance optimization |

## 2. Project Description

This project implements an e-commerce search engine aggregating product data from major Vietnamese platforms (Shopee, Tiki, Chợ Tốt, eBay). The system focuses on automated data collection, scalable indexing (SPIMI), and effective ranking (BM25 + Semantic AI).

### Key Features (Milestone 3 Completed)

- **Vector Search (Semantic AI)**: Powered by `PhoBERT` (`sup-SimCSE-Vietnamese-phobert-base`) and `FAISS` to match products contextually and semantically instead of exact-matching.
- **Hybrid Ranking Engine**: Implements **Reciprocal Rank Fusion (RRF)** to combine both lexical (BM25) and semantic (Vector) search with **Dynamic Weighting** via query intent analysis.
- **Evaluation Framework**: Automated evaluation suite calculating Information Retrieval (IR) metrics: `Precision@K`, `Recall@K`, `nDCG@K`, `MRR`, and `F1@K`.
- **Modern Web Interface**: A beautifully designed Glassmorphism web UI built with `Streamlit` featuring multiple operational modes (BM25, Vector, Hybrid), deep filters, and real-time response limits.
- **Data Collection & Indexing**: Async crawlers with anti-bot handling and a custom SPIMI implementation for large-scale indexing.

## 3. Dataset Statistics

**Total Collected:** **1,454,599 products**

| Platform | Documents | Share | Status |
| :--- | :--- | :--- | :--- |
| **Shopee** | 800,284 | 55.0% | Included |
| **Tiki** | 435,203 | 29.9% | Included |
| **Chợ Tốt** | 114,370 | 7.9% | Included |
| **eBay** | 104,742 | 7.2% | Included |

**Data Location:**
- **Full Dataset**: Contact Team / [Google Drive Link]
- **Sample Data**: `data_sample/` (for format exploration)

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
python src/crawler/spiders/ebay_async_spider.py
```

### 4.3. Indexing & Search Engine 

```bash
# 1. Build Inverted Index (BM25)
python src/indexer/spimi.py

# 2. Build Vector Index (PhoBERT + FAISS)
python build_vector_index.py

# 3. Start the Web UI Dashboard
streamlit run src/ui/app.py
```

### 4.4. System Evaluation

```bash
# Evaluate System Quality across 15 standard Queries (Ground Truth)
python evaluate.py
```

## 5. Project Structure

```
SEG301-Project/
├── docs/                   # Milestone Reports & Architecture Reviews
├── data_sample/            # Sample JSONL & Output files
├── src/                    # Source Code
│   ├── crawler/            # Spiders & verification scripts
│   ├── indexer/            # SPIMI & Compression
│   ├── ranking/            # BM25, Vector Search, & Hybrid Ranking
│   ├── evaluation/         # Metrics (nDCG@K, MRR) & Ground truth JSON
│   └── ui/                 # Web Interface UI (Streamlit)
├── evaluate.py             # Evaluation Script
├── build_vector_index.py   # Vector Encoding Script
├── requirements.txt
└── README.md
```
