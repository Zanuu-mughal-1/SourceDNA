from __future__ import annotations

from .analysis import analyze_documents
from .fetcher import fetch_many
from .search import search_web


async def analyze_claim(claim: str, source_urls: list[str] | None = None, max_sources: int = 12):
    urls = [str(u) for u in (source_urls or [])]
    warnings: list[str] = []
    if not urls:
        urls = await search_web(claim, max_results=max_sources)
    urls = urls[:max_sources]
    docs, fetch_warnings = await fetch_many(urls)
    warnings.extend(fetch_warnings)
    return analyze_documents(claim, docs, warnings)
