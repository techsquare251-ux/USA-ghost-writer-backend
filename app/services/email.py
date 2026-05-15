from datetime import datetime
from email.message import EmailMessage
import logging
from uuid import uuid4

import aiosmtplib
from aiosmtplib.errors import SMTPReadTimeoutError

from app.core.config import settings


logger = logging.getLogger(__name__)


def build_plain_message(payload: dict[str, str | None]) -> str:
    lines = [
        f"Name: {payload.get('name')}",
        f"Email: {payload.get('email')}",
        f"Phone: {payload.get('phone')}",
        f"Service Interest: {payload.get('service') or 'N/A'}",
        f"Context: {payload.get('context') or 'N/A'}",
        f"Message: {payload.get('message') or 'N/A'}",
        f"SMS Consent: {'Yes' if payload.get('sms_consent') else 'No'}",
    ]
    return "\n".join(lines)


def build_admin_html(payload: dict[str, str | None]) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#1B263B;">
      <h2 style="color:#0B3C6D;">New contact request</h2>
      <p><strong>Name:</strong> {payload.get('name')}</p>
      <p><strong>Email:</strong> {payload.get('email')}</p>
      <p><strong>Phone:</strong> {payload.get('phone')}</p>
      <p><strong>Service Interest:</strong> {payload.get('service') or 'N/A'}</p>
      <p><strong>Context:</strong> {payload.get('context') or 'N/A'}</p>
      <p><strong>Message:</strong><br />{payload.get('message') or 'N/A'}</p>
      <p><strong>SMS Consent:</strong> {"Yes" if payload.get('sms_consent') else "No"}</p>
    </div>
    """


def build_user_html(payload: dict[str, str | None]) -> str:
    return f"""
    <div style="margin:0;background:#F8F9FC;padding:32px 16px;">
      <div style="max-width:680px;margin:0 auto;background:#FFFFFF;border:1px solid #D8E0EE;border-radius:20px;overflow:hidden;box-shadow:0 18px 50px rgba(11,60,109,0.08);font-family:Arial,sans-serif;color:#1B263B;">
        <div style="background:linear-gradient(135deg,#0B3C6D 0%,#1E5288 58%,#D4A017 140%);padding:34px 36px;color:#FFFFFF;position:relative;">
          <div style="display:inline-flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:999px;background:rgba(255,255,255,0.16);border:1px solid rgba(255,255,255,0.22);font-weight:700;letter-spacing:0.08em;">UGW</div>
          <p style="margin:18px 0 8px;font-size:11px;letter-spacing:.2em;text-transform:uppercase;opacity:.82;">USA Ghost Writer</p>
          <h2 style="margin:0;font-size:30px;line-height:1.1;">We received your message</h2>
          <p style="margin:12px 0 0;font-size:15px;max-width:540px;line-height:1.6;opacity:.96;">Thanks for reaching out. A member of our team will review your message and get back to you shortly.</p>
        </div>

        <div style="padding:34px 36px;">
          <p style="margin:0 0 14px;font-size:16px;">Hi {payload.get('name')},</p>
          <p style="margin:0 0 22px;font-size:15px;line-height:1.8;color:#334155;">We’ve successfully received your message and our consultant will reach out shortly. In the meantime, you can explore our services, review our packages, or browse recent work to see how we help authors bring their books to market with confidence.</p>

          <div style="margin:0 0 24px;padding:22px;border-radius:18px;background:#F8F9FC;border:1px solid #E6EBF4;">
            <p style="margin:0 0 12px;font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#0B3C6D;font-weight:700;">Your request</p>
            <p style="margin:0 0 8px;"><strong>Name:</strong> {payload.get('name')}</p>
            <p style="margin:0 0 8px;"><strong>Email:</strong> {payload.get('email')}</p>
            <p style="margin:0 0 8px;"><strong>Service Interest:</strong> {payload.get('service') or 'N/A'}</p>
            <p style="margin:0;"><strong>Message:</strong> {payload.get('message') or 'N/A'}</p>
          </div>

          <div style="display:flex;gap:12px;flex-wrap:wrap;margin:0 0 24px;">
            <a href="https://usaghostwriter.com/services" style="display:inline-block;padding:12px 18px;border-radius:999px;background:#0B3C6D;color:#FFFFFF;text-decoration:none;font-weight:700;font-size:14px;">Explore Services</a>
            <a href="https://usaghostwriter.com/packages" style="display:inline-block;padding:12px 18px;border-radius:999px;background:#D4A017;color:#1B263B;text-decoration:none;font-weight:700;font-size:14px;">View Packages</a>
            <a href="https://usaghostwriter.com/portfolio" style="display:inline-block;padding:12px 18px;border-radius:999px;background:#F8F9FC;color:#0B3C6D;text-decoration:none;font-weight:700;font-size:14px;border:1px solid #D8E0EE;">See Portfolio</a>
          </div>

          <div style="padding:18px 20px;border-left:4px solid #C1121F;background:#FFF5F5;border-radius:12px;">
            <p style="margin:0;font-size:14px;line-height:1.7;color:#7F1D1D;">If your request is urgent, feel free to reply directly to this email and we’ll prioritize it for review.</p>
          </div>
        </div>
      </div>
    </div>
    """


async def send_email(subject: str, recipients: list[str], html_body: str, text_body: str, ics_attachment: str | None = None) -> None:
    normalized_recipients = [
        recipient.strip()
        for recipient in recipients
        if recipient and recipient.strip() and recipient.strip().lower() != "none"
    ]
    if not normalized_recipients:
        raise ValueError("No valid recipients provided.")

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = ", ".join(normalized_recipients)
    message["Subject"] = subject
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    if ics_attachment:
        message.add_attachment(
            ics_attachment.encode("utf-8"),
            maintype="text",
            subtype="calendar",
            filename="meeting.ics",
            params={"method": "REQUEST", "charset": "UTF-8"},
        )

    timeout_seconds = max(10, settings.smtp_timeout_seconds)
    for attempt in range(2):
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_pass,
                start_tls=not settings.smtp_secure,
                use_tls=settings.smtp_secure,
                timeout=timeout_seconds,
            )
            return
        except SMTPReadTimeoutError:
            if attempt == 1:
                raise
            logger.warning(
                "SMTP timeout on attempt %s for subject '%s'; retrying once.",
                attempt + 1,
                subject,
            )


async def send_contact_emails(payload: dict[str, str | None]) -> None:
    admin_subject = f"New contact request from {payload.get('name')}"
    user_subject = "We received your message"

    text_body = build_plain_message(payload)
    admin_html = build_admin_html(payload)
    user_html = build_user_html(payload)

    try:
        await send_email(admin_subject, settings.admin_email_list, admin_html, text_body)
    except Exception:
        logger.exception("Failed to send admin contact email.")

    try:
        await send_email(user_subject, [str(payload.get("email"))], user_html, text_body)
    except Exception:
        logger.exception("Failed to send user contact email.")


def build_booking_plain(payload: dict[str, str | None]) -> str:
    lines = [
        "Meeting booked:",
        f"Name: {payload.get('name')}",
        f"Email: {payload.get('email')}",
        f"Phone: {payload.get('phone')}",
        f"Start: {payload.get('start')}",
        f"End: {payload.get('end')}",
        f"Message: {payload.get('message') or 'N/A'}",
    ]
    return "\n".join(lines)


def build_booking_user_plain(payload: dict[str, str | None]) -> str:
    lines = [
        "Your meeting is confirmed.",
        f"Name: {payload.get('name')}",
        f"Start: {payload.get('start')}",
        f"End: {payload.get('end')}",
        f"Message: {payload.get('message') or 'N/A'}",
        "",
        "If you need to reschedule, reply to this email and our team will help you.",
    ]
    return "\n".join(lines)


def build_booking_admin_html(payload: dict[str, str | None]) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#1B263B;">
      <h2 style="color:#0B3C6D;">New meeting booked</h2>
      <p><strong>Name:</strong> {payload.get('name')}</p>
      <p><strong>Email:</strong> {payload.get('email')}</p>
      <p><strong>Phone:</strong> {payload.get('phone')}</p>
      <p><strong>Start:</strong> {payload.get('start')}</p>
      <p><strong>End:</strong> {payload.get('end')}</p>
      <p><strong>Message:</strong><br />{payload.get('message') or 'N/A'}</p>
    </div>
    """


def build_booking_user_html(payload: dict[str, str | None]) -> str:
    return f"""
    <div style="margin:0;background:#F8F9FC;padding:32px 16px;">
      <div style="max-width:640px;margin:0 auto;background:#FFFFFF;border:1px solid #D8E0EE;border-radius:18px;overflow:hidden;box-shadow:0 18px 50px rgba(11,60,109,0.08);font-family:Arial,sans-serif;color:#1B263B;">
        <div style="background:linear-gradient(135deg,#0B3C6D 0%,#1E5288 60%,#D4A017 140%);padding:28px 32px;color:#FFFFFF;">
          <div style="display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:999px;background:rgba(255,255,255,0.16);border:1px solid rgba(255,255,255,0.22);font-weight:700;letter-spacing:0.08em;">UGW</div>
          <p style="margin:16px 0 8px;font-size:11px;letter-spacing:.18em;text-transform:uppercase;opacity:.8;">USA Ghost Writer</p>
          <h2 style="margin:0;font-size:28px;line-height:1.15;">Your meeting is confirmed</h2>
        </div>
        <div style="padding:32px;">
          <p style="margin:0 0 14px;font-size:16px;">Hi {payload.get('name')},</p>
          <p style="margin:0 0 24px;font-size:15px;line-height:1.7;color:#334155;">Your call has been booked successfully. Here are the details:</p>
          <div style="margin:0 0 24px;padding:20px;border-radius:16px;background:#F8F9FC;border:1px solid #E6EBF4;">
            <p style="margin:0 0 8px;"><strong>Start:</strong> {payload.get('start')}</p>
            <p style="margin:0 0 8px;"><strong>End:</strong> {payload.get('end')}</p>
            <p style="margin:0;"><strong>Message:</strong> {payload.get('message') or 'N/A'}</p>
          </div>
          <p style="margin:0;color:#334155;">We look forward to speaking with you.</p>
        </div>
      </div>
    </div>
    """


def build_ics_calendar(payload: dict[str, str | None]) -> str:
    """Build an ICS (iCalendar) file for the booking."""
    start = payload.get("start", "")
    end = payload.get("end", "")
    name = payload.get("name", "Client")
    email = payload.get("email", "")
    phone = payload.get("phone", "")
    message = payload.get("message", "")

    def to_ics_time(iso_str: str) -> str:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y%m%dT%H%M%S")

    start_ics = to_ics_time(start)
    end_ics = to_ics_time(end)
    uid = f"{uuid4()}@usaghostwriter.com"
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    description = f"Phone: {phone}\\nMessage: {message}" if message else f"Phone: {phone}"

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//USA Ghost Writer//Publishing Consultation//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{start_ics}
DTEND:{end_ics}
SUMMARY:Publishing consultation with {name}
DESCRIPTION:{description}
LOCATION:Phone/Video Call
ORGANIZER:mailto:support@usaghostwriter.com
ATTENDEE:mailto:{email}
STATUS:CONFIRMED
SEQUENCE:0
END:VEVENT
END:VCALENDAR
"""
    return ics


async def send_booking_emails(payload: dict[str, str | None]) -> None:
    admin_subject = f"Meeting booked by {payload.get('name')}"
    user_subject = "Your meeting is confirmed"

    text_body = build_booking_plain(payload)
    user_text_body = build_booking_user_plain(payload)
    admin_html = build_booking_admin_html(payload)
    user_html = build_booking_user_html(payload)
    ics_content = build_ics_calendar(payload)

    try:
        await send_email(admin_subject, settings.admin_email_list, admin_html, text_body)
    except Exception:
        logger.exception("Failed to send admin booking email.")

    try:
        await send_email(
            user_subject,
            [str(payload.get("email"))],
            user_html,
            user_text_body,
            ics_attachment=ics_content,
        )
    except Exception:
        logger.exception("Failed to send user booking email.")
