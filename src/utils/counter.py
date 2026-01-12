import json

file_path = 'data/processed/tiki_products.jsonl'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        count = 0
        sources = {}
        for line in f:
            count += 1
            # Kiểm tra nhanh xem dòng có lỗi JSON không
            try:
                data = json.loads(line)
                src = data.get('source', 'unknown')
                sources[src] = sources.get(src, 0) + 1
            except:
                pass
                
    print(f"📊 TỔNG SỐ DOCS: {count:,}")
    print("Chi tiết nguồn:", sources)
except FileNotFoundError:
    print("Chưa có file dữ liệu nào.")