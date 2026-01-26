"""
Crawler Manager - Handles checkpoints and duplicate filtering.
"""

import json
import os
from datetime import datetime
from typing import Set


class CrawlState:
    """Manage crawl progress with checkpoints and duplicate filtering."""
    
    def __init__(self, state_dir: str = "data/crawl_state"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
        
        self.checkpoint_file = os.path.join(state_dir, "checkpoint.json")
        self.crawled_ids_file = os.path.join(state_dir, "crawled_ids.txt")
        
        # Load existing state
        self.checkpoint = self._load_checkpoint()
        self.crawled_ids: Set[str] = self._load_crawled_ids()
    
    def _load_checkpoint(self) -> dict:
        """Load checkpoint from file."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"completed_categories": [], "current_category": None, "last_page": 0}
    
    def _load_crawled_ids(self) -> Set[str]:
        """Load set of already crawled product IDs."""
        ids = set()
        if os.path.exists(self.crawled_ids_file):
            with open(self.crawled_ids_file, 'r', encoding='utf-8') as f:
                for line in f:
                    ids.add(line.strip())
        return ids
    
    def save_checkpoint(self, platform: str, category: str, page: int) -> None:
        """Save current crawl progress."""
        self.checkpoint = {
            "platform": platform,
            "current_category": category,
            "last_page": page,
            "completed_categories": self.checkpoint.get("completed_categories", []),
            "timestamp": datetime.now().isoformat(),
        }
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoint, f, indent=2, ensure_ascii=False)
    
    def mark_category_complete(self, platform: str, category: str) -> None:
        """Mark a category as fully crawled."""
        key = f"{platform}:{category}"
        completed = self.checkpoint.get("completed_categories", [])
        if key not in completed:
            completed.append(key)
        self.checkpoint["completed_categories"] = completed
        self.checkpoint["current_category"] = None
        self.checkpoint["last_page"] = 0
        
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoint, f, indent=2, ensure_ascii=False)
    
    def is_category_completed(self, platform: str, category: str) -> bool:
        """Check if category was already crawled."""
        key = f"{platform}:{category}"
        return key in self.checkpoint.get("completed_categories", [])
    
    def get_resume_page(self, platform: str, category: str) -> int:
        """Get the page to resume from for a category."""
        if (self.checkpoint.get("platform") == platform and 
            self.checkpoint.get("current_category") == category):
            return self.checkpoint.get("last_page", 0)
        return 0
    
    def is_crawled(self, product_id: str) -> bool:
        """Check if a product ID was already crawled."""
        return product_id in self.crawled_ids
    
    def mark_crawled(self, product_id: str) -> None:
        """Mark a product ID as crawled."""
        if product_id not in self.crawled_ids:
            self.crawled_ids.add(product_id)
            # Append to file
            with open(self.crawled_ids_file, 'a', encoding='utf-8') as f:
                f.write(product_id + '\n')
    
    def filter_new_ids(self, product_ids: list) -> list:
        """Filter out already crawled product IDs."""
        return [pid for pid in product_ids if pid not in self.crawled_ids]
    
    def get_stats(self) -> dict:
        """Get crawl statistics."""
        return {
            "total_crawled_products": len(self.crawled_ids),
            "completed_categories": len(self.checkpoint.get("completed_categories", [])),
            "current_category": self.checkpoint.get("current_category"),
            "last_page": self.checkpoint.get("last_page", 0),
        }
    
    def print_status(self) -> None:
        """Print current crawl status."""
        stats = self.get_stats()
        print("\n" + "="*50)
        print("📊 CRAWL STATUS")
        print("="*50)
        print(f"   Products crawled: {stats['total_crawled_products']:,}")
        print(f"   Categories done:  {stats['completed_categories']}")
        if stats['current_category']:
            print(f"   Current:          {stats['current_category']} (page {stats['last_page']})")
        print("="*50)
    
    def reset(self) -> None:
        """Reset all state (use carefully!)."""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        if os.path.exists(self.crawled_ids_file):
            os.remove(self.crawled_ids_file)
        self.checkpoint = {}
        self.crawled_ids = set()
        print("✅ Crawl state has been reset")


# Global instance
crawl_state = CrawlState()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            crawl_state.print_status()
        elif cmd == "reset":
            confirm = input("⚠️ This will reset all progress. Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                crawl_state.reset()
            else:
                print("Cancelled.")
    else:
        crawl_state.print_status()
