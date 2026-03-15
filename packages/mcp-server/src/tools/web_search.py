import asyncio
import logging

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


def _web_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in results
        ]
    except Exception as e:
        logger.warning(f"Web search failed for '{query}': {e}")
        return []


def _news_search(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("body", ""),
                "date": r.get("date", ""),
                "source": r.get("source", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"News search failed for '{query}': {e}")
        return []


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    return await asyncio.to_thread(_web_search, query, max_results)


async def news_search(query: str, max_results: int = 5) -> list[dict]:
    return await asyncio.to_thread(_news_search, query, max_results)


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Returns titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "news_search",
            "description": "Search for recent news articles. Returns titles, URLs, snippets, dates, and sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "News search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
]


async def execute_tool(name: str, args: dict) -> list[dict] | str:
    if name == "web_search":
        return await web_search(args["query"], args.get("max_results", 5))
    elif name == "news_search":
        return await news_search(args["query"], args.get("max_results", 5))
    return f"Unknown tool: {name}"
