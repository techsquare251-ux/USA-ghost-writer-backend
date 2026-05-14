from fastapi import APIRouter

from app.api.routes.auth_google import router as google_auth_router
from app.api.routes.booking import router as booking_router
from app.api.routes.contact import router as contact_router

api_router = APIRouter()
api_router.include_router(contact_router)
api_router.include_router(google_auth_router)
api_router.include_router(booking_router)
