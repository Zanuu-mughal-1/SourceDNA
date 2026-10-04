from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .models import SourceDocument
from .utils import absolute_http_links, clean_text, domain_of, is_safe_public_url, normalize_url

USER_AGENT = "SourceDNA/0.1 (+https://github.com/yourname/sourcedna; evidence provenance research)"
MAX_BYTES = 2_000_000


def _extract_date(soup: BeautifulSoup) -> str | None:
    candidates = [
        ("meta", {"property": "article:published_time"}, "content"),
        ("meta", {"name": "date"}, "content"),
        ("meta", {"name": "pubdate"}, "content"),
        ("meta", {"itemprop": "datePublished"}, "content"),
        ("time", {}, "datetime"),
    ]
    for tag, attrs, key in candidates:
        el = soup.find(tag, attrs=attrs)
        value = el.get(key) if el else None
        if value:
            value = str(value).strip()
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
            except ValueError:
                return value[:80]
    return None


def _extract_main_text(soup: BeautifulSoup) -> str:
    for bad in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form"]):
        bad.decompose()
    preferred = soup.find("article") or soup.find("main") or soup.body or soup
    parts = [clean_text(x.get_text(" ", strip=True)) for x in preferred.find_all(["h1", "h2", "p", "li", "blockquote"])]
    text = clean_text(" ".join(p for p in parts if len(p) >= 20))
    if not text:
        text = clean_text(preferred.get_text(" ", strip=True))
    return text[:80_000]


async def fetch_document(client: httpx.AsyncClient, url: str, rank: int | None = None) -> SourceDocument:
    url = normalize_url(url)
    if not is_safe_public_url(url):
        raise ValueError(f"Unsafe or unsupported URL: {url}")

    async with client.stream("GET", url, follow_redirects=True) as response:
        response.raise_for_status()
        ctype = response.headers.get("content-type", "")
        if "text/html" not in ctype and "text/plain" not in ctype:
            raise ValueError(f"Unsupported content type: {ctype or 'unknown'}")
        buf = bytearray()
        async for chunk in response.aiter_bytes():
            buf.extend(chunk)
            if len(buf) > MAX_BYTES:
                break
        html = bytes(buf).decode(response.encoding or "utf-8", errors="replace")
        final_url = str(response.url)

    soup = BeautifulSoup(html, "html.parser")
    title = clean_text((soup.title.string if soup.title and soup.title.string else "")) or domain_of(final_url)
    links = absolute_http_links(final_url, [a.get("href", "") for a in soup.find_all("a", href=True)])
    text = _extract_main_text(soup)
    if len(text) < 120:
        raise ValueError("Page did not contain enough readable text")

    sid = "s_" + hashlib.sha1(final_url.encode()).hexdigest()[:10]
    return SourceDocument(
        id=sid,
        url=final_url,
        domain=domain_of(final_url),
        title=title[:300],
        text=text,
        published_at=_extract_date(soup),
        links=links,
        search_rank=rank,
    )


async def fetch_many(urls: list[str], concurrency: int = 6) -> tuple[list[SourceDocument], list[str]]:
    timeout = httpx.Timeout(15.0, connect=8.0)
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.2"}
    semaphore = asyncio.Semaphore(concurrency)
    docs: list[SourceDocument] = []
    warnings: list[str] = []

    async with httpx.AsyncClient(timeout=timeout, limits=limits, headers=headers) as client:
        async def one(i: int, url: str):
            async with semaphore:
                try:
                    docs.append(await fetch_document(client, url, i + 1))
                except Exception as exc:
                    warnings.append(f"Could not read {url}: {type(exc).__name__}: {exc}")

        await asyncio.gather(*(one(i, u) for i, u in enumerate(urls)))

    docs.sort(key=lambda d: d.search_rank or 999)
    return docs, warnings
