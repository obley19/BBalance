"""
Unit tests for BM25 ranker.
"""
import pytest
from src.ranking.bm25 import BM25Ranker


class TestBM25Ranker:
    """Tests for BM25 algorithm."""
    
    @pytest.fixture
    def ranker_with_mock(self):
        """Build BM25Ranker with mock index data."""
        ranker = BM25Ranker(k1=1.5, b=0.75)
        ranker.inverted_index = {
            "iphone": [("doc1", 3), ("doc2", 1)],
            "samsung": [("doc2", 2), ("doc3", 1)],
            "điện_thoại": [("doc1", 2), ("doc2", 1), ("doc3", 1)],
        }
        ranker.doc_count = 3
        ranker.doc_lengths = {"doc1": 8, "doc2": 6, "doc3": 5}
        ranker.avg_doc_length = 6.33
        return ranker

    def test_idf_rare_term_higher(self, ranker_with_mock):
        """Rare terms (fewer docs) should have higher IDF than common terms."""
        idf_rare = ranker_with_mock.compute_idf("samsung")       # 2 docs
        idf_common = ranker_with_mock.compute_idf("điện_thoại")  # 3 docs
        assert idf_rare > idf_common

    def test_idf_unknown_term_zero(self, ranker_with_mock):
        """Non-existent term -> IDF = 0."""
        assert ranker_with_mock.compute_idf("xyz_nonexist") == 0.0

    def test_rank_returns_sorted(self, ranker_with_mock):
        """Results must be sorted descending by score."""
        results = ranker_with_mock.rank("iphone điện_thoại", top_k=3)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_rank_top_k(self, ranker_with_mock):
        """Must return exactly top_k results or fewer."""
        results = ranker_with_mock.rank("iphone", top_k=1)
        assert len(results) == 1

    def test_rank_returns_tuples(self, ranker_with_mock):
        """Output must follow contract: list of (str, float) tuples."""
        results = ranker_with_mock.rank("iphone", top_k=2)
        for doc_id, score in results:
            assert isinstance(doc_id, str)
            assert isinstance(score, float)
