from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import settings
from app.tools import calendar as calendar_tools
from app.tools.search import search_web
from app.tools.weather import get_weather

SYSTEM_PROMPT = (
    "You are a personal AI assistant. Use the available tools when you need "
    "current information such as web search results, weather, or the user's "
    "Google Calendar. Be concise and accurate."
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
