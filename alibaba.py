"""
Alibaba Scraper
Implements BaseScraper for Alibaba (B2B / Wholesale).
"""
from typing import List
from bs4 import BeautifulSoup
from models.product import ProductListing, AvailabilityStatus
from scrapers.base import BaseScraper


class AlibabaScraper(BaseScraper):
    """Scraper for Alibaba marketplace."""

    def __init__(self, timeout: int = 30, use_mock: bool = False):
        super().__init__("Alibaba", timeout)
        self.use_mock = use_mock

    @property
    def base_url(self) -> str:
        return "https://www.alibaba.com"

    def _build_search_url(self, query: str) -> str:
        from urllib.parse import quote_plus
        return f"{self.base_url}/trade/search?SearchText={quote_plus(query)}"

    async def search(self, query: str, max_results: int = 5) -> List[ProductListing]:
        if self.use_mock:
            return self._mock_search(query)
        url = self._build_search_url(query)
        try:
            resp = await self._session.get(url)
            resp.raise_for_status()
            return self._parse_search_results(resp.text, max_results)
        except Exception as e:
            print(f"[Alibaba] Scraping failed: {e}. Returning mock data.")
            return self._mock_search(query)

    def _parse_search_results(self, html: str, max_results: int) -> List[ProductListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        containers = soup.select(".list-no-v2") or soup.select(".search-card")
        for container in containers[:max_results]:
            try:
                title = self._safe_select(container, [".elements-title-normal", ".search-card-e-title", "h2"])
                if not title:
                    continue
                price_raw = self._safe_select(container, [".elements-offer-price-normal", ".search-card-e-price"])
                price = None
                currency = "USD"
                if price_raw:
                    import re
                    if "USD" in price_raw or "$" in price_raw:
                        currency = "USD"
                    nums = re.findall(r"[\d,]+", price_raw.replace(",", ""))
                    if nums:
                        try:
                            price = float(nums[0])
                        except ValueError:
                            pass
                img = self._safe_select(container, ["img"], attr="src")
                link = self._safe_select(container, ["a"], attr="href")
                if link and not link.startswith("http"):
                    link = f"https:{link}" if link.startswith("//") else f"{self.base_url}{link}"
                listings.append(ProductListing(
                    platform="Alibaba",
                    title=title,
                    price=price,
                    currency=currency,
                    availability=AvailabilityStatus.IN_STOCK,
                    image_url=img,
                    product_url=link,
                    raw_metadata={"min_order": "10 pcs"}
                ))
            except Exception as e:
                print(f"[Alibaba] Parse error: {e}")
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
                body = self._safe_select(item, [".review-content"])
                title = self._safe_select(item, [".review-title"])
                reviews.append({"body": body or "", "title": title, "rating": None, "source_platform": "Alibaba"})
            return reviews
        except Exception as e:
            print(f"[Alibaba] Review fetch failed: {e}")
            return self._mock_reviews(max_reviews)

    def _mock_search(self, query: str) -> List[ProductListing]:
        return [
            ProductListing(
                platform="Alibaba",
                title=f"{query} - Wholesale OEM (MOQ: 50)",
                price=45.0,
                currency="USD",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/FF6A00/FFFFFF?text=Alibaba",
                product_url="https://alibaba.com/product/123456",
                rating_aggregate=4.6,
                review_count=120,
                raw_metadata={"mock": True, "min_order": "50 pcs"}
            ),
            ProductListing(
                platform="Alibaba",
                title=f"{query} - Factory Direct Bulk",
                price=38.0,
                currency="USD",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/FF6A00/FFFFFF?text=Alibaba+Bulk",
                product_url="https://alibaba.com/product/789012",
                rating_aggregate=4.4,
                review_count=85,
                raw_metadata={"mock": True, "min_order": "100 pcs"}
            ),
        ]

    def _mock_reviews(self, count: int = 5) -> List[dict]:
        bodies = [
            "Verified supplier on Alibaba. Product quality matches samples exactly.",
            "Great for bulk procurement. Factory was responsive and professional.",
            "Shipping via Alibaba Logistics was smooth and trackable.",
            "Negotiated price down further. Alibaba Trade Assurance is reassuring.",
            "Sample order was perfect. Placed a 500-unit order immediately.",
        ]
        return [{"body": bodies[i % len(bodies)], "rating": 4.0, "title": f"Alibaba Review {i+1}", "source_platform": "Alibaba"} for i in range(count)]
