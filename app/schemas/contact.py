from pydantic import BaseModel, EmailStr, Field


class ContactCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=7, max_length=50)
    email: EmailStr
    service: str | None = Field(default=None, max_length=120)
    message: str | None = Field(default=None, max_length=4000)
    context: str | None = Field(default=None, max_length=120)
    sms_consent: bool = False


class ContactResponse(BaseModel):
    success: bool
    message: str
