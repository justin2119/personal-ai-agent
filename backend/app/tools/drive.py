import functools
import io
import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.readonly",
]
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
MAX_READ_CHARS = 20000
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
TEXT_MIME_PREFIXES = ("text/",)
TEXT_MIME_EXACT = {
    "application/json",
    "application/xml",
    "application/javascript",
    "application/x-yaml",
    "application/yaml",
    "application/csv",
}
TOKEN_ERROR_MESSAGE = (
    "Erreur Google Drive : token OAuth (token.json) introuvable ou invalide. "
    "Veuillez exécuter le flux OAuth."
)


class DriveAuthError(Exception):
    """The OAuth token is missing, invalid, or could not be refreshed."""


def _get_service():
    """Build the Google Drive client from the same OAuth2 token.json used by calendar.py.

    The token is refreshed automatically when expired. It must have been created
    with the drive.readonly scope included in SCOPES.
    Raises DriveAuthError (never RuntimeError) when the token is unusable.
    """
    if not os.path.exists(TOKEN_FILE):
        raise DriveAuthError(f"OAuth token not found at {TOKEN_FILE}")
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as exc:
        raise DriveAuthError(
            f"OAuth token at {TOKEN_FILE} is invalid ({type(exc).__name__})"
        ) from exc


def _safe_tool(func):
    """Convert any exception raised by a tool into a readable error string."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DriveAuthError as exc:
            logger.warning("Drive auth problem in %s: %s", func.__name__, exc)
            return TOKEN_ERROR_MESSAGE
        except HttpError as exc:
            logger.warning("Drive API error in %s: %s", func.__name__, exc)
            return f"Erreur Google Drive : l'API a renvoyé une erreur (HTTP {exc.resp.status})."
        except Exception as exc:
            logger.exception("Unexpected error in %s", func.__name__)
            return f"Erreur Google Drive inattendue dans {func.__name__} : {type(exc).__name__}."

    return wrapper


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


@_safe_tool
def search_drive_files(query: str, max_results: int = 10) -> str:
    """Search Google Drive files by name or full text content."""
    service = _get_service()
    escaped = _escape(query)
    q = f"(name contains '{escaped}' or fullText contains '{escaped}') and trashed = false"
    result = (
        service.files()
        .list(
            q=q,
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
        )
        .execute()
    )
    files = result.get("files", [])
    if not files:
        return f"No Drive files found for '{query}'."
    lines = []
    for f in files:
        lines.append(
            f"- {f.get('name')} (id: {f.get('id')}, type: {f.get('mimeType')}, "
            f"modified: {f.get('modifiedTime')}, link: {f.get('webViewLink')})"
        )
    return "\n".join(lines)


@_safe_tool
def read_drive_file(file_id: str) -> str:
    """Read the text content of a Google Drive file.

    Google Docs are exported as plain text. Text-based files are downloaded as-is.
    Other file types are not supported.
    """
    service = _get_service()
    meta = (
        service.files()
        .get(fileId=file_id, fields="id, name, mimeType")
        .execute()
    )
    name = meta.get("name")
    mime = meta.get("mimeType", "")

    if mime == GOOGLE_DOC_MIME:
        data = service.files().export(fileId=file_id, mimeType="text/plain").execute()
        text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
    elif mime.startswith(TEXT_MIME_PREFIXES) or mime in TEXT_MIME_EXACT:
        request = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        text = buffer.getvalue().decode("utf-8", errors="replace")
    else:
        return f"Cannot read '{name}': unsupported file type {mime}."

    if len(text) > MAX_READ_CHARS:
        text = text[:MAX_READ_CHARS] + f"\n\n[truncated at {MAX_READ_CHARS} characters]"
    return f"{name}:\n{text}"
