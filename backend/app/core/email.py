"""Minimal e-mail delivery.

If SMTP is configured (``SMTP_HOST``) the message is sent; otherwise it is
logged, which keeps development and demos working without a mail server. The
interface is intentionally tiny so it can be swapped for a provider SDK later.
"""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("app.email")


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text e-mail, or log it when SMTP is not configured."""
    if not settings.SMTP_HOST:
        logger.info("E-mail (SMTP nao configurado) para %s | %s\n%s", to, subject, body)
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_TLS:
                smtp.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        logger.info("E-mail enviado para %s (%s)", to, subject)
    except Exception:  # pragma: no cover - depends on external service
        logger.exception("Falha ao enviar e-mail para %s", to)
        raise
