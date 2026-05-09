"""
scoring/trust_score.py
-----------------------
Assignment Task 2 — Trust Score Algorithm

Formula
-------
    Trust Score = w1·author_credibility
                + w2·citation_score
                + w3·domain_authority
                + w4·recency_score
                + w5·medical_disclaimer_score

All components are in [0, 1].  Final score is also in [0, 1].

Weights (sum = 1.0):
    author_credibility       0.25
    citation_score           0.20
    domain_authority         0.25
    recency_score            0.20
    medical_disclaimer_score 0.10

Edge cases handled:
  - Missing author          → penalise author_credibility to 0.3
  - Missing publish date    → neutral recency (0.5)
  - Multiple authors        → average credibility
  - Non-English content     → no penalty (neutral)
  - Long articles           → chunking handles; no score impact
  - No transcript (YouTube) → no penalty

Abuse-prevention logic:
  - Fake / low-credibility authors   → cross-checked against known-org list
  - SEO spam blogs                   → low domain authority penalty
  - Misleading medical content       → penalise missing disclaimer
  - Outdated information             → strong recency decay
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════
# COMPONENT WEIGHTS
# ═══════════════════════════════════════════════════════════════════════════
WEIGHTS = {
    "author_credibility":       0.25,
    "citation_score":           0.20,
    "domain_authority":         0.25,
    "recency_score":            0.20,
    "medical_disclaimer_score": 0.10,
}


# ═══════════════════════════════════════════════════════════════════════════
# KNOWN-ORGANISATION LOOKUP  (abuse-prevention: fake-author check)
# ═══════════════════════════════════════════════════════════════════════════
TRUSTED_ORGS = {
    # AI labs & Tech Giants
    "openai", "google", "google scholar", "deepmind", "meta", "meta ai", 
    "microsoft", "ms", "anthropic", "huggingface", "hugging face", "cohere", 
    "stability ai", "mistral", "nvidia", "tesla", "tcs", "apple", "ibm", "perplexity",
    # Academic
    "mit", "stanford", "carnegie mellon", "cmu", "oxford", "cambridge",
    "harvard", "berkeley", "toronto", "montreal", "mila", "inria",
    # Medical / research publishers
    "nih", "who", "ncbi", "nature", "science", "elsevier", "springer",
    "pubmed", "lancet", "jama", "bmj", "nejm",
    # Known YouTube educators
    "3blue1brown", "andrej karpathy", "yannic kilcher", "lex fridman",
    "two minute papers", "sentdex", "siraj raval",
}

# ── Domain authority table ────────────────────────────────────────────────────
# 0–1 reflecting general domain trustworthiness for AI/medical content.
DOMAIN_AUTHORITY: dict[str, float] = {
    # Scientific / medical
    "pubmed.ncbi.nlm.nih.gov": 1.00,
    "ncbi.nlm.nih.gov":        1.00,
    "nature.com":              0.97,
    "science.org":             0.96,
    "thelancet.com":           0.95,
    "nejm.org":                0.95,
    "jamanetwork.com":         0.94,
    "bmj.com":                 0.95,
    "arxiv.org":               0.90,
    "openai.com":              0.88,
    "deepmind.google":         0.88,
    "deepmind.com":            0.87,
    "ai.google":               0.87,
    "research.google":         0.87,
    "anthropic.com":           0.85,
    "mistral.ai":              0.82,
    "huggingface.co":          0.82,
    # Educational
    "mit.edu":                 0.90,
    "stanford.edu":            0.90,
    "youtube.com":             0.62,   # platform, not publisher
    # Lower-authority
    "medium.com":              0.50,
    "wordpress.com":           0.40,
    "blogspot.com":            0.35,
    "substack.com":            0.55,
    "towardsdatascience.com":  0.65,
}

# Medical keywords that require a disclaimer
MEDICAL_KEYWORDS = [
    "diagnos", "treatment", "therapy", "patient", "clinical",
    "drug", "dose", "symptom", "disease", "medical advice",
    "prognosis", "surgery", "prescription",
]

DISCLAIMER_PHRASES = [
    "consult a doctor", "consult your physician", "not medical advice",
    "seek professional", "medical professional", "healthcare provider",
    "this is not a substitute", "for informational purposes only",
    "disclaimer", "speak with your doctor",
]


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def compute_trust_score(item: dict) -> dict:
    """
    Compute and attach trust_score + score_breakdown to *item*.

    Args:
        item: Scraped content dict (must have at least 'source_url', 'source_type').

    Returns:
        Same dict augmented with 'trust_score' (str, 2 dp) and 'score_breakdown'.
    """
    text      = _extract_text(item)
    author    = item.get("author", "")
    url       = item.get("source_url", "")
    pub_date  = item.get("published_date", "")
    src_type  = item.get("source_type", "")
    cit_count = item.get("_citation_count", 0)

    # ── Component scores ───────────────────────────────────────────────────
    author_score     = _score_author(author, src_type)
    citation_score   = _score_citations(text, cit_count, src_type)
    domain_score     = _score_domain(url)
    recency_score    = _score_recency(pub_date)
    disclaimer_score = _score_disclaimer(text)

    # ── Weighted sum ───────────────────────────────────────────────────────
    raw = (
        WEIGHTS["author_credibility"]       * author_score +
        WEIGHTS["citation_score"]           * citation_score +
        WEIGHTS["domain_authority"]         * domain_score +
        WEIGHTS["recency_score"]            * recency_score +
        WEIGHTS["medical_disclaimer_score"] * disclaimer_score
    )

    # ── Abuse-prevention penalties ─────────────────────────────────────────
    raw = _apply_abuse_penalties(raw, item, text, url)

    final = round(min(max(raw, 0.0), 1.0), 4)

    item["trust_score"] = f"{final:.2f}"
    item["score_breakdown"] = {
        "author_credibility":       round(author_score,     4),
        "citation_score":           round(citation_score,   4),
        "domain_authority":         round(domain_score,     4),
        "recency_score":            round(recency_score,    4),
        "medical_disclaimer_score": round(disclaimer_score, 4),
        "abuse_penalty_applied":    round(raw - final, 4) if raw > final else 0.0,
        "final_trust_score":        final,
    }
    return item


def batch_score(items: list[dict]) -> list[dict]:
    """Score all items in-place and return them."""
    return [compute_trust_score(item) for item in items]


# ═══════════════════════════════════════════════════════════════════════════
# COMPONENT SCORERS
# ═══════════════════════════════════════════════════════════════════════════

def _score_author(author: str, src_type: str) -> float:
    """
    Author credibility score (0–1).

    Edge cases:
      - Missing author           → 0.30
      - Multiple authors (CSV)   → average of individual scores
      - YouTube channel matched  → treated like org credibility
    """
    if not author or author.strip().lower() in ("unknown", "n/a", ""):
        return 0.30   # EDGE CASE: missing author

    # Multiple authors — average their individual scores
    if "," in author:
        parts  = [p.strip() for p in author.split(",") if p.strip()]
        scores = [_single_author_score(p, src_type) for p in parts]
        return round(sum(scores) / len(scores), 4)

    return _single_author_score(author, src_type)


def _single_author_score(name: str, src_type: str) -> float:
    lower = name.lower()

    # Check against trusted organisations (abuse-prevention: fake-author detection)
    for org in TRUSTED_ORGS:
        if org in lower:
            return 0.90

    # Source-type heuristics
    if src_type == "pubmed":
        return 0.75   # indexed authors generally credible
    if src_type == "youtube":
        return 0.55   # channel identity without verification
    if src_type == "blog":
        return 0.50   # generic blog author

    return 0.45


def _score_citations(text: str, explicit_count: int, src_type: str) -> float:
    """
    Citation density score (0–1).

    Sources:
      - PubMed reference count (from XML)
      - DOI patterns in text
      - URL links count
      - Reference markers [1], [23]
    """
    if src_type == "pubmed":
        # PubMed: use reference list length; cap at 60 refs = 1.0
        return min(explicit_count / 60, 1.0)

    # Heuristic for blogs/YouTube
    dois  = len(re.findall(r"\bdoi:\s*\S+", text, re.IGNORECASE))
    urls  = len(re.findall(r"https?://\S+", text))
    refs  = len(re.findall(r"\[?\d+\]", text))
    total = dois * 5 + urls * 1 + refs * 2

    if src_type == "youtube":
        return min(total / 30, 0.60)   # cap YouTube at 0.60
    return min(total / 50, 0.80)        # cap blogs at 0.80


def _score_domain(url: str) -> float:
    """
    Domain authority score (0–1).

    Abuse-prevention: SEO spam domains (low authority) are naturally penalised.
    """
    if not url:
        return 0.40

    host = urlparse(url).netloc.lower().lstrip("www.")

    # Exact match
    if host in DOMAIN_AUTHORITY:
        return DOMAIN_AUTHORITY[host]

    # Partial match (e.g. sub.nature.com)
    for domain, score in DOMAIN_AUTHORITY.items():
        if domain in host:
            return score

    # TLD heuristic — .edu/.gov/.ac.uk are generally trustworthy
    tld = host.rsplit(".", 1)[-1]
    if tld in ("edu", "gov", "ac"):
        return 0.82
    if tld in ("org",):
        return 0.65

    return 0.45   # unknown domain


def _score_recency(pub_date: str) -> float:
    """
    Recency score (0–1).

    Decay schedule:
      < 6 months   → 1.00
      < 1 year     → 0.85
      < 2 years    → 0.70
      < 3 years    → 0.50
      < 5 years    → 0.30
      ≥ 5 years    → 0.15   (ABUSE-PREVENTION: outdated information penalty)

    Edge case: missing date → 0.50 (neutral)
    """
    if not pub_date:
        return 0.50   # EDGE CASE: missing date

    try:
        # Handle both YYYY-MM-DD and YYYY
        if len(pub_date) == 4:
            pub_date = pub_date + "-01-01"
        dt       = datetime.fromisoformat(pub_date[:10]).replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).days
    except (ValueError, OverflowError):
        return 0.50

    if age_days < 0:
        return 1.00        # future date — treat as very recent
    if age_days < 182:
        return 1.00
    if age_days < 365:
        return 0.85
    if age_days < 730:
        return 0.70
    if age_days < 1095:
        return 0.50
    if age_days < 1825:
        return 0.30
    return 0.15            # 5+ years old


def _score_disclaimer(text: str) -> float:
    """
    Medical disclaimer score (0–1).

    Logic:
      - Content has NO medical keywords → neutral (0.50)
      - Content IS medical AND has disclaimer → 1.00
      - Content IS medical but NO disclaimer → 0.00  (ABUSE-PREVENTION)
    """
    lower = text.lower()
    is_medical = any(kw in lower for kw in MEDICAL_KEYWORDS)

    if not is_medical:
        return 0.50   # neutral for non-medical content

    has_disclaimer = any(phrase in lower for phrase in DISCLAIMER_PHRASES)
    return 1.00 if has_disclaimer else 0.00


# ═══════════════════════════════════════════════════════════════════════════
# ABUSE PREVENTION PENALTIES
# ═══════════════════════════════════════════════════════════════════════════

def _apply_abuse_penalties(score: float, item: dict, text: str, url: str) -> float:
    """
    Apply additional rule-based penalties for known abuse patterns.

    1. Fake / unverified author + low domain → -0.10
    2. Very short content (< 100 words) → -0.05 (likely SEO stub)
    3. Medical topic without disclaimer → already 0.0 in component; no extra penalty
    4. Keyword stuffing detection → -0.08
    """
    penalties = 0.0

    # 1. Suspicious author + low-authority domain
    author = item.get("author", "").lower()
    domain_score = _score_domain(url)
    is_unknown_author = not author or author in ("unknown", "n/a", "")
    if is_unknown_author and domain_score < 0.55:
        penalties += 0.10

    # 2. Very short content
    words = len(text.split())
    if words < 100:
        penalties += 0.05

    # 3. Keyword stuffing: same word > 5 % of all words
    if words > 50:
        word_freq = {}
        for w in text.lower().split():
            w = re.sub(r"[^a-z]", "", w)
            if len(w) > 4:
                word_freq[w] = word_freq.get(w, 0) + 1
        if word_freq:
            max_freq = max(word_freq.values())
            if max_freq / words > 0.05:
                penalties += 0.08

    return score - penalties


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _extract_text(item: dict) -> str:
    for field in ("_raw_text", "content", "abstract", "transcript"):
        if item.get(field):
            return item[field]
    return " ".join(item.get("content_chunks", []))


# ── Smoke-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    samples = [
        {
            "source_url":  "https://pubmed.ncbi.nlm.nih.gov/12345678/",
            "source_type": "pubmed",
            "author":      "Smith J, Doe A",
            "published_date": "2024-06-01",
            "_raw_text": (
                "This peer-reviewed study evaluates large language model safety "
                "in clinical decision support. Patients should consult a doctor "
                "before acting on any information. doi:10.1234/ai.2024.001"
            ),
            "_citation_count": 40,
        },
        {
            "source_url":  "https://medium.com/spamblog/ai-tricks",
            "source_type": "blog",
            "author":      "",
            "published_date": "2019-01-01",
            "_raw_text":   "AI AI AI AI AI amazing AI tricks click now AI AI.",
            "_citation_count": 0,
        },
    ]
    for s in samples:
        r = compute_trust_score(s)
        print(f"\nURL: {s['source_url']}")
        print(f"Trust Score: {r['trust_score']}")
        for k, v in r["score_breakdown"].items():
            print(f"  {k}: {v}")
