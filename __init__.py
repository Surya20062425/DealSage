"""Scraper implementations for supported marketplaces."""
from scrapers.base import BaseScraper
from scrapers.amazon import AmazonScraper
from scrapers.ebay import EbayScraper
from scrapers.flipkart import FlipkartScraper
from scrapers.meesho import MeeshoScraper
from scrapers.myntra import MyntraScraper
from scrapers.alibaba import AlibabaScraper
from scrapers.ajio import AjioScraper
from scrapers.reliance import RelianceScraper

__all__ = [
    "BaseScraper",
    "AmazonScraper",
    "EbayScraper",
    "FlipkartScraper",
    "MeeshoScraper",
    "MyntraScraper",
    "AlibabaScraper",
    "AjioScraper",
    "RelianceScraper",
]
