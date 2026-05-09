"""
tagging.py
----------
Lightweight zero-dependency keyword-based tagging for scraped content.
Assigns topic tags (e.g. "safety", "bias", "LLM", "healthcare") from a
curated taxonomy without requiring an ML model or external API call.
"""

from __future__ import annotations
import re


# ── Tag taxonomy ──────────────────────────────────────────────────────────
# Each entry: tag_name → list of trigger keywords / phrases (case-insensitive)
TAXONOMY: dict[str, list[str]] = {
    "LLM": [
        "large language model", "llm", "gpt", "gemini", "claude",
        "chatgpt", "language model", "transformer", "generative ai",
    ],
    "safety": [
        "safety", "alignment", "ai risk", "existential risk",
        "red-team", "red team", "guardrail", "jailbreak", "misuse",
    ],
    "bias": [
        "bias", "fairness", "discrimination", "demographic",
        "representation", "equity", "stereotype",
    ],
    "healthcare": [
        "healthcare", "clinical", "medical", "patient", "diagnosis",
        "drug", "radiology", "ehr", "electronic health record",
    ],
    "interpretability": [
        "explainability", "interpretability", "xai", "explainable",
        "saliency", "attention map", "feature importance", "shap", "lime",
    ],
    "benchmark": [
        "benchmark", "leaderboard", "evaluation", "metric", "mmlu",
        "hellaswag", "gsm8k", "humaneval", "swebench",
    ],
    "multimodal": [
        "multimodal", "vision-language", "image-text", "vlm",
        "stable diffusion", "dall-e", "text-to-image",
    ],
    "policy": [
        "regulation", "policy", "governance", "eu ai act",
        "legislation", "compliance", "ethics committee",
    ],
    "robotics": [
        "robotics", "robot", "autonomous system", "embodied ai",
        "manipulation", "locomotion",
    ],
    "research": [
        "paper", "arxiv", "preprint", "peer-reviewed", "journal",
        "conference", "neurips", "icml", "iclr", "acl",
    ],
}


def tag_content(text: str, max_tags: int = 8) -> list[str]:
    """
    Return a deduplicated list of topic tags found in *text*.

    Args:
        text (str): The raw text to analyse.
        max_tags (int): Maximum number of tags to return (highest-match first).

    Returns:
        list[str]: Sorted list of matching tag names.
    """
    if not text:
        return []

    lower = text.lower()
    hit_counts: dict[str, int] = {}

    for tag, keywords in TAXONOMY.items():
        count = sum(
            len(re.findall(re.escape(kw), lower))
            for kw in keywords
        )
        if count:
            hit_counts[tag] = count

    # Sort by hit frequency (descending) then alphabetically for ties
    ranked = sorted(hit_counts.items(), key=lambda x: (-x[1], x[0]))
    return [tag for tag, _ in ranked[:max_tags]]


def tag_batch(items: list[dict], text_field: str = "content") -> list[dict]:
    """
    Tag every item in *items* in-place using the specified *text_field*.
    Falls back to 'abstract' or 'transcript' if *text_field* is absent.

    Returns:
        list[dict]: The same list, each item augmented with a 'tags' key.
    """
    for item in items:
        text = item.get(text_field) or item.get("abstract") or item.get("transcript", "")
        item["tags"] = tag_content(text)
    return items


# ── Quick smoke-test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = (
        "This paper presents a benchmark for evaluating large language model "
        "safety and fairness. We study bias in healthcare LLMs and propose "
        "new interpretability metrics using SHAP values."
    )
    tags = tag_content(sample)
    print("Tags:", tags)
