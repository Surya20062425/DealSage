"""
Myntra Scraper
Implements BaseScraper for Myntra (India - Fashion & Lifestyle).
"""
from typing import List
from bs4 import BeautifulSoup
from models.product import ProductListing, AvailabilityStatus
from scrapers.base import BaseScraper


class MyntraScraper(BaseScraper):
    """Scraper for Myntra marketplace."""

    def __init__(self, timeout: int = 30, use_mock: bool = False):
        super().__init__("Myntra", timeout)
        self.use_mock = use_mock

    @property
    def base_url(self) -> str:
        return "https://www.myntra.com"

    def _build_search_url(self, query: str) -> str:
        from urllib.parse import quote_plus
        return f"{self.base_url}/{quote_plus(query)}"

    async def search(self, query: str, max_results: int = 5) -> List[ProductListing]:
        if self.use_mock:
            return self._mock_search(query)
        url = self._build_search_url(query)
        try:
            resp = await self._session.get(url)
            resp.raise_for_status()
            return self._parse_search_results(resp.text, max_results)
        except Exception as e:
            print(f"[Myntra] Scraping failed: {e}. Returning mock data.")
            return self._mock_search(query)

    def _parse_search_results(self, html: str, max_results: int) -> List[ProductListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        containers = soup.select(".product-base") or soup.select("[data-testid='product-wrapper']")
        for container in containers[:max_results]:
            try:
                title = self._safe_select(container, [".product-product", "h3", ".product-title"])
                if not title:
                    continue
                price_raw = self._safe_select(container, [".product-discountedPrice", ".product-price"])
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
                    platform="Myntra",
                    title=title,
                    price=price,
                    currency="INR",
                    availability=AvailabilityStatus.IN_STOCK,
                    image_url=img,
                    product_url=link,
                    raw_metadata={}
                ))
            except Exception as e:
                print(f"[Myntra] Parse error: {e}")
                continue
        return listings

    async def fetch_reviews(self, product_url: str, max_reviews: int = 20) -> List[dict]:
        if self.use_mock or not product_url:
            return self._mock_reviews(max_reviews)
        try:
            resp = await self._session.get(product_url)
            soup = BeautifulSoup(resp.text, "lxml")
            reviews = []
            for item in soup.select(".user-review")[:max_reviews]:
                body = self._safe_select(item, [".review-text"])
                title = self._safe_select(item, [".review-title"])
                reviews.append({"body": body or "", "title": title, "rating": None, "source_platform": "Myntra"})
            return reviews
        except Exception as e:
            print(f"[Myntra] Review fetch failed: {e}")
            return self._mock_reviews(max_reviews)

    def _mock_search(self, query: str) -> List[ProductListing]:
        return [
            ProductListing(
                platform="Myntra",
                title=f"{query} - Myntra Exclusive",
                price=1999.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/FF3F6C/FFFFFF?text=Myntra",
                product_url="https://myntra.com/123456",
                rating_aggregate=4.3,
                review_count=890,
                raw_metadata={"mock": True}
            ),
            ProductListing(
                platform="Myntra",
                title=f"{query} - Trending Style",
                price=1599.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/FF3F6C/FFFFFF?text=Myntra+Style",
                product_url="https://myntra.com/789012",
                rating_aggregate=4.0,
                review_count=456,
                raw_metadata={"mock": True}
            ),
        ]

    def _mock_reviews(self, count: int = 5) -> List[dict]:
        bodies = [
            "Myntra packaging is always premium. Love the unboxing experience.",
            "Fabric quality is exactly as shown in photos. Very satisfied.",
            "Size chart was accurate. Fits perfectly. Great Myntra purchase.",
            "Fast delivery and easy returns policy. Myntra never disappoints.",
            "Stylish design and good material. Worth the price on Myntra.",
        ]
        return [{"body": bodies[i % len(bodies)], "rating": 4.0, "title": f"Myntra Review {i+1}", "source_platform": "Myntra"} for i in range(count)]
