# Evaluation Metrics — Đánh giá chất lượng tìm kiếm
# Milestone 3: Hữu — Evaluation System
#
# Cung cấp các hàm tính metric tiêu chuẩn trong Information Retrieval:
# - Precision@K
# - Recall@K
# - nDCG@K (Normalized Discounted Cumulative Gain)
# - MRR (Mean Reciprocal Rank)

import math


def precision_at_k(retrieved_ids, relevant_ids, k):
    """
    Precision@K: Trong top K kết quả, bao nhiêu % là relevant.

    Công thức: P@K = |{retrieved[:K] ∩ relevant}| / K

    Args:
        retrieved_ids: List doc_ids đã sắp xếp theo ranking
        relevant_ids: Set/List doc_ids thực sự liên quan
        k: Số kết quả để đánh giá

    Returns:
        float: Giá trị Precision@K trong [0, 1]

    Ví dụ:
        retrieved = ["d1", "d2", "d3", "d4", "d5"]
        relevant  = ["d1", "d3", "d5"]
        P@3 = |{"d1","d3"} ∩ {"d1","d3","d5"}| / 3 = 2/3 = 0.667
    """
    if k <= 0:
        return 0.0

    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_set)

    return relevant_in_top_k / k


def recall_at_k(retrieved_ids, relevant_ids, k):
    """
    Recall@K: Trong tất cả docs relevant, bao nhiêu % đã tìm được trong top K.

    Công thức: R@K = |{retrieved[:K] ∩ relevant}| / |relevant|

    Args:
        retrieved_ids: List doc_ids đã sắp xếp theo ranking
        relevant_ids: Set/List doc_ids thực sự liên quan
        k: Số kết quả để đánh giá

    Returns:
        float: Giá trị Recall@K trong [0, 1]
    """
    if k <= 0 or not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_set)

    return relevant_in_top_k / len(relevant_set)


def ndcg_at_k(retrieved_ids, relevant_ids, k):
    """
    nDCG@K: Normalized Discounted Cumulative Gain.

    Đánh giá chất lượng ranking CÓ XÉT THỨ TỰ:
    - Kết quả relevant ở vị trí cao → điểm cao hơn
    - Kết quả relevant ở vị trí thấp → điểm thấp hơn (bị "discount")

    Công thức:
        DCG@K  = Σ (rel_i / log2(i + 2))   cho i = 0..K-1
        IDCG@K = DCG khi tất cả relevant xếp đầu (best case)
        nDCG@K = DCG@K / IDCG@K

    Args:
        retrieved_ids: List doc_ids đã sắp xếp theo ranking
        relevant_ids: Set/List doc_ids thực sự liên quan
        k: Số kết quả để đánh giá

    Returns:
        float: Giá trị nDCG@K trong [0, 1]
    """
    if k <= 0 or not relevant_ids:
        return 0.0

    relevant_set = set(relevant_ids)

    # Tính DCG@K: cộng 1/log2(i+2) nếu doc ở vị trí i là relevant
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        if doc_id in relevant_set:
            dcg += 1.0 / math.log2(i + 2)

    # Tính IDCG@K: ranking lý tưởng (tất cả relevant xếp đầu)
    ideal_k = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_k))

    if idcg == 0:
        return 0.0

    return dcg / idcg


def mrr(queries_results):
    """
    MRR (Mean Reciprocal Rank): Trung bình nghịch đảo hạng.

    Đo trung bình 1/rank của kết quả relevant đầu tiên.
    MRR = 1 → Kết quả relevant luôn ở vị trí 1.
    MRR = 0 → Không tìm thấy kết quả relevant nào.

    Args:
        queries_results: List of tuples (retrieved_ids, relevant_ids)
            - retrieved_ids: List doc_ids theo ranking
            - relevant_ids: Set/List doc_ids relevant

    Returns:
        float: Giá trị MRR trong [0, 1]

    Ví dụ:
        Query 1: relevant ở rank 1 → RR = 1/1 = 1.0
        Query 2: relevant ở rank 3 → RR = 1/3 = 0.333
        MRR = (1.0 + 0.333) / 2 = 0.667
    """
    if not queries_results:
        return 0.0

    total_rr = 0.0
    for retrieved_ids, relevant_ids in queries_results:
        relevant_set = set(relevant_ids)
        rr = 0.0
        for rank, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant_set:
                rr = 1.0 / rank
                break
        total_rr += rr

    return total_rr / len(queries_results)


def f1_at_k(retrieved_ids, relevant_ids, k):
    """
    F1@K: Harmonic mean của Precision@K và Recall@K.

    Args:
        retrieved_ids: List doc_ids đã sắp xếp theo ranking
        relevant_ids: Set/List doc_ids thực sự liên quan
        k: Số kết quả để đánh giá

    Returns:
        float: Giá trị F1@K trong [0, 1]
    """
    p = precision_at_k(retrieved_ids, relevant_ids, k)
    r = recall_at_k(retrieved_ids, relevant_ids, k)

    if p + r == 0:
        return 0.0

    return 2 * p * r / (p + r)


def evaluate_search_engine(engine, ground_truth, top_k=10, search_mode="bm25"):
    """
    Đánh giá toàn bộ Search Engine trên bộ ground truth.

    Args:
        engine: SearchEngine instance đã load()
        ground_truth: Dict với key "queries", mỗi query có "query" và "relevant_docs"
        top_k: Số kết quả đánh giá
        search_mode: "bm25" hoặc "hybrid"

    Returns:
        Dict chứa các metric trung bình + chi tiết từng query
    """
    # Chuyển search mode nếu cần
    if engine.search_mode != search_mode:
        engine.set_search_mode(search_mode)

    queries = ground_truth["queries"]
    results_detail = []
    mrr_inputs = []

    for q_data in queries:
        query = q_data["query"]
        relevant = q_data["relevant_docs"]

        # Chạy search
        search_results = engine.search(query, top_k=top_k)
        retrieved = [r["id"] for r in search_results]

        # Tính metrics cho query này
        p5 = precision_at_k(retrieved, relevant, 5)
        p10 = precision_at_k(retrieved, relevant, 10)
        r10 = recall_at_k(retrieved, relevant, 10)
        ndcg10 = ndcg_at_k(retrieved, relevant, 10)
        f1_10 = f1_at_k(retrieved, relevant, 10)

        results_detail.append({
            "query": query,
            "retrieved_count": len(retrieved),
            "relevant_count": len(relevant),
            "P@5": round(p5, 4),
            "P@10": round(p10, 4),
            "R@10": round(r10, 4),
            "nDCG@10": round(ndcg10, 4),
            "F1@10": round(f1_10, 4),
        })

        mrr_inputs.append((retrieved, relevant))

    # Tính trung bình
    n = len(results_detail)
    avg = {
        "search_mode": search_mode,
        "num_queries": n,
        "avg_P@5": round(sum(r["P@5"] for r in results_detail) / n, 4) if n else 0,
        "avg_P@10": round(sum(r["P@10"] for r in results_detail) / n, 4) if n else 0,
        "avg_R@10": round(sum(r["R@10"] for r in results_detail) / n, 4) if n else 0,
        "avg_nDCG@10": round(sum(r["nDCG@10"] for r in results_detail) / n, 4) if n else 0,
        "avg_F1@10": round(sum(r["F1@10"] for r in results_detail) / n, 4) if n else 0,
        "MRR": round(mrr(mrr_inputs), 4),
    }

    return {
        "summary": avg,
        "details": results_detail,
    }
