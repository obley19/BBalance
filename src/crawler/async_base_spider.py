import os
import json
import asyncio
from typing import Set, Union, Dict
from abc import ABC, abstractmethod

class AsyncBaseSpider(ABC):
    """
    Abstract Base Class for Async Spiders.
    Handles output file management, deduplication (seen set), and saving.
    """
    source = "async_base"
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        
        # Setup data paths
        self.output_dir = "data/processed"
        self.output_file = os.path.join(self.output_dir, f"{self.source}_products.jsonl")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.seen: Set[str] = set()
        
    def load_existing_data(self):
        """Read existing JSONL to populate self.seen set."""
        if not os.path.exists(self.output_file):
            return
            
        print(f"🔄 [{self.source}] Loading existing data from {self.output_file}...")
        count = 0
        try:
            with open(self.output_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if "id" in data:
                            self.seen.add(data["id"])
                            count += 1
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ [{self.source}] Error loading data: {e}")
            pass
        print(f"✅ [{self.source}] Loaded {count} existing items.")

    def save_product(self, product_data: Union[Dict, object]):
        """
        Save product to file. 
        Accepts dict or ProductItem (object with to_dict method).
        """
        if hasattr(product_data, "to_dict"):
            data_dict = product_data.to_dict()
        else:
            data_dict = product_data
            
        pid = data_dict.get("id")
        if not pid:
            return # Skip invalid
            
        if pid in self.seen:
            return # Skip duplicate

        # Write to file
        try:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data_dict, ensure_ascii=False) + "\n")
            self.seen.add(pid)
        except Exception as e:
            print(f"❌ [{self.source}] Error saving product: {e}")

    @abstractmethod
    async def crawl_category(self, category_id: str, max_pages: int) -> None:
        pass
