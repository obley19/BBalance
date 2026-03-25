# Console App - Ứng dụng dòng lệnh tìm kiếm sản phẩm
# Milestone 2 Requirement

import os
import time
import argparse
from src.search.engine import SearchEngine


def format_price(amount):
    """Format số tiền sang dạng VNĐ."""
    try:
        if amount == 0:
            return "Lien he"
        return f"{amount:,.0f} d".replace(",", ".")
    except:
        return str(amount)


def main():
    parser = argparse.ArgumentParser(description="E-Commerce Search Engine Console")
    parser.add_argument("--mode", type=str, choices=["bm25", "hybrid"], default="bm25",
                        help="Chế độ tìm kiếm: 'bm25' (keyword cơ bản) hoặc 'hybrid' (kết hợp vector semantic)")
    args = parser.parse_args()

    print("=" * 70)
    print("  E-COMMERCE SEARCH ENGINE - Console App")
    print("=" * 70)

    index_dir = "data/index"
    data_path = "data/MASTER_DATA_CLEAN.jsonl"
    vector_index_dir = "data/vector_index"

    # Kiểm tra xem đã build index chưa
    if not os.path.exists(index_dir):
        print(f"Error: Index directory '{index_dir}' not found.")
        print("Please run build_index.py first.")
        return

    # Khởi tạo và load engine với mode được chỉ định
    engine = SearchEngine(
        index_dir=index_dir,
        data_path=data_path,
        search_mode=args.mode,
        vector_index_dir=vector_index_dir
    )

    print(f"\nLoading Search Engine in {args.mode.upper()} mode...")
    start = time.time()
    engine.load()
    print(f"Loading completed in {time.time() - start:.2f} seconds.\n")

    # Vòng lặp nhận input từ người dùng
    while True:
        print("-" * 70)
        query = input("Search (type 'exit' to quit): ").strip()

        if query.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break

        if not query:
            continue

        print(f"\nSearching for: '{query}'...")
        start = time.time()

        # Gọi search engine lấy top 10
        results = engine.search(query, top_k=10)

        search_time = time.time() - start

        if not results:
            print(f"No results found for '{query}'.")
            continue

        print(f"Found {len(results)} results in {search_time * 1000:.2f} ms:\n")

        # Hiển thị kết quả
        for i, res in enumerate(results, 1):
            title = res.get('title', 'N/A')
            price = format_price(res.get('price', 0))
            platform = res.get('platform', 'Unknown')
            score = res.get('bm25_score', 0)
            link = res.get('link', '')

            print(f"{i:2d}. [{platform}] {title}")
            print(f"    Price: {price}")
            print(f"    BM25 Score: {score}")
            print(f"    Link: {link}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
