from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

url = make_url(settings.database_url)
connect_args: dict[str, object] = {}
sslmode = str(url.query.get("sslmode", "")).lower()
if sslmode:
    updated_query = dict(url.query)
    updated_query.pop("sslmode", None)
    url = url.set(query=updated_query)
    if sslmode in {"require", "verify-ca", "verify-full"}:
        connect_args["ssl"] = True

engine = create_async_engine(url, echo=False, pool_pre_ping=True, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
