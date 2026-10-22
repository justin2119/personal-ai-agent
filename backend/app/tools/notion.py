import functools
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
TEXT_LIMIT = 2000
TIMEOUT = 15


def _headers() -> dict:
    if not settings.NOTION_API_KEY:
        raise RuntimeError("NOTION_API_KEY is not configured.")
    return {
        "Authorization": f"Bearer {settings.NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _safe_async_tool(func):
    """Convert any exception raised by an async Notion tool into a readable error string."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RuntimeError as exc:
            return f"Erreur Notion : {exc}"
        except httpx.HTTPStatusError as exc:
            logger.warning("Notion API error in %s: HTTP %s", func.__name__, exc.response.status_code)
            return f"Erreur Notion : l'API a renvoyé une erreur (HTTP {exc.response.status_code})."
        except httpx.HTTPError as exc:
            logger.warning("Notion request failed in %s: %s", func.__name__, type(exc).__name__)
            return f"Erreur Notion : connexion impossible ({type(exc).__name__})."
        except Exception as exc:
            logger.exception("Unexpected error in %s", func.__name__)
            return f"Erreur Notion inattendue dans {func.__name__} : {type(exc).__name__}."

    return wrapper


def _title_of(item: dict) -> str:
    """Extract the human-readable title of a Notion page or database."""
    if item.get("object") == "database":
        parts = item.get("title", [])
    else:
        parts = []
        for prop in item.get("properties", {}).values():
            if prop.get("type") == "title":
                parts = prop.get("title", [])
                break
    text = "".join(p.get("plain_text", "") for p in parts).strip()
    return text or "(untitled)"


def _paragraph_blocks(content: str) -> list[dict]:
    """Split plain text into paragraph blocks, respecting Notion's per-text length limit."""
    blocks = []
    for line in content.split("\n"):
        if not line.strip():
            continue
        for start in range(0, len(line), TEXT_LIMIT):
            chunk = line[start : start + TEXT_LIMIT]
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
                }
            )
    return blocks


@_safe_async_tool
async def search_notion(query: str, max_results: int = 5) -> str:
    """Search the Notion workspace for pages and databases by title."""
    payload = {"query": query, "page_size": max(1, min(max_results, 100))}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(f"{NOTION_API_URL}/search", headers=_headers(), json=payload)
        resp.raise_for_status()
        results = resp.json().get("results", [])[:max_results]
    if not results:
        return f"No Notion pages or databases found for '{query}'."
    lines = []
    for item in results:
        kind = item.get("object", "item")
        lines.append(f"- [{kind}] {_title_of(item)} (id: {item.get('id')}, url: {item.get('url')})")
    return "\n".join(lines)


@_safe_async_tool
async def create_notion_page(parent_page_id: str, title: str, content: str = "") -> str:
    """Create a child page under a parent Notion page, with a title and paragraph content."""
    payload = {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": title[:TEXT_LIMIT]}}]}
        },
        "children": _paragraph_blocks(content),
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(f"{NOTION_API_URL}/pages", headers=_headers(), json=payload)
        resp.raise_for_status()
        page = resp.json()
    return f"Notion page created: '{title}' (id: {page.get('id')}, url: {page.get('url')})"
