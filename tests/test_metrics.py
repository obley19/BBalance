"""
Unit tests for Evaluation Metrics.
Milestone 3: Hữu — Evaluation System
"""
import pytest
from src.evaluation.metrics import (
    precision_at_k, recall_at_k, ndcg_at_k, mrr, f1_at_k
)


class TestPrecisionAtK:
    """Tests cho Precision@K."""

    def test_perfect_precision(self):
        """Tất cả top K đều relevant → P@K = 1.0."""
        retrieved = ["d1", "d2", "d3"]
        relevant = ["d1", "d2", "d3"]
        assert precision_at_k(retrieved, relevant, 3) == 1.0

    def test_zero_precision(self):
        """Không có relevant nào trong top K → P@K = 0."""
        retrieved = ["d4", "d5", "d6"]
        relevant = ["d1", "d2", "d3"]
        assert precision_at_k(retrieved, relevant, 3) == 0.0

    def test_partial_precision(self):
        """2 trong 5 là relevant → P@5 = 0.4."""
        retrieved = ["d1", "d4", "d2", "d5", "d6"]
        relevant = ["d1", "d2", "d3"]
        assert precision_at_k(retrieved, relevant, 5) == 0.4

    def test_k_zero(self):
        """K = 0 → P@0 = 0."""
        assert precision_at_k(["d1"], ["d1"], 0) == 0.0


class TestRecallAtK:
    """Tests cho Recall@K."""

    def test_perfect_recall(self):
        """Tìm được hết tất cả relevant → R@K = 1.0."""
        retrieved = ["d1", "d2", "d3", "d4"]
        relevant = ["d1", "d2"]
        assert recall_at_k(retrieved, relevant, 4) == 1.0

    def test_partial_recall(self):
        """Tìm được 1 trong 3 → R@K = 1/3."""
        retrieved = ["d1", "d4", "d5"]
        relevant = ["d1", "d2", "d3"]
        assert abs(recall_at_k(retrieved, relevant, 3) - 1/3) < 0.001

    def test_empty_relevant(self):
        """Không có ground truth → R@K = 0."""
        assert recall_at_k(["d1"], [], 1) == 0.0


class TestNDCGAtK:
    """Tests cho nDCG@K."""

    def test_perfect_ranking(self):
        """Tất cả relevant xếp trước → nDCG = 1.0."""
        retrieved = ["d1", "d2", "d3", "d4"]
        relevant = ["d1", "d2"]
        assert ndcg_at_k(retrieved, relevant, 4) == 1.0

    def test_zero_ndcg(self):
        """Không tìm thấy relevant nào → nDCG = 0."""
        retrieved = ["d4", "d5", "d6"]
        relevant = ["d1", "d2"]
        assert ndcg_at_k(retrieved, relevant, 3) == 0.0

    def test_ndcg_penalizes_late_relevance(self):
        """Relevant ở rank 1 tốt hơn relevant ở rank 3."""
        relevant = ["d1"]
        # d1 ở rank 1
        ndcg_top = ndcg_at_k(["d1", "d2", "d3"], relevant, 3)
        # d1 ở rank 3
        ndcg_bottom = ndcg_at_k(["d2", "d3", "d1"], relevant, 3)
        assert ndcg_top > ndcg_bottom

    def test_ndcg_range(self):
        """nDCG luôn trong [0, 1]."""
        retrieved = ["d1", "d3", "d2"]
        relevant = ["d1", "d2"]
        score = ndcg_at_k(retrieved, relevant, 3)
        assert 0.0 <= score <= 1.0


class TestMRR:
    """Tests cho Mean Reciprocal Rank."""

    def test_perfect_mrr(self):
        """Relevant luôn ở rank 1 → MRR = 1.0."""
        data = [
            (["d1", "d2"], ["d1"]),
            (["d3", "d4"], ["d3"]),
        ]
        assert mrr(data) == 1.0

    def test_mixed_mrr(self):
        """Query 1: rank 1, Query 2: rank 3 → MRR = (1 + 1/3) / 2."""
        data = [
            (["d1", "d2", "d3"], ["d1"]),      # RR = 1
            (["d4", "d5", "d1"], ["d1"]),       # RR = 1/3
        ]
        expected = (1.0 + 1/3) / 2
        assert abs(mrr(data) - expected) < 0.001

    def test_no_relevant_found(self):
        """Không tìm thấy relevant → RR = 0 cho query đó."""
        data = [
            (["d4", "d5"], ["d1"]),  # RR = 0
        ]
        assert mrr(data) == 0.0

    def test_empty(self):
        """Không có query → MRR = 0."""
        assert mrr([]) == 0.0


class TestF1AtK:
    """Tests cho F1@K."""

    def test_perfect_f1(self):
        """P=1, R=1 → F1=1."""
        retrieved = ["d1", "d2"]
        relevant = ["d1", "d2"]
        assert f1_at_k(retrieved, relevant, 2) == 1.0

    def test_zero_f1(self):
        """P=0, R=0 → F1=0."""
        assert f1_at_k(["d3"], ["d1"], 1) == 0.0
