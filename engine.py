"""
Intelligence Layer: Review Aggregation & LLM Consensus
Uses OpenAI (or compatible) API to synthesize review corpora into actionable insights.
"""
import os
import json
from typing import List, Optional
from datetime import datetime
from models.product import ProductListing, Review, ConsensusReport


class ReviewAnalyticsEngine:
    """
    Aggregates reviews across platforms and generates
    a consensus verdict via LLM synthesis.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("OpenAI package not installed. Run: pip install openai")
        return self._client

    def aggregate_reviews(self, listings: List[ProductListing]) -> List[Review]:
        """Flatten all reviews from all listings into a single corpus."""
        corpus = []
        for listing in listings:
            corpus.extend(listing.reviews)
        return corpus

    def generate_consensus(self, listings: List[ProductListing], product_query: str) -> Optional[ConsensusReport]:
        """
        Send aggregated review text to LLM and return structured consensus.
        Falls back to heuristic analysis if LLM is unavailable.
        """
        corpus = self.aggregate_reviews(listings)
        if not corpus:
            return None

        review_texts = [f"[{r.source_platform}] {r.title or 'No title'}: {r.body}" for r in corpus]
        combined_text = "\n---\n".join(review_texts[:50])  # Cap token usage

        system_prompt = """You are an expert consumer analyst. Analyze the provided product reviews and output a JSON object with exactly these keys:
- verdict: one of ["Buy", "Wait", "Skip"]
- confidence: float 0.0-1.0
- pros: list of strings (max 5)
- cons: list of strings (max 5)
- summary: string (2-3 sentences)
- key_themes: list of strings (max 5 recurring topics)

Be concise, objective, and base your verdict strictly on the review evidence."""

        user_prompt = f"Product: {product_query}\n\nReviews:\n{combined_text}"

        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=800,
            )
            raw = json.loads(resp.choices[0].message.content)
            return ConsensusReport(
                verdict=raw.get("verdict", "Wait"),
                confidence=raw.get("confidence", 0.5),
                pros=raw.get("pros", []),
                cons=raw.get("cons", []),
                summary=raw.get("summary", "No summary available."),
                key_themes=raw.get("key_themes", []),
                generated_at=datetime.utcnow()
            )
        except Exception as e:
            print(f"[Analytics] LLM call failed: {e}. Using heuristic fallback.")
            return self._heuristic_consensus(corpus, product_query)

    def _heuristic_consensus(self, corpus: List[Review], product_query: str) -> ConsensusReport:
        """Fallback when LLM is unavailable: simple keyword-based analysis."""
        positive_keywords = ["love", "great", "excellent", "best", "amazing", "perfect", "recommend", "good", "happy", "satisfied"]
        negative_keywords = ["hate", "worst", "terrible", "broken", "defective", "poor", "bad", "disappointed", "waste", "return"]

        pos_count = sum(1 for r in corpus for kw in positive_keywords if kw in r.body.lower())
        neg_count = sum(1 for r in corpus for kw in negative_keywords if kw in r.body.lower())
        total = pos_count + neg_count or 1

        confidence = round(max(pos_count, neg_count) / total, 2)
        if pos_count > neg_count * 1.5:
            verdict = "Buy"
        elif neg_count > pos_count * 1.2:
            verdict = "Skip"
        else:
            verdict = "Wait"

        return ConsensusReport(
            verdict=verdict,
            confidence=confidence,
            pros=["Positive sentiment detected in reviews"] if pos_count > 0 else [],
            cons=["Negative sentiment detected in reviews"] if neg_count > 0 else [],
            summary=f"Heuristic analysis of {len(corpus)} reviews suggests a '{verdict}' verdict based on sentiment ratios.",
            key_themes=["Sentiment analysis fallback"],
            generated_at=datetime.utcnow()
        )
