"""
Flipkart Scraper
Implements BaseScraper for Flipkart (India).
"""
from typing import List
from bs4 import BeautifulSoup
from models.product import ProductListing, AvailabilityStatus
from scrapers.base import BaseScraper


class FlipkartScraper(BaseScraper):
    """Scraper for Flipkart marketplace."""

    def __init__(self, timeout: int = 30, use_mock: bool = False):
        super().__init__("Flipkart", timeout)
        self.use_mock = use_mock

    @property
    def base_url(self) -> str:
        return "https://www.flipkart.com"

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
            print(f"[Flipkart] Scraping failed: {e}. Returning mock data.")
            return self._mock_search(query)

    def _parse_search_results(self, html: str, max_results: int) -> List[ProductListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        containers = soup.select("._1AtVbE") or soup.select("[data-id]")

        for container in containers[:max_results]:
            try:
                title = self._safe_select(container, ["._4rR01T", ".s1Q9rs", "._2WkVRV"])
                if not title:
                    continue

                price_raw = self._safe_select(container, ["._30jeq3", "._1_WHN1"])
                price = None
                if price_raw:
                    import re
                    nums = re.findall(r"[\d,]+", price_raw.replace(",", ""))
                    if nums:
                        try:
                            price = float(nums[0])
                        except ValueError:
                            pass

                img = self._safe_select(container, ["._396cs4", "img"], attr="src")
                link = self._safe_select(container, ["._1fQZEK", "a._2rpwqI"], attr="href")
                if link and not link.startswith("http"):
                    link = f"{self.base_url}{link}"

                rating = self._safe_select(container, ["._3LWZlK"])
                rating_val = None
                if rating:
                    try:
                        rating_val = float(rating)
                    except ValueError:
                        pass

                listings.append(ProductListing(
                    platform="Flipkart",
                    title=title,
                    price=price,
                    currency="INR",
                    availability=AvailabilityStatus.IN_STOCK,
                    image_url=img,
                    product_url=link,
                    rating_aggregate=rating_val,
                    raw_metadata={}
                ))
            except Exception as e:
                print(f"[Flipkart] Parse error: {e}")
                continue

        return listings

    async def fetch_reviews(self, product_url: str, max_reviews: int = 20) -> List[dict]:
        if self.use_mock or not product_url:
            return self._mock_reviews(max_reviews)
        try:
            resp = await self._session.get(product_url)
            soup = BeautifulSoup(resp.text, "lxml")
            reviews = []
            for item in soup.select("._27M-vq")[:max_reviews]:
                body = self._safe_select(item, [".t-ZTKy div div"])
                title = self._safe_select(item, ["._2-N8zT"])
                reviews.append({"body": body or "", "title": title, "rating": None, "source_platform": "Flipkart"})
            return reviews
        except Exception as e:
            print(f"[Flipkart] Review fetch failed: {e}")
            return self._mock_reviews(max_reviews)

    def _mock_search(self, query: str) -> List[ProductListing]:
        return [
            ProductListing(
                platform="Flipkart",
                title=f"{query} - Flipkart Assured",
                price=24999.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/2874F0/FFFFFF?text=Flipkart",
                product_url="https://flipkart.com/p/itm123",
                rating_aggregate=4.4,
                review_count=3421,
                raw_metadata={"mock": True}
            ),
            ProductListing(
                platform="Flipkart",
                title=f"{query} - Special Price Deal",
                price=21999.0,
                currency="INR",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/2874F0/FFFFFF?text=Flipkart+Deal",
                product_url="https://flipkart.com/p/itm456",
                rating_aggregate=4.1,
                review_count=1890,
                raw_metadata={"mock": True}
            ),
        ]

    def _mock_reviews(self, count: int = 5) -> List[dict]:
        bodies = [
            "Flipkart delivery was super fast. Product is genuine and well packed.",
            "Great price during the Big Billion Days sale. Totally worth it.",
            "Build quality is solid. Flipkart Assured badge gave me confidence.",
            "Had some issues with warranty registration but product works fine.",
            "Best deal I found online. Would recommend Flipkart for this product.",
        ]
        return [{"body": bodies[i % len(bodies)], "rating": 4.0, "title": f"Flipkart Review {i+1}", "source_platform": "Flipkart"} for i in range(count)]
