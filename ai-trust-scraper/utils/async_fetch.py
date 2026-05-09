"""
async_fetch.py
--------------
Async HTTP helper using aiohttp.
Provides a thin wrapper around GET requests with retry logic,
rate-limiting, and a shared session for connection pooling.

Usage:
    from utils.async_fetch import fetch_html, fetch_json

    html = await fetch_html("https://example.com")
    data = await fetch_json("https://api.example.com/data")
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logging.warning(
        "[async_fetch] aiohttp not installed — falling back to urllib. "
        "Run: pip install aiohttp"
    )

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────
DEFAULT_TIMEOUT     = aiohttp.ClientTimeout(total=30) if AIOHTTP_AVAILABLE else None
DEFAULT_HEADERS     = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control":   "no-cache",
    "Pragma":          "no-cache",
}
MAX_RETRIES         = 3
RETRY_BACKOFF_BASE  = 2   # seconds; actual delay = RETRY_BACKOFF_BASE ** attempt

# HTTP status codes that are transient → retry with backoff
_RETRIABLE_STATUSES  = {429, 500, 502, 503, 504}
# HTTP status codes that mean "access denied" → skip with a WARNING, not ERROR
_ACCESS_DENIED_STATUSES = {401, 403, 404, 410}

# ── Shared session ─────────────────────────────────────────────────────────
_session: Optional["aiohttp.ClientSession"] = None


async def get_session() -> "aiohttp.ClientSession":
    """Return a reusable aiohttp session (created lazily)."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            headers=DEFAULT_HEADERS,
            timeout=DEFAULT_TIMEOUT,
        )
    return _session


async def close_session() -> None:
    """Close the shared session gracefully. Call before program exit."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None
        logger.debug("[async_fetch] Session closed.")


# ── Core fetch functions ───────────────────────────────────────────────────

async def fetch_html(url: str, retries: int = MAX_RETRIES) -> str:
    """
    Fetch a URL and return the response body as a string.

    Args:
        url (str): The URL to fetch.
        retries (int): Number of retry attempts on transient errors.

    Returns:
        str: Response body text, or empty string on failure.
    """
    if not AIOHTTP_AVAILABLE:
        return await _urllib_fallback(url)

    session = await get_session()
    for attempt in range(1, retries + 1):
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                text = await resp.text(errors="replace")
                logger.debug(f"[async_fetch] GET {url} → {resp.status}")
                return text
        except aiohttp.ClientResponseError as exc:
            if exc.status in _RETRIABLE_STATUSES:
                delay = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    f"[async_fetch] {exc.status} on attempt {attempt}/{retries} "
                    f"for {url}. Retrying in {delay}s…"
                )
                await asyncio.sleep(delay)
            elif exc.status in _ACCESS_DENIED_STATUSES:
                logger.warning(
                    f"[async_fetch] HTTP {exc.status} — access denied/not found, skipping: {url}"
                )
                return ""
            else:
                logger.warning(f"[async_fetch] HTTP {exc.status} — skipping: {url}")
                return ""
        except Exception as exc:
            delay = RETRY_BACKOFF_BASE ** attempt
            logger.warning(
                f"[async_fetch] Attempt {attempt}/{retries} failed ({exc}). "
                f"Retrying in {delay}s…"
            )
            await asyncio.sleep(delay)

    logger.error(f"[async_fetch] All {retries} attempts failed for {url}")
    return ""


async def fetch_json(url: str, retries: int = MAX_RETRIES) -> Any:
    """
    Fetch a URL and return the parsed JSON body.

    Returns:
        Any: Parsed JSON (dict / list), or None on failure.
    """
    if not AIOHTTP_AVAILABLE:
        import json
        raw = await _urllib_fallback(url)
        try:
            return json.loads(raw)
        except Exception:
            return None

    session = await get_session()
    for attempt in range(1, retries + 1):
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
                logger.debug(f"[async_fetch] JSON GET {url} → {resp.status}")
                return data
        except Exception as exc:
            delay = RETRY_BACKOFF_BASE ** attempt
            logger.warning(f"[async_fetch] JSON attempt {attempt}/{retries} failed ({exc}).")
            await asyncio.sleep(delay)

    return None


async def fetch_many(urls: list[str], concurrency: int = 5) -> list[str]:
    """
    Fetch multiple URLs concurrently, honouring *concurrency* limit.

    Returns:
        list[str]: Response texts in the same order as *urls*.
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def _bounded_fetch(url: str) -> str:
        async with semaphore:
            return await fetch_html(url)

    return list(await asyncio.gather(*[_bounded_fetch(u) for u in urls]))


# ── urllib fallback (no aiohttp) ───────────────────────────────────────────

async def _urllib_fallback(url: str) -> str:
    """Blocking urllib request wrapped in a thread-pool executor."""
    import urllib.request
    loop = asyncio.get_event_loop()
    def _get():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:
            logger.error(f"[async_fetch] urllib fallback failed for {url}: {exc}")
            return ""
    return await loop.run_in_executor(None, _get)


# ── Quick smoke-test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    async def _main():
        html = await fetch_html("https://httpbin.org/get")
        print(html[:300])
        await close_session()

    asyncio.run(_main())
