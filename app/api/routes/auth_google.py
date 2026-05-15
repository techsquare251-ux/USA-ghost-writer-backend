from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.models.oauth_token import OAuthToken
from app.services.google_calendar import (
    build_google_flow,
    serialize_credentials,
    build_calendar_service,
)

router = APIRouter(prefix="/api/auth/google", tags=["auth"])


@router.get("/start")
async def google_auth_start() -> dict[str, str]:
    try:
        flow = build_google_flow()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return {"auth_url": auth_url}


@router.get("/callback")
async def google_auth_callback(
    code: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    if not settings.google_redirect_uri:
        raise HTTPException(status_code=500, detail="Google redirect URI is not configured.")

    try:
        flow = build_google_flow()
        flow.fetch_token(code=code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to complete Google OAuth.") from exc

    token_data = serialize_credentials(flow.credentials)
    token = await session.scalar(select(OAuthToken).where(OAuthToken.provider == "google"))
    if token:
        token.access_token = token_data["access_token"]
        token.refresh_token = token_data.get("refresh_token") or token.refresh_token
        token.token_type = token_data.get("token_type")
        token.scope = token_data.get("scope")
        token.expires_at = token_data.get("expires_at")
    else:
        token = OAuthToken(
            provider="google",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data.get("token_type"),
            scope=token_data.get("scope"),
            expires_at=token_data.get("expires_at"),
        )
        session.add(token)

    await session.commit()
    return {"success": "true", "message": "Google Calendar connected."}


@router.get("/status")
async def google_auth_status(session: AsyncSession = Depends(get_session)) -> dict:
    """Return whether a Google OAuth token is stored and the calendar owner email."""
    token = await session.scalar(select(OAuthToken).where(OAuthToken.provider == "google"))
    if not token:
        return {"connected": False}

    token_data = {
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
        "token_type": token.token_type,
        "scope": token.scope,
        "expires_at": token.expires_at,
    }

    try:
        service = build_calendar_service(token_data)
        cal = service.calendars().get(calendarId="primary").execute()
        owner = cal.get("id")
        summary = cal.get("summary")
        return {"connected": True, "calendar_id": owner, "calendar_summary": summary}
    except Exception:
        return {"connected": False}


@router.post("/clear")
async def google_auth_clear(session: AsyncSession = Depends(get_session)) -> dict:
    """Clear stored Google OAuth token (useful to force reauthorization)."""
    token = await session.scalar(select(OAuthToken).where(OAuthToken.provider == "google"))
    if not token:
        return {"cleared": False, "message": "No token found."}

    await session.delete(token)
    await session.commit()
    return {"cleared": True}
