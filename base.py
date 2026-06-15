"""
Base Scraper Interface
Enforces a uniform contract across all marketplace scrapers.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from models.product import ProductListing


class BaseScraper(ABC):
    """
    Abstract base for all marketplace scrapers.
    Implementations must be async-capable and return normalized ProductListing objects.
    """

    def __init__(self, platform_name: str, timeout: int = 30):
        self.platform_name = platform_name
        self.timeout = timeout
        self._session = None

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Root URL of the marketplace."""
        pass

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[ProductListing]:
        """
        Execute a search query and return normalized listings.
        Must handle HTTP transport, parsing, and normalization internally.
        """
        pass

    @abstractmethod
    async def fetch_reviews(self, product_url: str, max_reviews: int = 20) -> List[dict]:
        """
        Fetch review corpus for a specific product.
        Returns raw review dicts; normalization happens in the caller.
        """
        pass

    async def __aenter__(self):
        import httpx
        self._session = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "DNT": "1",
                "Connection": "keep-alive",
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()

    def _build_search_url(self, query: str) -> str:
        """Override to construct platform-specific search URLs."""
        from urllib.parse import quote_plus
        return f"{self.base_url}/s?k={quote_plus(query)}"

    @staticmethod
    def _safe_select(soup, selectors: list, attr: Optional[str] = None, default=None):
        """Utility: try multiple CSS selectors, optionally extract an attribute."""
        for sel in selectors:
            tag = soup.select_one(sel)
            if tag:
                if attr:
                    return tag.get(attr, default)
                return tag.get_text(strip=True)
        return default
