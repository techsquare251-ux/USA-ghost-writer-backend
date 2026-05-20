from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import PortfolioCoverImage, PortfolioItem
from app.schemas.portfolio import PortfolioCategory, PortfolioItemCreate, PortfolioItemUpdate

PORTFOLIO_SEED_ITEMS: list[dict[str, Any]] = [
    {
        "id": "book-1",
        "title": "2 Salty 2 Be Sweet",
        "author": "Kendra Ellison",
        "category": "published_book",
        "genre": "Children's",
        "cover_image": "/books/2-salty-2-be-sweet.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "The first book in a series following Julienne Thyme, a smart young girl who solves a culinary mystery with her friends.",
        "sort_order": 1,
    },
    {
        "id": "book-2",
        "title": "Positive1: Live a Positive or Negative Life?",
        "author": "Darnell Devon Drew Jr.",
        "category": "published_book",
        "genre": "Self-Help",
        "cover_image": "/books/positive-1.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A self-help journey through doubt and transition, showing how choosing positivity can reshape outlook and reality.",
        "sort_order": 2,
    },
    {
        "id": "book-3",
        "title": "Principal's Matter: Empowering School Administrators and Organizational Leaders",
        "author": "Jorge A. Rivas",
        "category": "published_book",
        "genre": "Leadership",
        "cover_image": "/books/principals-matter.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A leadership guide for school principals and organizational leaders focused on trust, growth, and shared vision.",
        "sort_order": 3,
    },
    {
        "id": "book-4",
        "title": "The Making of the Iron Lady: How One White Woman Went from an Aristocratic Background to Overcoming Homelessness Then Back to Wealth and Success with Two Doctorates",
        "author": "Sophia Rothschild",
        "category": "published_book",
        "genre": "Memoir",
        "cover_image": "/books/the-making-of-the-iron-lady.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A memoir of a dramatic journey from privilege to homelessness and back to success with two doctoral degrees.",
        "sort_order": 4,
    },
    {
        "id": "book-5",
        "title": "Great Answers to Life's Questions: 1,000 Sayings to Enhance Modern Living",
        "author": "Marcus L. Whitman",
        "category": "published_book",
        "genre": "Non-Fiction",
        "cover_image": "/books/lifes.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A collection of 1,000 sayings blending ancient proverbs and modern reflections for daily encouragement.",
        "sort_order": 5,
    },
    {
        "id": "book-6",
        "title": "The Physics of Religion: From Buddha to Jesus",
        "author": "Dr. William Joel Meggs",
        "category": "published_book",
        "genre": "Religion & Spirituality",
        "cover_image": "/books/the-physics-of-religion.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A thought-provoking work linking enlightenment and quantum physics as shared properties of nature.",
        "sort_order": 6,
    },
    {
        "id": "book-7",
        "title": "Fires of Change: A Journey Through Life and Flavor - A Cookbook",
        "author": "Chef Guaracyara \"Guara\" Pimenta",
        "category": "published_book",
        "genre": "Cookbook",
        "cover_image": "/books/fires-of-change.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A Brazilian-born chef shares favorite recipes with the life stories and traditions behind them.",
        "sort_order": 7,
    },
    {
        "id": "book-8",
        "title": "Jesus Walks Into a Bar",
        "author": "Caleb R. Hawthorne",
        "category": "published_book",
        "genre": "Religion & Spirituality",
        "cover_image": "/books/jesus-walk-into-a-bar.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A witty, honest take on big theological questions aimed at skeptics and curious believers alike.",
        "sort_order": 8,
    },
    {
        "id": "book-9",
        "title": "From Broken to Redeemed",
        "author": "Elena Marquez",
        "category": "published_book",
        "genre": "Memoir",
        "cover_image": "/books/from-broken-to-redeemed.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A personal story of survival and healing, anchored in faith and the promise of redemption.",
        "sort_order": 9,
    },
    {
        "id": "book-10",
        "title": "The Dairy of God: A Journey of Love, Life, and the Power Within",
        "author": "Sofia Reynolds",
        "category": "published_book",
        "genre": "Children's",
        "cover_image": "/books/the-dairy-of-god.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A children's story about love, self-discovery, and courage, told through a young girl's voice.",
        "sort_order": 10,
    },
    {
        "id": "book-11",
        "title": "He Loved Me to Death: From Hell to Heaven",
        "author": "Danielle Brooks",
        "category": "published_book",
        "genre": "Memoir",
        "cover_image": "/books/he-loved-me-to-death.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A harrowing memoir of surviving decades of abuse and finding strength beyond the trauma.",
        "sort_order": 11,
    },
    {
        "id": "book-12",
        "title": "Universal Lady Justice Aya (Part 1 - Volume 1)",
        "author": "Kenji Mori",
        "category": "published_book",
        "genre": "Graphic Novel",
        "cover_image": "/books/lady-justice-aya.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A manga-style story set in 2084 where magic, alien factions, and conspiracy collide.",
        "sort_order": 12,
    },
    {
        "id": "book-13",
        "title": "Weekly Planner",
        "author": "Lauren Sinclair",
        "category": "published_book",
        "genre": "Planner",
        "cover_image": "/books/waply-phnna.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A motivational weekly planner with goal-setting, self-care pages, and inspirational quotes.",
        "sort_order": 13,
    },
    {
        "id": "book-14",
        "title": "Mastering Tai Chi Chuan",
        "author": "Victor Liang",
        "category": "published_book",
        "genre": "Health & Wellness",
        "cover_image": "/books/mastering-tai-chi-chuan.jpeg",
        "amazon_url": "https://amazon.com",
        "description": "A guide to improving mobility, balance, and well-being through daily Tai Chi practice.",
        "sort_order": 14,
    },
]


async def seed_portfolio_items(session: AsyncSession) -> None:
    existing_count = await session.scalar(select(func.count()).select_from(PortfolioItem))
    if existing_count:
        return

    session.add_all(PortfolioItem(**item) for item in PORTFOLIO_SEED_ITEMS)
    await session.commit()


async def list_portfolio_items(
    session: AsyncSession,
    category: PortfolioCategory | None = None,
) -> list[PortfolioItem]:
    statement = select(PortfolioItem).order_by(PortfolioItem.sort_order.asc(), PortfolioItem.created_at.asc())
    if category:
        statement = statement.where(PortfolioItem.category == category)

    result = await session.scalars(statement)
    return list(result.all())


async def get_portfolio_item(session: AsyncSession, item_id: str) -> PortfolioItem | None:
    return await session.get(PortfolioItem, item_id)


async def create_portfolio_item(session: AsyncSession, payload: PortfolioItemCreate) -> PortfolioItem:
    existing = await session.get(PortfolioItem, payload.id)
    if existing:
        raise ValueError("Portfolio item already exists.")

    item = PortfolioItem(**payload.model_dump(by_alias=True))
    session.add(item)
    await session.flush()
    await session.refresh(item)
    return item


async def update_portfolio_item(
    session: AsyncSession,
    item_id: str,
    payload: PortfolioItemUpdate,
) -> PortfolioItem:
    item = await session.get(PortfolioItem, item_id)
    if not item:
        raise LookupError("Portfolio item not found.")

    updates = payload.model_dump(by_alias=True, exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)

    await session.flush()
    await session.refresh(item)
    return item


async def delete_portfolio_item(session: AsyncSession, item_id: str) -> bool:
    item = await session.get(PortfolioItem, item_id)
    if not item:
        return False

    await session.delete(item)
    await session.flush()
    return True


async def save_portfolio_cover_image(session: AsyncSession, item_id: str, upload_file: UploadFile) -> str:
    """
    Save an uploaded portfolio cover image to the database.
    Returns the public route for the stored image.
    """
    content = await upload_file.read()
    filename = Path(upload_file.filename or f"{item_id}.bin").name or f"{item_id}.bin"
    content_type = upload_file.content_type or "application/octet-stream"

    cover_image = await session.get(PortfolioCoverImage, item_id)
    if cover_image is None:
        cover_image = PortfolioCoverImage(
            item_id=item_id,
            filename=filename,
            content_type=content_type,
            data=content,
        )
        session.add(cover_image)
    else:
        cover_image.filename = filename
        cover_image.content_type = content_type
        cover_image.data = content

    await session.flush()
    return f"/api/portfolio/{item_id}/cover-image"


async def get_portfolio_cover_image(session: AsyncSession, item_id: str) -> PortfolioCoverImage | None:
    return await session.get(PortfolioCoverImage, item_id)


async def delete_portfolio_cover_image(session: AsyncSession, item_id: str) -> bool:
    cover_image = await session.get(PortfolioCoverImage, item_id)
    if not cover_image:
        return False

    await session.delete(cover_image)
    await session.flush()
    return True
