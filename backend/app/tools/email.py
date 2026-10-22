import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)

PREVIEW_CHARS = 300
SMTP_TIMEOUT = 30


def _build_message(to: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


def _send_via_smtp(msg: EmailMessage) -> None:
    """Send the message over SSL (port 465) or STARTTLS (any other port)."""
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP is not configured: SMTP_HOST, SMTP_USER and SMTP_PASSWORD are required.")

    context = ssl.create_default_context()
    if settings.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=SMTP_TIMEOUT) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
            server.starttls(context=context)
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)


def send_email(to: str, subject: str, body: str, confirmed: bool = False) -> str:
    """Send an email via SMTP, only after explicit confirmation.

    If confirmed is False, nothing is sent. The function returns a summary
    (recipient, subject, body preview) that must be shown to the user, who must
    explicitly approve it. Only call again with confirmed=True after that approval.
    Errors are returned as a string, never raised.
    """
    if not confirmed:
        preview = body if len(body) <= PREVIEW_CHARS else body[:PREVIEW_CHARS] + "..."
        return (
            "CONFIRMATION REQUIRED. The email has NOT been sent.\n"
            f"To: {to}\n"
            f"Subject: {subject}\n"
            f"Body preview:\n{preview}\n\n"
            "Ask the user for explicit confirmation. Call send_email again with confirmed=True only if they approve."
        )

    try:
        msg = _build_message(to, subject, body)
        _send_via_smtp(msg)
    except RuntimeError as exc:
        return f"Erreur email : {exc} L'email n'a pas été envoyé."
    except Exception as exc:
        logger.exception("SMTP send failed")
        return f"Erreur email : l'envoi a échoué ({type(exc).__name__}). L'email n'a pas été envoyé."
    return f"Email sent to {to} with subject '{subject}'."
