import time
from src.search.engine import SearchEngine

engine = SearchEngine('data/index', 'data/MASTER_DATA_CLEAN.jsonl')
engine.load()

def test_params(query, k1, b):
    print(f"\\n--- Testing '{query}' with k1={k1}, b={b} ---")
    engine.ranker.k1 = k1
    engine.ranker.b = b
    res = engine.search(query, top_k=6)
    for r in res:
        print(f"{r['bm25_score']:.2f} | {r['price']} | {r['title'][:80]}")

queries = ["iphone 17", "iphone 15 pro max", "samsung galaxy s24 ultra"]

for q in queries:
    test_params(q, 1.5, 0.75) # Baseline
    test_params(q, 1.2, 0.90) # Penalize length more
    test_params(q, 0.8, 0.95) # Reduce TF impact
    test_params(q, 0.5, 1.0)  # Strong anti-stuffing
