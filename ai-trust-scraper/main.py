"""
main.py
-------
Entry point for the AI Trust Scraper pipeline.

Usage:
  python main.py
  python main.py --log-level DEBUG
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from scraper.blog_scraper    import scrape_blogs
from scraper.youtube_scraper import scrape_youtube
from scraper.pubmed_scraper  import scrape_pubmed
from scoring.trust_score     import batch_score
from utils.async_fetch       import close_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")

OUTPUT_DIR = Path(__file__).parent / "output" / "scraped_data"

# ── Clean schema fields (strip internal _ fields before saving) ─────────────
SCHEMA_FIELDS = [
    "source_url", "source_type", "title", "author", "published_date",
    "language", "region", "topic_tags", "trust_score", "content_chunks",
    "score_breakdown",
]

def _clean(item: dict) -> dict:
    """Return only the public-facing assignment schema fields."""
    return {k: item[k] for k in SCHEMA_FIELDS if k in item}


def _save(items: list[dict], filename: str) -> Path:
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(items)} item(s) → {path}")
    return path


async def main() -> None:
    parser = argparse.ArgumentParser(description="AI Trust Scraper — Assignment Runner")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()
    logging.getLogger().setLevel(args.log_level)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Run all scrapers concurrently ─────────────────────────────────────
    logger.info("Starting all scrapers concurrently…")
    try:
        blog_items, yt_items, pm_items = await asyncio.gather(
            scrape_blogs(),
            scrape_youtube(),
            scrape_pubmed(max_results=1),
            return_exceptions=False,
        )
    except Exception as exc:
        logger.error(f"Scraper error: {exc}")
        await close_session()
        return
    finally:
        await close_session()

    # ── Apply trust scoring ───────────────────────────────────────────────
    logger.info("Applying trust scores…")
    blog_items = batch_score(blog_items)
    yt_items   = batch_score(yt_items)
    pm_items   = batch_score(pm_items)

    # ── Save combined JSON file ──────────────────────────────────────────
    all_items = blog_items + yt_items + pm_items
    all_items.sort(key=lambda x: float(x.get("trust_score") or 0), reverse=True)
    
    combined_path = OUTPUT_DIR.parent / "scraped_data.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump([_clean(i) for i in all_items], f, indent=2, ensure_ascii=False)

    # ── Summary report ────────────────────────────────────────────────────
    logger.info("\n" + "═" * 60)
    logger.info(f"  Blogs scraped:   {len(blog_items)}")
    logger.info(f"  YouTube scraped: {len(yt_items)}")
    logger.info(f"  PubMed scraped:  {len(pm_items)}")
    logger.info(f"  Total:           {len(all_items)}")
    logger.info("═" * 60)
    logger.info("Sample trust scores:")
    for item in all_items[:6]:
        logger.info(
            f"  [{item['source_type']:8s}] {item.get('title','')[:50]:50s} → {item['trust_score']}"
        )
    logger.info(f"\nOutput directory: {combined_path.resolve()}")
    logger.info("Pipeline complete.")


if __name__ == "__main__":
    asyncio.run(main())
