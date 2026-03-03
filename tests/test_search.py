"""
End-to-End Tests for the Search Engine pipeline.
Validates the flow: JSONL Data -> SPIMI Index -> BM25 Ranker -> SearchEngine Results.
"""
import json
import pytest
from src.indexer.spimi import SPIMIIndexer
from src.search.engine import SearchEngine


class TestSearchEngineE2E:
    """E2E Test Suite for SearchEngine."""
    
    @pytest.fixture
    def sample_system(self, tmp_path):
        """
        Fixture to set up a mini search engine environment.
        Creates sample documents, builds an index, and returns a loaded SearchEngine.
        """
        # 1. Create Sample JSONL Data
        data_file = tmp_path / "sample.jsonl"
        docs = [
            {
                "id": "s1", "title": "iPhone 15 Pro Max", 
                "title_segmented": "iphone 15 pro max", "title_clean": "iphone 15 pro max", 
                "price": 25000000, "platform": "shopee", "link": "https://shopee.vn/1"
            },
            {
                "id": "s2", "title": "Samsung Galaxy S24", 
                "title_segmented": "samsung galaxy s24", "title_clean": "samsung galaxy s24", 
                "price": 20000000, "platform": "tiki", "link": "https://tiki.vn/2"
            },
            {
                "id": "s3", "title": "Tai nghe iPhone chính hãng", 
                "title_segmented": "tai_nghe iphone chính_hãng", "title_clean": "tai nghe iphone chinh hang", 
                "price": 500000, "platform": "shopee", "link": "https://shopee.vn/3"
            },
        ]
        
        with open(data_file, "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        
        # 2. Build Index using SPIMI
        index_dir = str(tmp_path / "index")
        indexer = SPIMIIndexer(block_size_mb=100)
        indexer.build_index(str(data_file), index_dir)
        
        # 3. Create and Load Search Engine
        engine = SearchEngine(index_dir=index_dir, data_path=str(data_file))
        engine.load()
        
        return engine

    def test_search_returns_results(self, sample_system):
        """Test basic search returns expected structure and items."""
        results = sample_system.search("iphone", top_k=5)
        
        assert len(results) > 0
        # Results should be enriched dicts
        assert "bm25_score" in results[0]
        assert "title" in results[0]
        assert "platform" in results[0]

    def test_search_relevance(self, sample_system):
        """Test BM25 relevance ordering."""
        # Query "iphone" -> Doc s1 (iPhone 15 Pro Max) should rank higher than 
        # s3 (Tai nghe iPhone) due to term frequency or document length ratios.
        results = sample_system.search("iphone", top_k=5)
        
        top_ids = [r["id"] for r in results]
        assert "s1" in top_ids
        assert len(results) == 2 # Only s1 and s3 contain "iphone"

    def test_search_no_results(self, sample_system):
        """Test searching for non-existent terms returns empty list."""
        results = sample_system.search("xyznonexist", top_k=5)
        assert len(results) == 0
