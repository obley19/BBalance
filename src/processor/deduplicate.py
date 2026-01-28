"""
Deduplicate crawled products - Keep latest version of each product.
Usage: python deduplicate.py [file_or_all]
"""

import json
import os
import sys
from datetime import datetime


def deduplicate_file(filepath: str) -> tuple[int, int]:
    """
    Deduplicate a JSONL file, keeping the latest version of each product.
    
    Returns:
        (original_count, deduplicated_count)
    """
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return 0, 0
    
    products = {}  # id -> product (keep latest by crawled_at)
    original_count = 0
    
    # Read all products
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                product = json.loads(line)
                original_count += 1
                
                pid = product.get('id')
                if not pid:
                    continue
                
                # Check if we already have this product
                if pid in products:
                    # Compare crawled_at, keep newer
                    existing = products[pid]
                    existing_time = existing.get('crawled_at', '')
                    new_time = product.get('crawled_at', '')
                    
                    if new_time > existing_time:
                        products[pid] = product
                else:
                    products[pid] = product
                    
            except json.JSONDecodeError:
                continue
    
    # Write back deduplicated products
    with open(filepath, 'w', encoding='utf-8') as f:
        for product in products.values():
            f.write(json.dumps(product, ensure_ascii=False) + '\n')
    
    return original_count, len(products)


def deduplicate_all():
    """Deduplicate all JSONL files in data/processed/"""
    data_dir = "data/processed"
    
    if not os.path.exists(data_dir):
        print(f"❌ Directory not found: {data_dir}")
        return
    
    files = [f for f in os.listdir(data_dir) if f.endswith('.jsonl')]
    
    if not files:
        print("⚠️ No JSONL files found")
        return
    
    print(f"\n{'='*60}")
    print("📊 DEDUPLICATION REPORT")
    print('='*60)
    
    total_original = 0
    total_dedup = 0
    
    for filename in sorted(files):
        filepath = os.path.join(data_dir, filename)
        original, dedup = deduplicate_file(filepath)
        
        removed = original - dedup
        pct = (removed / original * 100) if original > 0 else 0
        
        print(f"📄 {filename}")
        print(f"   Before: {original:,} | After: {dedup:,} | Removed: {removed:,} ({pct:.1f}%)")
        
        total_original += original
        total_dedup += dedup
    
    print('='*60)
    print(f"📊 TOTAL: {total_original:,} → {total_dedup:,} ({total_original - total_dedup:,} duplicates removed)")
    print('='*60)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if arg == "all":
        deduplicate_all()
    elif os.path.exists(arg):
        original, dedup = deduplicate_file(arg)
        print(f"✅ Deduplicated: {original:,} → {dedup:,} ({original - dedup:,} duplicates removed)")
    else:
        print(f"Usage:")
        print(f"  python deduplicate.py all              # Dedup all files")
        print(f"  python deduplicate.py path/to/file.jsonl  # Dedup specific file")
