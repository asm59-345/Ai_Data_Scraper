"""
chunking.py
-----------
Splits long text into overlapping semantic chunks suitable for embedding,
vector-store ingestion, or RAG pipelines.

Strategy
--------
1. Split on paragraph boundaries first (double newline).
2. If a paragraph exceeds `max_tokens`, split on sentence boundaries.
3. Apply a sliding-window overlap so context is preserved at chunk edges.
"""

from __future__ import annotations
import re


# ── Defaults ───────────────────────────────────────────────────────────────
DEFAULT_CHUNK_SIZE    = 512   # target tokens per chunk (≈ words for English)
DEFAULT_CHUNK_OVERLAP = 64    # overlap between consecutive chunks (tokens)
SENTENCE_ENDINGS      = re.compile(r"(?<=[.!?])\s+")


def chunk_text(
    text: str,
    chunk_size:    int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split *text* into overlapping chunks of roughly *chunk_size* words.

    Args:
        text (str): Raw input text.
        chunk_size (int): Target chunk size in words.
        chunk_overlap (int): Number of words to overlap between chunks.

    Returns:
        list[str]: List of text chunks (non-empty strings).
    """
    if not text or not text.strip():
        return []

    # Step 1 — split into paragraphs
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    # Step 2 — further split oversized paragraphs on sentence boundaries
    sentences: list[str] = []
    for para in paragraphs:
        if _word_count(para) <= chunk_size:
            sentences.append(para)
        else:
            sentences.extend(_split_sentences(para))

    # Step 3 — pack sentences into sliding-window chunks
    return _pack_chunks(sentences, chunk_size, chunk_overlap)


def chunk_batch(
    items: list[dict],
    text_field: str = "content",
    chunk_size:    int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict]:
    """
    Chunk every item in *items* in-place.
    Falls back to 'abstract' or 'transcript' if *text_field* is absent.

    Returns:
        list[dict]: The same list, each item augmented with a 'chunks' key.
    """
    for item in items:
        text = item.get(text_field) or item.get("abstract") or item.get("transcript", "")
        item["chunks"] = chunk_text(text, chunk_size, chunk_overlap)
    return items


# ── Helpers ────────────────────────────────────────────────────────────────

def _word_count(text: str) -> int:
    return len(text.split())


def _split_sentences(text: str) -> list[str]:
    """Split *text* on sentence-ending punctuation."""
    parts = SENTENCE_ENDINGS.split(text)
    return [p.strip() for p in parts if p.strip()]


def _pack_chunks(
    sentences: list[str],
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """
    Greedily pack *sentences* into chunks with sliding-window overlap.
    """
    chunks: list[str] = []
    current_words: list[str] = []

    for sentence in sentences:
        sent_words = sentence.split()

        # If adding this sentence would overflow, flush the current chunk
        if current_words and _word_count(" ".join(current_words)) + len(sent_words) > chunk_size:
            chunks.append(" ".join(current_words))
            # Keep the last `overlap` words for continuity
            current_words = current_words[-overlap:] if overlap else []

        current_words.extend(sent_words)

    # Flush the final chunk
    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


# ── Quick smoke-test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    LONG_TEXT = (
        "Artificial intelligence has made remarkable strides in recent years. "
        "Large language models have demonstrated unprecedented capabilities "
        "across a wide range of tasks. However, concerns about safety, bias, "
        "and transparency remain at the forefront of research.\n\n"
        "Researchers are now focusing on alignment techniques that ensure "
        "models behave in accordance with human values. This includes "
        "reinforcement learning from human feedback (RLHF), constitutional AI, "
        "and interpretability methods such as SHAP and LIME.\n\n"
        "The regulatory landscape is also evolving rapidly, with the EU AI Act "
        "setting new compliance requirements for high-risk AI systems."
    )

    chunks = chunk_text(LONG_TEXT, chunk_size=50, chunk_overlap=10)
    for i, chunk in enumerate(chunks, 1):
        print(f"── Chunk {i} ({_word_count(chunk)} words) ──")
        print(chunk)
        print()
