# Platform-specific spiders
from .tiki_spider import TikiSpider
from .lazada_spider import LazadaSpider
from .sendo_spider import SendoSpider
from .fptshop_spider import FPTShopSpider
from .dienmayxanh_spider import DienMayXanhSpider
from .cellphones_spider import CellphoneSSpider

# Async spiders
from .tiki_async_spider import TikiAsyncSpider
from .cellphones_async_spider import CellphoneSAsyncSpider
from .dienmayxanh_async_spider import DienMayXanhAsyncSpider
from .fptshop_async_spider import FPTShopAsyncSpider
from .lazada_async_spider import LazadaAsyncSpider
from .sendo_async_spider import SendoAsyncSpider

from .ebay_async_spider import EbayAsyncSpider

# Browser-based spider (Selenium)
from .lazada_browser_spider import LazadaBrowserSpider

__all__ = [
    'TikiSpider',
    'LazadaSpider',
    'SendoSpider',
    'FPTShopSpider',
    'DienMayXanhSpider',
    'CellphoneSSpider',
    # Async
    'TikiAsyncSpider',
    'CellphoneSAsyncSpider',
    'DienMayXanhAsyncSpider',
    'FPTShopAsyncSpider',
    'LazadaAsyncSpider',
    'SendoAsyncSpider',
    'EbayAsyncSpider',
    # Browser-based
    'LazadaBrowserSpider',
]
