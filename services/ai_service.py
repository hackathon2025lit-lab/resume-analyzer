"""Gemini AI analysis service.

Sends the resume text, parsed fields, target role and weighted criteria to
the Gemini API and returns a structured analysis. If the API key is not
configured or the request fails, it transparently falls back to the local
deterministic analyzer so an analysis is ALWAYS produced.
"""
from __future__ import annotations

import json
import re

from config import Config
from services import local_analyzer

_PROMPT = """You are an expert technical recruiter and ATS specialist.
Analyze the following resume for the target role: "{role}".

The candidate selected these evaluation criteria with weights (percent):
{criteria}

Weigh your overall assessment according to these weights.

Parsed resume fields (JSON):
{parsed}

Full resume text:
\"\"\"
{text}
\"\"\"

Return ONLY a valid JSON object (no markdown, no commentary) with EXACTLY
these keys:
- overall_score, ats_score, technical_skills_score, soft_skills_score,
  formatting_score, grammar_score, experience_score, education_score,
  project_score, keyword_match  (all integers 0-100)
- career_level (string), industry_readiness (string)
- strengths, weaknesses, missing_skills, missing_keywords,
  recommended_keywords, improvement_suggestions, actionable_suggestions,
  formatting_issues, duplicate_content  (all arrays of short strings)
- professional_summary_review, project_review, achievements_review,
  resume_length_review  (strings)
- category_scores: object mapping "Skills","Experience","Education",
  "Projects","ATS","Grammar","Formatting","Keywords" to integers 0-100
- improved: object with keys summary (string), project_descriptions (array),
  experience_descriptions (array), achievements (array),
  skills_ordering (string), formatting_suggestions (array)
Base every score on the actual resume content. Do not invent experience.
"""


def _configured() -> bool:
    return Config.gemini_configured()


def _extract_json(text: str) -> dict | None:
    """Pull the first JSON object out of a model response."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _call_gemini(prompt: str) -> dict | None:
    try:
        import google.generativeai as genai
    except ImportError:
        return None
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel(Config.GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.4,
                "response_mime_type": "application/json",
            },
        )
        return _extract_json(getattr(response, "text", "") or "")
    except Exception:
        return None


def _merge(base: dict, ai: dict) -> dict:
    """Overlay AI values on top of the local baseline, keeping completeness."""
    merged = dict(base)
    for key, value in ai.items():
        if value in (None, "", [], {}):
            continue
        merged[key] = value
    # Keep locally-computed structures the AI is not asked to produce.
    for key in ("ats_details", "skills_gap", "grammar_issues",
                "repeated_keywords", "matched_keywords"):
        merged.setdefault(key, base.get(key))
    merged["engine"] = "gemini"
    return merged


def analyze(raw_text: str, parsed: dict, role: str, criteria: dict) -> dict:
    """Run analysis, preferring Gemini and falling back to local engine."""
    base = local_analyzer.analyze(raw_text, parsed, role, criteria)

    if not _configured():
        base["engine"] = "local"
        base["engine_note"] = (
            "GEMINI_API_KEY not set - used built-in offline analyzer.")
        return base

    criteria_str = json.dumps(criteria or {}, indent=2)
    parsed_str = json.dumps({k: v for k, v in parsed.items()
                             if k != "raw_text"}, indent=2)[:6000]
    prompt = _PROMPT.format(
        role=role, criteria=criteria_str, parsed=parsed_str,
        text=(raw_text or "")[:12000],
    )

    ai = _call_gemini(prompt)
    if not ai:
        base["engine"] = "local"
        base["engine_note"] = (
            "Gemini request failed - used built-in offline analyzer.")
        return base

    return _merge(base, ai)
