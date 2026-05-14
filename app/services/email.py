from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings


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
    <div style=\"font-family:Arial,sans-serif;line-height:1.5;color:#1B263B;\">
      <h2 style=\"color:#0B3C6D;\">New contact request</h2>
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
    <div style=\"font-family:Arial,sans-serif;line-height:1.6;color:#1B263B;\">
      <h2 style=\"color:#0B3C6D;\">We received your request</h2>
      <p>Hi {payload.get('name')},</p>
      <p>Thanks for reaching out. Our team will reply shortly. Here is a copy of your request:</p>
      <ul>
        <li><strong>Service Interest:</strong> {payload.get('service') or 'N/A'}</li>
        <li><strong>Message:</strong> {payload.get('message') or 'N/A'}</li>
      </ul>
      <p>We appreciate your interest in USA Ghost Writer.</p>
    </div>
    """


async def send_email(subject: str, recipients: list[str], html_body: str, text_body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_pass,
        start_tls=not settings.smtp_secure,
        use_tls=settings.smtp_secure,
        timeout=10,
    )


async def send_contact_emails(payload: dict[str, str | None]) -> None:
    admin_subject = f"New contact request from {payload.get('name')}"
    user_subject = "We received your message"

    text_body = build_plain_message(payload)
    admin_html = build_admin_html(payload)
    user_html = build_user_html(payload)

    await send_email(admin_subject, settings.admin_email_list, admin_html, text_body)
    await send_email(user_subject, [str(payload.get("email"))], user_html, text_body)
