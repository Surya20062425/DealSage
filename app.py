"""
E-Commerce Aggregator & Review Analytics
Presentation Layer - Streamlit Dark Theme UI
"""
import os
import asyncio
from datetime import datetime

import streamlit as st
import pandas as pd

from aggregator import AggregatorEngine
from analytics.engine import ReviewAnalyticsEngine
from scrapers import (
    AmazonScraper, EbayScraper, FlipkartScraper,
    MeeshoScraper, MyntraScraper, AlibabaScraper,
    AjioScraper, RelianceScraper
)
from models.product import AggregatedResult

# ───────────────────────────────────────────────
# PAGE CONFIGURATION (Dark Theme enforced)
# ───────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Aggregator & Review Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────────────────────────────
# CUSTOM CSS FOR PREMIUM DARK UI
# ───────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117 !important;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #00FFB9;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #8899A6;
        text-align: center;
        margin-bottom: 2rem;
    }
    .platform-card {
        background: linear-gradient(135deg, #1F2937 0%, #162033 100%);
        border: 1px solid #2D3748;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .platform-card:hover {
        border-color: #00FFB9;
        box-shadow: 0 0 20px rgba(0, 255, 185, 0.1);
    }
    .price-tag {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00FFB9;
    }
    .verdict-buy {
        background: linear-gradient(135deg, #00FFB9, #00CC94);
        color: #0E1117;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.2rem;
        display: inline-block;
    }
    .verdict-wait {
        background: linear-gradient(135deg, #FFB800, #FF9500);
        color: #0E1117;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.2rem;
        display: inline-block;
    }
    .verdict-skip {
        background: linear-gradient(135deg, #FF4757, #FF2E43);
        color: #FFFFFF;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.2rem;
        display: inline-block;
    }
    .badge-amazon { background: #FF9900; color: #000; }
    .badge-ebay { background: #E53238; color: #FFF; }
    .badge-flipkart { background: #2874F0; color: #FFF; }
    .badge-meesho { background: #F43397; color: #FFF; }
    .badge-myntra { background: #FF3F6C; color: #FFF; }
    .badge-alibaba { background: #FF6A00; color: #FFF; }
    .badge-ajio { background: #2C4152; color: #FFF; }
    .badge-reliance { background: #E31837; color: #FFF; }
    .badge-reliance-digital { background: #E31837; color: #FFF; }
    .platform-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .rating-stars {
        color: #FFB800;
        font-size: 1.1rem;
    }
    .section-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #00FFB9, transparent);
        margin: 2rem 0;
    }
    .pros-box {
        background: rgba(0, 255, 185, 0.08);
        border-left: 4px solid #00FFB9;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    .cons-box {
        background: rgba(255, 71, 87, 0.08);
        border-left: 4px solid #FF4757;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    .stButton>button {
        background: linear-gradient(135deg, #00FFB9, #00CC94) !important;
        color: #0E1117 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 255, 185, 0.3) !important;
    }
    .metric-card {
        background: #1F2937;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #2D3748;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #00FFB9;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #8899A6;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .buy-link {
        display: inline-block;
        background: #00FFB9;
        color: #0E1117;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.85rem;
        transition: all 0.2s;
    }
    .buy-link:hover {
        background: #00CC94;
        transform: scale(1.05);
    }
    .review-card {
        background: #162033;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #00FFB9;
    }
    .review-platform {
        font-size: 0.7rem;
        color: #00FFB9;
        font-weight: 700;
        text-transform: uppercase;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .comparison-table tr:nth-child(even) { background-color: #162033; }
    .comparison-table tr:hover { background-color: #1F2937; }
    .comparison-table th {
        background-color: #1F2937;
        color: #00FFB9;
        font-weight: 700;
        padding: 1rem;
        text-align: left;
        border-bottom: 2px solid #00FFB9;
    }
    .comparison-table td {
        padding: 1rem;
        color: #FFFFFF;
        border-bottom: 1px solid #2D3748;
    }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# SIDEBAR
# ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; margin-bottom:2rem;">
        <h1 style="color:#00FFB9; font-size:1.5rem;">🛒 PriceWise</h1>
        <p style="color:#8899A6; font-size:0.8rem;">Multi-Platform E-Commerce Aggregator</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <p style="color:#8899A6; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">
            Supported Platforms
        </p>
    </div>
    """, unsafe_allow_html=True)

    platforms = [
        ("Amazon", "#FF9900", "🌐"),
        ("eBay", "#E53238", "🌐"),
        ("Flipkart", "#2874F0", "🇮🇳"),
        ("Meesho", "#F43397", "🇮🇳"),
        ("Myntra", "#FF3F6C", "🇮🇳"),
        ("Alibaba", "#FF6A00", "🌐"),
        ("Ajio", "#2C4152", "🇮🇳"),
        ("Reliance Digital", "#E31837", "🇮🇳"),
    ]

    for name, color, flag in platforms:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
            <span style="font-size:1rem;">{flag}</span>
            <span style="background:{color}; color:#FFF; padding:0.15rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:700;">
                {name}
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1F2937; margin:1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown("""
    <p style="color:#8899A6; font-size:0.7rem; text-align:center;">
        🔒 Data is normalized & aggregated in real-time.<br>
        Reviews are analyzed via AI for consensus.
    </p>
    """, unsafe_allow_html=True)

# ───────────────────────────────────────────────
# MAIN CONTENT
# ───────────────────────────────────────────────
st.markdown('<div class="main-header">E-Commerce Aggregator & Review Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Compare prices, ratings, and AI-powered reviews across 8 major platforms instantly</div>', unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input(
        "",
        placeholder="Enter product name or model (e.g., iPhone 15, Sony WH-1000XM5, Nike Air Max)...",
        label_visibility="collapsed",
    )
with col2:
    search_clicked = st.button("🔍 SEARCH", use_container_width=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ───────────────────────────────────────────────
# SEARCH EXECUTION
# ───────────────────────────────────────────────
if search_clicked and query:
    with st.spinner("🚀 Scanning 8 platforms concurrently..."):
        all_scrapers = [
            AmazonScraper, EbayScraper, FlipkartScraper,
            MeeshoScraper, MyntraScraper, AlibabaScraper,
            AjioScraper, RelianceScraper
        ]

        analytics = ReviewAnalyticsEngine()

        engine = AggregatorEngine(
            scrapers=all_scrapers,
            analytics=analytics,
            max_results_per_platform=3,
            max_reviews_per_product=10,
            use_mock=True,
        )

        result = asyncio.run(engine.search(query))

    # ── METRICS BAR ──
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(result.listings)}</div>
            <div class="metric-label">Listings Found</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(result.platforms_searched)}</div>
            <div class="metric-label">Platforms Scanned</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{result.total_reviews_analyzed}</div>
            <div class="metric-label">Reviews Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    with mcol4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{result.search_duration_ms}ms</div>
            <div class="metric-label">Search Time</div>
        </div>
        """, unsafe_allow_html=True)

    # ── AI CONSENSUS ──
    if result.consensus:
        st.markdown("<h2 style='color:#00FFB9; margin-top:2rem;'>🤖 AI Consensus Report</h2>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            verdict_class = f"verdict-{result.consensus.verdict.lower()}"
            st.markdown(f"""
            <div style="text-align:center; padding:2rem; background:#1F2937; border-radius:16px; border:1px solid #2D3748;">
                <p style="color:#8899A6; font-size:0.9rem; margin-bottom:0.5rem;">AI Recommendation</p>
                <div class="{verdict_class}">{result.consensus.verdict}</div>
                <p style="color:#8899A6; font-size:0.8rem; margin-top:1rem;">
                    Confidence: {result.consensus.confidence:.0%} · Generated {result.consensus.generated_at.strftime("%H:%M:%S")}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#162033; padding:1rem; border-radius:10px; margin:1rem 0;">
            <p style="color:#FFFFFF; font-style:italic;">💡 {result.consensus.summary}</p>
        </div>
        """, unsafe_allow_html=True)

        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown('<div class="pros-box">', unsafe_allow_html=True)
            st.markdown("<h4 style='color:#00FFB9; margin-top:0;'>✅ Pros</h4>", unsafe_allow_html=True)
            for pro in result.consensus.pros:
                st.markdown(f"<p style='color:#FFFFFF; margin:0.3rem 0;'>• {pro}</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with pc2:
            st.markdown('<div class="cons-box">', unsafe_allow_html=True)
            st.markdown("<h4 style='color:#FF4757; margin-top:0;'>❌ Cons</h4>", unsafe_allow_html=True)
            for con in result.consensus.cons:
                st.markdown(f"<p style='color:#FFFFFF; margin:0.3rem 0;'>• {con}</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if result.consensus.key_themes:
            st.markdown("<p style='color:#8899A6; font-size:0.8rem; margin-top:1rem;'>🔑 Key Themes: " + ", ".join(result.consensus.key_themes) + "</p>", unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── PRICE COMPARISON MATRIX ──
    st.markdown("<h2 style='color:#00FFB9;'>📊 Price Comparison Matrix</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8899A6; font-size:0.9rem;'>All platforms sorted by price (lowest first). Click 'Buy Now' to visit the product page.</p>", unsafe_allow_html=True)

    df_data = []
    for listing in sorted(result.listings, key=lambda x: (x.price or float("inf"))):
        badge_class = f"badge-{listing.platform.lower().replace(" ", "-")}"
        df_data.append({
            "Platform": f'<span class="platform-badge {badge_class}">{listing.platform}</span>',
            "Product": listing.title[:60] + ("..." if len(listing.title) > 60 else ""),
            "Price": listing.get_price_display(),
            "Raw Price": listing.price or float("inf"),
            "Currency": listing.currency,
            "Rating": f"⭐ {listing.rating_aggregate:.1f}" if listing.rating_aggregate else "—",
            "Reviews": listing.review_count or len(listing.reviews),
            "Availability": "🟢 In Stock" if listing.availability.value == "in_stock" else "🔴 Out of Stock",
            "Link": f'<a href="{listing.product_url or "#"}" target="_blank" class="buy-link">Buy Now →</a>' if listing.product_url else "—",
        })

    # Custom HTML table
    table_html = '<table class="comparison-table" style="width:100%; border-collapse:collapse;">'
    table_html += '<tr><th>Platform</th><th>Product</th><th>Price</th><th>Rating</th><th>Reviews</th><th>Status</th><th>Action</th></tr>'

    for row in df_data:
        is_best_price = result.best_price and result.best_price.platform == row["Platform"].split(">")[1].split("<")[0]
        is_best_rated = result.best_rated and result.best_rated.platform == row["Platform"].split(">")[1].split("<")[0]

        price_display = row["Price"]
        if is_best_price:
            price_display = f'<span style="color:#00FFB9; font-weight:700;">🔥 {row["Price"]}</span>'
        if is_best_rated:
            price_display += ' <span style="color:#FFB800; font-size:0.7rem;">⭐ Best Rated</span>'

        table_html += "<tr>"
        table_html += f"<td>{row['Platform']}</td>"
        table_html += f"<td>{row['Product']}</td>"
        table_html += f"<td>{price_display}</td>"
        table_html += f"<td>{row['Rating']}</td>"
        table_html += f"<td>{row['Reviews']}</td>"
        table_html += f"<td>{row['Availability']}</td>"
        table_html += f"<td>{row['Link']}</td>"
        table_html += "</tr>"

    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)

    # ── INDIVIDUAL PLATFORM CARDS ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:#00FFB9;'>🏪 Platform Listings</h2>", unsafe_allow_html=True)

    platform_groups = {}
    for listing in result.listings:
        platform_groups.setdefault(listing.platform, []).append(listing)

    for platform, items in platform_groups.items():
        with st.expander(f"📦 {platform} — {len(items)} listing(s)", expanded=True):
            cols = st.columns(min(len(items), 3))
            for idx, item in enumerate(items):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="platform-card">
                        <p style="color:#8899A6; font-size:0.7rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">
                            {platform}
                        </p>
                        <p style="color:#FFFFFF; font-weight:600; font-size:0.95rem; margin-bottom:0.5rem; line-height:1.4;">
                            {item.title[:50]}{"..." if len(item.title) > 50 else ""}
                        </p>
                        <p class="price-tag">{item.get_price_display()}</p>
                        <p class="rating-stars">{"⭐" * int(item.rating_aggregate or 0)} {item.rating_aggregate or "N/A"}</p>
                        <p style="color:#8899A6; font-size:0.75rem; margin-top:0.5rem;">
                            {item.review_count or len(item.reviews)} reviews · {item.availability.value.replace("_", " ").title()}
                        </p>
                        {f'<a href="{item.product_url}" target="_blank" class="buy-link" style="margin-top:0.5rem;">Buy on {platform} →</a>' if item.product_url else ""}
                    </div>
                    """, unsafe_allow_html=True)

    # ── REVIEWS SECTION ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:#00FFB9;'>💬 Recent Reviews</h2>", unsafe_allow_html=True)

    all_reviews = []
    for listing in result.listings:
        for review in listing.reviews[:3]:
            all_reviews.append((listing.platform, review))

    if all_reviews:
        for platform, review in all_reviews[:15]:
            st.markdown(f"""
            <div class="review-card">
                <span class="review-platform">{platform}</span>
                <p style="color:#FFFFFF; margin:0.5rem 0; font-size:0.9rem;">{review.body[:200]}{"..." if len(review.body) > 200 else ""}</p>
                <p style="color:#8899A6; font-size:0.75rem; margin:0;">
                    {f"⭐ {review.rating}" if review.rating else ""} · {review.title or "No title"}
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No reviews available for this product.")

    # ── FOOTER ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(f"""
    <p style="color:#8899A6; font-size:0.75rem; text-align:center;">
        Search completed in {result.search_duration_ms}ms · 
        Platforms: {', '.join(result.platforms_searched)} · 
        {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </p>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center; padding:3rem 0; color:#8899A6;">
        <p style="font-size:1.2rem; margin-bottom:1rem;">👆 Enter a product name above to begin comparison</p>
        <p style="font-size:0.9rem;">We will scan Amazon, eBay, Flipkart, Meesho, Myntra, Alibaba, Ajio, and Reliance Digital simultaneously.</p>
    </div>
    """, unsafe_allow_html=True)

    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        st.markdown("""
        <div class="metric-card" style="height:100%;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">⚡</div>
            <div style="color:#FFFFFF; font-weight:600; margin-bottom:0.5rem;">Concurrent Search</div>
            <div style="color:#8899A6; font-size:0.8rem;">All 8 platforms scanned in parallel via async engine</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol2:
        st.markdown("""
        <div class="metric-card" style="height:100%;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">🧠</div>
            <div style="color:#FFFFFF; font-weight:600; margin-bottom:0.5rem;">AI Consensus</div>
            <div style="color:#8899A6; font-size:0.8rem;">LLM-powered Buy/Wait/Skip verdict from all reviews</div>
        </div>
        """, unsafe_allow_html=True)
    with fcol3:
        st.markdown("""
        <div class="metric-card" style="height:100%;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">📊</div>
            <div style="color:#FFFFFF; font-weight:600; margin-bottom:0.5rem;">Price Matrix</div>
            <div style="color:#8899A6; font-size:0.8rem;">Unified comparison table sorted by lowest price</div>
        </div>
        """, unsafe_allow_html=True)
