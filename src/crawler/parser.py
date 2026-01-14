"""
Parser module for HTML processing and Vietnamese word segmentation.
Merged from processor/cleaner.py - Data cleaning and text normalization.
"""

import re
import html
from pyvi import ViTokenizer  # Thư viện tách từ tiếng Việt


class DataCleaner:
    """Class for cleaning and normalizing Vietnamese text data."""
    
    def __init__(self):
        # Regex để tìm tất cả các thẻ HTML (VD: <div>, <br>, </a>)
        self.html_tag_re = re.compile(r'<[^>]+>')
        
        # Regex để tìm các ký tự đặc biệt không phải chữ số hoặc chữ cái tiếng Việt/Anh
        # Giữ lại khoảng trắng để không bị dính chữ
        self.special_char_re = re.compile(r'[^\w\s\dđĐa-zA-Zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ]')

    def clean_html(self, raw_html: str) -> str:
        """
        Loại bỏ toàn bộ thẻ HTML và decode các ký tự entity (VD: &amp; -> &)
        
        Args:
            raw_html: Raw HTML string
            
        Returns:
            Cleaned text without HTML tags
        """
        if not raw_html:
            return ""
        
        # 1. Unescape HTML entities (ví dụ: &nbsp; -> space)
        text = html.unescape(raw_html)
        
        # 2. Xóa thẻ HTML bằng Regex
        text = self.html_tag_re.sub(' ', text)
        
        # 3. Xóa khoảng trắng thừa (VD: "  iPhone   " -> "iPhone")
        text = ' '.join(text.split())
        
        return text

    def normalize_text(self, text: str) -> str:
        """
        Chuẩn hóa văn bản để Indexing (Search Engine cần cái này)
        Input: "Điện thoại iPhone 14 Pro Max!"
        Output: "điện_thoại iphone 14 pro max"
        
        Args:
            text: Raw Vietnamese text
            
        Returns:
            Normalized and segmented text
        """
        if not text:
            return ""
        
        # 1. Chuyển về chữ thường
        text = text.lower()
        
        # 2. Làm sạch rác HTML trước (đề phòng)
        text = self.clean_html(text)
        
        # 3. Tách từ tiếng Việt bằng PyVi (Quan trọng cho Semantic Search)
        # VD: "tính năng" -> "tính_năng"
        text = ViTokenizer.tokenize(text)
        
        return text
    
    def remove_boilerplate(self, text: str) -> str:
        """Remove common boilerplate text from product descriptions."""
        boilerplate = "Giá sản phẩm trên Tiki đã bao gồm thuế"
        if boilerplate in text:
            return text.split(boilerplate)[0].strip()
        return text


def parse_html(html_content: str) -> dict:
    """
    Parse HTML content and extract structured data.
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        Dictionary containing extracted data
    """
    cleaner = DataCleaner()
    return {"text": cleaner.clean_html(html_content)}


def segment_vietnamese(text: str) -> str:
    """
    Perform Vietnamese word segmentation using PyVi.
    
    Args:
        text: Raw Vietnamese text
        
    Returns:
        Segmented text with words separated by underscores
    """
    return ViTokenizer.tokenize(text)


def clean_text(text: str) -> str:
    """
    Clean text by removing HTML tags, scripts, and extra whitespace.
    
    Args:
        text: Raw text with potential HTML artifacts
        
    Returns:
        Cleaned text
    """
    cleaner = DataCleaner()
    return cleaner.clean_html(text)


# --- Phần Test chạy thử ---
if __name__ == "__main__":
    cleaner = DataCleaner()
    
    # Test với đoạn mô tả bẩn
    dirty_desc = """<h5>Nội dung quảng cáo</h5>\n<p>iPhone 14 Pro Max. Bắt trọn chi tiết.</p>"""
    
    print("🔻 GỐC:", dirty_desc)
    print("✅ SAU KHI CLEAN:", cleaner.clean_html(dirty_desc))
    
    dirty_title = "Điện thoại iPhone 14 Pro Max - Hàng Chính Hãng"
    print("\n🔻 GỐC:", dirty_title)
    print("✅ SAU KHI NORMALIZE (Cho Indexer):", cleaner.normalize_text(dirty_title))
