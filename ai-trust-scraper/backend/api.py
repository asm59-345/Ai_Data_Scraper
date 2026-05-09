"""
backend/api.py
--------------
FastAPI REST API for the AI Trust Scraper project.

Endpoints:
  GET    /                     Health check
  POST   /scrape               Trigger the scraping pipeline (background task)
  GET    /scrape/status        Pipeline running / last-run status
  GET    /results              Paginated results (filters: min_score, tag, source)
  GET    /results/{source}     Filter by source type
  GET    /stats                Aggregated statistics
  GET    /tags                 All unique tags across all results
  DELETE /results              Clear the results file

Run from project root:
  uvicorn backend.api:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ── Ensure project root is on sys.path so scraper/scoring/utils import cleanly
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scraper.blog_scraper    import scrape_blogs
from scraper.pubmed_scraper  import scrape_pubmed
from scraper.youtube_scraper import scrape_youtube
from scoring.trust_score     import batch_score
from utils.async_fetch       import close_session

# ── Output file resolution (priority order) ──────────────────────────────────
#   1. output/scraped_data.json       — required by assignment
NEW_OUTPUT_FILE    = ROOT / "output" / "scraped_data.json"
LEGACY_OUTPUT_FILE = ROOT / "output" / "scraped_data.json"
# API-triggered scrapes write to the new path so they appear first next time
API_OUTPUT_FILE    = NEW_OUTPUT_FILE

# Ensure directories exist
NEW_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("api")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Trust Scraper API",
    description=(
        "Scrape, score, and explore AI content from Blogs, YouTube, and PubMed.\n\n"
        "**Trust scores** are normalised to floats in [0, 1] (displayed as 0–100)."
    ),
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")

# ── In-memory scrape state ────────────────────────────────────────────────────
_scrape_status: dict = {"running": False, "last_run": None, "error": None}


# ── Pydantic models ───────────────────────────────────────────────────────────
class ScrapeRequest(BaseModel):
    sources:     list[Literal["blog", "youtube", "pubmed"]] = ["blog", "pubmed", "youtube"]
    pubmed_max:  int = 1
    blog_urls:   list[str] = []   # override blog URLs  (empty = use defaults)
    youtube_ids: list[str] = []   # override video IDs  (empty = use defaults)
    query:       Optional[str] = None


class ScrapeStatusResponse(BaseModel):
    running:  bool
    last_run: Optional[str]
    error:    Optional[str]
    last_execution_time_ms: Optional[float] = None


# ── Schema normalisation ──────────────────────────────────────────────────────
def _normalise_item(item: dict) -> dict:
    """
    Unify both the OLD schema (source, tags, score 0-100) and the
    NEW schema (source_type, topic_tags, score 0-1) into a single
    consistent shape that the frontend expects.

    Output guarantee:
      - source_type  (str)
      - source_url   (str)
      - title        (str)
      - author       (str)
      - published_date (str)
      - topic_tags   (list[str])
      - trust_score  (float, 0–1)
      - score_breakdown (dict)
      - content_chunks  (list[str])
    """
    # source_type — old schema used "source"
    if "source_type" not in item and "source" in item:
        item["source_type"] = item["source"]

    # source_url — old schema used "url"
    if "source_url" not in item and "url" in item:
        item["source_url"] = item["url"]

    # topic_tags — old schema used "tags"
    if "topic_tags" not in item and "tags" in item:
        item["topic_tags"] = item["tags"]

    # published_date — old schema used "date"
    if "published_date" not in item and "date" in item:
        item["published_date"] = item["date"]

    # author — old schema may not have it
    item.setdefault("author", "")

    # content_chunks — old schema used "chunks"
    if "content_chunks" not in item:
        item["content_chunks"] = item.get("chunks", [])

    # trust_score — normalise to 0-1 float
    ts = item.get("trust_score", 0)
    if isinstance(ts, str):
        try:
            ts = float(ts)
        except ValueError:
            ts = 0.0
    # Old scorer returned 0–100; convert to 0–1
    if isinstance(ts, (int, float)) and ts > 1.0:
        ts = ts / 100.0
    item["trust_score"] = round(float(ts), 4)

    return item


# ── Data persistence ──────────────────────────────────────────────────────────
def _load_results() -> dict:
    """
    Load results from the best available file.
    Returns: { generated_at, total_items, items[] }
    """
    for path in (NEW_OUTPUT_FILE, LEGACY_OUTPUT_FILE):
        if path.exists() and path.stat().st_size > 10:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                # New pipeline writes a bare list; legacy writes { items: [...] }
                if isinstance(raw, list):
                    return {
                        "generated_at": None,
                        "total_items": len(raw),
                        "items": raw,
                    }
                if isinstance(raw, dict) and "items" in raw:
                    return raw
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(f"Could not read {path}: {exc}")

    return {"generated_at": None, "total_items": 0, "items": []}


def _save_results(items: list[dict], execution_time_ms: float = 0) -> None:
    """Persist results to the API output file and individual source files."""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "execution_time_ms": round(execution_time_ms, 2),
        "total_items": len(items),
        "items": items,
    }
    # Save the main scraped_data.json
    API_OUTPUT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info(f"Saved {len(items)} items → {API_OUTPUT_FILE}")


# ── Background scrape pipeline ────────────────────────────────────────────────
async def _run_pipeline(req: ScrapeRequest) -> None:
    global _scrape_status
    _scrape_status["running"] = True
    _scrape_status["error"] = None

    import time
    start_time = time.time()
    try:
        tasks = []
        if "blog" in req.sources:
            tasks.append(scrape_blogs(req.blog_urls or None))
        if "youtube" in req.sources:
            tasks.append(scrape_youtube(query=req.query, video_ids=req.youtube_ids or None))
        if "pubmed" in req.sources:
            if req.query:
                tasks.append(scrape_pubmed(query=req.query, max_results=req.pubmed_max))
            else:
                tasks.append(scrape_pubmed(max_results=req.pubmed_max))

        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: list[dict] = []
        for r in results_nested:
            if isinstance(r, Exception):
                logger.error(f"Scraper task error: {r}")
            else:
                all_items.extend(r)

        scored = batch_score(all_items)
        scored = [_normalise_item(i) for i in scored]
        scored.sort(key=lambda x: x.get("trust_score", 0), reverse=True)

        execution_time_ms = (time.time() - start_time) * 1000
        _save_results(scored, execution_time_ms)
        _scrape_status["last_run"] = datetime.now(timezone.utc).isoformat()
        _scrape_status["last_execution_time_ms"] = round(execution_time_ms, 2)
        logger.info(f"Pipeline complete — {len(scored)} items saved in {execution_time_ms:.2f}ms.")

    except Exception as exc:
        _scrape_status["error"] = str(exc)
        logger.exception("Pipeline failed")
    finally:
        _scrape_status["running"] = False
        await close_session()


# ── Routes ────────────────────────────────────────────────────────────────────

@api_router.get("/", summary="Health check", tags=["System"])
async def health():
    """Returns API status and timestamp."""
    return {
        "status": "ok",
        "service": "AI Trust Scraper API v2.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "docs": "/docs",
    }


@api_router.post("/scrape", summary="Trigger the scraping pipeline", tags=["Scraper"])
async def trigger_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Starts the scraping pipeline in the background.
    Poll `GET /scrape/status` to check progress.
    """
    if _scrape_status["running"]:
        raise HTTPException(status_code=409, detail="A scrape is already in progress.")
    background_tasks.add_task(_run_pipeline, req)
    return {"message": "Scraping pipeline started.", "sources": req.sources}


@api_router.get(
    "/scrape/status",
    response_model=ScrapeStatusResponse,
    summary="Pipeline status",
    tags=["Scraper"],
)
async def scrape_status():
    """Returns whether the pipeline is running and when it last completed."""
    return _scrape_status


@api_router.get("/results", summary="All scraped results (paginated + filtered)", tags=["Results"])
async def get_results(
    limit:     int            = Query(100, ge=1, le=1000, description="Max items to return"),
    offset:    int            = Query(0,   ge=0,          description="Pagination offset"),
    min_score: float          = Query(0.0, ge=0.0, le=1.0, description="Minimum trust score (0–1)"),
    tag:       Optional[str]  = Query(None, description="Filter by topic tag"),
    source:    Optional[str]  = Query(None, description="Filter by source type (blog/pubmed/youtube/openai/…)"),
):
    """
    Returns paginated, filtered results.
    All trust scores are normalised to 0–1.
    """
    data  = _load_results()
    items = [_normalise_item(i) for i in data["items"]]

    if min_score > 0:
        items = [i for i in items if i.get("trust_score", 0) >= min_score]

    if tag:
        items = [
            i for i in items
            if tag in i.get("topic_tags", i.get("tags", []))
        ]

    if source:
        items = [
            i for i in items
            if i.get("source_type", i.get("source", "")) == source
        ]

    total = len(items)
    return {
        "generated_at": data.get("generated_at"),
        "total_items":  total,
        "limit":        limit,
        "offset":       offset,
        "items":        items[offset: offset + limit],
    }


@api_router.get("/results/{source_type}", summary="Results filtered by source type", tags=["Results"])
async def get_results_by_source(
    source_type: str,
    limit: int = Query(50, ge=1, le=500),
):
    """Returns results for a specific source (e.g. pubmed, blog, openai, youtube)."""
    data = _load_results()
    items = [
        _normalise_item(i) for i in data["items"]
        if i.get("source_type", i.get("source", "")) == source_type
    ]
    return {
        "source_type": source_type,
        "total_items": len(items),
        "items":       items[:limit],
    }


@api_router.get("/stats", summary="Aggregated statistics", tags=["Results"])
async def get_stats():
    """
    Returns high-level statistics about all scraped content:
    total items, avg/min/max trust scores, breakdown by source, top tags.
    """
    data  = _load_results()
    items = [_normalise_item(i) for i in data["items"]]

    if not items:
        return {"message": "No data yet. Run POST /scrape first."}

    scores  = [i.get("trust_score", 0) for i in items]
    sources = Counter(
        i.get("source_type", i.get("source", "unknown")) for i in items
    )
    all_tags = [
        t for i in items
        for t in i.get("topic_tags", i.get("tags", []))
    ]
    top_tags = Counter(all_tags).most_common(10)

    return {
        "total_items":     len(items),
        "generated_at":    data.get("generated_at"),
        "execution_time_ms": data.get("execution_time_ms", 0),
        "avg_trust_score": round(sum(scores) / len(scores), 4) if scores else 0,
        "max_trust_score": round(max(scores), 4) if scores else 0,
        "min_trust_score": round(min(scores), 4) if scores else 0,
        "by_source":       dict(sources),
        "top_tags":        [{"tag": t, "count": c} for t, c in top_tags],
    }


@api_router.get("/tags", summary="All unique tags across all results", tags=["Results"])
async def get_tags():
    """Returns every unique topic tag found across all scraped content."""
    data = _load_results()
    all_tags = sorted({
        t for i in data["items"]
        for t in i.get("topic_tags", i.get("tags", []))
    })
    return {"tags": all_tags, "count": len(all_tags)}


@api_router.delete("/results", summary="Clear the results file", tags=["System"])
async def clear_results():
    """Wipes the current results and resets to an empty state."""
    _save_results([])
    return {"message": "Results cleared."}


app.include_router(api_router)

# ── Serve Frontend ────────────────────────────────────────────────────────────
FRONTEND_DIR = ROOT / "frontend" / "dist"

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        path = FRONTEND_DIR / full_path
        if path.is_file():
            return FileResponse(path)
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    logger.warning(f"Frontend dist folder not found at {FRONTEND_DIR}. "
                   "Run 'npm run build' in the frontend directory.")

