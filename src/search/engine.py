# Search Engine - Module tích hợp SPIMI Index + BM25 Ranking + Hybrid Search
# Kết nối các thành phần lại và cung cấp API search

import json
import re
from pyvi import ViTokenizer  # Tách từ tiếng Việt - đồng bộ với cách index đã xử lý data
from src.ranking.bm25 import BM25Ranker
from src.ranking.vector import VectorSearcher, HybridSearcher



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

    def __init__(self, index_dir="data/index", data_path="data/MASTER_DATA_CLEAN.jsonl",
                 search_mode="bm25", vector_index_dir="data/vector_index"):
        """
        Khởi tạo SearchEngine.

        Args:
            index_dir: Thư mục chứa inverted_index.pkl + metadata.pkl
            data_path: Đường dẫn file JSONL gốc
            search_mode: "bm25" (mặc định) hoặc "hybrid" (BM25 + Vector)
            vector_index_dir: Thư mục chứa FAISS index (chỉ dùng khi hybrid)
        """
        self.index_dir = index_dir
        self.data_path = data_path
        self.search_mode = search_mode
        self.vector_index_dir = vector_index_dir
        self.ranker = BM25Ranker()
        self.doc_store = {}  # lưu toàn bộ thông tin sản phẩm để hiển thị

        # Hybrid search components (chỉ khởi tạo khi cần)
        self.vector_searcher = None
        self.hybrid_searcher = None

    # Các fields cần lưu trong doc_store (chỉ giữ fields hiển thị, bỏ phần nặng)
    DISPLAY_FIELDS = ["title", "price", "platform", "category", "link", "image_url"]

    def load(self):
        """Nạp index và document store vào RAM."""
        print("Loading Search Engine...")

        # Load BM25 index (inverted_index.pkl + metadata.pkl)
        self.ranker.load_index(self.index_dir)

        # Load document store: ưu tiên doc_store.pkl (nhanh), fallback JSONL (chậm)
        import os
        import pickle
        doc_store_pkl = os.path.join(self.index_dir, "doc_store.pkl")

        if os.path.exists(doc_store_pkl):
            # Nhanh: load pickle (~5-10s thay vì ~40s)
            print(f"Loading document store from {doc_store_pkl}...")
            with open(doc_store_pkl, 'rb') as f:
                self.doc_store = pickle.load(f)
        else:
            # Chậm: parse JSONL gốc (fallback nếu chưa build doc_store.pkl)
            print(f"doc_store.pkl not found, loading from JSONL (slow)...")
            print(f"Tip: Run 'python -c \"from src.search.engine import SearchEngine; SearchEngine.build_doc_store()\"' to build it.")
            self._load_from_jsonl()

        # Load Vector Search (nếu hybrid mode)
        if self.search_mode == "hybrid":
            self._load_vector_search()

        print(f"Engine ready: {len(self.doc_store)} products loaded.")
        print(f"Search mode: {self.search_mode}")

    def _load_from_jsonl(self):
        """Fallback: đọc JSONL gốc vào doc_store (chậm nhưng luôn hoạt động)."""
        print(f"Loading document store from {self.data_path}...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    doc = json.loads(line.strip())
                    doc_id = doc.get('id')
                    if doc_id:
                        # Chỉ giữ fields cần hiển thị
                        self.doc_store[doc_id] = {
                            field: doc.get(field, "") for field in self.DISPLAY_FIELDS
                        }
                except json.JSONDecodeError:
                    continue

    @staticmethod
    def build_doc_store(data_path="data/MASTER_DATA_CLEAN.jsonl",
                        output_dir="data/index"):
        """
        Pre-build doc_store.pkl từ JSONL gốc. Chạy 1 lần.
        Chỉ giữ các fields hiển thị → file nhỏ hơn, load nhanh hơn.

        Usage:
            python -c "from src.search.engine import SearchEngine; SearchEngine.build_doc_store()"
        """
        import os
        import pickle

        print(f"Building doc_store.pkl from {data_path}...")
        doc_store = {}
        count = 0

        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    doc = json.loads(line.strip())
                    doc_id = doc.get('id')
                    if doc_id:
                        doc_store[doc_id] = {
                            field: doc.get(field, "")
                            for field in SearchEngine.DISPLAY_FIELDS
                        }
                        count += 1
                        if count % 200000 == 0:
                            print(f"  Processed {count} products...")
                except json.JSONDecodeError:
                    continue

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "doc_store.pkl")
        with open(output_path, 'wb') as f:
            pickle.dump(doc_store, f)

        # Tính kích thước file
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Saved doc_store.pkl: {count} products, {size_mb:.1f} MB")
        print(f"   Path: {output_path}")

    def _load_vector_search(self):
        """Load VectorSearcher + HybridSearcher cho chế độ hybrid."""
        try:
            print("Loading Vector Search components...")
            self.vector_searcher = VectorSearcher()
            self.vector_searcher.load_model()
            self.vector_searcher.load_index(self.vector_index_dir)

            self.hybrid_searcher = HybridSearcher(
                bm25_ranker=self.ranker,
                vector_searcher=self.vector_searcher,
                bm25_weight=0.5,
                vector_weight=0.5,
            )
            print("Hybrid search ready.")
        except Exception as e:
            print(f"Warning: Failed to load vector search: {e}")
            print("Falling back to BM25-only mode.")
            self.search_mode = "bm25"

    def set_search_mode(self, mode):
        """
        Chuyển đổi search mode lúc runtime.

        Args:
            mode: "bm25", "vector", hoặc "hybrid"
        """
        if mode in ["hybrid", "vector"] and self.hybrid_searcher is None:
            self._load_vector_search()
        self.search_mode = mode
        print(f"Search mode changed to: {self.search_mode}")

    def expand_query(self, query):
        """
        Mở rộng truy vấn: chuyển từ viết tắt sang từ đầy đủ.
        Ví dụ: "ip 17 prm" -> "iphone 17 pro max"
              "ip 14prm" -> "iphone 14 pro max" (tự tách 14prm thành 14 + prm)
        """
        # Bước 1: Tách các token dính nhau (VD: "14prm" -> "14" + "prm")
        # Regex tách chỗ nào số gặp chữ hoặc chữ gặp số
        raw_tokens = query.lower().split()
        tokens = []
        for t in raw_tokens:
            # Tách "14prm" → ["14", "prm"], "256gb" → ["256", "gb"]
            sub_tokens = re.findall(r'[a-zA-Zàáảãạăắặằẵẳâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+|\d+', t)
            if sub_tokens:
                tokens.extend(sub_tokens)
            else:
                tokens.append(t)

        # Bước 2: Thay thế từ viết tắt
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

    def segment_query(self, query):
        """
        Tách từ tiếng Việt cho query, đồng bộ với cách dữ liệu đã được index.
        Quan trọng: Dữ liệu trong index đã qua PyVi (M1), nên query cũng phải qua PyVi
        để đảm bảo token khớp nhau.

        Ví dụ: "bao cao su" -> "bao_cao_su"  (khớp với token trong index)
               "điện thoại" -> "điện_thoại"
               "tai nghe bluetooth" -> "tai_nghe bluetooth"
        """
        segmented = ViTokenizer.tokenize(query)

        # In ra nếu query bị thay đổi sau segmentation
        if segmented != query:
            print(f"  Query segmented: '{query}' -> '{segmented}'")

        return segmented

    def search(self, query, top_k=10):
        """
        Tìm kiếm sản phẩm theo từ khóa.
        Trả về list dict chứa thông tin sản phẩm + điểm.
        Hỗ trợ 2 mode: "bm25" (keyword) và "hybrid" (keyword + semantic).
        """
        # Bước 0: Mở rộng từ viết tắt
        expanded_query = self.expand_query(query)

        # Bước 1: Tách từ tiếng Việt (đồng bộ với index)
        segmented_query = self.segment_query(expanded_query)

        # Bước 2: Lấy ranked results (BM25, Vector, hoặc Hybrid)
        if self.search_mode == "hybrid" and self.hybrid_searcher is not None:
            ranked_results = self.hybrid_searcher.search(
                segmented_query, top_k=top_k * 5
            )
        elif self.search_mode == "vector" and self.hybrid_searcher is not None:
            raw_vector_results = self.hybrid_searcher.vector_searcher.search(
                segmented_query, top_k=top_k * 5
            )
            # Lọc điểm vector quá thấp
            ranked_results = [(d, s) for d, s in raw_vector_results if s >= 0.55]
        else:
            # BM25 only
            ranked_results = self.ranker.rank(segmented_query, top_k=top_k * 5)


        # Bước 3: Gắn thông tin sản phẩm
        results = []

        for doc_id, score in ranked_results:
            product = self.doc_store.get(doc_id, {})
            title = product.get("title", "N/A")
            
            # Lọc bớt rác từ quá trình crawl (title chỉ chứa số, giá tiền, hoặc % giảm giá)
            # Match các title rác như: "-24%", "123.000đ", "123", "99,000 vnd"
            if re.fullmatch(r'[\d\.,\-%\s]+(?:đ|vnd)?', title.lower().strip()):
                continue
                
            results.append({
                "id": doc_id,
                "title": title,
                "price": product.get("price", 0),
                "platform": product.get("platform", "Unknown"),
                "category": product.get("category", ""),
                "link": product.get("link", ""),
                "image_url": product.get("image_url", ""),
                "bm25_score": round(score, 4),
            })

        # Sắp xếp lại toàn bộ theo độ liên quan (score) chính xác nhất
        results.sort(key=lambda x: x["bm25_score"], reverse=True)

        # Bỏ qua Platform Diversification theo yêu cầu, chỉ trả về Top K tinh khiết nhất
        return results[:top_k]

    def diversify_results(self, results, top_k=10, max_per_platform=3):
        """
        Đa dạng hóa kết quả: tránh 1 sàn chiếm hết top kết quả.
        Thuật toán Round-Robin: lần lượt lấy từ mỗi sàn theo thứ tự score.

        Ví dụ: Nếu có 8 kết quả Chợ Tốt + 2 Tiki, thay vì hiển thị 8 Chợ Tốt,
        sẽ xen kẽ: Chợ Tốt → Tiki → Chợ Tốt → Tiki → Chợ Tốt → ...
        """
        print(f"Diversifying {len(results)} ")
        if len(results) <= top_k:
            return results

        # Loại bỏ kết quả quá thấp so với top 1 (tránh kéo phụ kiện score 3 vào top)
        # Nếu top 1 score = 40, chỉ giữ kết quả score >= 12 (30% của 40)
        #if results:
           # top_score = results[0]["bm25_score"]
           # min_score = top_score * 0.2  # ngưỡng tối thiểu = 20% score cao nhất
           # results = [r for r in results if r["bm25_score"] >= min_score]

        # Nhóm kết quả theo platform, giữ nguyên thứ tự score
        by_platform = {}
        for r in results:
            platform = r["platform"]
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(r)

        # Nếu chỉ có 1 sàn thì không cần diversify
        if len(by_platform) <= 1:
            return results[:top_k]

        # Round-robin: lấy lần lượt từ mỗi sàn
        # Sắp xếp sàn theo score cao nhất của sàn đó (sàn có top 1 cao nhất đi trước)
        platform_order = sorted(by_platform.keys(),
                                key=lambda p: by_platform[p][0]["bm25_score"],
                                reverse=True)

        diversified = []
        platform_count = {}  # đếm số kết quả mỗi sàn đã lấy

        # Lấy round-robin cho tới khi đủ top_k
        round_num = 0
        while len(diversified) < top_k:
            added_this_round = False

            for platform in platform_order:
                if len(diversified) >= top_k:
                    break

                items = by_platform[platform]
                count = platform_count.get(platform, 0)

                # Còn item chưa lấy và chưa vượt giới hạn mỗi sàn
                if count < len(items) and count < max_per_platform:
                    diversified.append(items[count])
                    platform_count[platform] = count + 1
                    added_this_round = True

            # Nếu tất cả sàn đều đã đạt max, nới lỏng giới hạn
            if not added_this_round:
                max_per_platform += 1

            round_num += 1
            if round_num > 50:  # an toàn, tránh vòng lặp vô hạn
                break

        return diversified

