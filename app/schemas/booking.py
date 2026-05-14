from datetime import date

from pydantic import BaseModel, EmailStr, Field


class AvailabilityResponse(BaseModel):
    date: date
    slots: list[str]


class BookingRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=50)
    date: date
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    message: str | None = Field(default=None, max_length=2000)
    context: str | None = Field(default="booking", max_length=120)


class BookingResponse(BaseModel):
    success: bool
    message: str
    event_id: str | None = None
