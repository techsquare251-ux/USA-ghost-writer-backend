from __future__ import annotations

from pydantic import BaseModel, Field


class TrustpilotReview(BaseModel):
    id: str
    author: str
    country: str = ""
    headline: str = ""
    quote: str
    date: str = ""
    rating: int = Field(ge=1, le=5)
    source: str = "trustpilot"


class TrustpilotReviewListResponse(BaseModel):
    source: str = "trustpilot"
    fetched_at: str
    cached: bool
    limit: int
    reviews: list[TrustpilotReview]
