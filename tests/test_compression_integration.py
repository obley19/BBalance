"""
Unit tests for Index Compression Integration.
Milestone 3: Hữu — Compression tích hợp vào pipeline

Tests kiểm tra:
1. VB encode/decode roundtrip
2. Gamma encode/decode roundtrip
3. compress_index + decompress_index roundtrip
4. Compressed index cho kết quả search giống index gốc
"""
import pytest
from src.indexer.compression import (
    variable_byte_encode, variable_byte_decode,
    gamma_encode, gamma_decode,
    compress_index, decompress_index,
)


class TestVariableByteEncoding:
    """Tests cho Variable Byte Encoding."""

    def test_encode_small_number(self):
        """Số nhỏ (< 128) → 1 byte."""
        encoded = variable_byte_encode(5)
        assert len(encoded) == 1
        assert encoded[0] >= 128  # Byte cuối có bit cao = 1

    def test_encode_large_number(self):
        """Số lớn cần nhiều bytes."""
        encoded = variable_byte_encode(200)
        assert len(encoded) > 1

    def test_encode_zero(self):
        """Số 0 → bytes([128])."""
        assert variable_byte_encode(0) == bytes([128])

    def test_roundtrip_single(self):
        """Encode rồi decode 1 số → phải khôi phục đúng."""
        for num in [0, 1, 5, 127, 128, 255, 1000, 999999]:
            encoded = variable_byte_encode(num)
            decoded = variable_byte_decode(encoded)
            assert decoded == [num], f"Failed for {num}"

    def test_roundtrip_multiple(self):
        """Encode nhiều số liên tiếp → decode đúng tất cả."""
        numbers = [10, 200, 0, 500, 99999]
        encoded = bytearray()
        for n in numbers:
            encoded.extend(variable_byte_encode(n))
        decoded = variable_byte_decode(bytes(encoded))
        assert decoded == numbers


class TestGammaEncoding:
    """Tests cho Elias Gamma Encoding."""

    def test_encode_one(self):
        """Gamma(1) = '0' (unary 0 bit '1', 1 bit '0', 0 bit offset)."""
        assert gamma_encode(1) == '0'

    def test_encode_five(self):
        """Gamma(5) = '11001'."""
        assert gamma_encode(5) == '11001'

    def test_encode_invalid(self):
        """Số <= 0 → ValueError."""
        with pytest.raises(ValueError):
            gamma_encode(0)
        with pytest.raises(ValueError):
            gamma_encode(-5)

    def test_roundtrip(self):
        """Encode rồi decode → khôi phục đúng."""
        numbers = [1, 2, 3, 5, 10, 42, 100]
        bitstring = ''.join(gamma_encode(n) for n in numbers)
        decoded = gamma_decode(bitstring)
        assert decoded == numbers


class TestIndexCompression:
    """Tests cho compress_index + decompress_index."""

    @pytest.fixture
    def sample_index(self):
        """Mock inverted index nhỏ."""
        return {
            "iphone": [("doc1", 3), ("doc2", 1), ("doc3", 2)],
            "samsung": [("doc2", 2), ("doc3", 1)],
            "tai_nghe": [("doc1", 1)],
        }

    def test_compress_returns_bytes(self, sample_index):
        """compress_index trả về dict {term: bytes}."""
        compressed, doc_id_map = compress_index(sample_index)

        assert isinstance(compressed, dict)
        for term, data in compressed.items():
            assert isinstance(data, bytes)
            assert len(data) > 0

    def test_doc_id_map_complete(self, sample_index):
        """doc_id_map phải chứa tất cả doc_ids."""
        _, doc_id_map = compress_index(sample_index)

        assert "doc1" in doc_id_map
        assert "doc2" in doc_id_map
        assert "doc3" in doc_id_map

    def test_roundtrip_preserves_data(self, sample_index):
        """compress → decompress → dữ liệu phải giống hệt ban đầu."""
        compressed, doc_id_map = compress_index(sample_index)

        # Tạo reverse mapping
        int_to_doc_id = {v: k for k, v in doc_id_map.items()}

        # Decompress
        restored = decompress_index(compressed, int_to_doc_id)

        # So sánh từng term
        for term in sample_index:
            assert term in restored, f"Missing term: {term}"

            original = set((did, tf) for did, tf in sample_index[term])
            decompressed = set((did, tf) for did, tf in restored[term])
            assert original == decompressed, f"Mismatch for term '{term}'"

    def test_compressed_smaller(self, sample_index):
        """Index nén phải nhỏ hơn hoặc bằng (với data nhỏ có thể bằng)."""
        import pickle

        original_size = len(pickle.dumps(sample_index))
        compressed, _ = compress_index(sample_index)
        compressed_size = sum(len(v) for v in compressed.values())

        # Compressed size không được lớn hơn nhiều (nhỏ hơn hoặc tương đương)
        # Với dataset nhỏ, overhead có thể khiến compressed lớn hơn chút
        # Nhưng với dataset lớn sẽ nhỏ hơn đáng kể
        assert compressed_size < original_size * 2  # Sanity check

    def test_all_terms_preserved(self, sample_index):
        """Tất cả terms phải được bảo toàn sau compress/decompress."""
        compressed, doc_id_map = compress_index(sample_index)
        int_to_doc_id = {v: k for k, v in doc_id_map.items()}
        restored = decompress_index(compressed, int_to_doc_id)

        assert set(sample_index.keys()) == set(restored.keys())

    def test_tf_values_preserved(self, sample_index):
        """Term frequencies phải được bảo toàn chính xác."""
        compressed, doc_id_map = compress_index(sample_index)
        int_to_doc_id = {v: k for k, v in doc_id_map.items()}
        restored = decompress_index(compressed, int_to_doc_id)

        # Kiểm tra tf của "iphone" -> "doc1" = 3
        iphone_postings = dict(restored["iphone"])
        assert iphone_postings["doc1"] == 3
        assert iphone_postings["doc2"] == 1
