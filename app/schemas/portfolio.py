from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PortfolioCategory = Literal["published_book", "upcoming_book"]
PortfolioGenre = Literal[
    "Children's",
    "Cookbook",
    "Graphic Novel",
    "Health & Wellness",
    "Leadership",
    "Memoir",
    "Non-Fiction",
    "Planner",
    "Religion & Spirituality",
    "Self-Help",
]


class PortfolioItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=220)
    author: str = Field(min_length=1, max_length=180)
    category: PortfolioCategory
    genre: PortfolioGenre
    coverImage: str = Field(min_length=1, max_length=255, alias="cover_image")
    amazonUrl: str = Field(min_length=1, max_length=500, alias="amazon_url")
    description: str | None = Field(default=None, max_length=4000)
    sortOrder: int = Field(default=0, ge=0, alias="sort_order")


class PortfolioItemCreate(PortfolioItemBase):
    id: str = Field(min_length=1, max_length=64)


class PortfolioItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=220)
    author: str | None = Field(default=None, min_length=1, max_length=180)
    category: PortfolioCategory | None = None
    genre: PortfolioGenre | None = None
    coverImage: str | None = Field(default=None, min_length=1, max_length=255, alias="cover_image")
    amazonUrl: str | None = Field(default=None, min_length=1, max_length=500, alias="amazon_url")
    description: str | None = Field(default=None, max_length=4000)
    sortOrder: int | None = Field(default=None, ge=0, alias="sort_order")


class PortfolioItemResponse(PortfolioItemBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
