"""Heuristic ATS (Applicant Tracking System) compatibility scanner.

Returns a 0-100 ATS score plus a breakdown of checks. Works entirely
offline so an ATS result is always available.
"""
from __future__ import annotations

import re

from utils.constants import keywords_for_role

STANDARD_SECTIONS = [
    "experience", "education", "skills", "projects", "summary",
    "certification", "contact",
]


def scan(raw_text: str, parsed: dict, role: str) -> dict:
    text = raw_text or ""
    low = text.lower()
    checks: list[dict] = []

    def add(name: str, ok: bool, weight: int, detail: str) -> None:
        checks.append({"name": name, "passed": ok, "weight": weight,
                       "detail": detail})

    # Contact information present.
    has_contact = bool(parsed.get("email")) and bool(parsed.get("phone"))
    add("Contact information", has_contact, 10,
        "Email and phone found" if has_contact
        else "Missing email or phone number")

    # Standard section headings.
    found_sections = [s for s in STANDARD_SECTIONS if s in low]
    add("Standard section headings", len(found_sections) >= 4, 15,
        f"Detected {len(found_sections)} standard sections")

    # Keyword coverage for the target role.
    role_kw = keywords_for_role(role)
    matched = [k for k in role_kw if k in low]
    coverage = len(matched) / max(1, len(role_kw))
    add("Role keyword coverage", coverage >= 0.4, 25,
        f"{len(matched)}/{len(role_kw)} target keywords present")

    # No tables (ATS parsers struggle with them). Heuristic: many aligned
    # columns / tab characters.
    has_tables = bool(re.search(r"\t.*\t", text)) or "|" in text
    add("No complex tables", not has_tables, 10,
        "Tables/columns detected" if has_tables else "No problematic tables")

    # Readable length.
    words = len(re.findall(r"\w+", text))
    good_len = 300 <= words <= 1200
    add("Appropriate length", good_len, 10,
        f"{words} words")

    # Bullet points for readability.
    has_bullets = bool(re.search(r"[•\u2022\-\*]\s", text))
    add("Uses bullet points", has_bullets, 5,
        "Bullet points found" if has_bullets else "No bullet points detected")

    # Dates present (for experience/education chronology).
    has_dates = bool(re.search(r"(19|20)\d{2}", text))
    add("Dates present", has_dates, 5,
        "Year references found" if has_dates else "No dates detected")

    # Avoids images-only content (we already have text, so pass if text long).
    add("Machine-readable text", words > 50, 10,
        "Text extracted successfully")

    # Standard fonts / no special glyphs overload (heuristic).
    weird = len(re.findall(r"[^\x00-\x7F]", text))
    add("Clean character set", weird < words, 5,
        f"{weird} non-standard characters")

    earned = sum(c["weight"] for c in checks if c["passed"])
    total = sum(c["weight"] for c in checks)
    score = round(earned / total * 100) if total else 0

    return {
        "ats_score": score,
        "checks": checks,
        "matched_keywords": matched,
        "missing_keywords": [k for k in role_kw if k not in low],
    }
