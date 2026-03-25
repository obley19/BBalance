"""
Script to build the FAISS Vector Index from cleaned data.
Milestone 3: Vector Search

Chạy 1 lần (offline) để tạo FAISS index cho semantic search.
Tương tự build_index.py cho BM25/SPIMI index.

Usage:
    python build_vector_index.py
"""
import time
from src.ranking.vector import VectorSearcher


def main():
    print("=" * 60)
    print("🧠 BUILDING FAISS VECTOR INDEX 🧠")
    print("=" * 60)

    input_file = "data/MASTER_DATA_CLEAN.jsonl"
    output_dir = "data/vector_index"

    print(f"Input:  {input_file}")
    print(f"Output: {output_dir}")
    print()

    start_time = time.time()

    # Khởi tạo VectorSearcher với PhoBERT model
    searcher = VectorSearcher(
        model_name="VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
    )

    try:
        # Build FAISS index (load model → encode → build → save)
        searcher.build_index(
            documents_path=input_file,
            output_path=output_dir,
            batch_size=256,  # Tăng nếu có GPU đủ VRAM
        )

        elapsed = time.time() - start_time
        print(f"\n✅ Vector index built successfully in {elapsed:.2f} seconds!")
        print(f"Files saved in: {output_dir}/")
        print(f"  - faiss_index.bin")
        print(f"  - doc_id_mapping.pkl")
        print(f"\nYou can now run the search engine with hybrid mode:")
        print(f"  python run_search.py --mode hybrid")

    except FileNotFoundError:
        print(f"\n❌ Error: Input file '{input_file}' not found.")
        print("Please ensure you have the processed data file.")
    except ImportError as e:
        print(f"\n❌ Error: Missing dependency: {e}")
        print("Please install: pip install sentence-transformers faiss-cpu")


if __name__ == "__main__":
    main()
