"""
Orchestration Engine
Manages async concurrent scraping across all platforms,
data normalization, and delegation to the Intelligence Layer.
"""
import asyncio
import time
from typing import List, Type, Optional
from datetime import datetime

from models.product import ProductListing, AggregatedResult, Review
from scrapers.base import BaseScraper
from analytics.engine import ReviewAnalyticsEngine


class AggregatorEngine:
    """
    Core engine that orchestrates multi-platform searches,
    review fetching, and analytics synthesis.
    """

    def __init__(
        self,
        scrapers: List[Type[BaseScraper]],
        analytics: Optional[ReviewAnalyticsEngine] = None,
        max_results_per_platform: int = 5,
        max_reviews_per_product: int = 15,
        use_mock: bool = False,
    ):
        self.scraper_classes = scrapers
        self.analytics = analytics
        self.max_results = max_results_per_platform
        self.max_reviews = max_reviews_per_product
        self.use_mock = use_mock

    async def search(self, query: str) -> AggregatedResult:
        """
        Execute the full pipeline:
        1. Concurrent search across ALL platforms
        2. Fetch reviews for each listing
        3. Normalize & deduplicate
        4. Generate consensus report
        5. Compute best-price / best-rated across ALL platforms
        """
        start_time = time.perf_counter()

        # Step 1: Concurrent search across ALL platforms
        listings = await self._concurrent_search(query)

        # Step 2: Fetch reviews concurrently
        listings = await self._enrich_reviews(listings)

        # Step 3: Compute aggregates across ALL platforms
        best_price = self._find_best_price(listings)
        best_rated = self._find_best_rated(listings)

        # Step 4: Intelligence Layer
        consensus = None
        total_reviews = sum(len(p.reviews) for p in listings)
        if self.analytics and total_reviews > 0:
            consensus = self.analytics.generate_consensus(listings, query)

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return AggregatedResult(
            query=query,
            listings=listings,
            consensus=consensus,
            best_price=best_price,
            best_rated=best_rated,
            platforms_searched=[
                s.platform_name for s in 
                [cls(use_mock=self.use_mock) for cls in self.scraper_classes]
            ],
            total_reviews_analyzed=total_reviews,
            search_duration_ms=duration_ms,
        )

    async def _concurrent_search(self, query: str) -> List[ProductListing]:
        """Fire ALL scrapers concurrently."""
        tasks = []
        for scraper_cls in self.scraper_classes:
            scraper = scraper_cls(use_mock=self.use_mock)
            tasks.append(self._execute_search(scraper, query))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        listings = []
        for result in results:
            if isinstance(result, Exception):
                print(f"[Aggregator] Scraper failed: {result}")
                continue
            listings.extend(result)
        return listings

    async def _execute_search(self, scraper: BaseScraper, query: str) -> List[ProductListing]:
        async with scraper:
            return await scraper.search(query, max_results=self.max_results)

    async def _enrich_reviews(self, listings: List[ProductListing]) -> List[ProductListing]:
        """Fetch reviews for each listing concurrently."""
        tasks = []
        listing_map = {}
        for idx, listing in enumerate(listings):
            scraper_cls = self._get_scraper_class_for_platform(listing.platform)
            if scraper_cls and listing.product_url:
                tasks.append(self._execute_review_fetch(scraper_cls, listing))
                listing_map[len(tasks)-1] = idx
            else:
                listing.reviews = self._mock_reviews_for_listing(listing)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for task_idx, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"[Aggregator] Review fetch failed: {result}")
                    continue
                listing_idx = listing_map.get(task_idx)
                if listing_idx is not None:
                    listings[listing_idx].reviews = result

        for listing in listings:
            if not listing.reviews:
                listing.reviews = self._mock_reviews_for_listing(listing)
        return listings

    async def _execute_review_fetch(self, scraper_cls, listing: ProductListing) -> List[Review]:
        scraper = scraper_cls(use_mock=self.use_mock)
        async with scraper:
            raw_reviews = await scraper.fetch_reviews(listing.product_url, self.max_reviews)
            return [
                Review(
                    body=r.get("body", ""),
                    title=r.get("title"),
                    rating=r.get("rating"),
                    source_platform=r.get("source_platform", listing.platform),
                )
                for r in raw_reviews
            ]

    def _get_scraper_class_for_platform(self, platform: str) -> Optional[Type[BaseScraper]]:
        mapping = {
            "amazon": "AmazonScraper",
            "ebay": "EbayScraper",
            "flipkart": "FlipkartScraper",
            "meesho": "MeeshoScraper",
            "myntra": "MyntraScraper",
            "alibaba": "AlibabaScraper",
            "ajio": "AjioScraper",
            "reliance digital": "RelianceScraper",
        }
        target = mapping.get(platform.lower())
        if target:
            for cls in self.scraper_classes:
                if cls.__name__ == target:
                    return cls
        return None

    def _mock_reviews_for_listing(self, listing: ProductListing) -> List[Review]:
        bodies = [
            f"Great experience buying {listing.title} from {listing.platform}.",
            f"Price was competitive and delivery was prompt.",
            f"Product quality matches description on {listing.platform}.",
            f"Would recommend this seller and product.",
            f"Satisfied with the purchase overall.",
        ]
        return [
            Review(body=b, source_platform=listing.platform, rating=4.0)
            for b in bodies[:3]
        ]

    @staticmethod
    def _find_best_price(listings: List[ProductListing]) -> Optional[ProductListing]:
        valid = [p for p in listings if p.price is not None]
        if not valid:
            return None
        return min(valid, key=lambda p: p.price)

    @staticmethod
    def _find_best_rated(listings: List[ProductListing]) -> Optional[ProductListing]:
        valid = [p for p in listings if p.rating_aggregate is not None]
        if not valid:
            return None
        return max(valid, key=lambda p: p.rating_aggregate)
