"""
scraper/arxiv_scraper.py
------------------------
Scrapes research papers from arXiv using its official API.
Returns data matching the BaseAssignmentSchema.
"""

from __future__ import annotations
import asyncio
from bs4 import BeautifulSoup
from utils.async_fetch import fetch_html
from utils.tagging import tag_content
from utils.chunking import chunk_text

async def scrape_arxiv(query: str | None = None, max_results: int = 5) -> list[dict]:
    """
    Search arXiv for research papers.
    """
    search_query = query.replace(" ", "+") if query else "artificial+intelligence"
    url = f"http://export.arxiv.org/api/query?search_query=all:{search_query}&start=0&max_results={max_results}"
    
    # We can use fetch_html since it just returns the response text
    xml_data = await fetch_html(url)
    if not xml_data:
        return []

    soup = BeautifulSoup(xml_data, "xml")
    entries = soup.find_all("entry")
    
    results = []
    for entry in entries:
        title = entry.find("title").text.strip().replace("\n", " ") if entry.find("title") else "Untitled"
        summary = entry.find("summary").text.strip().replace("\n", " ") if entry.find("summary") else ""
        
        # Extract authors
        authors = [a.find("name").text.strip() for a in entry.find_all("author") if a.find("name")]
        author_str = ", ".join(authors) if authors else "Unknown Author"
        
        # Extract date
        published = entry.find("published").text.strip() if entry.find("published") else ""
        if published:
            published = published[:10]  # YYYY-MM-DD
            
        link = entry.find("id").text.strip() if entry.find("id") else ""
        
        tags = tag_content(summary)
        chunks = chunk_text(summary)
        
        results.append({
            "source_url":     link,
            "source_type":    "arxiv",
            "title":          title,
            "author":         author_str,
            "published_date": published,
            "language":       "en",
            "region":         "Global",
            "topic_tags":     tags,
            "trust_score":    "",
            "content_chunks": chunks,
            "_raw_text":      summary,
        })
        
    print(f"[ArXivScraper] Scraped {len(results)} arXiv paper(s).")
    return results

if __name__ == "__main__":
    async def _main():
        res = await scrape_arxiv("large language models", 2)
        import json
        print(json.dumps(res, indent=2))
    asyncio.run(_main())
