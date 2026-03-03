# SPIMI Indexer - Xây dựng chỉ mục ngược
# Thuật toán Single-Pass In-Memory Indexing

import json
import os
import pickle
from collections import defaultdict


class SPIMIIndexer:
    """
    Class triển khai thuật toán SPIMI để xây dựng inverted index.
    Chia nhỏ dữ liệu thành các block, index trên RAM rồi ghi xuống đĩa.
    """

    def __init__(self, block_size_mb=500):
        # Giới hạn bộ nhớ cho mỗi block (đơn vị MB)
        self.block_size_mb = block_size_mb
        
        # Dictionary chính lưu inverted index tạm trên RAM
        # Cấu trúc: { "term": [(doc_id, tf), (doc_id, tf), ...] }
        self.current_block = defaultdict(list)
        
        self.block_count = 0
        self.current_memory = 0  # ước tính RAM đang dùng (bytes)
        
        # Lưu chiều dài mỗi document (cần cho BM25 sau này)
        self.doc_lengths = {}

    def tokenize(self, text):
        """Tách text thành danh sách token, bỏ token quá ngắn."""
        if not text:
            return []
        # Chuyển về chữ thường rồi tách theo khoảng trắng
        tokens = text.lower().split()
        # Bỏ các token chỉ có 1 ký tự (nhiễu)
        result = []
        for t in tokens:
            if len(t) > 1:
                result.append(t)
        return result

    def add_document(self, doc_id, tokens):
        """Thêm 1 document vào block hiện tại trên RAM."""
        
        # Bước 1: Đếm tần suất xuất hiện của mỗi từ trong document này (TF)
        tf_map = {}
        for token in tokens:
            if token in tf_map:
                tf_map[token] += 1
            else:
                tf_map[token] = 1

        # Bước 2: Thêm posting (doc_id, tf) vào inverted index
        for term, tf in tf_map.items():
            self.current_block[term].append((doc_id, tf))

        # Bước 3: Ghi lại chiều dài document = tổng số token
        self.doc_lengths[doc_id] = len(tokens)

        # Bước 4: Ước tính bộ nhớ tăng thêm (~50 bytes mỗi posting)
        self.current_memory += len(tf_map) * 50

    def is_block_full(self):
        """Kiểm tra block đã chạm giới hạn bộ nhớ chưa."""
        limit = self.block_size_mb * 1024 * 1024  # đổi MB sang bytes
        return self.current_memory >= limit

    def write_block_to_disk(self, output_dir):
        """Ghi block hiện tại xuống đĩa, giải phóng RAM."""
        
        os.makedirs(output_dir, exist_ok=True)

        # Sắp xếp các term theo thứ tự alphabet (yêu cầu của SPIMI)
        sorted_block = {}
        for key in sorted(self.current_block.keys()):
            sorted_block[key] = self.current_block[key]

        # Ghi ra file pickle
        block_path = os.path.join(output_dir, f"block_{self.block_count}.pkl")
        with open(block_path, 'wb') as f:
            pickle.dump(sorted_block, f)

        print(f"  Block {self.block_count}: {len(sorted_block)} terms, "
              f"~{self.current_memory / 1024 / 1024:.1f}MB")

        # Reset lại block trên RAM để tiếp tục đọc dữ liệu
        self.current_block = defaultdict(list)
        self.current_memory = 0
        self.block_count += 1

        return block_path

    def build_index(self, documents_path, output_path):
        """
        Pipeline chính: đọc JSONL -> tokenize -> tạo block -> merge.
        """
        print(f"SPIMI Indexing starting on: {documents_path}")

        block_files = []
        doc_count = 0
        blocks_dir = os.path.join(output_path, "blocks")
        os.makedirs(blocks_dir, exist_ok=True)

        # Đọc file JSONL từng dòng (streaming - không load hết vào RAM)
        with open(documents_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    doc = json.loads(line.strip())
                    doc_id = doc.get('id', '')

                    # Ưu tiên dùng title đã tách từ (PyVi), fallback sang title gốc
                    text = doc.get('title_segmented')
                    if not text:
                        text = doc.get('title_clean', '')
                    if not text:
                        text = doc.get('title', '')

                    tokens = self.tokenize(text)
                    if not tokens:
                        continue

                    self.add_document(doc_id, tokens)
                    doc_count += 1

                    # In tiến độ mỗi 100k docs
                    if doc_count % 100000 == 0:
                        print(f"  Processed {doc_count} documents...")

                    # Kiểm tra RAM đầy -> flush xuống đĩa
                    if self.is_block_full():
                        block_path = self.write_block_to_disk(blocks_dir)
                        block_files.append(block_path)

                except json.JSONDecodeError:
                    continue

        # Ghi nốt block cuối cùng (chưa đầy nhưng vẫn còn data)
        if self.current_block:
            block_path = self.write_block_to_disk(blocks_dir)
            block_files.append(block_path)

        print(f"\nExtracted {doc_count} docs into {len(block_files)} blocks.")

        # Gọi module merge để ghép các block lại
        from src.indexer.merging import n_way_merge
        final_index_path = os.path.join(output_path, "inverted_index.pkl")
        n_way_merge(block_files, final_index_path)

        # Lưu metadata cho BM25 sử dụng
        total_length = 0
        for length in self.doc_lengths.values():
            total_length += length
        avg_length = total_length / len(self.doc_lengths) if self.doc_lengths else 0

        metadata = {
            "doc_count": doc_count,
            "doc_lengths": self.doc_lengths,
            "avg_doc_length": avg_length,
        }
        metadata_path = os.path.join(output_path, "metadata.pkl")
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

        print(f"Index + Metadata saved to: {output_path}")
        return final_index_path
