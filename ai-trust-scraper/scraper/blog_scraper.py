"""
scraper/blog_scraper.py
------------------------
Scrapes exactly 3 blog posts and returns objects matching the assignment schema.
Extracts: author, published_date, language, region, topic_tags, content_chunks.

Target blogs (stable, publicly accessible):
  1. HuggingFace Blog — /blog/llama3
  2. HuggingFace Blog — /blog/smollm2
  3. HuggingFace Blog — /blog/open-llm-leaderboard-v2
"""

from __future__ import annotations
import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from utils.async_fetch import fetch_html
from utils.tagging import tag_content
from utils.chunking import chunk_text

# ── Detect language (optional dep) ─────────────────────────────────────────
try:
    from langdetect import detect as _detect_lang
    def detect_language(text: str) -> str:
        try:
            return _detect_lang(text[:500]) if text else "en"
        except Exception:
            return "en"
except ImportError:
    def detect_language(text: str) -> str:
        return "en"   # fallback

# ── Known region map by domain keyword ─────────────────────────────────────
DOMAIN_REGION: dict[str, str] = {
    "huggingface": "US",
    "openai":      "US",
    "deepmind":    "US",
    "google":      "US",
    "nature":      "GB",
    "bbc":         "GB",
    "mit":         "US",
}

TARGET_BLOGS = [
    # Hugging Face
    "https://huggingface.co/blog/",
    # DeepMind
    "https://deepmind.google/discover/blog/",
    # OpenAI
    "https://openai.com/index/",
    # Anthropic
    "https://www.anthropic.com/",
    # Perplexity
    "https://www.perplexity.ai/hub/blog/",
    # Microsoft
    "https://blogs.microsoft.com/blog/"
]


# ── Public entry point ──────────────────────────────────────────────────────

async def scrape_blogs(urls: list[str] | None = None) -> list[dict]:
    """
    Scrape blog posts and return a list of assignment-schema dicts.
    Falls back to TARGET_BLOGS if no URLs are supplied.
    """
    targets = (urls or TARGET_BLOGS)[:3]
    tasks   = [_scrape_one(url) for url in targets]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"[BlogScraper] ERROR on {targets[i]}: {r}")
        elif r:
            out.append(r)
    print(f"[BlogScraper] Scraped {len(out)} blog post(s).")
    return out


async def _scrape_one(url: str) -> dict | None:
    html = await fetch_html(url)
    if not html:
        print(f"[BlogScraper] No content for {url}")
        return None

    soup = BeautifulSoup(html, "lxml")

    # ── Metadata ────────────────────────────────────────────────────────────
    title   = _meta(soup, "og:title") or _tag_text(soup, "h1") or "Untitled"
    author  = (
        _meta(soup, "article:author")
        or _meta(soup, "author")
        or _meta(soup, "twitter:creator")
        or _byline(soup)
        or urlparse(url).netloc.replace("www.", "").split(".")[0].capitalize() + " Team"
    )
    pub_date = (
        _meta(soup, "article:published_time")
        or _meta(soup, "datePublished")
        or _time_tag(soup)
        or ""
    )
    if pub_date:
        pub_date = pub_date[:10]   # keep YYYY-MM-DD only

    # ── Content ─────────────────────────────────────────────────────────────
    for tag in soup(["nav", "footer", "script", "style", "header", "aside", "form"]):
        tag.decompose()

    article_el = soup.find("article") or soup.find("main") or soup.body
    raw_text   = article_el.get_text(" ", strip=True) if article_el else ""

    # ── Language & region ───────────────────────────────────────────────────
    lang_attr = soup.html.get("lang", "") if soup.html else ""
    language  = lang_attr.split("-")[0] if lang_attr else detect_language(raw_text)
    region    = _region_from_url(url)

    # ── Tags & chunks ───────────────────────────────────────────────────────
    tags   = tag_content(raw_text)
    chunks = chunk_text(raw_text)

    return {
        "source_url":     url,
        "source_type":    "blog",
        "title":          title,
        "author":         author,
        "published_date": pub_date,
        "language":       language,
        "region":         region,
        "topic_tags":     tags,
        "trust_score":    "",        # filled by trust_score module
        "content_chunks": chunks,
        "_raw_text":      raw_text,  # kept for scoring; stripped before final save
    }


# ── Helpers ─────────────────────────────────────────────────────────────────

def _meta(soup: BeautifulSoup, name: str) -> str:
    """Look for <meta property|name="…"> content."""
    el = soup.find("meta", property=name) or soup.find("meta", attrs={"name": name})
    return (el.get("content") or "").strip() if el else ""


def _tag_text(soup: BeautifulSoup, tag: str) -> str:
    el = soup.find(tag)
    return el.get_text(strip=True) if el else ""


def _byline(soup: BeautifulSoup) -> str:
    """Try common byline CSS selectors."""
    selectors = [
        "[class*='author']", "[class*='byline']", "[rel='author']",
        "[itemprop='author']", "[class*='writer']",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            if text and len(text) < 80:
                return text
    return ""


def _time_tag(soup: BeautifulSoup) -> str:
    el = soup.find("time")
    if el:
        return el.get("datetime") or el.get_text(strip=True)
    return ""


def _region_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    for keyword, region in DOMAIN_REGION.items():
        if keyword in host:
            return region
    # TLD heuristic
    tld = host.rsplit(".", 1)[-1]
    TLD_MAP = {"uk": "GB", "de": "DE", "fr": "FR", "cn": "CN", "in": "IN", "jp": "JP"}
    return TLD_MAP.get(tld, "US")


# ── Smoke-test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def _main():
        posts = await scrape_blogs()
        for p in posts:
            print(f"\n  Title:  {p['title'][:60]}")
            print(f"  Author: {p['author']}")
            print(f"  Date:   {p['published_date']}")
            print(f"  Lang:   {p['language']}  Region: {p['region']}")
            print(f"  Tags:   {p['topic_tags']}")
            print(f"  Chunks: {len(p['content_chunks'])}")

    asyncio.run(_main())
