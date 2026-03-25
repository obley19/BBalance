import os
import pickle
import time
from src.indexer.compression import compress_index

def main():
    print("==================================================")
    print("🗜️ COMPRESSING INVERTED INDEX... (Variable Byte)")
    print("==================================================")
    
    input_path = "data/index/inverted_index.pkl"
    output_compressed = "data/index/compressed_index.pkl"
    output_mapping = "data/index/doc_id_mapping.pkl"

    if not os.path.exists(input_path):
        print(f"Lỗi: Không tìm thấy {input_path}")
        return

    print("1. Đang nạp inverted_index gốc lên RAM...")
    start_time = time.time()
    with open(input_path, 'rb') as f:
        idx = pickle.load(f)
    print(f"   => Xong ({time.time() - start_time:.2f} giây). Số Terms: {len(idx)}")

    print("2. Đang thực thi thuật toán nén Variable Byte + Delta Encoding (vui lòng đợi vài phút)...")
    start_time = time.time()
    compressed_idx, doc_id_to_int = compress_index(idx)
    print(f"   => Nén hoàn tất! ({time.time() - start_time:.2f} giây).")

    print("3. Đang ghi file nén xuống ổ cứng...")
    with open(output_compressed, 'wb') as f:
        pickle.dump(compressed_idx, f)
    with open(output_mapping, 'wb') as f:
        pickle.dump(doc_id_to_int, f)

    # Đo kích thước để so sánh
    orig_size = os.path.getsize(input_path) / (1024*1024)
    comp_size = os.path.getsize(output_compressed) / (1024*1024)
    
    print("==================================================")
    print(f"✅ ĐÃ NÉN THÀNH CÔNG!")
    print(f"Kích thước gốc: {orig_size:.1f} MB")
    print(f"Kích thước nén: {comp_size:.1f} MB (Tiết kiệm {(orig_size-comp_size)/orig_size*100:.1f}%)")
    print("==================================================")

if __name__ == "__main__":
    main()
