"""
Unit tests for HybridSearcher.
Milestone 3: Hybrid Ranking (BM25 + Vector)

Tests sử dụng mock objects để test logic kết hợp score,
không cần load model thật.
"""
import pytest
from src.ranking.vector import HybridSearcher


class MockBM25Ranker:
    """Mock BM25Ranker trả về kết quả cố định."""

    def rank(self, query, top_k=10):
        # Giả lập BM25 scores (thường 0-50)
        return [
            ("doc1", 45.0),
            ("doc2", 30.0),
            ("doc3", 20.0),
            ("doc4", 10.0),
        ][:top_k]


class MockVectorSearcher:
    """Mock VectorSearcher trả về kết quả cố định."""

    def search(self, query, top_k=10):
        # Giả lập Vector similarity scores (0-1)
        return [
            ("doc2", 0.95),   # doc2 xếp cao nhất về semantic
            ("doc1", 0.80),
            ("doc5", 0.75),   # doc5 chỉ có trong vector results
            ("doc3", 0.60),
        ][:top_k]


class TestHybridSearcher:
    """Test suite cho HybridSearcher."""

    @pytest.fixture
    def hybrid(self):
        """Fixture: HybridSearcher với mock components."""
        return HybridSearcher(
            bm25_ranker=MockBM25Ranker(),
            vector_searcher=MockVectorSearcher(),
            bm25_weight=0.5,
            vector_weight=0.5,
        )

    def test_hybrid_returns_results(self, hybrid):
        """Hybrid search phải trả về danh sách kết quả không rỗng."""
        results = hybrid.search("iphone 15", top_k=5)

        assert len(results) > 0
        assert len(results) <= 5

    def test_hybrid_returns_tuples(self, hybrid):
        """Output phải đúng contract: list[(str, float)]."""
        results = hybrid.search("iphone", top_k=3)

        for doc_id, score in results:
            assert isinstance(doc_id, str)
            assert isinstance(score, (int, float))

    def test_hybrid_returns_sorted(self, hybrid):
        """Kết quả phải sắp xếp giảm dần theo hybrid score."""
        results = hybrid.search("iphone", top_k=5)
        scores = [s for _, s in results]

        assert scores == sorted(scores, reverse=True)

    def test_hybrid_includes_both_sources(self, hybrid):
        """Hybrid phải chứa kết quả từ cả BM25 và Vector."""
        results = hybrid.search("iphone", top_k=5)
        result_ids = [doc_id for doc_id, _ in results]

        # doc1 từ BM25, doc5 chỉ từ Vector
        assert "doc1" in result_ids  # Có trong cả BM25 và Vector
        assert "doc5" in result_ids  # Chỉ có trong Vector results

    def test_dynamic_weights_bm25_heavy(self, hybrid):
        """Query chứa nhiều thông số kỹ thuật (iphone, 15, pro, max, gb) -> Ưu tiên BM25."""
        w_bm25, w_vector = hybrid._analyze_query_weights("iphone 15 pro max 256gb")
        assert w_bm25 == 0.8
        assert w_vector == 0.2

    def test_dynamic_weights_vector_heavy(self, hybrid):
        """Query dài và chứa ngữ nghĩa (không chứa mã máy) -> Ưu tiên Vector."""
        # Query: 6 từ, không hề có số/mã
        w_bm25, w_vector = hybrid._analyze_query_weights("điện thoại thông minh chụp ảnh đẹp")
        assert w_bm25 == 0.2
        assert w_vector == 0.8

    def test_dynamic_weights_balanced(self, hybrid):
        """Query chứa cả chữ thường và mã máy nhưng mã không thống trị."""
        # 4 từ, có "14" là mã
        w_bm25, w_vector = hybrid._analyze_query_weights("ốp lưng iphone 14")
        assert w_bm25 == 0.6
        assert w_vector == 0.4

    def test_dynamic_weights_behavior_in_search(self):
        """Trọng số động phải thay đổi thứ hạng kết quả."""
        hybrid = HybridSearcher(
            bm25_ranker=MockBM25Ranker(),
            vector_searcher=MockVectorSearcher(),
        )

        # "thông số dày đặc" -> BM25 heavy (0.8 vs 0.2)
        # Mock BM25 có "doc1" ở top 1. Mock Vector có "doc2" ở top 1.
        bm25_heavy_query = "iphone 15 pro max 256gb"
        res_bm25 = hybrid.search(bm25_heavy_query, top_k=3)

        # "câu ngữ nghĩa dài" -> Vector heavy (0.2 vs 0.8)
        vector_heavy_query = "điện thoại thông minh chụp ảnh đẹp"
        res_vector = hybrid.search(vector_heavy_query, top_k=3)

        # BM25 heavy sẽ xếp "doc1" lên đầu
        assert res_bm25[0][0] == "doc1"

        # Vector heavy sẽ xếp "doc2" lên đầu
        assert res_vector[0][0] == "doc2"
