"""
Unit tests for VectorSearcher.
Milestone 3: Vector Search

Tests sử dụng mock data nhỏ để chạy nhanh.
Lưu ý: Cần cài sentence-transformers và faiss-cpu.
"""
import pytest
import numpy as np
import json
import os


class TestVectorSearcher:
    """Test suite cho VectorSearcher."""

    @pytest.fixture(scope="class")
    def searcher(self):
        """
        Fixture: Load model 1 lần cho cả class (tiết kiệm thời gian).
        scope="class" → model chỉ load 1 lần, dùng chung cho tất cả tests.
        """
        from src.ranking.vector import VectorSearcher

        vs = VectorSearcher(
            model_name="VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
        )
        vs.load_model()
        return vs

    def test_embed_text_returns_vector(self, searcher):
        """embed_text phải trả về numpy array với đúng dimension."""
        embedding = searcher.embed_text("điện thoại iPhone 15")

        assert isinstance(embedding, np.ndarray)
        assert embedding.ndim == 1  # 1D vector
        assert embedding.shape[0] == searcher.dimension  # 768 cho PhoBERT

    def test_embed_text_normalized(self, searcher):
        """Embedding đã normalize → L2 norm ≈ 1.0."""
        embedding = searcher.embed_text("samsung galaxy s24")

        l2_norm = np.linalg.norm(embedding)
        assert abs(l2_norm - 1.0) < 0.01  # Cho phép sai số nhỏ

    def test_embed_batch_shape(self, searcher):
        """embed_batch trả về ma trận (n, dimension)."""
        texts = ["iphone 15", "samsung s24", "tai nghe bluetooth"]
        embeddings = searcher.embed_batch(texts, show_progress=False)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (3, searcher.dimension)

    def test_embed_text_different_texts_different_vectors(self, searcher):
        """Hai text khác nhau phải cho embedding khác nhau."""
        emb1 = searcher.embed_text("điện thoại iPhone")
        emb2 = searcher.embed_text("bàn ghế gỗ")

        # Cosine similarity (đã normalize → dot product = cosine)
        similarity = np.dot(emb1, emb2)
        assert similarity < 0.95  # Phải khác nhau rõ ràng

    def test_semantic_similarity(self, searcher):
        """Text có ý nghĩa gần nhau phải có similarity cao hơn text không liên quan."""
        emb_phone = searcher.embed_text("điện thoại iPhone giá rẻ")
        emb_related = searcher.embed_text("mua điện thoại iphone")
        emb_unrelated = searcher.embed_text("bàn ghế gỗ phòng khách")

        # "điện thoại iPhone giá rẻ" với "mua điện thoại iphone" phải gần hơn "bàn ghế"
        sim_related = np.dot(emb_phone, emb_related)
        sim_unrelated = np.dot(emb_phone, emb_unrelated)
        assert sim_related > sim_unrelated

    def test_build_and_search(self, searcher, tmp_path):
        """Build mini index → search → phải trả ra kết quả."""
        # Tạo sample JSONL
        docs = [
            {"id": "v1", "title": "iPhone 15 Pro Max 256GB",
             "title_segmented": "iphone 15 pro max 256gb"},
            {"id": "v2", "title": "Samsung Galaxy S24 Ultra",
             "title_segmented": "samsung galaxy s24 ultra"},
            {"id": "v3", "title": "Tai nghe Bluetooth Sony",
             "title_segmented": "tai_nghe bluetooth sony"},
            {"id": "v4", "title": "Bàn làm việc gỗ tự nhiên",
             "title_segmented": "bàn làm_việc gỗ tự_nhiên"},
        ]

        data_file = tmp_path / "sample.jsonl"
        with open(data_file, "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")

        # Build index
        index_dir = str(tmp_path / "vector_index")
        searcher.build_index(str(data_file), index_dir, batch_size=4)

        # Search
        results = searcher.search("điện thoại iPhone", top_k=3)

        assert len(results) > 0
        assert len(results) <= 3

        # Kết quả phải trả về tuple (doc_id, score)
        for doc_id, score in results:
            assert isinstance(doc_id, str)
            assert isinstance(score, float)

    def test_search_top_k(self, searcher, tmp_path):
        """top_k=2 phải trả về đúng 2 kết quả."""
        # Tạo sample JSONL
        docs = [
            {"id": "t1", "title_segmented": "iphone 15"},
            {"id": "t2", "title_segmented": "samsung s24"},
            {"id": "t3", "title_segmented": "xiaomi 14"},
        ]

        data_file = tmp_path / "top_k_test.jsonl"
        with open(data_file, "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")

        index_dir = str(tmp_path / "top_k_index")
        searcher.build_index(str(data_file), index_dir, batch_size=4)

        results = searcher.search("điện thoại", top_k=2)
        assert len(results) == 2

    def test_search_relevance_ranking(self, searcher, tmp_path):
        """Kết quả search phải được sắp xếp giảm dần theo score."""
        docs = [
            {"id": "r1", "title_segmented": "iPhone 15 Pro Max"},
            {"id": "r2", "title_segmented": "ốp lưng iPhone"},
            {"id": "r3", "title_segmented": "bàn ghế văn phòng"},
        ]

        data_file = tmp_path / "rank_test.jsonl"
        with open(data_file, "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")

        index_dir = str(tmp_path / "rank_index")
        searcher.build_index(str(data_file), index_dir, batch_size=4)

        results = searcher.search("iPhone 15", top_k=3)
        scores = [s for _, s in results]

        # Scores phải giảm dần
        assert scores == sorted(scores, reverse=True)
