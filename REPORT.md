# Data Scraping & Trust Scoring Assignment: Technical Report

**Objective:** To design and implement an end-to-end multi-source web scraper combined with a deterministic algorithm to evaluate and assign credibility scores to the retrieved content.

---

## 1. Scraping Strategy

The scraping architecture is fundamentally decentralized, relying on individual, highly-specialized modules (`blog_scraper.py`, `youtube_scraper.py`, `pubmed_scraper.py`) to handle the unique data structures of their respective targets. These modules are orchestrated by an asynchronous FastAPI backend pipeline (`api.py`), enabling highly concurrent and non-blocking I/O operations. 

- **PubMed**: Rather than scraping raw HTML, which is prone to structure changes, the strategy utilizes the official NCBI E-utilities REST API. This ensures maximum stability and yields highly structured XML/JSON data, easily parsed for `authors`, `abstracts`, and `publication_dates`.
- **YouTube**: We query the YouTube search index dynamically, scraping the initial page HTML to extract target Video IDs via Regex. From there, `youtube-transcript-api` is used to intercept the underlying closed-captioning JSON payloads directly, avoiding complex headless browser setups and bypassing traditional ad-blockers.
- **Blogs**: We fetch raw DOM data using `aiohttp` and parse it via `BeautifulSoup4`. The strategy strips out repetitive site layouts (`<nav>`, `<footer>`, `<aside>`) to isolate the core `<article>` or `<div class="content">`.

*All unstructured data is then uniformly mapped to a strict JSON Schema prior to being passed to the NLP utilities.*

---

## 2. Topic Tagging Method

To auto-generate relevant topics without relying on external, paid LLM APIs, the system utilizes a predefined heuristic dictionary method in `utils/tagging.py`. 

The text is converted to lowercase and scanned against a comprehensive `TAG_DICTIONARY` comprised of domain-specific arrays (e.g., `{"AI": ["artificial intelligence", "machine learning", "neural network"], "Healthcare": ["medical", "cancer", "clinical"]}`). If any associated keyword sequence is detected within the content chunks, the overarching topic tag (e.g., "AI", "Healthcare") is appended to the `topic_tags` array. This strategy guarantees extremely low computational overhead while maintaining high accuracy for targeted subject matter.

---

## 3. Trust Score Algorithm

The system quantifies reliability using a multi-factor polynomial equation. Each axis is normalized to a value between `0.0` and `1.0` and multiplied by a weighted coefficient.

**Formula:**
`Trust Score = (Author * 0.40) + (Citations * 0.20) + (Domain * 0.20) + (Recency * 0.10) + (Disclaimer * 0.10)`

1. **Author Credibility (Max 0.4)**: Cross-references the scraped author/channel against a meticulously curated hash-set (`TRUSTED_ORGS`). Matches yield full points.
2. **Citation Count / Impact (Max 0.2)**: For PubMed, the algorithm maps raw citation counts using a non-linear threshold (e.g., `>50 = 0.2`). For YouTube, it evaluates the channel view ratio.
3. **Domain Authority (Max 0.2)**: Content sourced directly from `.gov` or `.edu` registries receives maximum domain authority. Recognized corporate domains (`openai.com`) receive `0.15`, while unknown domains fallback to `0.05`.
4. **Recency Penalty (Max 0.1)**: Ensures AI and medical information is modern. Content published within the last 365 days receives `0.1`. Older content undergoes a decay factor.
5. **Medical Disclaimer Presence (Max 0.1)**: Scans the final paragraphs of the text for legal string tokens ("not medical advice", "consult your physician").

---

## 4. Edge Case Handling & Abuse Prevention

The system is rigorously hardened against poor data formats and SEO manipulation:

- **Missing Metadata:** If an `author` cannot be verified, the `author_credibility` metric defaults to a baseline of `0.05` instead of failing, allowing high-quality but anonymous content to still achieve an average score via domain authority and citations.
- **Multiple Authors:** In PubMed articles featuring extensive co-author lists, the system parses the list. If any *single* author or organization matches our trusted database, the full author score is awarded.
- **Non-English Content:** The scraper flags content language. Although translation is currently outside the scope, we track language codes strictly to ensure downstream datasets can segregate non-English inputs seamlessly.
- **Long Articles:** `chunking.py` enforces a `max_length` (e.g., 500 characters). If a paragraph exceeds this limit, it is cleanly severed at the nearest terminating punctuation (`.`, `!`, `?`), ensuring subsequent semantic analysis tools are never subjected to buffer-overflows or context-limit exhaustion.
- **Abuse Prevention**: 
  - *SEO Spam:* Penalized inherently by the `Domain Authority` rule. Unknown blog URLs cannot exceed `0.05` in the domain category.
  - *Fake Authors:* Unless the name string matches the strict string-distance rules in `TRUSTED_ORGS`, fake authoritative names are ignored.
  - *Misleading Health Content:* If PubMed articles or YouTube videos discuss medical terms without explicit disclaimers or high citations, their score drops heavily, ensuring end-users are visually warned of untrusted content.
