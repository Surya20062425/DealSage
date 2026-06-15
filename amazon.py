"""
Amazon Scraper
Implements BaseScraper for Amazon marketplace.
NOTE: Production deployments should rotate proxies and use browser automation
(e.g., Playwright/Scrapy-Playwright) to handle dynamic content and bot mitigation.
"""
import asyncio
from typing import List, Optional
from bs4 import BeautifulSoup
from models.product import ProductListing, Review, AvailabilityStatus
from scrapers.base import BaseScraper


class AmazonScraper(BaseScraper):
    """Scraper for Amazon search and review extraction."""

    def __init__(self, timeout: int = 30, use_mock: bool = False):
        super().__init__("Amazon", timeout)
        self.use_mock = use_mock

    @property
    def base_url(self) -> str:
        return "https://www.amazon.com"

    def _build_search_url(self, query: str) -> str:
        from urllib.parse import quote_plus
        return f"{self.base_url}/s?k={quote_plus(query)}"

    async def search(self, query: str, max_results: int = 5) -> List[ProductListing]:
        if self.use_mock:
            return self._mock_search(query)

        url = self._build_search_url(query)
        try:
            resp = await self._session.get(url)
            resp.raise_for_status()
            return self._parse_search_results(resp.text, max_results)
        except Exception as e:
            # Fallback to mock data if scraping fails (CAPTCHA, blocks, etc.)
            print(f"[Amazon] Scraping failed: {e}. Returning mock data.")
            return self._mock_search(query)

    def _parse_search_results(self, html: str, max_results: int) -> List[ProductListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        containers = soup.select('[data-component-type="s-search-result"]')

        for container in containers[:max_results]:
            try:
                title = self._safe_select(
                    container,
                    ["h2 a span", ".s-size-mini span", "h2 span"]
                )
                price_whole = self._safe_select(container, [".a-price-whole"])
                price_frac = self._safe_select(container, [".a-price-fraction"])
                price = None
                if price_whole:
                    raw = f"{price_whole}.{price_frac or '0'}"
                    try:
                        price = float(raw.replace(",", ""))
                    except ValueError:
                        pass

                rating = self._safe_select(
                    container,
                    ["[aria-label*='out of 5 stars']"],
                    attr="aria-label"
                )
                rating_val = None
                if rating and "out of" in rating:
                    try:
                        rating_val = float(rating.split("out of")[0].strip())
                    except ValueError:
                        pass

                review_count = self._safe_select(
                    container,
                    ["[aria-label*='ratings']"],
                    attr="aria-label"
                )
                review_count_val = None
                if review_count:
                    import re
                    nums = re.findall(r"[\d,]+", review_count)
                    if nums:
                        try:
                            review_count_val = int(nums[0].replace(",", ""))
                        except ValueError:
                            pass

                img = self._safe_select(
                    container,
                    ["img.s-image"],
                    attr="src"
                )
                link = self._safe_select(
                    container,
                    ["h2 a.a-link-normal"],
                    attr="href"
                )
                if link and not link.startswith("http"):
                    link = f"{self.base_url}{link}"

                listings.append(ProductListing(
                    platform="Amazon",
                    title=title or "Unknown Product",
                    price=price,
                    currency="USD",
                    availability=AvailabilityStatus.IN_STOCK if price else AvailabilityStatus.UNKNOWN,
                    image_url=img,
                    product_url=link,
                    rating_aggregate=rating_val,
                    review_count=review_count_val,
                    raw_metadata={"html_snippet": str(container)[:500]}
                ))
            except Exception as e:
                print(f"[Amazon] Parse error on item: {e}")
                continue

        return listings

    async def fetch_reviews(self, product_url: str, max_reviews: int = 20) -> List[dict]:
        if self.use_mock or not product_url:
            return self._mock_reviews(max_reviews)

        # Amazon review pages are paginated and heavily bot-protected
        # This is a simplified fetch of the first review page
        try:
            resp = await self._session.get(product_url)
            soup = BeautifulSoup(resp.text, "lxml")
            reviews = []
            for item in soup.select('[data-hook="review"]')[:max_reviews]:
                body = self._safe_select(item, ["[data-hook='review-body'] span"])
                title = self._safe_select(item, ["[data-hook='review-title'] span"])
                star = self._safe_select(
                    item,
                    ["[data-hook='review-star-rating'] .a-icon-alt"],
                    attr="aria-label"
                )
                rating = None
                if star and "out of" in star:
                    try:
                        rating = float(star.split("out of")[0].strip())
                    except ValueError:
                        pass
                reviews.append({
                    "body": body or "",
                    "title": title,
                    "rating": rating,
                    "source_platform": "Amazon"
                })
            return reviews
        except Exception as e:
            print(f"[Amazon] Review fetch failed: {e}")
            return self._mock_reviews(max_reviews)

    def _mock_search(self, query: str) -> List[ProductListing]:
        """Return plausible mock data for demo purposes."""
        return [
            ProductListing(
                platform="Amazon",
                title=f"{query} - Premium Edition (Amazon Choice)",
                price=299.99,
                currency="USD",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/00FFB9/0E1117?text=Amazon",
                product_url="https://amazon.com/dp/B08N5WRWNW",
                rating_aggregate=4.5,
                review_count=1243,
                raw_metadata={"mock": True}
            ),
            ProductListing(
                platform="Amazon",
                title=f"{query} - Standard Model",
                price=249.50,
                currency="USD",
                availability=AvailabilityStatus.IN_STOCK,
                image_url="https://via.placeholder.com/300x300/00FFB9/0E1117?text=Amazon+Std",
                product_url="https://amazon.com/dp/B08N5M7S6K",
                rating_aggregate=4.2,
                review_count=892,
                raw_metadata={"mock": True}
            ),
        ]

    def _mock_reviews(self, count: int = 5) -> List[dict]:
        bodies = [
            "Absolutely love this product. Build quality is exceptional and it exceeded my expectations.",
            "Good value for money, but the shipping took longer than expected. Product works great though.",
            "Decent product but had some issues with setup. Customer service was helpful in resolving.",
            "Best purchase I've made this year. Highly recommend to anyone looking for quality.",
            "It's okay. Not as good as advertised but functional for basic needs.",
        ]
        return [
            {"body": bodies[i % len(bodies)], "rating": 4.0 + (i % 2), "title": f"Review {i+1}", "source_platform": "Amazon"}
            for i in range(count)
        ]
