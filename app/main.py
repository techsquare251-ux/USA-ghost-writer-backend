from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.services.portfolio import seed_portfolio_items


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_portfolio_items(session)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

origins = {settings.frontend_url, "http://127.0.0.1:3000"}
if settings.frontend_url.startswith("https://www."):
    origins.add(settings.frontend_url.replace("https://www.", "https://", 1))
elif settings.frontend_url.startswith("https://"):
    origins.add(settings.frontend_url.replace("https://", "https://www.", 1))

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
