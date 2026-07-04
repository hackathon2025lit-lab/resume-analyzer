"""Resume text extraction and field parsing.

Text extraction:
  * PDF  -> pdfplumber (primary) with PyMuPDF (fitz) fallback.
  * DOCX -> python-docx.

Field parsing uses well-tested regular expressions and section detection.
This keeps the "always works" contract even when the AI service is offline.
"""
from __future__ import annotations

import re
import tempfile
import zipfile
from pathlib import Path

import pdfplumber
import fitz  # PyMuPDF
from docx import Document

# Resume file types we can read directly (i.e. not archives).
DOCUMENT_EXTENSIONS = ("pdf", "docx")

# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text(path: Path, ext: str) -> str:
    ext = ext.lower()
    if ext == "pdf":
        return _extract_pdf(path)
    if ext == "docx":
        return _extract_docx(path)
    if ext == "zip":
        return _extract_zip(path)
    raise ValueError(f"Unsupported file type: {ext}")


def _extract_zip(path: Path) -> str:
    """Extract text from the first PDF/DOCX resume inside a ZIP archive."""
    try:
        with zipfile.ZipFile(str(path)) as archive:
            members = [
                m for m in archive.namelist()
                if not m.endswith("/")
                and not Path(m).name.startswith((".", "__"))
                and Path(m).suffix.lower().lstrip(".") in DOCUMENT_EXTENSIONS
            ]
            if not members:
                raise ValueError(
                    "The ZIP archive contains no PDF or DOCX resume.")
            members.sort()
            member = members[0]
            inner_ext = Path(member).suffix.lower().lstrip(".")
            with tempfile.TemporaryDirectory() as tmp:
                # Extract only the chosen member, guarding against zip-slip.
                target = Path(tmp) / Path(member).name
                with archive.open(member) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                return extract_text(target, inner_ext)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Could not read ZIP archive: {exc}") from exc


def _extract_pdf(path: Path) -> str:
    text_parts: list[str] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        text = "\n".join(text_parts).strip()
        if text:
            return text
    except Exception:
        text = ""

    # Fallback to PyMuPDF for tricky/encoded PDFs.
    try:
        doc = fitz.open(str(path))
        text = "\n".join(page.get_text() for page in doc).strip()
        doc.close()
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Could not read PDF: {exc}") from exc
    return text


def _extract_docx(path: Path) -> str:
    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" ".join(cell.text for cell in row.cells))
    return "\n".join(parts).strip()


# ---------------------------------------------------------------------------
# Field parsing
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(
    r"(?:(?:\+?\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?)?\d{3,4}[\s.\-]?\d{3,4})"
)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_\-./]+")
LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[A-Za-z0-9_\-./]+"
)
URL_RE = re.compile(r"https?://[^\s)]+")

SECTION_ALIASES = {
    "skills": ["skills", "technical skills", "core competencies", "expertise"],
    "technical_skills": ["technical skills", "programming", "technologies",
                         "tech stack", "tools"],
    "soft_skills": ["soft skills", "interpersonal skills", "personal skills"],
    "education": ["education", "academic", "qualification", "qualifications"],
    "certifications": ["certification", "certifications", "licenses",
                       "courses"],
    "experience": ["experience", "work experience", "employment",
                   "professional experience", "work history"],
    "projects": ["projects", "personal projects", "academic projects"],
    "languages": ["languages", "language proficiency"],
    "achievements": ["achievements", "accomplishments", "awards", "honors"],
    "internships": ["internship", "internships", "training"],
    "summary": ["summary", "objective", "profile", "about"],
}

# Common technical skills used to classify the skills section.
KNOWN_TECH = {
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "sql",
    "html", "css", "react", "angular", "vue", "node", "django", "flask",
    "fastapi", "spring", "express", "tensorflow", "pytorch", "keras",
    "pandas", "numpy", "scikit-learn", "docker", "kubernetes", "aws", "gcp",
    "azure", "git", "linux", "mongodb", "postgresql", "mysql", "redis",
    "kafka", "spark", "hadoop", "tableau", "power bi", "excel", "jira",
    "rest", "graphql", "ci/cd", "jenkins", "terraform", "ansible",
}

SOFT_SKILL_HINTS = {
    "communication", "leadership", "teamwork", "collaboration",
    "problem solving", "problem-solving", "adaptability", "creativity",
    "time management", "critical thinking", "management", "presentation",
    "negotiation", "mentoring", "organization",
}


def _split_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _find_sections(lines: list[str]) -> dict[str, list[str]]:
    """Group lines under detected section headers."""
    sections: dict[str, list[str]] = {}
    current = "header"
    sections[current] = []

    # Map header text -> canonical section key.
    lookup: dict[str, str] = {}
    for key, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            lookup[alias] = key

    for line in lines:
        low = re.sub(r"[^a-z ]", "", line.lower()).strip()
        matched = None
        # A header line is short and matches an alias.
        if len(low) <= 40:
            for alias, key in lookup.items():
                if low == alias or low.startswith(alias + " ") or \
                        low.endswith(" " + alias) or low == alias + "s":
                    matched = key
                    break
        if matched:
            current = matched
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def _guess_name(lines: list[str], email: str) -> str:
    """The name is usually the first non-contact line at the top."""
    for line in lines[:6]:
        low = line.lower()
        if EMAIL_RE.search(line) or PHONE_RE.search(line):
            continue
        if any(w in low for w in ("resume", "curriculum", "cv")):
            continue
        letters = re.sub(r"[^A-Za-z ]", "", line).strip()
        words = letters.split()
        if 1 < len(words) <= 5 and len(letters) >= 3:
            return line.strip()
    # Derive from the email local-part as a last resort.
    if email:
        local = email.split("@")[0]
        parts = re.split(r"[._\-]", local)
        return " ".join(p.capitalize() for p in parts if p)
    return ""


def _extract_skill_items(chunk: list[str]) -> list[str]:
    items: list[str] = []
    for line in chunk:
        for token in re.split(r"[,\u2022•|/;·]|\s{2,}", line):
            token = token.strip(" .:-\t")
            if 1 < len(token) <= 40:
                items.append(token)
    # De-duplicate preserving order.
    seen, out = set(), []
    for it in items:
        key = it.lower()
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out[:60]


def parse_fields(text: str) -> dict:
    """Extract structured fields from raw resume text."""
    lines = _split_lines(text)
    joined = "\n".join(lines)
    lower = joined.lower()

    email_match = EMAIL_RE.search(joined)
    email = email_match.group(0) if email_match else ""

    # Phone: pick the longest plausible match to avoid catching stray numbers.
    phones = [p for p in PHONE_RE.findall(joined) if len(re.sub(r"\D", "", p)) >= 8]
    phone = max(phones, key=len).strip() if phones else ""

    github = GITHUB_RE.search(joined)
    linkedin = LINKEDIN_RE.search(joined)

    sections = _find_sections(lines)

    def section_text(key: str) -> list[str]:
        return sections.get(key, [])

    skills_chunk = section_text("skills") + section_text("technical_skills")
    all_skills = _extract_skill_items(skills_chunk)

    technical_skills = [s for s in all_skills
                        if s.lower() in KNOWN_TECH]
    # Also scan whole text for known tech not in a dedicated section.
    for tech in KNOWN_TECH:
        if re.search(rf"(?<![a-z]){re.escape(tech)}(?![a-z])", lower):
            if tech not in [t.lower() for t in technical_skills]:
                technical_skills.append(tech)

    soft_skills = _extract_skill_items(section_text("soft_skills"))
    if not soft_skills:
        soft_skills = [s for s in SOFT_SKILL_HINTS if s in lower]

    # Address heuristic: line with a comma near a pincode/state keyword.
    address = ""
    for line in lines[:12]:
        if re.search(r"\d{5,6}", line) and "," in line and not EMAIL_RE.search(line):
            address = line.strip()
            break

    parsed = {
        "name": _guess_name(lines, email),
        "email": email,
        "phone": phone,
        "address": address,
        "github": (github.group(0) if github else ""),
        "linkedin": (linkedin.group(0) if linkedin else ""),
        "skills": all_skills,
        "technical_skills": sorted(set(technical_skills), key=str.lower),
        "soft_skills": sorted(set(soft_skills), key=str.lower),
        "education": section_text("education"),
        "certifications": section_text("certifications"),
        "experience": section_text("experience"),
        "projects": section_text("projects"),
        "languages": _extract_skill_items(section_text("languages")),
        "achievements": section_text("achievements"),
        "internships": section_text("internships"),
        "summary": " ".join(section_text("summary")),
        "word_count": len(re.findall(r"\w+", joined)),
    }
    return parsed


def parse_resume(path: Path, ext: str) -> tuple[str, dict]:
    """Return (raw_text, parsed_fields) for a resume file."""
    text = extract_text(path, ext)
    if not text.strip():
        raise ValueError("No readable text found in the document.")
    return text, parse_fields(text)
