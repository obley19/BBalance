
import asyncio
import sys
import os

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.crawler.spiders.chotot_async_spider import ChototAsyncSpider

async def main():
    print("🚀 Starting Cho Tot Crawler (API Mode)...")
    
    spider = ChototAsyncSpider(max_concurrent=5)
    print(f"📂 Output file: {spider.output_file}")
    
    # Categories to crawl
    # You can pass 'laptop', 'phone', or raw IDs
    categories = ["laptop"]
    
    for cat in categories:
        # Max pages 50 => ~1000 items
        # To get 100k items, user needs loop many categories or high max_pages
        await spider.crawl_category(cat, max_pages=100)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
