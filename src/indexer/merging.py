# Merging - Ghép các block index thành 1 inverted index hoàn chỉnh

import pickle
from collections import defaultdict


def merge_two_blocks(block1, block2):
    """Ghép 2 block dictionary lại thành 1."""
    
    merged = {}

    # Lấy tất cả term từ cả 2 block
    all_terms = set(block1.keys()) | set(block2.keys())

    for term in all_terms:
        # Nối danh sách postings của cùng 1 term
        list1 = block1.get(term, [])
        list2 = block2.get(term, [])
        merged[term] = list1 + list2

    # Sắp xếp lại theo alphabet
    sorted_merged = {}
    for key in sorted(merged.keys()):
        sorted_merged[key] = merged[key]

    return sorted_merged


def n_way_merge(block_files, output_path):
    """
    Ghép tất cả các file block thành 1 inverted index cuối cùng.
    Dùng phương pháp merge tuần tự (sequential merge).
    """
    print(f"\nMerging {len(block_files)} index blocks...")

    if not block_files:
        print("No block files to merge.")
        return output_path

    # Load block đầu tiên làm base
    with open(block_files[0], 'rb') as f:
        merged = pickle.load(f)
    print(f"  Loaded base block 1/{len(block_files)}, terms: {len(merged)}")

    # Lần lượt merge từng block tiếp theo vào
    for i in range(1, len(block_files)):
        block_path = block_files[i]
        with open(block_path, 'rb') as f:
            block = pickle.load(f)

        merged = merge_two_blocks(merged, block)
        print(f"  Merged block {i+1}/{len(block_files)}, total unique terms: {len(merged)}")

    # Ghi kết quả cuối cùng
    with open(output_path, 'wb') as f:
        pickle.dump(merged, f)

    print(f"Final merged index saved with {len(merged)} unique terms.")
    return output_path
