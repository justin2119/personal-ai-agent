import logging

from tavily import AsyncTavilyClient

from app.config import settings

logger = logging.getLogger(__name__)


async def search_web(query: str, max_results: int = 5) -> str:
    """Search the web with Tavily and return a summary of the top results.

    Never raises: on a missing API key or any Tavily failure, returns an error string.
    """
    if not settings.TAVILY_API_KEY:
        return "Erreur recherche web : clé TAVILY_API_KEY non configurée."
    try:
        client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
        response = await client.search(query=query, max_results=max_results)
    except Exception as exc:
        logger.warning("Tavily search failed: %s", type(exc).__name__)
        return f"Erreur recherche web : la recherche a échoué ({type(exc).__name__})."
    lines = []
    for item in response.get("results", []):
        lines.append(f"- {item.get('title')}: {item.get('url')}\n  {item.get('content')}")
    return "\n".join(lines) or "No results found."
