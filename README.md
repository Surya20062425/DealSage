# 🛒 E-Commerce Aggregator & Review Analytics

A highly scalable, modular Python application that aggregates product listings and reviews from **8 major e-commerce platforms**, normalizes the data, and generates AI-powered consensus recommendations.

## Architecture

```
├── Presentation Layer     → Streamlit (Dark Theme)
├── Orchestration Layer    → aggregator.py (Async Engine)
├── Data Acquisition Layer → scrapers/ (BaseScraper + 8 implementations)
├── Intelligence Layer     → analytics/engine.py (LLM Consensus)
└── Data Models            → models/product.py (Pydantic)
```

## Supported Platforms

| Platform | Region | Type |
|----------|--------|------|
| Amazon | Global | Marketplace |
| eBay | Global | Marketplace |
| Flipkart | India | Marketplace |
| Meesho | India | Social Commerce |
| Myntra | India | Fashion |
| Alibaba | Global | B2B Wholesale |
| Ajio | India | Fashion |
| Reliance Digital | India | Electronics |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your OpenAI API key (optional, for AI consensus)
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Launch the app
streamlit run app.py
```

## Configuration

Dark theme is enforced via `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#00FFB9"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1F2937"
textColor = "#FFFFFF"
font = "sans serif"
```

## Features

- **Unified Product Search**: Concurrent async search across all 8 platforms
- **Data Normalization**: Standardized Pydantic schemas for all scraped data
- **Price Comparison Matrix**: Sorted by lowest price with platform badges
- **AI Consensus Engine**: LLM-generated Buy/Wait/Skip verdict with Pros/Cons
- **Review Analytics**: Aggregated sentiment analysis across all platforms
- **Direct Referral Links**: One-click "Buy Now" buttons to each platform

## Production Notes

- Set `use_mock=False` in `AggregatorEngine` for live scraping
- For production scraping, rotate proxies and use browser automation (Playwright/Scrapy)
- Respect each platform's `robots.txt` and Terms of Service
- Consider rate limiting to avoid IP blocks
