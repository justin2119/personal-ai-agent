from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.providers.openai import OpenAIProvider

try:
    # Recent pydantic-ai versions
    from pydantic_ai.models.openai import OpenAIChatModel as OpenAIModel
except ImportError:
    # Older pydantic-ai versions
    from pydantic_ai.models.openai import OpenAIModel

from app.config import settings
from app.tools import calendar as calendar_tools
from app.tools import drive as drive_tools
from app.tools import email as email_tools
from app.tools import notion as notion_tools
from app.tools.search import search_web
from app.tools.weather import get_weather

SYSTEM_PROMPT = (
    "You are a personal AI assistant. Use the available tools when you need "
    "current information such as web search results, weather, the user's "
    "Google Calendar, the user's Google Drive files, the user's Notion workspace, or sending email. "
    "Be concise and accurate.\n\n"
    "Email rule: never send an email on your own initiative. First call send_email with confirmed=False "
    "to get a summary. Show the user the recipient, the subject and the body preview, and ask for explicit "
    "confirmation. Only call send_email with confirmed=True after the user clearly approves that exact "
    "version. If the user changes anything, prepare a new summary and ask again."
)


def build_model() -> OpenAIModel:
    client = AsyncOpenAI(
        api_key=settings.RODIUM_API_KEY,
        base_url=settings.RODIUM_BASE_URL,
    )
    return OpenAIModel(
        model_name="default",
        provider=OpenAIProvider(openai_client=client),
    )


agent = Agent(
    build_model(),
    system_prompt=SYSTEM_PROMPT,
    tools=[search_web, get_weather],
)


@agent.tool
async def list_calendar_events(ctx: RunContext[None], max_results: int = 10) -> str:
    """List the user's upcoming Google Calendar events.

    Args:
        ctx: The run context.
        max_results: Maximum number of events to return.
    """
    return calendar_tools.list_calendar_events(max_results=max_results)


@agent.tool
async def create_calendar_event(
    ctx: RunContext[None],
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
) -> str:
    """Create an event in the user's Google Calendar.

    Args:
        ctx: The run context.
        summary: Title of the event.
        start_time: Start as ISO 8601 with UTC offset, e.g. 2026-10-25T14:00:00+01:00.
        end_time: End as ISO 8601 with UTC offset, e.g. 2026-10-25T15:00:00+01:00.
        description: Optional event description.
    """
    return calendar_tools.create_calendar_event(
        summary=summary,
        start_time=start_time,
        end_time=end_time,
        description=description,
    )


@agent.tool
async def search_drive_files(ctx: RunContext[None], query: str, max_results: int = 10) -> str:
    """Search the user's Google Drive files by name or full text content.

    Args:
        ctx: The run context.
        query: Text to search for in file names and contents.
        max_results: Maximum number of files to return.
    """
    return drive_tools.search_drive_files(query=query, max_results=max_results)


@agent.tool
async def read_drive_file(ctx: RunContext[None], file_id: str) -> str:
    """Read the text content of a Google Drive file (Google Docs and text files).

    Args:
        ctx: The run context.
        file_id: The Drive file ID, as returned by search_drive_files.
    """
    return drive_tools.read_drive_file(file_id=file_id)


@agent.tool
async def send_email(
    ctx: RunContext[None],
    to: str,
    subject: str,
    body: str,
    confirmed: bool = False,
) -> str:
    """Send an email via SMTP. Requires explicit user confirmation.

    Call with confirmed=False first to get a summary for the user. Only use confirmed=True
    after the user has explicitly approved that exact recipient, subject and body.

    Args:
        ctx: The run context.
        to: Recipient email address.
        subject: Email subject.
        body: Plain text email body.
        confirmed: Set to True only after explicit user approval.
    """
    return email_tools.send_email(to=to, subject=subject, body=body, confirmed=confirmed)


@agent.tool
async def search_notion(ctx: RunContext[None], query: str, max_results: int = 5) -> str:
    """Search the user's Notion workspace for pages and databases by title.

    Args:
        ctx: The run context.
        query: Text to search for in page and database titles.
        max_results: Maximum number of results to return.
    """
    return await notion_tools.search_notion(query=query, max_results=max_results)


@agent.tool
async def create_notion_page(
    ctx: RunContext[None],
    parent_page_id: str,
    title: str,
    content: str = "",
) -> str:
    """Create a new child page in Notion under a parent page.

    Args:
        ctx: The run context.
        parent_page_id: The ID of the parent Notion page, as returned by search_notion.
        title: Title of the new page.
        content: Text content; each line becomes a paragraph block.
    """
    return await notion_tools.create_notion_page(
        parent_page_id=parent_page_id,
        title=title,
        content=content,
    )
