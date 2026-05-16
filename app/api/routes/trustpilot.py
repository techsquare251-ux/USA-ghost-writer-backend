from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query

from app.schemas.trustpilot import TrustpilotReviewListResponse
from app.services.trustpilot import fetch_trustpilot_reviews

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/trustpilot", response_model=TrustpilotReviewListResponse)
async def get_trustpilot_reviews(
    limit: int = Query(default=5, ge=1, le=10),
) -> TrustpilotReviewListResponse:
    try:
        reviews, cached = await fetch_trustpilot_reviews(limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not fetch Trustpilot reviews.") from exc

    return TrustpilotReviewListResponse(
        fetched_at=datetime.now(UTC).isoformat(),
        cached=cached,
        limit=limit,
        reviews=reviews,
    )
