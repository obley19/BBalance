
import json
import os
import glob
from datetime import datetime

# Config
DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "merged_data.jsonl")

# File specific mappings
# If the file matches key, we expect that general structure
FILES_TO_PROCESS = [
    os.path.join(DATA_DIR, "ebay_products.jsonl"),
    os.path.join(DATA_DIR, "chotot_all.jsonl"),
]

def clean_price(price):
    if isinstance(price, (int, float)):
        return int(price)
    if isinstance(price, str):
        import re
        nums = re.findall(r'\d+', price.replace('.', '').replace(',', ''))
        if nums:
            return int(nums[0])
    return 0

def normalize_row(row):
    """Normalize a single data row to common schema (MASTER_DATA_CLEAN format)."""
    # Base fields
    normalized = {
        "id": row.get("id"),
        "title": row.get("title") or row.get("name") or row.get("subject"),
        "price": clean_price(row.get("price")),
        "original_price": clean_price(row.get("original_price") or row.get("list_price") or row.get("price") or 0),
        "sold_count": int(row.get("sold_count") or row.get("all_time_quantity_sold") or 0),
        "platform": (row.get("platform") or row.get("source") or "").lower(),
        "category": row.get("category") or "",
        "brand": row.get("brand") or "No Brand",
        "link": row.get("link") or row.get("url") or row.get("product_url"),  # Support cả 'url' cũ
        "image_url": row.get("image_url") or row.get("image") or row.get("thumbnail_url"),
        # NLP fields (rỗng ban đầu, điền sau khi clean)
        "title_clean": row.get("title_clean") or "",
        "title_segmented": row.get("title_segmented") or "",
        "source_file": row.get("source_file") or "",
    }
    
    # Validation
    if not normalized["id"] or not normalized["title"]:
        return None
        
    # Ensure category is string
    if isinstance(normalized["category"], list):
        normalized["category"] = " > ".join(normalized["category"])
    
    # Normalize ID if missing platform prefix
    if normalized["platform"] and not normalized["id"].startswith(normalized["platform"]):
        normalized["id"] = f"{normalized['platform']}_{normalized['id']}"

    return normalized

def main():
    print(f"🚀 Starting normalization...")
    print(f"📂 Output: {OUTPUT_FILE}")
    
    seen_ids = set()
    total_count = 0
    skipped_count = 0
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        for file_path in FILES_TO_PROCESS:
            if not os.path.exists(file_path):
                print(f"⚠️ File not found: {file_path}")
                continue
                
            print(f"Processing: {os.path.basename(file_path)}...")
            file_count = 0
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        try:
                            line = line.strip()
                            if not line: continue
                            
                            raw_data = json.loads(line)
                            
                            # Handle wrapped structures if any (e.g. wrapper around item)
                            # Assuming flat here based on previous checks
                            
                            clean_data = normalize_row(raw_data)
                            
                            if not clean_data:
                                continue
                                
                            # Deduplicate
                            if clean_data["id"] in seen_ids:
                                skipped_count += 1
                                continue
                                
                            seen_ids.add(clean_data["id"])
                            
                            # Write
                            out_f.write(json.dumps(clean_data, ensure_ascii=False) + "\n")
                            file_count += 1
                            total_count += 1
                            
                        except Exception as e:
                            # print(f"Row error: {e}")
                            pass
            except Exception as e:
                print(f"File error {file_path}: {e}")
            
            print(f"   -> Added {file_count} items.")

    print(f"\n✅ Merging Complete!")
    print(f"📊 Total items: {total_count}")
    print(f"🗑️ Duplicates removed: {skipped_count}")

if __name__ == "__main__":
    main()
