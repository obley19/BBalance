"""
Utility script to count and analyze documents in the dataset.
Moved from src/utils/counter.py
"""

import json
from pathlib import Path


def count_documents(file_path: str) -> dict:
    """
    Count documents in a JSONL file and analyze by source.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        Dictionary with count and source breakdown
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            count = 0
            sources = {}
            for line in f:
                count += 1
                try:
                    data = json.loads(line)
                    src = data.get('source', 'unknown')
                    sources[src] = sources.get(src, 0) + 1
                except json.JSONDecodeError:
                    pass
                    
        return {"total": count, "sources": sources}
    except FileNotFoundError:
        return {"error": "File not found"}


if __name__ == "__main__":
    # Default path - adjust as needed
    data_path = Path(__file__).parent.parent / 'data' / 'processed' / 'tiki_products.jsonl'
    
    result = count_documents(str(data_path))
    
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(f"📊 TỔNG SỐ DOCS: {result['total']:,}")
        print("Chi tiết nguồn:", result['sources'])
