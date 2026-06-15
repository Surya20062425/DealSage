"""
Data Models & Normalization Layer
Standardizes raw scraped data into strict, validated schemas.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class AvailabilityStatus(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"
    PREORDER = "preorder"


class Review(BaseModel):
    """Normalized review entity."""
    rating: Optional[float] = Field(None, ge=0, le=5)
    title: Optional[str] = None
    body: str
    author: Optional[str] = None
    date: Optional[datetime] = None
    verified_purchase: bool = False
    source_platform: str


class ProductListing(BaseModel):
    """
    Universal product schema.
    All scrapers must normalize raw data into this format.
    """
    platform: str = Field(..., description="Source marketplace")
    product_id: Optional[str] = None
    title: str
    price: Optional[float] = Field(None, ge=0)
    currency: str = "USD"
    availability: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    rating_aggregate: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = Field(None, ge=0)
    reviews: List[Review] = Field(default_factory=list)
    raw_metadata: dict = Field(default_factory=dict)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        mapping = {
            "$": "USD", "usd": "USD", "US$": "USD",
            "€": "EUR", "eur": "EUR",
            "£": "GBP", "gbp": "GBP",
            "¥": "JPY", "jpy": "JPY",
            "₹": "INR", "inr": "INR",
        }
        return mapping.get(v, v.upper()) if v else "USD"

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            cleaned = v.replace(",", "").replace("$", "").replace("€", "").replace("£", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    def get_price_display(self) -> str:
        if self.price is None:
            return "N/A"
        symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹"}
        sym = symbols.get(self.currency, self.currency)
        return f"{sym}{self.price:,.2f}"


class ConsensusReport(BaseModel):
    """Output from the Intelligence Layer."""
    verdict: str = Field(..., pattern="^(Buy|Wait|Skip)$")
    confidence: float = Field(..., ge=0, le=1)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    summary: str
    key_themes: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class AggregatedResult(BaseModel):
    """Final payload delivered to the Presentation Layer."""
    query: str
    listings: List[ProductListing]
    consensus: Optional[ConsensusReport] = None
    best_price: Optional[ProductListing] = None
    best_rated: Optional[ProductListing] = None
    platforms_searched: List[str] = Field(default_factory=list)
    total_reviews_analyzed: int = 0
    search_duration_ms: Optional[int] = None
