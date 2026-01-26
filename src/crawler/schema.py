from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any
import time
import json

@dataclass
class ProductItem:
    """
    Unified Product Schema for all crawler platforms.
    """
    id: str  # Unique ID: {platform}_{original_id}
    platform: str # shopee, tiki, lazada, chotot, ebay
    title: str
    price: int
    url: str
    
    # Optional fields with defaults
    original_price: Optional[int] = None
    image_url: Optional[str] = ""
    category: Optional[str] = "" # Primary category or breadcrumb
    brand: Optional[str] = "No Brand"
    
    rating: float = 0.0
    review_count: int = 0
    sold_count: int = 0
    location: str = ""
    
    crawled_at: int = field(default_factory=lambda: int(time.time()))
    extra_data: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        # Validation / Data Cleaning
        if self.original_price is None:
            self.original_price = self.price
            
        # Ensure ID is string
        self.id = str(self.id)
        
        # Clean Title (remove newlines)
        if self.title:
            self.title = self.title.strip().replace('\n', ' ').replace('\r', '')

    def to_dict(self):
        """Convert to dictionary for saving."""
        return asdict(self)
        
    def to_json_line(self):
        """Convert to JSON line string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)
