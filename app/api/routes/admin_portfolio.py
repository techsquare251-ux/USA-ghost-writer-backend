from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.schemas.portfolio import PortfolioItemCreate, PortfolioItemResponse, PortfolioItemUpdate
from app.services.portfolio import (
    create_portfolio_item,
    delete_portfolio_item,
    delete_portfolio_cover_image,
    list_portfolio_items,
    save_portfolio_cover_image,
    update_portfolio_item,
)

router = APIRouter(prefix="/api/admin/portfolio", tags=["admin-portfolio"])


async def require_admin_token(request: Request) -> None:
    if not settings.admin_api_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin API token is not configured.")

    token = request.headers.get("x-admin-token")
    if token != settings.admin_api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")


@router.get("", response_model=list[PortfolioItemResponse], response_model_by_alias=False)
async def admin_list_portfolio_items(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> list[PortfolioItemResponse]:
    await require_admin_token(request)
    items = await list_portfolio_items(session)
    return [
        PortfolioItemResponse.model_validate(
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
        for item in items
    ]


@router.post("", response_model=PortfolioItemResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=False)
async def admin_create_portfolio_item(
    request: Request,
    session: AsyncSession = Depends(get_session),
    # Form fields for multipart uploads - make them required with ...
    id: str = Form(...),
    title: str = Form(...),
    author: str = Form(...),
    category: str = Form(...),
    genre: str = Form(...),
    amazon_url: str = Form(...),
    description: str | None = Form(None),
    sort_order: int = Form(0),
    cover_image: UploadFile = File(...),  # Required for new items
) -> PortfolioItemResponse:
    await require_admin_token(request)
    
    try:
        cover_image_path = await save_portfolio_cover_image(session, id, cover_image)
        
        payload = PortfolioItemCreate(
            id=id,
            title=title,
            author=author,
            category=category,
            genre=genre,
            cover_image=cover_image_path,
            amazon_url=amazon_url,
            description=description,
            sort_order=sort_order,
        )
        
        item = await create_portfolio_item(session, payload)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error saving cover image: {str(exc)}") from exc
    
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


@router.put("/{item_id}", response_model=PortfolioItemResponse, response_model_by_alias=False)
async def admin_update_portfolio_item(
    item_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    # Form fields for multipart uploads
    title: str = Form(None),
    author: str = Form(None),
    category: str = Form(None),
    genre: str = Form(None),
    amazon_url: str = Form(None),
    description: str = Form(None),
    sort_order: int = Form(None),
    cover_image: UploadFile = File(None),
) -> PortfolioItemResponse:
    await require_admin_token(request)
    
    content_type = request.headers.get("content-type", "")
    
    # Handle JSON request
    if "application/json" in content_type:
        try:
            import json
            body = await request.body()
            data = json.loads(body)
            payload = PortfolioItemUpdate(**data)
            item = await update_portfolio_item(session, item_id, payload)
            await session.commit()
        except LookupError as exc:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except Exception as exc:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error saving cover image: {str(exc)}") from exc
    # Handle multipart form data
    else:
        # Save cover image if provided
        cover_image_path = None
        if cover_image and cover_image.filename:
            cover_image_path = await save_portfolio_cover_image(session, item_id, cover_image)
        
        # Build update payload - only include provided fields
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if author is not None:
            update_data["author"] = author
        if category is not None:
            update_data["category"] = category
        if genre is not None:
            update_data["genre"] = genre
        if amazon_url is not None:
            update_data["amazon_url"] = amazon_url
        if description is not None:
            update_data["description"] = description
        if sort_order is not None:
            update_data["sort_order"] = sort_order
        if cover_image_path is not None:
            update_data["cover_image"] = cover_image_path
        
        payload = PortfolioItemUpdate(**update_data)
        
        try:
            item = await update_portfolio_item(session, item_id, payload)
            await session.commit()
        except LookupError as exc:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except Exception as exc:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error saving cover image: {str(exc)}") from exc
    
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


@router.delete("/{item_id}")
async def admin_delete_portfolio_item(
    item_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    await require_admin_token(request)
    try:
        await delete_portfolio_cover_image(session, item_id)
        deleted = await delete_portfolio_item(session, item_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio item not found.")
        await session.commit()
    except HTTPException:
        await session.rollback()
        raise
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"deleted": True}
