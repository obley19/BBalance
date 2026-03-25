# Vector/Semantic Search + Hybrid Ranking
# Milestone 3: Final Product
# Sử dụng Sentence-Transformers (PhoBERT) + FAISS cho semantic search

import os
import json
import pickle
import numpy as np


class VectorSearcher:
    """
    Semantic search sử dụng vector embeddings.

    Dùng PhoBERT (sup-SimCSE-VietNamese) để encode text thành vector,
    sau đó tìm kiếm bằng FAISS (Facebook AI Similarity Search).

    Flow:
    1. Load model → embed query → FAISS top-k → trả (doc_id, score)
    """

    def __init__(self, model_name="VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"):
        """
        Khởi tạo VectorSearcher.

        Args:
            model_name: Tên model trên HuggingFace cho Vietnamese embeddings
        """
        self.model_name = model_name
        self.model = None       # SentenceTransformer model
        self.index = None       # FAISS index
        self.doc_ids = []       # Mapping: FAISS internal id → doc_id gốc
        self.dimension = None   # Chiều của embedding vector (768 cho PhoBERT)

    def load_model(self):
        """
        Load embedding model từ HuggingFace.
        Model sẽ được cache sau lần đầu download (~500MB).
        """
        from sentence_transformers import SentenceTransformer

        print(f"Loading embedding model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.dimension}")

    def embed_text(self, text):
        """
        Encode 1 đoạn text thành vector embedding.

        Args:
            text: Chuỗi văn bản đầu vào

        Returns:
            numpy array (dimension,) — vector đã normalize (unit length)
        """
        if self.model is None:
            raise RuntimeError("Model chưa load. Gọi load_model() trước.")

        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding

    def embed_batch(self, texts, batch_size=64, show_progress=True):
        """
        Encode nhiều text cùng lúc (batch) để tối ưu tốc độ.

        Args:
            texts: List các chuỗi văn bản
            batch_size: Số lượng text xử lý mỗi batch
            show_progress: Hiển thị progress bar

        Returns:
            numpy array (n_texts, dimension) — ma trận embeddings
        """
        if self.model is None:
            raise RuntimeError("Model chưa load. Gọi load_model() trước.")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,  # L2 normalize → dùng Inner Product = Cosine Similarity
            show_progress_bar=show_progress,
        )
        return embeddings

    def build_index(self, documents_path, output_path, batch_size=256):
        """
        Build FAISS index từ file JSONL.

        Đọc streaming → batch encode → thêm vào FAISS → lưu ra disk.

        Args:
            documents_path: Đường dẫn tới file JSONL (VD: MASTER_DATA_CLEAN.jsonl)
            output_path: Thư mục lưu FAISS index + mapping
            batch_size: Số documents encode mỗi batch
        """
        import faiss

        if self.model is None:
            self.load_model()

        os.makedirs(output_path, exist_ok=True)

        # Bước 1: Đọc toàn bộ documents (cần doc_id + text)
        print(f"Reading documents from: {documents_path}")
        doc_ids = []
        texts = []
        count = 0

        with open(documents_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    doc = json.loads(line.strip())
                    doc_id = doc.get('id', '')
                    # Ưu tiên title_segmented → title_clean → title (giống SPIMI)
                    text = (doc.get('title_segmented')
                            or doc.get('title_clean')
                            or doc.get('title', ''))

                    if not text or not doc_id:
                        continue

                    doc_ids.append(doc_id)
                    texts.append(text)
                    count += 1

                    if count % 100000 == 0:
                        print(f"  Read {count} documents...")

                except json.JSONDecodeError:
                    continue

        print(f"Total documents to embed: {count}")

        # Bước 2: Batch encode tất cả texts
        print(f"Encoding {count} documents (batch_size={batch_size})...")
        all_embeddings = self.embed_batch(texts, batch_size=batch_size)

        # Bước 3: Build FAISS index
        # Dùng IndexFlatIP (Inner Product) vì embeddings đã normalize (L2)
        # → Inner Product = Cosine Similarity
        dimension = all_embeddings.shape[1]
        print(f"Building FAISS index (dimension={dimension})...")

        index = faiss.IndexFlatIP(dimension)
        index.add(all_embeddings.astype(np.float32))

        print(f"FAISS index built: {index.ntotal} vectors")

        # Bước 4: Lưu ra disk
        faiss_path = os.path.join(output_path, "faiss_index.bin")
        faiss.write_index(index, faiss_path)

        mapping_path = os.path.join(output_path, "doc_id_mapping.pkl")
        with open(mapping_path, 'wb') as f:
            pickle.dump(doc_ids, f)

        print(f"Saved FAISS index: {faiss_path}")
        print(f"Saved ID mapping: {mapping_path} ({len(doc_ids)} docs)")

        # Cập nhật state
        self.index = index
        self.doc_ids = doc_ids
        self.dimension = dimension

    def load_index(self, index_dir):
        """
        Load FAISS index + ID mapping đã build từ disk.

        Args:
            index_dir: Thư mục chứa faiss_index.bin + doc_id_mapping.pkl
        """
        import faiss

        faiss_path = os.path.join(index_dir, "faiss_index.bin")
        mapping_path = os.path.join(index_dir, "doc_id_mapping.pkl")

        print(f"Loading FAISS index from: {faiss_path}")
        self.index = faiss.read_index(faiss_path)

        with open(mapping_path, 'rb') as f:
            self.doc_ids = pickle.load(f)

        self.dimension = self.index.d
        print(f"FAISS index loaded: {self.index.ntotal} vectors, dim={self.dimension}")

    def search(self, query, top_k=10):
        """
        Tìm kiếm semantic: embed query → FAISS nearest neighbors.

        Args:
            query: Chuỗi truy vấn
            top_k: Số kết quả trả về

        Returns:
            List[(doc_id, similarity_score)] — sắp xếp giảm dần theo score
        """
        if self.index is None:
            raise RuntimeError("Index chưa load. Gọi load_index() trước.")
        if self.model is None:
            raise RuntimeError("Model chưa load. Gọi load_model() trước.")

        # Embed query thành vector
        query_vector = self.embed_text(query)
        query_vector = np.array([query_vector], dtype=np.float32)

        # FAISS search: trả về (distances, indices)
        # distances = similarity scores (vì dùng Inner Product)
        # indices = vị trí trong index
        scores, indices = self.index.search(query_vector, top_k)

        # Map FAISS indices → doc_ids
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            score = float(scores[0][i])

            if idx < 0 or idx >= len(self.doc_ids):
                continue  # Invalid index (xảy ra khi index nhỏ hơn top_k)

            doc_id = self.doc_ids[idx]
            results.append((doc_id, score))

        return results


class HybridSearcher:
    """
    Kết hợp BM25 (keyword matching) + Vector Search (semantic similarity).

    Ý tưởng: BM25 tốt cho exact keyword match, Vector tốt cho semantic meaning.
    Kết hợp cả 2 sẽ cho kết quả tốt hơn khi dùng riêng lẻ.

    Công thức: hybrid_score = bm25_weight * norm(bm25_score) + vector_weight * norm(vector_score)
    """

    def __init__(self, bm25_ranker, vector_searcher,
                 bm25_weight=0.5, vector_weight=0.5):
        """
        Khởi tạo HybridSearcher.

        Args:
            bm25_ranker: Instance BM25Ranker đã load index
            vector_searcher: Instance VectorSearcher đã load model + index
            bm25_weight: Trọng số cho BM25 score (default 0.5)
            vector_weight: Trọng số cho Vector score (default 0.5)
        """
        self.bm25_ranker = bm25_ranker
        self.vector_searcher = vector_searcher
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight

    def _analyze_query_weights(self, query):
        """
        Phân tích query để quyết định trọng số động cho BM25 và Vector.
        - Chứa mã model, spec kỹ thuật (15, s24, gb, pro) → Ưu tiên BM25 (keyword matching).
        - Câu dài, mô tả semantic chung chung → Ưu tiên Vector (ngữ nghĩa).
        """
        import re
        words = query.lower().split()
        if not words:
            return self.bm25_weight, self.vector_weight

        # Pattern tìm mã sản phẩm, dung lượng, phiên bản (chứa số hoặc chữ+số hoặc keyword kỹ thuật)
        tech_pattern = re.compile(r'\d+[a-z]*|[a-z]+\d+|pro|max|ultra|plus|mini|gb|tb|mah', re.IGNORECASE)
        tech_words = [w for w in words if tech_pattern.search(w)]

        tech_ratio = len(tech_words) / len(words)

        if tech_ratio >= 0.5:
            # Query chứa nhiểu thông số/mã model -> BM25 cực kỳ quan trọng
            return 0.8, 0.2
        elif len(words) >= 5 and tech_ratio <= 0.2:
            # Truy vấn rất dài, mô tả ngữ nghĩa -> Vector quan trọng
            return 0.2, 0.8
        elif tech_ratio > 0:
            # Có thông số kỹ thuật nhưng không chiếm đa số -> Ưu tiên BM25 nhẹ
            return 0.6, 0.4
        else:
            # Trả về config mặc định
            return self.bm25_weight, self.vector_weight

    def search(self, query, top_k=10):
        """
        Hybrid search: kết hợp kết quả BM25 + Vector bằng thuật toán Reciprocal Rank Fusion (RRF).
        Sử dụng Dynamic Weighting để tự động điều chỉnh trọng số BM25/Vector dựa trên loại query.
        """
        # Dynamic Weighting
        dyn_bm25_w, dyn_vector_w = self._analyze_query_weights(query)

        # In log để theo dõi trọng số
        print(f"  [Hybrid] Dynamic Weights cho '{query}': BM25={dyn_bm25_w:.1f}, Vector={dyn_vector_w:.1f}")

        # Tăng candidate pool để có độ phủ tốt hơn giữa 2 phương pháp
        candidate_k = top_k * 5

        # Bước 1: Lấy top-K từ BM25 và Vector
        bm25_results = self.bm25_ranker.rank(query, top_k=candidate_k)
        vector_results = self.vector_searcher.search(query, top_k=candidate_k)

        # Tránh lỗi trả về rác khi gõ ký tự bừa bãi: Cosine Similarity < 0.55 sẽ bị loại bỏ
        vector_results = [(doc_id, score) for doc_id, score in vector_results if score >= 0.55]

        # Nếu cả 2 đều không tìm thấy gì -> Trả về rỗng
        if not bm25_results and not vector_results:
            return []

        combined = {}
        RRF_K = 60  # Hằng số chuẩn hóa của RRF (thường là 60)

        # Cộng điểm RRF từ kết quả BM25
        for rank, (doc_id, _) in enumerate(bm25_results):
            combined[doc_id] = combined.get(doc_id, 0.0) + dyn_bm25_w * (1.0 / (RRF_K + rank))

        # Cộng điểm RRF từ kết quả Vector
        for rank, (doc_id, _) in enumerate(vector_results):
            combined[doc_id] = combined.get(doc_id, 0.0) + dyn_vector_w * (1.0 / (RRF_K + rank))

        # Nhân scale lên 100 để hiển thị điểm
        for doc_id in combined:
            combined[doc_id] *= 100.0

        # Sort giảm dần theo hybrid score
        ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
