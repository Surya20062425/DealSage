"""
Meesho Scraper
Implements BaseScraper for Meesho (India).
"""
from typing import List
from bs4 import BeautifulSoup
from models.product import ProductListing, AvailabilityStatus
from scrapers.base import BaseScraper


class MeeshoScraper(BaseScraper):
    """Scraper for Meesho marketplace."""

    def __init__(self, timeout: int = 30, use_mock: bool = False):
        super().__init__("Meesho", timeout)
        self.use_mock = use_mock

    @property
    def base_url(self) -> str:
        return "https://www.meesho.com"

    def _build_search_url(self, query: str) -> str:
        from urllib.parse import quote_plus
        return f"{self.base_url}/search?q={quote_plus(query)}"

    async def search(self, query: str, max_results: int = 5) -> List[ProductListing]:
        if self.use_mock:
            return self._mock_search(query)
        url = self._build_search_url(query)
        try:
            resp = await self._session.get(url)
            resp.raise_for_status()
            return self._parse_search_results(resp.text, max_results)
        except Exception as e:
            print(f"[Meesho] Scraping failed: {e}. Returning mock data.")
            return self._mock_search(query)

    def _parse_search_results(self, html: str, max_results: int) -> List[ProductListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        containers = soup.select(".sc-bxivhb") or soup.select("[data-testid='product-card']")
        for container in containers[:max_results]:
            try:
                title = self._safe_select(container, [".sc-EHOje", "h4", ".product-title"])
                if not title:
                    continue
                price_raw = self._safe_select(container, [".sc-ifAKCX", ".price", ".sc-bxivhb"])
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
                    platform="Meesho",
                    title=title,
                    price=price,
                    currency="INR",
                    availability=AvailabilityStatus.IN_STOCK,
                    image_url=img,
                    product_url=link,
                    raw_metadata={}
                ))
            except Exception as e:
                print(f"[Meesho] Parse error: {e}")
                continue
        return listings

    async def fetch_reviews(self, product_url: str, max_reviews: int = 20) -> List[dict]:
        if self.use_mock or not product_url:
            return self._mock_reviews(max_reviews)
        try:
            resp = await self._session.get(product_url)
            soup = BeautifulSoup(resp.text, "lxml")
            reviews = []
            for item in soup.select(".review-card")[:max_reviews]:
                body = self._safe_select(item, [".review-text"])
                title = self._safe_select(item, [".review-title"])
                reviews.append({"body": body or "", "title": title, "rating": None, "source_platform": "Meesho"})
            return reviews
        except Exception as e:
            print(f"[Meesho] Review fetch failed: {e}")
            return self._mock_reviews(max_reviews)

    def _mock_search(self, query: str) -> List[ProductListing]:
        return [
            ProductListing(
                platform="Meesho",
                title=f"{query} - Meesho Bestseller",
                price=899.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/F43397/FFFFFF?text=Meesho",
                product_url="https://meesho.com/p/abc123",
                rating_aggregate=4.2,
                review_count=567,
                raw_metadata={"mock": True}
            ),
            ProductListing(
                platform="Meesho",
                title=f"{query} - Wholesale Price",
                price=749.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/F43397/FFFFFF?text=Meesho+Wholesale",
                product_url="https://meesho.com/p/xyz789",
                rating_aggregate=3.9,
                review_count=234,
                raw_metadata={"mock": True}
            ),
        ]

    def _mock_reviews(self, count: int = 5) -> List[dict]:
        bodies = [
            "Very affordable price on Meesho. Quality is decent for the cost.",
            "Good for reselling. Margins are excellent on this platform.",
            "Delivery took a bit long but product arrived safely.",
            "Meesho packaging is simple but effective. No complaints.",
            "Great for bulk orders. Will order again for my business.",
        ]
        return [{"body": bodies[i % len(bodies)], "rating": 4.0, "title": f"Meesho Review {i+1}", "source_platform": "Meesho"} for i in range(count)]
