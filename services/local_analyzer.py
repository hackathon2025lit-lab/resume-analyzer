"""Deterministic, offline resume analysis engine.

Produces the full analysis result structure used across the app. It is
used directly when the Gemini API key is not configured, and it also
provides the baseline scores that the AI service refines. This guarantees
that an analysis is ALWAYS generated for a valid resume.
"""
from __future__ import annotations

import re

from services import ats_service, grammar_service, keyword_service, skills_service


def _clamp(value: float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(value))))


def _score_experience(parsed: dict, raw: str) -> int:
    exp = " ".join(parsed.get("experience", []))
    years = [int(y) for y in re.findall(r"(19|20)\d{2}", raw)]
    span = (max(years) - min(years)) if len(years) >= 2 else 0
    base = 45
    base += min(30, len(exp.split()) // 12)
    base += min(20, span * 4)
    if parsed.get("internships"):
        base += 5
    return _clamp(base)


def _score_education(parsed: dict) -> int:
    edu = " ".join(parsed.get("education", [])).lower()
    if not edu:
        return 40
    base = 60
    for kw, pts in (("phd", 35), ("master", 25), ("bachelor", 20),
                    ("b.tech", 20), ("b.e", 18), ("diploma", 10)):
        if kw in edu:
            base += pts
            break
    if parsed.get("certifications"):
        base += 8
    return _clamp(base)


def _score_projects(parsed: dict) -> int:
    proj = parsed.get("projects", [])
    if not proj:
        return 35
    return _clamp(45 + min(45, len(" ".join(proj).split()) // 8))


def _score_formatting(parsed: dict, raw: str) -> int:
    score = 60
    if re.search(r"[•\u2022\-\*]\s", raw):
        score += 12
    sections = sum(1 for k in ("experience", "education", "skills", "projects")
                   if parsed.get(k))
    score += sections * 6
    if "  " in raw:
        score -= 6
    return _clamp(score)


def _score_technical(parsed: dict) -> int:
    n = len(parsed.get("technical_skills", []))
    return _clamp(40 + min(55, n * 6))


def _score_soft(parsed: dict) -> int:
    n = len(parsed.get("soft_skills", []))
    return _clamp(45 + min(45, n * 9))


def _career_level(parsed: dict, raw: str, exp_score: int) -> str:
    low = raw.lower()
    if any(w in low for w in ("intern", "fresher", "student")) and exp_score < 55:
        return "Entry Level"
    if exp_score >= 80 or any(w in low for w in ("lead", "manager",
                                                 "principal", "head")):
        return "Senior Level"
    if exp_score >= 60:
        return "Mid Level"
    return "Entry / Junior Level"


def _build_improvements(parsed: dict) -> dict:
    top_skills = ", ".join(parsed.get("technical_skills", [])[:6]) or \
        "your core technologies"
    return {
        "summary": (
            f"Results-driven professional skilled in {top_skills}. "
            "Proven ability to deliver measurable impact through well-built, "
            "maintainable solutions. Seeking to apply strong technical and "
            "problem-solving skills to drive team and product success."
        ),
        "project_descriptions": [
            "Start each project bullet with an action verb and end with a "
            "quantified result (e.g. 'reduced load time by 40%').",
            "Name the tech stack and your specific contribution, not the "
            "team's overall work.",
        ],
        "experience_descriptions": [
            "Convert responsibility statements into achievement statements "
            "with metrics (%, $, time saved).",
            "Use the pattern: Action + Context + Measurable Result.",
        ],
        "achievements": [
            "Quantify awards and recognitions (rank, percentile, scale).",
            "Tie achievements to business or academic impact.",
        ],
        "skills_ordering": (
            "List the most role-relevant technical skills first, group by "
            "category (Languages, Frameworks, Tools, Cloud), and remove "
            "outdated or irrelevant skills."
        ),
        "formatting_suggestions": [
            "Use a single, consistent bullet style throughout.",
            "Keep to a clean single-column layout for ATS compatibility.",
            "Ensure consistent date formats and section spacing.",
        ],
    }


def analyze(raw_text: str, parsed: dict, role: str, criteria: dict) -> dict:
    ats = ats_service.scan(raw_text, parsed, role)
    kw = keyword_service.analyze(raw_text, role)
    gap = skills_service.analyze(parsed, role)
    grammar = grammar_service.check(raw_text)

    technical_score = _score_technical(parsed)
    soft_score = _score_soft(parsed)
    formatting_score = _score_formatting(parsed, raw_text)
    experience_score = _score_experience(parsed, raw_text)
    education_score = _score_education(parsed)
    project_score = _score_projects(parsed)
    grammar_score = grammar["grammar_score"]
    ats_score = ats["ats_score"]
    keyword_match = kw["keyword_match"]

    # Component scores mapped to weightable criteria.
    component = {
        "skills": (technical_score + soft_score) / 2,
        "experience": experience_score,
        "education": education_score,
        "projects": project_score,
        "ats": ats_score,
        "grammar": grammar_score,
        "formatting": formatting_score,
        "keywords": keyword_match,
        "achievements": 70 if parsed.get("achievements") else 45,
        "certifications": 75 if parsed.get("certifications") else 45,
        "leadership": 70 if re.search(r"lead|mentor|manage",
                                      raw_text.lower()) else 45,
        "communication": min(95, soft_score + 5),
    }

    # Weighted overall score using user criteria (falls back to equal weight).
    weights = {k: float(v) for k, v in (criteria or {}).items() if float(v) > 0}
    if weights:
        total_w = sum(weights.values())
        overall = sum(component.get(k, 60) * w for k, w in weights.items())
        overall = overall / total_w if total_w else 0
    else:
        vals = [technical_score, experience_score, education_score,
                project_score, ats_score, grammar_score, formatting_score]
        overall = sum(vals) / len(vals)
    overall_score = _clamp(overall)

    # Strengths / weaknesses derived from component scores.
    labels = {
        "skills": "Skills", "experience": "Experience",
        "education": "Education", "projects": "Projects", "ats": "ATS",
        "grammar": "Grammar", "formatting": "Formatting",
        "keywords": "Keyword match",
    }
    ranked = sorted(component.items(), key=lambda kv: kv[1], reverse=True)
    strengths = [f"Strong {labels.get(k, k)} ({int(v)}/100)"
                 for k, v in ranked[:4] if v >= 65]
    weaknesses = [f"Improve {labels.get(k, k)} ({int(v)}/100)"
                  for k, v in ranked[::-1][:4] if v < 65]
    if not strengths:
        strengths = ["Resume text is machine-readable and parseable."]
    if not weaknesses:
        weaknesses = ["Add more quantified achievements to stand out."]

    exp_score = experience_score
    career = _career_level(parsed, raw_text, exp_score)
    readiness = ("Industry Ready" if overall_score >= 75 else
                 "Nearly Ready" if overall_score >= 60 else
                 "Needs Improvement")

    word_count = parsed.get("word_count") or len(re.findall(r"\w+", raw_text))
    length_review = (
        "Ideal length." if 350 <= word_count <= 900 else
        "Resume is short; add more detail on impact and projects."
        if word_count < 350 else
        "Resume is long; tighten to the most relevant, recent content."
    )

    # Duplicate content detection (repeated lines).
    lines = [ln.strip().lower() for ln in raw_text.splitlines() if ln.strip()]
    seen, dupes = set(), []
    for ln in lines:
        if len(ln) > 25 and ln in seen and ln not in dupes:
            dupes.append(ln)
        seen.add(ln)

    formatting_issues = [c["detail"] for c in ats["checks"]
                         if not c["passed"] and c["name"] in
                         ("Standard section headings", "No complex tables",
                          "Uses bullet points", "Appropriate length")]

    suggestions = []
    if kw["missing_keywords"]:
        suggestions.append(
            "Incorporate missing role keywords: " +
            ", ".join(kw["missing_keywords"][:6]) + ".")
    if gap["missing_skills"]:
        suggestions.append(
            "Close skill gaps in: " + ", ".join(gap["missing_skills"][:6]) + ".")
    if grammar["issues"]:
        suggestions.append("Fix grammar/wording issues flagged below.")
    suggestions.append("Quantify achievements with concrete metrics.")
    suggestions.append("Tailor the summary to the target role.")

    return {
        "overall_score": overall_score,
        "ats_score": ats_score,
        "technical_skills_score": technical_score,
        "soft_skills_score": soft_score,
        "formatting_score": formatting_score,
        "grammar_score": grammar_score,
        "experience_score": experience_score,
        "education_score": education_score,
        "project_score": project_score,
        "keyword_match": keyword_match,
        "career_level": career,
        "industry_readiness": readiness,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_skills": gap["missing_skills"],
        "missing_keywords": kw["missing_keywords"],
        "repeated_keywords": kw["repeated_keywords"],
        "recommended_keywords": kw["recommended_keywords"],
        "matched_keywords": kw["matched_keywords"],
        "improvement_suggestions": suggestions,
        "actionable_suggestions": suggestions,
        "professional_summary_review": (
            parsed.get("summary") and
            "Summary present; make it role-specific and metric-driven." or
            "No professional summary found; add a 2-3 line targeted summary."),
        "project_review": (
            "Projects listed; add stack + quantified impact per project."
            if parsed.get("projects") else
            "No projects section found; add 2-3 relevant projects."),
        "achievements_review": (
            "Achievements present; quantify them."
            if parsed.get("achievements") else
            "Add an achievements/awards section with measurable outcomes."),
        "resume_length_review": f"{word_count} words. {length_review}",
        "formatting_issues": formatting_issues,
        "duplicate_content": dupes,
        "category_scores": {
            "Skills": _clamp(component["skills"]),
            "Experience": experience_score,
            "Education": education_score,
            "Projects": project_score,
            "ATS": ats_score,
            "Grammar": grammar_score,
            "Formatting": formatting_score,
            "Keywords": keyword_match,
        },
        "ats_details": ats,
        "skills_gap": gap,
        "grammar_issues": grammar["issues"],
        "improved": _build_improvements(parsed),
        "engine": "local",
    }
