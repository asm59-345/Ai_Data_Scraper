"""
scraper/youtube_scraper.py
---------------------------
Scrapes exactly 2 YouTube videos and returns assignment-schema dicts.

Metadata strategy (no API key required):
  - Title & channel name → YouTube oEmbed endpoint
  - Publish date         → YouTube page HTML (og:updated_time / datePublished JSON-LD)
  - Description          → YouTube page JSON-LD or meta
  - Transcript           → youtube-transcript-api

Target videos (AI/ML focus):
  1. Andrej Karpathy — "Let's build GPT: from scratch"  (kCc8FmEb1nY)
  2. 3Blue1Brown — "But what is a neural network?"       (aircAruvnKk)
"""

from __future__ import annotations
import asyncio
import json
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from utils.async_fetch import fetch_html, fetch_json
from utils.tagging import tag_content
from utils.chunking import chunk_text

try:
    from langdetect import detect as _detect_lang
    def detect_language(text: str) -> str:
        try:
            return _detect_lang(text[:500]) if text else "en"
        except Exception:
            return "en"
except ImportError:
    def detect_language(text: str) -> str:
        return "en"

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_OK = True
except ImportError:
    TRANSCRIPT_OK = False

# ── Target video IDs ─────────────────────────────────────────────────────────
TARGET_VIDEO_IDS = [
    "kCc8FmEb1nY",   # Andrej Karpathy — Let's build GPT from scratch
    "aircAruvnKk",   # 3Blue1Brown — But what is a neural network?
]


# ── Public entry point ────────────────────────────────────────────────────────

async def scrape_youtube(query: str | None = None, video_ids: list[str] | None = None, lang: str = "en") -> list[dict]:
    """Return assignment-schema dicts for each video ID or search query."""
    if query:
        ids = await _search_youtube_ids(query)
    else:
        ids = video_ids or TARGET_VIDEO_IDS
        
    tasks  = [_scrape_video(vid, lang) for vid in ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"[YouTubeScraper] ERROR on {ids[i]}: {r}")
        elif r:
            out.append(r)
    print(f"[YouTubeScraper] Scraped {len(out)} video(s).")
    return out

async def _search_youtube_ids(query: str, max_results: int = 2) -> list[str]:
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    html = await fetch_html(url)
    matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html or "")
    seen = set()
    vids = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            vids.append(m)
            if len(vids) >= max_results:
                break
    return vids


async def _scrape_video(video_id: str, lang: str) -> dict:
    vid_url = f"https://www.youtube.com/watch?v={video_id}"

    # ── 1. oEmbed (title + channel name, no API key needed) ─────────────────
    oembed_url = f"https://www.youtube.com/oembed?url={vid_url}&format=json"
    oembed     = await fetch_json(oembed_url) or {}
    title      = oembed.get("title", f"YouTube video {video_id}")
    channel    = oembed.get("author_name", "Unknown Channel")

    # ── 2. Page HTML for date, description, region ──────────────────────────
    html        = await fetch_html(vid_url)
    pub_date    = ""
    description = ""
    region      = "US"

    if html:
        soup = BeautifulSoup(html, "lxml")

        # JSON-LD block often carries datePublished
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                ld = json.loads(script.string or "{}")
                if isinstance(ld, list):
                    ld = next((x for x in ld if "datePublished" in x), {})
                pub_date    = pub_date or ld.get("datePublished", "")[:10]
                description = description or ld.get("description", "")[:500]
                region      = ld.get("regionsAllowed", region)[:2] if isinstance(ld.get("regionsAllowed"), str) else region
            except Exception:
                pass

        # og meta fallback
        pub_date    = pub_date or _og(soup, "og:updated_time") or _og(soup, "og:video:release_date")
        description = description or _og(soup, "og:description") or ""
        if pub_date:
            pub_date = pub_date[:10]

    # ── 3. Transcript ─────────────────────────────────────────────────────────
    transcript_text = await _get_transcript(video_id, lang)
    if not transcript_text:
        transcript_text = description  # fall back to description if no transcript

    # ── 4. Tags & chunks ──────────────────────────────────────────────────────
    combined = f"{title} {description} {transcript_text}"
    tags     = tag_content(combined)
    chunks   = chunk_text(transcript_text or description)
    language = detect_language(transcript_text or description or title)

    return {
        "source_url":     vid_url,
        "source_type":    "youtube",
        "title":          title,
        "author":         channel,
        "published_date": pub_date,
        "language":       language,
        "region":         region if len(region) == 2 else "US",
        "topic_tags":     tags,
        "trust_score":    "",
        "content_chunks": chunks,
        "_raw_text":      transcript_text,
        "_description":   description,
    }


async def _get_transcript(video_id: str, lang: str) -> str:
    if not TRANSCRIPT_OK:
        return ""
    loop = asyncio.get_event_loop()
    try:
        segments = await loop.run_in_executor(
            None,
            lambda: YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, "en"])
        )
        return " ".join(s["text"] for s in segments)
    except Exception as exc:
        print(f"[YouTubeScraper] Transcript unavailable for {video_id}: {exc}")
        return ""


def _og(soup: BeautifulSoup, name: str) -> str:
    el = soup.find("meta", property=name) or soup.find("meta", attrs={"name": name})
    return (el.get("content") or "").strip() if el else ""


# ── Smoke-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def _main():
        videos = await scrape_youtube()
        for v in videos:
            print(f"\n  Title:   {v['title'][:60]}")
            print(f"  Channel: {v['author']}")
            print(f"  Date:    {v['published_date']}")
            print(f"  Lang:    {v['language']}  Region: {v['region']}")
            print(f"  Tags:    {v['topic_tags']}")
            print(f"  Chunks:  {len(v['content_chunks'])}")

    asyncio.run(_main())
