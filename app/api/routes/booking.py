from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.models.oauth_token import OAuthToken
from app.schemas.booking import AvailabilityResponse, BookingRequest, BookingResponse
from app.services.email import send_booking_emails
from app.services.google_calendar import build_calendar_service

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


def parse_time(value: str) -> time:
    return time.fromisoformat(value)


def resolve_business_window(target_date: date) -> tuple[datetime, datetime]:
    tz = ZoneInfo(settings.meeting_timezone)
    start = datetime.combine(target_date, parse_time(settings.business_hours_start), tzinfo=tz)
    end = datetime.combine(target_date, parse_time(settings.business_hours_end), tzinfo=tz)
    if end <= start:
        end = end + timedelta(days=1)
    return start, end


def build_busy_ranges(items: list[dict[str, str]]) -> list[tuple[datetime, datetime]]:
    buffer = timedelta(minutes=settings.meeting_buffer_minutes)
    busy_ranges: list[tuple[datetime, datetime]] = []
    for item in items:
        start = datetime.fromisoformat(item["start"])
        end = datetime.fromisoformat(item["end"])
        busy_ranges.append((start - buffer, end + buffer))
    return busy_ranges


def slot_available(slot_start: datetime, slot_end: datetime, busy_ranges: list[tuple[datetime, datetime]]) -> bool:
    for busy_start, busy_end in busy_ranges:
        if slot_start < busy_end and slot_end > busy_start:
            return False
    return True


def build_slot_times(target_date: date, busy_ranges: list[tuple[datetime, datetime]]) -> list[str]:
    duration = timedelta(minutes=settings.meeting_duration_minutes)
    start, end = resolve_business_window(target_date)

    slots: list[str] = []
    cursor = start
    while cursor + duration <= end:
        slot_end = cursor + duration
        if slot_available(cursor, slot_end, busy_ranges):
            slots.append(cursor.strftime("%H:%M"))
        cursor += duration

    return slots


async def load_google_token(session: AsyncSession) -> OAuthToken:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured.")
    token = await session.scalar(select(OAuthToken).where(OAuthToken.provider == "google"))
    if not token:
        raise HTTPException(status_code=500, detail="Google Calendar is not connected.")
    return token


@router.get("/availability", response_model=AvailabilityResponse)
async def availability(
    date: date,
    session: AsyncSession = Depends(get_session),
) -> AvailabilityResponse:
    token = await load_google_token(session)
    service = build_calendar_service({
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
        "token_type": token.token_type,
        "scope": token.scope,
    })

    start, end = resolve_business_window(date)
    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "items": [{"id": settings.google_calendar_id}],
    }
    result = service.freebusy().query(body=body).execute()
    busy = result.get("calendars", {}).get(settings.google_calendar_id, {}).get("busy", [])
    busy_ranges = build_busy_ranges(busy)

    slots = build_slot_times(date, busy_ranges)
    return AvailabilityResponse(date=date, slots=slots)


@router.post("/book", response_model=BookingResponse)
async def book_meeting(
    payload: BookingRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> BookingResponse:
    token = await load_google_token(session)
    service = build_calendar_service({
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
        "token_type": token.token_type,
        "scope": token.scope,
    })

    start_date = payload.date
    start_time = parse_time(payload.start_time)
    tz = ZoneInfo(settings.meeting_timezone)
    start_dt = datetime.combine(start_date, start_time, tzinfo=tz)
    end_dt = start_dt + timedelta(minutes=settings.meeting_duration_minutes)

    busy_result = service.freebusy().query(
        body={
            "timeMin": start_dt.isoformat(),
            "timeMax": end_dt.isoformat(),
            "items": [{"id": settings.google_calendar_id}],
        }
    ).execute()
    busy = busy_result.get("calendars", {}).get(settings.google_calendar_id, {}).get("busy", [])
    if not slot_available(start_dt, end_dt, build_busy_ranges(busy)):
        raise HTTPException(status_code=409, detail="That time is no longer available.")

    event = {
        "summary": f"Publishing consultation with {payload.name}",
        "description": "\n".join(
            [
                f"Name: {payload.name}",
                f"Email: {payload.email}",
                f"Phone: {payload.phone}",
                f"Message: {payload.message or 'N/A'}",
                f"Context: {payload.context or 'booking'}",
            ]
        ),
        "start": {"dateTime": start_dt.isoformat(), "timeZone": settings.meeting_timezone},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": settings.meeting_timezone},
        "attendees": [{"email": payload.email}] + [
            {"email": admin} for admin in settings.admin_email_list
        ],
    }

    created = service.events().insert(
        calendarId=settings.google_calendar_id,
        body=event,
        sendUpdates="none",
    ).execute()

    background_tasks.add_task(
        send_booking_emails,
        {
            "name": payload.name,
            "email": payload.email,
            "phone": payload.phone,
            "message": payload.message,
            "context": payload.context,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
        },
    )

    return BookingResponse(
        success=True,
        message="Your meeting is booked. We sent a confirmation email.",
        event_id=created.get("id"),
    )
