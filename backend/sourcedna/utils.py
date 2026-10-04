from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse, urljoin


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def domain_of(url: str) -> str:
    host = (urlparse(url).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def normalize_url(url: str) -> str:
    p = urlparse(url)
    scheme = p.scheme.lower()
    host = (p.hostname or "").lower()
    port = f":{p.port}" if p.port and not ((scheme == "http" and p.port == 80) or (scheme == "https" and p.port == 443)) else ""
    path = re.sub(r"/{2,}", "/", p.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return f"{scheme}://{host}{port}{path}" + (f"?{p.query}" if p.query else "")


def is_safe_public_url(url: str) -> bool:
    p = urlparse(url)
    if p.scheme not in {"http", "https"} or not p.hostname:
        return False
    host = p.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast)
    except ValueError:
        pass
    # Best-effort DNS guard. DNS rebinding must still be handled by production network policy.
    try:
        for _, _, _, _, sockaddr in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
    except socket.gaierror:
        # Let the HTTP layer report an unreachable host.
        return True
    return True


def absolute_http_links(base_url: str, links: list[str], max_links: int = 150) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for href in links:
        try:
            u = urljoin(base_url, href)
            p = urlparse(u)
            if p.scheme not in {"http", "https"}:
                continue
            u = normalize_url(u)
            if u not in seen:
                seen.add(u)
                out.append(u)
            if len(out) >= max_links:
                break
        except Exception:
            continue
    return out
