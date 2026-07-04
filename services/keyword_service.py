"""Keyword analysis: matched, missing, repeated and recommended keywords."""
from __future__ import annotations

import re
from collections import Counter

from utils.constants import keywords_for_role

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "was",
    "are", "were", "will", "your", "you", "our", "their", "them", "his",
    "her", "its", "into", "than", "then", "over", "such", "been", "being",
    "using", "used", "use", "able", "also", "which", "while", "where",
    "when", "what", "who", "how", "all", "any", "can", "had", "has",
}


def analyze(raw_text: str, role: str) -> dict:
    low = (raw_text or "").lower()
    role_kw = keywords_for_role(role)

    matched = [k for k in role_kw if k in low]
    missing = [k for k in role_kw if k not in low]

    # Repeated words (potential keyword stuffing / redundancy).
    words = [w for w in re.findall(r"[a-zA-Z][a-zA-Z\+\#\.]{2,}", low)
             if w not in STOPWORDS]
    counts = Counter(words)
    repeated = [{"word": w, "count": c}
                for w, c in counts.most_common(12) if c >= 4]

    # Recommended keywords = important role keywords currently missing.
    recommended = missing[:8]

    match_pct = round(len(matched) / max(1, len(role_kw)) * 100)

    return {
        "keyword_match": match_pct,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "repeated_keywords": repeated,
        "recommended_keywords": recommended,
    }
