"""
Evaluation Script — Đánh giá chất lượng Search Engine.
Milestone 3: Hữu — Evaluation System

Hỗ trợ 2 chế độ:
1. --build-ground-truth: Chạy search rồi xuất kết quả để đánh giá thủ công
2. (mặc định): Chạy evaluation tự động từ ground_truth.json đã đánh giá

Usage:
    # Bước 1: Sinh file ground truth (cần đánh giá thủ công sau)
    python evaluate.py --build-ground-truth

    # Bước 2: Sau khi đánh giá thủ công, chạy evaluation
    python evaluate.py                     # BM25 only
    python evaluate.py --mode hybrid       # Hybrid mode
    python evaluate.py --mode both         # So sánh cả 2
"""

import json
import argparse
import time
import os

from src.search.engine import SearchEngine
from src.evaluation.metrics import (
    precision_at_k, recall_at_k, ndcg_at_k, mrr, f1_at_k,
    evaluate_search_engine,
)


# Danh sách test queries cho ground truth
TEST_QUERIES = [
    {"query": "iphone 15 pro max", "category": "exact_product"},
    {"query": "samsung galaxy s24", "category": "exact_product"},
    {"query": "tai nghe bluetooth", "category": "category_search"},
    {"query": "ip 15 prm", "category": "abbreviation"},
    {"query": "laptop gaming", "category": "category_search"},
    {"query": "sạc dự phòng", "category": "category_search"},
    {"query": "điện thoại giá rẻ", "category": "broad_search"},
    {"query": "macbook air m2", "category": "exact_product"},
    {"query": "ss galaxy", "category": "abbreviation"},
    {"query": "ốp lưng iphone 14", "category": "accessory"},
    {"query": "máy tính bảng", "category": "category_search"},
    {"query": "chuột không dây", "category": "category_search"},
    {"query": "xiaomi redmi note 13", "category": "exact_product"},
    {"query": "camera hành trình", "category": "category_search"},
    {"query": "apple watch", "category": "exact_product"},
]


def build_ground_truth(engine, output_path="evaluation/ground_truth.json", top_k=20):
    """
    Chạy search cho mỗi query, xuất top kết quả để đánh giá thủ công.
    Sau khi chạy, người dùng cần mở file và đánh dấu relevant/irrelevant.
    """
    print("=" * 60)
    print("📋 BUILDING GROUND TRUTH DATASET")
    print("=" * 60)

    queries_data = []

    for q in TEST_QUERIES:
        query = q["query"]
        print(f"\nQuery: '{query}'")

        results = engine.search(query, top_k=top_k)
        retrieved_ids = [r["id"] for r in results]

        # Mặc định: top 5 = relevant (cần review thủ công!)
        queries_data.append({
            "query": query,
            "category": q["category"],
            "relevant_docs": retrieved_ids[:5],
            "all_results": [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "platform": r["platform"],
                    "score": r["bm25_score"],
                    "is_relevant": i < 5,  # Đánh dấu mặc định, cần review!
                }
                for i, r in enumerate(results)
            ],
            "notes": f"Auto-generated. TOP 5 marked relevant by default. PLEASE REVIEW!"
        })

        # In top 10 để reference
        for i, r in enumerate(results[:10], 1):
            marker = "✅" if i <= 5 else "❌"
            print(f"  {marker} {i}. [{r['platform']}] {r['title'][:60]}... (score={r['bm25_score']})")

    # Lưu file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ground_truth = {
        "description": "Ground truth dataset - AUTO-GENERATED, needs manual review",
        "version": "1.0",
        "created_by": "evaluate.py --build-ground-truth",
        "queries": queries_data,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Ground truth saved: {output_path}")
    print(f"   {len(queries_data)} queries, top {top_k} results each")
    print(f"\n⚠️  IMPORTANT: Mở file và review relevance labels trước khi chạy evaluation!")


def run_evaluation(engine, ground_truth_path, search_mode="bm25"):
    """Chạy evaluation và in kết quả."""

    # Load ground truth
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)

    print(f"\n{'=' * 60}")
    print(f"📊 EVALUATION — Mode: {search_mode.upper()}")
    print(f"{'=' * 60}")

    start = time.time()
    results = evaluate_search_engine(engine, ground_truth, top_k=10, search_mode=search_mode)
    elapsed = time.time() - start

    # In summary
    summary = results["summary"]
    print(f"\nSố queries: {summary['num_queries']}")
    print(f"Thời gian: {elapsed:.2f}s")
    print()
    print(f"  {'Metric':<15} {'Value':>10}")
    print(f"  {'-'*25}")
    print(f"  {'avg P@5':<15} {summary['avg_P@5']:>10.4f}")
    print(f"  {'avg P@10':<15} {summary['avg_P@10']:>10.4f}")
    print(f"  {'avg R@10':<15} {summary['avg_R@10']:>10.4f}")
    print(f"  {'avg nDCG@10':<15} {summary['avg_nDCG@10']:>10.4f}")
    print(f"  {'avg F1@10':<15} {summary['avg_F1@10']:>10.4f}")
    print(f"  {'MRR':<15} {summary['MRR']:>10.4f}")

    # In chi tiết từng query
    print(f"\n{'─' * 70}")
    print(f"  {'Query':<30} {'P@5':>6} {'P@10':>6} {'nDCG':>7} {'R@10':>6}")
    print(f"  {'─' * 55}")
    for d in results["details"]:
        q = d["query"][:28]
        print(f"  {q:<30} {d['P@5']:>6.3f} {d['P@10']:>6.3f} {d['nDCG@10']:>7.3f} {d['R@10']:>6.3f}")

    return results


def run_comparison(engine, ground_truth_path):
    """So sánh BM25 vs Hybrid."""
    print("\n" + "=" * 60)
    print("⚔️  COMPARISON: BM25 vs HYBRID")
    print("=" * 60)

    bm25_results = run_evaluation(engine, ground_truth_path, "bm25")
    hybrid_results = run_evaluation(engine, ground_truth_path, "hybrid")

    # Bảng so sánh
    bm25 = bm25_results["summary"]
    hybrid = hybrid_results["summary"]

    print(f"\n{'=' * 60}")
    print(f"📊 SUMMARY COMPARISON")
    print(f"{'=' * 60}")
    print(f"  {'Metric':<15} {'BM25':>10} {'Hybrid':>10} {'Diff':>10}")
    print(f"  {'-'*45}")

    for metric in ["avg_P@5", "avg_P@10", "avg_R@10", "avg_nDCG@10", "avg_F1@10", "MRR"]:
        b = bm25[metric]
        h = hybrid[metric]
        diff = h - b
        symbol = "↑" if diff > 0 else ("↓" if diff < 0 else "=")
        print(f"  {metric:<15} {b:>10.4f} {h:>10.4f} {diff:>+9.4f} {symbol}")


def main():
    parser = argparse.ArgumentParser(description="Search Engine Evaluation")
    parser.add_argument("--mode", choices=["bm25", "hybrid", "both"], default="bm25",
                        help="Search mode to evaluate")
    parser.add_argument("--build-ground-truth", action="store_true",
                        help="Build ground truth dataset (step 1)")
    parser.add_argument("--ground-truth", default="evaluation/ground_truth.json",
                        help="Path to ground truth JSON file")
    args = parser.parse_args()

    # Load engine
    engine = SearchEngine(
        index_dir="data/index",
        data_path="data/MASTER_DATA_CLEAN.jsonl",
        search_mode="bm25",
        vector_index_dir="data/vector_index",
    )
    print("Loading engine...")
    engine.load()

    if args.build_ground_truth:
        build_ground_truth(engine, args.ground_truth)
    elif args.mode == "both":
        run_comparison(engine, args.ground_truth)
    else:
        run_evaluation(engine, args.ground_truth, args.mode)


if __name__ == "__main__":
    main()
