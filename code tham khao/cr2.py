import requests
import time
import random
import os
from schema_shared import ProductItem

print("📂 CWD =", os.getcwd())

# ================== CONFIG ==================
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

OUTPUT_FILE = os.path.join(DATA_FOLDER, "tiki_all.jsonl")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9",
    "Referer": "https://tiki.vn/",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

SEEN = set()

# ================== CRAWL 1 CATEGORY ==================
def crawl_tiki_category(name, cid, max_pages=50):
    print(f"\n🚀 [TIKI] START {name} ({cid})")

    for page in range(1, max_pages + 1):
        print(f"[{name}] Page {page}/{max_pages}")

        url = (
            "https://tiki.vn/api/personalish/v1/blocks/listings"
            f"?limit=40&include=advertisement"
            f"&aggregations=2&version=home-persionalized"
            f"&trackity_id=123&category={cid}&page={page}"
        )

        try:
            resp = SESSION.get(url, timeout=20)
            if resp.status_code != 200:
                print("⚠️ HTTP", resp.status_code)
                break

            items = resp.json().get("data", [])
            if not items:
                break

            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                for item in items:
                    pid = f"tiki_{item.get('id')}"
                    if pid in SEEN:
                        continue
                    SEEN.add(pid)

                    original_price = item.get("list_price") or item.get("price")

                    product = ProductItem(
                        id=pid,
                        platform="tiki",
                        title=item.get("name", ""),
                        price=int(item.get("price", 0)),
                        original_price=int(original_price or 0),
                        url="https://tiki.vn/" + item.get("url_path", ""),
                        image_url=item.get("thumbnail_url", ""),
                        category=name,
                        brand=item.get("brand_name", "No Brand"),
                    )

                    f.write(product.to_json_line() + "\n")

            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print("❌ Error:", e)
            time.sleep(3)

    print(f"✅ [TIKI] FINISH {name}")

# ================== CATEGORY LIST ==================
TIKI_CATEGORIES = [
    {"name": "GIAYNAM", "id": 1686},
    {"name": "DIENTHOAI", "id": 1789},
    {"name": "LAPTOP", "id": 8095},
    {"name": "THOITRANGNU", "id": 931},
    {"name": "TAINGHE", "id": 8215},
    # cứ thêm category vào đây
]

# ================== MAIN ==================
if __name__ == "__main__":
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    for cat in TIKI_CATEGORIES:
        crawl_tiki_category(cat["name"], cat["id"], max_pages=50)

    print("\n🎉 DONE – TIKI ONLY")
    print("📦 Output:", OUTPUT_FILE)
