"""Lightweight grammar / writing-quality checker (offline heuristics)."""
from __future__ import annotations

import re

# Frequently misspelled words -> correction.
COMMON_MISSPELLINGS = {
    "recieve": "receive",
    "responsibilties": "responsibilities",
    "responsibile": "responsible",
    "acheivement": "achievement",
    "achivement": "achievement",
    "enviroment": "environment",
    "developement": "development",
    "experiance": "experience",
    "managment": "management",
    "seperate": "separate",
    "sucessful": "successful",
    "succesful": "successful",
    "occured": "occurred",
    "collaboratively": "collaboratively",
    "colaborate": "collaborate",
    "profesional": "professional",
    "wich": "which",
    "teh": "the",
    "analyse": "analyze",
    "priortize": "prioritize",
}

WEAK_WORDS = {
    "responsible for": "Led / Owned / Drove",
    "worked on": "Built / Delivered / Engineered",
    "helped": "Enabled / Accelerated",
    "duties included": "Delivered / Achieved",
    "various": "specific, named items",
    "stuff": "concrete deliverables",
    "things": "concrete deliverables",
}


def check(raw_text: str) -> dict:
    text = raw_text or ""
    low = text.lower()
    issues: list[dict] = []

    # Spelling.
    for wrong, right in COMMON_MISSPELLINGS.items():
        if re.search(rf"(?<![a-z]){wrong}(?![a-z])", low):
            issues.append({
                "type": "spelling",
                "problem": wrong,
                "suggestion": right,
                "message": f"Possible misspelling: '{wrong}' -> '{right}'.",
            })

    # Weak / passive phrasing.
    for weak, strong in WEAK_WORDS.items():
        if weak in low:
            issues.append({
                "type": "wording",
                "problem": weak,
                "suggestion": strong,
                "message": f"Replace weak phrase '{weak}' with stronger "
                           f"action verbs ({strong}).",
            })

    # Double spaces.
    if "  " in text:
        issues.append({
            "type": "formatting",
            "problem": "double spaces",
            "suggestion": "single space",
            "message": "Remove duplicated spaces for consistent spacing.",
        })

    # Sentences that are too long (readability).
    long_sentences = 0
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if len(sentence.split()) > 35:
            long_sentences += 1
    if long_sentences:
        issues.append({
            "type": "readability",
            "problem": f"{long_sentences} long sentence(s)",
            "suggestion": "split into concise bullet points",
            "message": "Break very long sentences into concise bullets.",
        })

    # First-person pronouns (resumes usually avoid them).
    pronouns = len(re.findall(r"\b(i|me|my|myself)\b", low))
    if pronouns > 3:
        issues.append({
            "type": "style",
            "problem": "first-person pronouns",
            "suggestion": "use implied-subject bullet points",
            "message": "Reduce first-person pronouns; start bullets with "
                       "action verbs.",
        })

    # Score: start at 100, subtract per issue, floor at 40.
    score = max(40, 100 - len(issues) * 8)

    return {
        "grammar_score": score,
        "issues": issues,
        "issue_count": len(issues),
    }
