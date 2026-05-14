from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactResponse
from app.services.email import send_contact_emails

router = APIRouter(prefix="/api/contact", tags=["contact"])


@router.post("", response_model=ContactResponse)
async def create_contact(
    payload: ContactCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> ContactResponse:
    contact = Contact(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        service=payload.service,
        message=payload.message,
        context=payload.context,
        sms_consent=payload.sms_consent,
    )

    session.add(contact)

    try:
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not save contact.") from exc

    background_tasks.add_task(send_contact_emails, payload.model_dump())

    return ContactResponse(
        success=True,
        message="Thanks! Your message was received. We will contact you shortly.",
    )
