"""
Reliance Digital Scraper
Implements BaseScraper for Reliance Digital (India - Electronics).
"""
from typing import List
from bs4 import BeautifulSoup
from models.product import ProductListing, AvailabilityStatus
from scrapers.base import BaseScraper


class RelianceScraper(BaseScraper):
    """Scraper for Reliance Digital marketplace."""

    def __init__(self, timeout: int = 30, use_mock: bool = False):
        super().__init__("Reliance Digital", timeout)
        self.use_mock = use_mock

    @property
    def base_url(self) -> str:
        return "https://www.reliancedigital.in"

    def _build_search_url(self, query: str) -> str:
        from urllib.parse import quote_plus
        return f"{self.base_url}/search?q={quote_plus(query)}:relevance"

    async def search(self, query: str, max_results: int = 5) -> List[ProductListing]:
        if self.use_mock:
            return self._mock_search(query)
        url = self._build_search_url(query)
        try:
            resp = await self._session.get(url)
            resp.raise_for_status()
            return self._parse_search_results(resp.text, max_results)
        except Exception as e:
            print(f"[Reliance] Scraping failed: {e}. Returning mock data.")
            return self._mock_search(query)

    def _parse_search_results(self, html: str, max_results: int) -> List[ProductListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        containers = soup.select(".product") or soup.select("[data-testid='product-card']")
        for container in containers[:max_results]:
            try:
                title = self._safe_select(container, [".product-title", "h3", ".plp-product-title"])
                if not title:
                    continue
                price_raw = self._safe_select(container, [".price", ".pdp-price", ".plp-product-price"])
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
                    platform="Reliance Digital",
                    title=title,
                    price=price,
                    currency="INR",
                    availability=AvailabilityStatus.IN_STOCK,
                    image_url=img,
                    product_url=link,
                    raw_metadata={}
                ))
            except Exception as e:
                print(f"[Reliance] Parse error: {e}")
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
                reviews.append({"body": body or "", "title": title, "rating": None, "source_platform": "Reliance Digital"})
            return reviews
        except Exception as e:
            print(f"[Reliance] Review fetch failed: {e}")
            return self._mock_reviews(max_reviews)

    def _mock_search(self, query: str) -> List[ProductListing]:
        return [
            ProductListing(
                platform="Reliance Digital",
                title=f"{query} - Reliance Digital Exclusive",
                price=26999.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/E31837/FFFFFF?text=Reliance",
                product_url="https://reliancedigital.in/p/123456",
                rating_aggregate=4.5,
                review_count=678,
                raw_metadata={"mock": True}
            ),
            ProductListing(
                platform="Reliance Digital",
                title=f"{query} - Store Pickup Available",
                price=25999.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/E31837/FFFFFF?text=Reliance+Store",
                product_url="https://reliancedigital.in/p/789012",
                rating_aggregate=4.2,
                review_count=432,
                raw_metadata={"mock": True}
            ),
        ]

    def _mock_reviews(self, count: int = 5) -> List[dict]:
        bodies = [
            "Bought from Reliance Digital store. Staff was knowledgeable and helpful.",
            "Genuine product with full manufacturer warranty. Trust Reliance Digital.",
            "Exchange offer was excellent. Saved a lot on the new purchase.",
            " EMI options made it affordable. Reliance Digital financing is smooth.",
            "Product delivered same day from nearby store. Amazing Reliance service.",
        ]
        return [{"body": bodies[i % len(bodies)], "rating": 4.0, "title": f"Reliance Review {i+1}", "source_platform": "Reliance Digital"} for i in range(count)]
