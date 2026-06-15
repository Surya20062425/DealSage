"""
eBay Scraper
Implements BaseScraper for eBay marketplace.
"""
from typing import List
from bs4 import BeautifulSoup
from models.product import ProductListing, AvailabilityStatus
from scrapers.base import BaseScraper


class EbayScraper(BaseScraper):
    """Scraper for eBay search and review extraction."""

    def __init__(self, timeout: int = 30, use_mock: bool = False):
        super().__init__("eBay", timeout)
        self.use_mock = use_mock

    @property
    def base_url(self) -> str:
        return "https://www.ebay.com"

    def _build_search_url(self, query: str) -> str:
        from urllib.parse import quote_plus
        return f"{self.base_url}/sch/i.html?_nkw={quote_plus(query)}"

    async def search(self, query: str, max_results: int = 5) -> List[ProductListing]:
        if self.use_mock:
            return self._mock_search(query)

        url = self._build_search_url(query)
        try:
            resp = await self._session.get(url)
            resp.raise_for_status()
            return self._parse_search_results(resp.text, max_results)
        except Exception as e:
            print(f"[eBay] Scraping failed: {e}. Returning mock data.")
            return self._mock_search(query)

    def _parse_search_results(self, html: str, max_results: int) -> List[ProductListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        # eBay uses multiple class patterns; try common ones
        containers = soup.select(".s-item__wrapper") or soup.select("[data-view='mi:1686|iid:1']")

        for container in containers[:max_results]:
            try:
                title = self._safe_select(
                    container,
                    [".s-item__title", ".s-item__title span", "h3.s-item__title"]
                )
                if not title or "Shop on eBay" in title:
                    continue

                price_raw = self._safe_select(
                    container,
                    [".s-item__price", ".s-item__sale-price", ".notranslate"]
                )
                price = None
                currency = "USD"
                if price_raw:
                    import re
                    # Extract numeric price
                    match = re.search(r"[\d,]+\.?\d*", price_raw.replace(",", ""))
                    if match:
                        try:
                            price = float(match.group())
                        except ValueError:
                            pass
                    if "EUR" in price_raw or "€" in price_raw:
                        currency = "EUR"
                    elif "GBP" in price_raw or "£" in price_raw:
                        currency = "GBP"

                img = self._safe_select(
                    container,
                    [".s-item__image-img", "img"],
                    attr="src"
                )
                link = self._safe_select(
                    container,
                    [".s-item__link", "a.s-item__link"],
                    attr="href"
                )

                rating = self._safe_select(
                    container,
                    [".s-item__reviews .clipped"],
                    attr="aria-label"
                )
                rating_val = None
                if rating and "out of" in rating:
                    try:
                        rating_val = float(rating.split("out of")[0].strip())
                    except ValueError:
                        pass

                listings.append(ProductListing(
                    platform="eBay",
                    title=title,
                    price=price,
                    currency=currency,
                    availability=AvailabilityStatus.IN_STOCK,
                    image_url=img,
                    product_url=link,
                    rating_aggregate=rating_val,
                    raw_metadata={}
                ))
            except Exception as e:
                print(f"[eBay] Parse error: {e}")
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
                body = self._safe_select(item, [".review-item-content p"])
                title = self._safe_select(item, [".review-item-title"])
                reviews.append({
                    "body": body or "",
                    "title": title,
                    "rating": None,
                    "source_platform": "eBay"
                })
            return reviews
        except Exception as e:
            print(f"[eBay] Review fetch failed: {e}")
            return self._mock_reviews(max_reviews)

    def _mock_search(self, query: str) -> List[ProductListing]:
        return [
            ProductListing(
                platform="eBay",
                title=f"{query} - Refurbished (eBay Certified)",
                price=219.00,
                currency="USD",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/FF6B00/0E1117?text=eBay",
                product_url="https://ebay.com/itm/123456789",
                rating_aggregate=4.3,
                review_count=156,
                raw_metadata={"mock": True}
            ),
            ProductListing(
                platform="eBay",
                title=f"{query} - Open Box Deal",
                price=189.99,
                currency="USD",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/FF6B00/0E1117?text=eBay+Open",
                product_url="https://ebay.com/itm/987654321",
                rating_aggregate=4.0,
                review_count=78,
                raw_metadata={"mock": True}
            ),
        ]

    def _mock_reviews(self, count: int = 5) -> List[dict]:
        bodies = [
            "Seller shipped fast and item was exactly as described. Great eBay experience.",
            "Product arrived with minor cosmetic damage but works perfectly. Good price.",
            "Not happy with the condition. Expected better for 'like new' listing.",
            "Solid deal. Would buy from this seller again without hesitation.",
            "Packaging was poor but item survived. Functionality is 100%.",
        ]
        return [
            {"body": bodies[i % len(bodies)], "rating": 4.0, "title": f"eBay Review {i+1}", "source_platform": "eBay"}
            for i in range(count)
        ]
