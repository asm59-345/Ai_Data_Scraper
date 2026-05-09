"""
scraper/pubmed_scraper.py
--------------------------
Scrapes exactly 1 PubMed article and returns an assignment-schema dict.

Uses the NCBI E-utilities REST API (no key required for low-volume use).
Default query: "large language model safety clinical" → picks top result.

Set NCBI_API_KEY env var to get 10 req/s instead of 3 req/s.
"""

from __future__ import annotations
import asyncio
import json
import os
import xml.etree.ElementTree as ET

from utils.async_fetch import fetch_html, fetch_json
from utils.tagging import tag_content
from utils.chunking import chunk_text

EUTILS_BASE   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_QUERY = "large language model safety medicine"


# ── Public entry point ────────────────────────────────────────────────────────

async def scrape_pubmed(
    query:       str = DEFAULT_QUERY,
    pmid:        str | None = None,
    max_results: int = 1,
) -> list[dict]:
    """
    Fetch PubMed article(s) and return assignment-schema dicts.

    Args:
        query:       Search query (used when pmid is None).
        pmid:        Fetch a specific article by PubMed ID.
        max_results: Number of articles to fetch via search (ignored if pmid set).
    """
    api_key = os.getenv("NCBI_API_KEY", "")
    key_qs  = f"&api_key={api_key}" if api_key else ""

    if pmid:
        pmids = [pmid]
    else:
        pmids = await _search(query, max_results, key_qs)

    if not pmids:
        print("[PubMedScraper] No PMIDs found.")
        return []

    articles = await _fetch_details(pmids, key_qs)
    results  = []
    for art in articles:
        text   = art["abstract"]
        tags   = tag_content(text)
        chunks = chunk_text(text)
        results.append({
            "source_url":     f"https://pubmed.ncbi.nlm.nih.gov/{art['pmid']}/",
            "source_type":    "pubmed",
            "title":          art["title"],
            "author":         art["authors"],          # comma-separated list
            "published_date": art["pub_date"],
            "language":       art["language"],
            "region":         art["country"],
            "journal":        art["journal"],
            "topic_tags":     tags,
            "trust_score":    "",
            "content_chunks": chunks,
            "_raw_text":      text,
            "_citation_count": art["citation_count"],  # used by trust scorer
        })

    print(f"[PubMedScraper] Scraped {len(results)} PubMed article(s).")
    return results


# ── E-utilities helpers ────────────────────────────────────────────────────────

async def _search(query: str, retmax: int, key_qs: str) -> list[str]:
    url = (
        f"{EUTILS_BASE}/esearch.fcgi"
        f"?db=pubmed&retmode=json&retmax={retmax}"
        f"&term={query.replace(' ', '+')}{key_qs}"
    )
    data = await fetch_json(url)
    try:
        return data["esearchresult"]["idlist"]
    except Exception:
        return []


async def _fetch_details(pmids: list[str], key_qs: str) -> list[dict]:
    url = (
        f"{EUTILS_BASE}/efetch.fcgi"
        f"?db=pubmed&retmode=xml&id={','.join(pmids)}{key_qs}"
    )
    xml_text = await fetch_html(url)
    return _parse_xml(xml_text)


def _parse_xml(xml_text: str) -> list[dict]:
    """Parse PubMed EFetch XML response."""
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        print(f"[PubMedScraper] XML parse error: {exc}")
        return []

    for art_el in root.findall(".//PubmedArticle"):
        pmid    = _txt(art_el, ".//PMID")
        title   = _txt(art_el, ".//ArticleTitle")
        journal = _txt(art_el, ".//Journal/Title") or _txt(art_el, ".//MedlineTA")

        # Authors — build "Last FM, Last FM, …" list
        author_els = art_el.findall(".//Author")
        authors    = []
        for a in author_els:
            last  = _txt(a, "LastName")
            fore  = _txt(a, "ForeName") or _txt(a, "Initials")
            if last:
                authors.append(f"{last} {fore}".strip())
            else:
                # Collective name
                coll = _txt(a, "CollectiveName")
                if coll:
                    authors.append(coll)
        author_str = ", ".join(authors) if authors else "Unknown"

        # Abstract — concatenate all AbstractText nodes
        abstract_parts = art_el.findall(".//AbstractText")
        abstract = " ".join((p.text or "").strip() for p in abstract_parts)

        # Publication date
        pub_year  = _txt(art_el, ".//PubDate/Year")
        pub_month = _txt(art_el, ".//PubDate/Month") or "01"
        pub_day   = _txt(art_el, ".//PubDate/Day")   or "01"
        pub_date  = f"{pub_year}-{pub_month.zfill(2)}-{pub_day.zfill(2)}" if pub_year else ""

        # Language
        lang_el  = art_el.find(".//Language")
        language = lang_el.text.strip().lower() if lang_el is not None and lang_el.text else "eng"
        # Map 3-letter to 2-letter ISO code
        LANG3 = {"eng": "en", "fre": "fr", "ger": "de", "spa": "es", "chi": "zh", "jpn": "ja"}
        language = LANG3.get(language, language[:2])

        # Country / region from MedlineJournalInfo
        country = _txt(art_el, ".//MedlineJournalInfo/Country") or "Unknown"

        # Estimate citation count from reference list length (EFetch doesn't give real count)
        ref_count = len(art_el.findall(".//Reference"))

        articles.append({
            "pmid":           pmid,
            "title":          title,
            "authors":        author_str,
            "journal":        journal,
            "abstract":       abstract,
            "pub_date":       pub_date,
            "language":       language,
            "country":        country,
            "citation_count": ref_count,
        })

    return articles


def _txt(element, xpath: str, default: str = "") -> str:
    node = element.find(xpath)
    return (node.text or default).strip() if node is not None and node.text else default


# ── Smoke-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def _main():
        arts = await scrape_pubmed()
        for a in arts:
            print(f"\n  Title:   {a['title'][:70]}")
            print(f"  Author:  {a['author'][:60]}")
            print(f"  Journal: {a.get('journal','')}")
            print(f"  Date:    {a['published_date']}")
            print(f"  Lang:    {a['language']}  Region: {a['region']}")
            print(f"  Tags:    {a['topic_tags']}")
            print(f"  Chunks:  {len(a['content_chunks'])}")

    asyncio.run(_main())
