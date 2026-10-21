from tavily import AsyncTavilyClient

from app.config import settings


async def search_web(query: str, max_results: int = 5) -> str:
    """Search the web with Tavily and return a summary of the top results."""
    client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
    response = await client.search(query=query, max_results=max_results)
    lines = []
    for item in response.get("results", []):
        lines.append(f"- {item.get('title')}: {item.get('url')}\n  {item.get('content')}")
    return "\n".join(lines) or "No results found."
