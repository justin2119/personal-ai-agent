from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import settings
from app.tools.search import search_web
from app.tools.weather import get_weather

SYSTEM_PROMPT = (
    "You are a personal AI assistant. Use the available tools when you need "
    "current information such as web search results or weather. Be concise and accurate."
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
