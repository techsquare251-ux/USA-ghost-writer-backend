from datetime import datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.core.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def build_google_flow() -> Flow:
    if not settings.google_client_id or not settings.google_client_secret or not settings.google_redirect_uri:
        raise ValueError("Google OAuth is not configured.")

    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )


def build_credentials(token_data: dict[str, Any]) -> Credentials:
    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def build_calendar_service(token_data: dict[str, Any]):
    creds = build_credentials(token_data)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def serialize_credentials(creds: Credentials) -> dict[str, Any]:
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_type": getattr(creds, "token_type", None),
        "scope": " ".join(creds.scopes) if creds.scopes else None,
        "expires_at": datetime.fromtimestamp(creds.expiry.timestamp()) if creds.expiry else None,
    }
