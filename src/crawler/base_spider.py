"""
Base Spider - Abstract base class for all platform spiders.
Provides common interface and utilities for multi-platform crawling.
"""

import json
import time
import random
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from .parser import DataCleaner
from .utils import get_random_user_agent, PLATFORM_CONFIGS


class BaseSpider(ABC):
    """Abstract base class for e-commerce platform spiders."""
    
    # Must be overridden by subclasses
    source: str = ""
    base_url: str = ""
    
    def __init__(self):
        self.cleaner = DataCleaner()
        self.config = PLATFORM_CONFIGS.get(self.source, {})
        self.rate_limit = self.config.get("rate_limit", 1.0)
        
        # Setup output paths
        self.output_dir = "data/processed"
        self.output_file = os.path.join(self.output_dir, f"{self.source}_products.jsonl")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Common headers
        self.headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    
    @abstractmethod
    def crawl_category(self, category_id: str, max_pages: int = 3) -> None:
        """
        Crawl all products in a category.
        
        Args:
            category_id: Category identifier (ID or slug)
            max_pages: Maximum number of pages to crawl
        """
        pass
    
    @abstractmethod
    def crawl_product_detail(self, product_id: str) -> Optional[dict]:
        """
        Crawl detailed information for a single product.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Raw product data dict or None if failed
        """
        pass
    
    @abstractmethod
    def parse_product(self, raw_data: dict) -> dict:
        """
        Parse raw API/HTML data into standardized schema format.
        
        Args:
            raw_data: Raw data from API or HTML parsing
            
        Returns:
            Product dict following data_schema.md format
        """
        pass
    
    def parse_category(self, raw_category) -> list[str]:
        """
        Convert raw category data to nested array format.
        
        Args:
            raw_category: Category data (string, list, or dict)
            
        Returns:
            List of category levels from general to specific
        """
        if not raw_category:
            return []
        
        # If already a list, return as-is
        if isinstance(raw_category, list):
            return [str(c).strip() for c in raw_category if c]
        
        # If string with separator, split it
        if isinstance(raw_category, str):
            # Try common separators: >, /, -
            for sep in [' > ', ' / ', ' - ', '>', '/', '-']:
                if sep in raw_category:
                    return [c.strip() for c in raw_category.split(sep) if c.strip()]
            # No separator found, return as single-item list
            return [raw_category.strip()]
        
        # If dict (nested structure), flatten it
        if isinstance(raw_category, dict):
            result = []
            current = raw_category
            while current:
                name = current.get('name') or current.get('title') or ''
                if name:
                    result.append(name)
                current = current.get('parent') or current.get('children')
                if isinstance(current, list):
                    current = current[0] if current else None
            return result
        
        return []
    
    def save_product(self, product: dict) -> None:
        """
        Save product to JSONL file (append mode).
        
        Args:
            product: Product dict in schema format
        """
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(product, ensure_ascii=False) + '\n')
        
        title_preview = product.get('title', '')[:40]
        print(f"✅ [{self.source}] Saved: {product['id']} - {title_preview}...")
    
    def sleep_random(self) -> None:
        """Sleep for a random duration to avoid rate limiting."""
        sleep_time = random.uniform(self.rate_limit * 0.5, self.rate_limit * 1.5)
        time.sleep(sleep_time)
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format."""
        return datetime.now().isoformat()
    
    def build_product_id(self, original_id) -> str:
        """Build unique product ID with platform prefix."""
        return f"{self.source}_{original_id}"
