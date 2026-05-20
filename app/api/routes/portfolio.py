from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.portfolio import PortfolioCategory, PortfolioItemResponse
from app.services.portfolio import get_portfolio_cover_image, list_portfolio_items

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])
logger = logging.getLogger(__name__)


def serialize_portfolio_item(item) -> PortfolioItemResponse | None:
    try:
        return PortfolioItemResponse.model_validate(
            {
                "id": item.id,
                "title": item.title,
                "author": item.author,
                "category": item.category,
                "genre": item.genre,
                "cover_image": item.cover_image,
                "amazon_url": item.amazon_url,
                "description": item.description,
                "sort_order": item.sort_order,
            }
        )
    except Exception:
        logger.exception("Skipping invalid portfolio item %s", getattr(item, "id", "unknown"))
        return None


@router.get("", response_model=list[PortfolioItemResponse], response_model_by_alias=False)
async def get_portfolio_items(
    category: PortfolioCategory | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[PortfolioItemResponse]:
    items = await list_portfolio_items(session, category=category)
    payload = [serialize_portfolio_item(item) for item in items]
    return [item for item in payload if item is not None]


@router.get("/{item_id}/cover-image")
async def get_portfolio_cover_image_route(
    item_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    cover_image = await get_portfolio_cover_image(session, item_id)
    if not cover_image:
        raise HTTPException(status_code=404, detail="Cover image not found.")

    return Response(
        content=cover_image.data,
        media_type=cover_image.content_type,
        headers={"Cache-Control": "no-store"},
    )
