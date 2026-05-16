from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

FALLBACK_REVIEWS: list[dict[str, Any]] = [
    {
        "id": "fallback-1",
        "author": "J. Carter",
        "country": "United States",
        "headline": "A polished and dependable publishing team",
        "quote": "They brought structure, clarity, and professionalism to every stage of our launch.",
        "date": "2026-02-11",
        "rating": 5,
        "source": "fallback",
    },
    {
        "id": "fallback-2",
        "author": "M. Alvarez",
        "country": "Canada",
        "headline": "Clear communication from start to finish",
        "quote": "Their process was structured and transparent, and every milestone was delivered on time.",
        "date": "2026-01-23",
        "rating": 5,
        "source": "fallback",
    },
]

_CACHE: dict[str, Any] = {
    "fetched_at": None,
    "reviews": [],
}


def _now() -> datetime:
    return datetime.now(UTC)


def _is_cache_fresh() -> bool:
    fetched_at = _CACHE.get("fetched_at")
    if not isinstance(fetched_at, datetime):
        return False
    ttl = timedelta(seconds=max(settings.trustpilot_cache_ttl_seconds, 60))
    return _now() - fetched_at < ttl


def _normalize_review(review: dict[str, Any]) -> dict[str, Any]:
    reviewer = review.get("consumer", {}) or review.get("reviewer", {}) or {}
    location = reviewer.get("countryCode") or reviewer.get("country") or review.get("country") or ""
    title = review.get("title") or review.get("headline") or ""
    text = review.get("text") or review.get("content") or review.get("message") or ""
    created_at = review.get("createdAt") or review.get("date") or review.get("created") or ""
    stars = review.get("stars") or review.get("rating") or 5
    stars = int(stars) if str(stars).isdigit() else 5
    reviewer_name = (
        reviewer.get("name")
        or review.get("name")
        or review.get("author")
        or review.get("consumerName")
        or "Verified Customer"
    )

    return {
        "id": str(review.get("id") or review.get("reviewId") or reviewer_name + created_at),
        "author": reviewer_name,
        "country": str(location),
        "headline": str(title),
        "quote": str(text),
        "date": str(created_at)[:10],
        "rating": max(1, min(5, stars)),
        "source": "trustpilot",
    }


def _sort_reviews(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(item: dict[str, Any]) -> tuple[int, str]:
        rating = int(item.get("rating") or 0)
        date = str(item.get("date") or "")
        return (-rating, date)

    return sorted(reviews, key=sort_key)


async def fetch_trustpilot_reviews(limit: int | None = None) -> tuple[list[dict[str, Any]], bool]:
    normalized_limit = max(1, min(limit or settings.trustpilot_default_limit, 10))

    if _is_cache_fresh() and _CACHE.get("reviews"):
        cached_reviews = list(_CACHE["reviews"][:normalized_limit])
        return cached_reviews, True

    if not settings.trustpilot_business_unit_id:
        fallback_reviews = list(FALLBACK_REVIEWS[:normalized_limit])
        _CACHE["fetched_at"] = _now()
        _CACHE["reviews"] = fallback_reviews
        logger.warning("Trustpilot reviews fallback served because the business unit ID is missing.")
        return fallback_reviews, False

    headers: dict[str, str] = {"Accept": "application/json"}
    if settings.trustpilot_api_key:
        headers["apikey"] = settings.trustpilot_api_key
    if settings.trustpilot_access_token:
        headers["Authorization"] = f"Bearer {settings.trustpilot_access_token}"

    base_url = settings.trustpilot_api_base_url.rstrip("/")
    business_unit_id = settings.trustpilot_business_unit_id
    url = f"{base_url}/v1/business-units/{business_unit_id}/reviews"
    params = {"perPage": normalized_limit, "page": 1, "language": "en-US"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()

        raw_reviews = payload.get("reviews") if isinstance(payload, dict) else payload
        if not isinstance(raw_reviews, list):
            raw_reviews = []

        reviews = _sort_reviews([_normalize_review(review) for review in raw_reviews])[:normalized_limit]
        if not reviews:
            reviews = list(FALLBACK_REVIEWS[:normalized_limit])
            logger.warning("Trustpilot reviews fallback served because the API returned no reviews.")

        _CACHE["fetched_at"] = _now()
        _CACHE["reviews"] = reviews
        return reviews, False
    except Exception:
        fallback_reviews = list(FALLBACK_REVIEWS[:normalized_limit])
        _CACHE["fetched_at"] = _now()
        _CACHE["reviews"] = fallback_reviews
        logger.warning("Trustpilot reviews fallback served because the Trustpilot fetch failed.")
        return fallback_reviews, False
