import functools
import logging
import os
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
TOKEN_ERROR_MESSAGE = (
    "Erreur Google Calendar : token OAuth (token.json) introuvable ou invalide. "
    "Veuillez exécuter le flux OAuth."
)


class CalendarAuthError(Exception):
    """The OAuth token is missing, invalid, or could not be refreshed."""


def _get_service():
    """Build the Google Calendar client from a saved OAuth2 token.

    The token.json file is created once by running the OAuth consent flow
    (google_auth_oauthlib InstalledAppFlow) with credentials.json from the
    Google Cloud console. The token is refreshed automatically when expired.
    Raises CalendarAuthError (never RuntimeError) when the token is unusable.
    """
    if not os.path.exists(TOKEN_FILE):
        raise CalendarAuthError(f"OAuth token not found at {TOKEN_FILE}")
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        return build("calendar", "v3", credentials=creds, cache_discovery=False)
    except Exception as exc:
        raise CalendarAuthError(
            f"OAuth token at {TOKEN_FILE} is invalid ({type(exc).__name__})"
        ) from exc


def _safe_tool(func):
    """Convert any exception raised by a tool into a readable error string."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CalendarAuthError as exc:
            logger.warning("Calendar auth problem in %s: %s", func.__name__, exc)
            return TOKEN_ERROR_MESSAGE
        except HttpError as exc:
            logger.warning("Calendar API error in %s: %s", func.__name__, exc)
            return f"Erreur Google Calendar : l'API a renvoyé une erreur (HTTP {exc.resp.status})."
        except Exception as exc:
            logger.exception("Unexpected error in %s", func.__name__)
            return f"Erreur Google Calendar inattendue dans {func.__name__} : {type(exc).__name__}."

    return wrapper


@_safe_tool
def list_calendar_events(max_results: int = 10) -> str:
    """List the upcoming events from the primary Google Calendar."""
    service = _get_service()
    now = datetime.now(timezone.utc).isoformat()
    result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = result.get("items", [])
    if not events:
        return "No upcoming events found."
    lines = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        lines.append(f"- {event.get('summary', '(no title)')}: {start} to {end}")
    return "\n".join(lines)


@_safe_tool
def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
) -> str:
    """Create an event in the primary Google Calendar.

    start_time and end_time must be ISO 8601 datetimes with a UTC offset,
    for example 2026-10-25T14:00:00+01:00.
    """
    service = _get_service()
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }
    event = service.events().insert(calendarId=CALENDAR_ID, body=body).execute()
    return f"Event created: {event.get('summary')} ({event.get('start', {}).get('dateTime')}), link: {event.get('htmlLink')}"
