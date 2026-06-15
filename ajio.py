"""
Ajio Scraper
Implements BaseScraper for Ajio (India - Fashion).
"""
from typing import List
from bs4 import BeautifulSoup
from models.product import ProductListing, AvailabilityStatus
from scrapers.base import BaseScraper


class AjioScraper(BaseScraper):
    """Scraper for Ajio marketplace."""

    def __init__(self, timeout: int = 30, use_mock: bool = False):
        super().__init__("Ajio", timeout)
        self.use_mock = use_mock

    @property
    def base_url(self) -> str:
        return "https://www.ajio.com"

    def _build_search_url(self, query: str) -> str:
        from urllib.parse import quote_plus
        return f"{self.base_url}/search/?text={quote_plus(query)}"

    async def search(self, query: str, max_results: int = 5) -> List[ProductListing]:
        if self.use_mock:
            return self._mock_search(query)
        url = self._build_search_url(query)
        try:
            resp = await self._session.get(url)
            resp.raise_for_status()
            return self._parse_search_results(resp.text, max_results)
        except Exception as e:
            print(f"[Ajio] Scraping failed: {e}. Returning mock data.")
            return self._mock_search(query)

    def _parse_search_results(self, html: str, max_results: int) -> List[ProductListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        containers = soup.select(".item") or soup.select("[data-testid='product-card']")
        for container in containers[:max_results]:
            try:
                title = self._safe_select(container, [".name", ".product-name", "h3"])
                if not title:
                    continue
                price_raw = self._safe_select(container, [".price", ".offer-price", ".net-price"])
                price = None
                if price_raw:
                    import re
                    nums = re.findall(r"[\d,]+", price_raw.replace(",", ""))
                    if nums:
                        try:
                            price = float(nums[0])
                        except ValueError:
                            pass
                img = self._safe_select(container, ["img"], attr="src")
                link = self._safe_select(container, ["a"], attr="href")
                if link and not link.startswith("http"):
                    link = f"{self.base_url}{link}"
                listings.append(ProductListing(
                    platform="Ajio",
                    title=title,
                    price=price,
                    currency="INR",
                    availability=AvailabilityStatus.IN_STOCK,
                    image_url=img,
                    product_url=link,
                    raw_metadata={}
                ))
            except Exception as e:
                print(f"[Ajio] Parse error: {e}")
                continue
        return listings

    async def fetch_reviews(self, product_url: str, max_reviews: int = 20) -> List[dict]:
        if self.use_mock or not product_url:
            return self._mock_reviews(max_reviews)
        try:
            resp = await self._session.get(product_url)
            soup = BeautifulSoup(resp.text, "lxml")
            reviews = []
            for item in soup.select(".review-item")[:max_reviews]:
                body = self._safe_select(item, [".review-text"])
                title = self._safe_select(item, [".review-title"])
                reviews.append({"body": body or "", "title": title, "rating": None, "source_platform": "Ajio"})
            return reviews
        except Exception as e:
            print(f"[Ajio] Review fetch failed: {e}")
            return self._mock_reviews(max_reviews)

    def _mock_search(self, query: str) -> List[ProductListing]:
        return [
            ProductListing(
                platform="Ajio",
                title=f"{query} - Ajio Gold",
                price=2499.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/2C4152/FFFFFF?text=Ajio",
                product_url="https://ajio.com/p/123456",
                rating_aggregate=4.1,
                review_count=345,
                raw_metadata={"mock": True}
            ),
            ProductListing(
                platform="Ajio",
                title=f"{query} - Trendy Pick",
                price=1799.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/2C4152/FFFFFF?text=Ajio+Trendy",
                product_url="https://ajio.com/p/789012",
                rating_aggregate=3.8,
                review_count=210,
                raw_metadata={"mock": True}
            ),
        ]

    def _mock_reviews(self, count: int = 5) -> List[dict]:
        bodies = [
            "Ajio has great curated collections. This product fits the aesthetic perfectly.",
            "Premium feel at a reasonable price. Ajio packaging is elegant.",
            "Delivery was within 2 days in Mumbai. Excellent Ajio service.",
            "Style is unique and not found on other platforms. Love Ajio exclusives.",
            "Quality is good but sizing runs slightly large. Check chart carefully.",
        ]
        return [{"body": bodies[i % len(bodies)], "rating": 4.0, "title": f"Ajio Review {i+1}", "source_platform": "Ajio"} for i in range(count)]
