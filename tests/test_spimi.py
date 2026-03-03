"""
Unit tests for SPIMI indexer.
"""
import os
import pickle
import tempfile
import pytest
from src.indexer.spimi import SPIMIIndexer


class TestSPIMIIndexer:
    """Tests for SPIMI algorithm."""
    
    def test_add_document(self):
        """Test adding documents to index."""
        indexer = SPIMIIndexer(block_size_mb=100)
        indexer.add_document("doc1", ["iphone", "15", "pro", "iphone"])
        
        assert "iphone" in indexer.current_block
        # iphone xuất hiện 2 lần -> tf = 2
        postings = indexer.current_block["iphone"]
        assert any(doc_id == "doc1" and tf == 2 for doc_id, tf in postings)

    def test_write_and_read_block(self):
        """Test writing block to disk."""
        indexer = SPIMIIndexer(block_size_mb=100)
        indexer.add_document("doc1", ["hello", "world"])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = indexer.write_block_to_disk(tmpdir)
            assert os.path.exists(path)
            
            with open(path, 'rb') as f:
                block = pickle.load(f)
            assert "hello" in block
            assert "world" in block

    def test_doc_lengths_tracking(self):
        """Test that document length (token count) is correctly tracked."""
        indexer = SPIMIIndexer()
        indexer.add_document("doc1", ["a", "b", "c"])
        indexer.add_document("doc2", ["x", "y"])
        
        assert indexer.doc_lengths["doc1"] == 3
        assert indexer.doc_lengths["doc2"] == 2

    def test_memory_limit_triggers_block_write(self):
        """Test that indexer respects memory limits by marking block full."""
        indexer = SPIMIIndexer(block_size_mb=0)  # 0MB means always full
        indexer.add_document("doc1", ["test"])
        assert indexer.is_block_full()
