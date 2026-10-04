from __future__ import annotations

import os
import httpx


class SearchNotConfigured(RuntimeError):
    pass


async def search_web(query: str, max_results: int = 12) -> list[str]:
    """Search the public web using Tavily when configured.

    SourceDNA deliberately keeps search provider logic separate from evidence scoring.
    This makes the engine testable and lets deployments swap providers later.
    """
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise SearchNotConfigured(
            "Live discovery needs TAVILY_API_KEY. You can still analyze pasted source URLs or run the built-in demo."
        )

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.post("https://api.tavily.com/search", json=payload)
        r.raise_for_status()
        data = r.json()
    urls: list[str] = []
    for item in data.get("results", []):
        url = item.get("url")
        if isinstance(url, str) and url.startswith(("http://", "https://")) and url not in urls:
            urls.append(url)
    return urls[:max_results]
