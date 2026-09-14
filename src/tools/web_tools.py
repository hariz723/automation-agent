"""Web search and web fetching tools for the automation agent."""

import re

import requests
from langchain_core.tools import tool


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for up-to-date information, documentation, news, or answers using DuckDuckGo.

    Args:
        query: The search term or question to look up.
        max_results: Maximum number of search results to return (default: 5).
    """
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    f"Title: {r.get('title', 'N/A')}\n"
                    f"URL: {r.get('href', 'N/A')}\n"
                    f"Snippet: {r.get('body', 'N/A')}"
                )

        if not results:
            return f"No results found for query: '{query}'"

        return "\n\n---\n\n".join(results)

    except Exception as e:
        return f"Web search error: {e!s}"


@tool
def fetch_webpage(url: str) -> str:
    """Fetch the text content of a webpage given its URL.

    Args:
        url: Full HTTP/HTTPS URL of the page to read.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Simple HTML tag stripping
        text = response.text
        text = re.sub(r"<script.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        # Truncate if extremely long
        max_chars = 8000
        if len(text) > max_chars:
            text = (
                text[:max_chars] + f"\n... [Truncated {len(text) - max_chars} remaining characters]"
            )

        return text if text else "Page returned empty content."

    except Exception as e:
        return f"Error fetching {url}: {e!s}"
