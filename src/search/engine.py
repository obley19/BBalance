# Search Engine - Module tích hợp SPIMI Index + BM25 Ranking
# Kết nối các thành phần lại và cung cấp API search

import json
from src.ranking.bm25 import BM25Ranker


# Bảng chuyển đổi từ viết tắt sang từ đầy đủ
# Người dùng hay gõ tắt khi tìm kiếm sản phẩm
SYNONYM_MAP = {
    "ip": "iphone",
    "iph": "iphone",
    "prm": "pro max",
    "promax": "pro max",
    "ss": "samsung",
    "sam": "samsung",
    "dt": "điện thoại",
    "mtb": "máy tính bảng",
    "tn": "tai nghe",
    "sac": "sạc",
}


class SearchEngine:
    """Lớp chính điều phối tìm kiếm: nhận query -> trả kết quả có đầy đủ thông tin."""

    def __init__(self, index_dir="data/index", data_path="data/MASTER_DATA_CLEAN.jsonl"):
        self.index_dir = index_dir
        self.data_path = data_path
        self.ranker = BM25Ranker()
        self.doc_store = {}  # lưu toàn bộ thông tin sản phẩm để hiển thị

    def load(self):
        """Nạp index và document store vào RAM."""
        print("Loading Search Engine...")

        # Load BM25 index (inverted_index.pkl + metadata.pkl)
        self.ranker.load_index(self.index_dir)

        # Load document store: đọc JSONL gốc vào dictionary
        # Mục đích: khi BM25 trả về doc_id, ta cần lấy title, price, link...
        print(f"Loading document store from {self.data_path}...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    doc = json.loads(line.strip())
                    doc_id = doc.get('id')
                    if doc_id:
                        self.doc_store[doc_id] = doc
                except json.JSONDecodeError:
                    continue

        print(f"Engine ready: {len(self.doc_store)} products loaded.")

    def expand_query(self, query):
        """
        Mở rộng truy vấn: chuyển từ viết tắt sang từ đầy đủ.
        Ví dụ: "ip 17 prm" -> "iphone 17 pro max"
        """
        tokens = query.lower().split()
        expanded = []

        for token in tokens:
            if token in SYNONYM_MAP:
                expanded.append(SYNONYM_MAP[token])
            else:
                expanded.append(token)

        result = " ".join(expanded)

        # In ra nếu query bị thay đổi
        if result != query.lower():
            print(f"  Query expanded: '{query}' -> '{result}'")

        return result

    def search(self, query, top_k=10):
        """
        Tìm kiếm sản phẩm theo từ khóa.
        Trả về list dict chứa thông tin sản phẩm + điểm BM25.
        """
        # Bước 0: Mở rộng từ viết tắt
        expanded_query = self.expand_query(query)

        # Bước 1: Gọi BM25 xếp hạng
        ranked_results = self.ranker.rank(expanded_query, top_k=top_k)

        # Bước 2: Gắn thêm thông tin sản phẩm từ doc_store
        results = []
        for doc_id, score in ranked_results:
            product = self.doc_store.get(doc_id, {})

            results.append({
                "id": doc_id,
                "title": product.get("title", "N/A"),
                "price": product.get("price", 0),
                "platform": product.get("platform", "Unknown"),
                "category": product.get("category", ""),
                "link": product.get("link", ""),
                "image_url": product.get("image_url", ""),
                "bm25_score": round(score, 4),
            })

        return results
