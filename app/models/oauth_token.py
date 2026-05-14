from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50), unique=True)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
