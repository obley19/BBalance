# SPIMI (Single-Pass In-Memory Indexing) - Xây dựng inverted index
# Milestone 2: Core Search Engine

import json          # Đọc file JSONL (mỗi dòng là 1 JSON object)
import os            # Tạo thư mục, ghép đường dẫn file
import pickle        # Serialize dictionary Python ra file nhị phân (.pkl)
from collections import defaultdict  # Dict tự khởi tạo giá trị mặc định
from src.crawler.parser import DataCleaner  # Tái sử dụng bộ cleaner từ M1


class SPIMIIndexer:
    """
    Implements SPIMI algorithm for building inverted index.

    SPIMI Process:
    1. Split documents into blocks that fit in memory
    2. For each block: build in-memory index -> write to disk
    3. Merge all block indices into final inverted index
    """

    def __init__(self, block_size_mb=500):
        self.block_size_mb = block_size_mb                # Ngưỡng RAM tối đa cho 1 block
        self.current_block = defaultdict(list)             # Bộ nhớ chính: term → [(doc_id, tf)]
        self.block_count = 0                               # Đếm số block đã flush
        self.current_memory = 0                            # Ước tính RAM đang dùng (bytes)
        self.doc_lengths = {}                              # doc_id → số tokens (cho BM25)
        self.cleaner = DataCleaner()

    def tokenize(self, text):
        """Tách text thành danh sách tokens."""
        if not text:
            return []                           # Guard clause: tránh crash khi text rỗng
        tokens = text.lower().split()           # Lowercase + tách theo khoảng trắng
        return [t for t in tokens if len(t) > 1]  # Loại token 1 ký tự (nhiễu)

    def add_document(self, doc_id, tokens):
        """Thêm 1 document vào block hiện tại trên RAM."""
        # Bước 1: Đếm TF (Term Frequency) cho document này
        tf_map = defaultdict(int)
        for token in tokens:
            tf_map[token] += 1              # Đếm: "iphone" xuất hiện 3 lần → tf = 3

        # Bước 2: Ghi posting vào inverted index trên RAM
        for term, tf in tf_map.items():
            self.current_block[term].append((doc_id, tf))  # Thêm (doc_id, tf) vào postings list

        # Bước 3: Lưu chiều dài document (cho BM25 tính length normalization)
        self.doc_lengths[doc_id] = len(tokens)  # Tổng số tokens = chiều dài doc

        # Bước 4: Ước tính RAM tăng thêm
        self.current_memory += len(tf_map) * 50  # ~50 bytes/posting (tuple + overhead)

    def is_block_full(self):
        """Kiểm tra block đã đầy RAM chưa."""
        return self.current_memory >= self.block_size_mb * 1024 * 1024  # Convert MB → bytes

    def write_block_to_disk(self, output_dir):
        """Flush block hiện tại xuống ổ cứng, giải phóng RAM."""
        os.makedirs(output_dir, exist_ok=True)          # Tạo thư mục nếu chưa có

        # Sort theo alphabet trước khi ghi (yêu cầu của SPIMI để merge sau)
        sorted_block = {}
        for key in sorted(self.current_block.keys()):
            sorted_block[key] = self.current_block[key]

        block_path = os.path.join(output_dir, f"block_{self.block_count}.pkl")
        with open(block_path, 'wb') as f:
            pickle.dump(sorted_block, f)                # Serialize ra file nhị phân

        print(f"  Block {self.block_count} saved: {len(sorted_block)} unique terms")

        # Reset trạng thái RAM
        self.current_block = defaultdict(list)           # Giải phóng RAM
        self.current_memory = 0                          # Reset bộ đếm
        self.block_count += 1
        return block_path

    def build_index(self, documents_path, output_path):
        """
        Build complete inverted index from documents.
        Đọc file JSONL streaming, chia block, merge thành index cuối.
        """
        block_files = []
        doc_count = 0
        blocks_dir = os.path.join(output_path, "blocks")

        print(f"Starting SPIMI indexing from: {documents_path}")
        print(f"Block size limit: {self.block_size_mb} MB")

        # Đọc streaming từng dòng, không load hết file vào RAM
        with open(documents_path, 'r', encoding='utf-8') as f:
            for line in f:                                        # Từng dòng một = O(1) RAM
                doc = json.loads(line.strip())
                doc_id = doc.get('id', '')

                # Ưu tiên title_segmented (đã tách từ bởi PyVi ở M1)
                text = doc.get('title_segmented') or doc.get('title_clean') or doc.get('title', '')
                tokens = self.tokenize(text)

                if not tokens:                # Bỏ qua doc rỗng
                    continue

                self.add_document(doc_id, tokens)
                doc_count += 1

                # In tiến độ mỗi 100K docs
                if doc_count % 100000 == 0:
                    print(f"  Processed {doc_count} documents...")

                if self.is_block_full():                          # RAM đầy?
                    block_path = self.write_block_to_disk(blocks_dir)  # → Flush!
                    block_files.append(block_path)

        # Flush block cuối cùng (chưa đầy nhưng vẫn còn data)
        if self.current_block:
            block_path = self.write_block_to_disk(blocks_dir)
            block_files.append(block_path)

        print(f"\nTotal documents indexed: {doc_count}")
        print(f"Total blocks created: {len(block_files)}")

        # Gọi module merging để ghép các block
        from src.indexer.merging import n_way_merge
        final_index_path = os.path.join(output_path, "inverted_index.pkl")
        n_way_merge(block_files, final_index_path)

        # Lưu Metadata cho BM25 - đây là CONTRACT giữa Indexer và Ranker
        avg_len = sum(self.doc_lengths.values()) / len(self.doc_lengths) if self.doc_lengths else 0
        metadata = {
            "doc_count": doc_count,                                    # N: tổng docs
            "doc_lengths": self.doc_lengths,                           # |D|: chiều dài mỗi doc
            "avg_doc_length": avg_len,                                 # avgdl
        }
        meta_path = os.path.join(output_path, "metadata.pkl")
        with open(meta_path, 'wb') as f:
            pickle.dump(metadata, f)

        print(f"Metadata saved: {doc_count} docs, avg length: {avg_len:.1f} tokens")
        print("Indexing complete!")

        return final_index_path
