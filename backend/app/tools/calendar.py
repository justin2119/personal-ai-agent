import os
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")


def _get_service():
    """Build the Google Calendar client from a saved OAuth2 token.

    The token.json file is created once by running the OAuth consent flow
    (google_auth_oauthlib InstalledAppFlow) with credentials.json from the
    Google Cloud console. The token is refreshed automatically when expired.
    """
    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError(
            f"Google OAuth token not found at {TOKEN_FILE}. Run the OAuth flow first."
        )
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


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
