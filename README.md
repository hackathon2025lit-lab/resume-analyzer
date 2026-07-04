# AI Resume Analyzer

A production-ready **AI Resume Analyzer** web application built with **Flask +
Python**, vanilla **HTML/CSS/JS**, **SQLite**, **Google Sign-In (OAuth 2.0)**
and the **Google Gemini API**. Upload a resume (PDF, DOCX or a ZIP archive
containing one), pick weighted
evaluation criteria and a target role, and get ATS scores, keyword insights,
skills-gap analysis, grammar checks, charts and downloadable reports.

No React, Next.js, TypeScript, Node.js, Tailwind or Bootstrap. Everything
starts at **zero** — there is no sample, demo or placeholder data. Real values
are generated only after a successful analysis.

---

## Features

- **Google Sign-In** (OAuth 2.0 / OpenID Connect) with session management and
  protected routes.
- **Dashboard** with live stats (all `0` until you analyze), upload, criteria
  selection, job-role selection and history.
- **Resume upload**: drag & drop or browse, PDF/DOCX/ZIP, 10 MB limit, format
  validation, upload progress, filename display and remove option. ZIP archives
  are unpacked and the first PDF/DOCX inside is analyzed.
- **Delete analyses** from the history page or directly from a results page.
- **Resume parsing** (pdfplumber + PyMuPDF fallback, python-docx): name, email,
  phone, address, skills, technical/soft skills, education, certifications,
  experience, projects, languages, achievements, internships, GitHub, LinkedIn.
- **Manual criteria selection** with checkboxes **and weight sliders** that the
  AI honours during scoring.
- **Job-role selection** (12 preset roles + custom role text input).
- **Gemini AI analysis**: overall/ATS/technical/soft/formatting/grammar/
  experience/education/project scores, keyword match, missing skills/keywords,
  industry readiness, career level, reviews and actionable suggestions.
- **ATS scanner**, **keyword analyzer**, **skills-gap analysis** with a learning
  roadmap, **grammar checker** and **resume-improvement** suggestions.
- **Charts** (custom vanilla-canvas): circular gauges + category bar chart.
- **Downloadable reports** (PDF via ReportLab, TXT) and **history export** (JSON).
- **History**: view, delete, download, search and sort.
- **Profile**: name, email, dates, totals and averages, recent activity.
- **Modern UI**: responsive, animated, gradient cards, **dark/light mode**.
- **Security**: filename sanitization, upload validation, path-traversal guards,
  HTTP-only session cookies, environment-based secrets.
- **Graceful offline mode**: if `GEMINI_API_KEY` is not set, a built-in
  deterministic analyzer produces a full analysis so nothing ever fails.

---

## Project structure

```
app.py                # Flask entrypoint / application factory
config/               # Environment-driven configuration
auth/                 # Google OAuth blueprint
routes/               # dashboard, resume (upload/analyze), history, profile
services/             # parser, ai (Gemini), ats, keyword, skills, grammar,
                      # local_analyzer, report generation
models/               # SQLite connection + user/resume/analysis data access
utils/                # security helpers + constants (roles, criteria, keywords)
templates/            # Jinja2 templates (base, login, dashboard, analysis, …)
static/css, static/js # styles + vanilla JS (upload, charts, theme, …)
database/schema.sql   # SQLite schema
uploads/ reports/     # runtime user files (git-ignored)
```

---

## Setup

### 1. Requirements
- Python 3.10+

### 2. Install
```bash
cd ai-resume-analyzer
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
```
Then edit `.env`:

| Variable | Description |
|---|---|
| `FLASK_SECRET_KEY` | Long random string for session signing |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth credentials |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GEMINI_MODEL` | Defaults to `gemini-1.5-flash` |

#### Google OAuth credentials
1. Go to <https://console.cloud.google.com/apis/credentials>.
2. Create an **OAuth client ID** (type: Web application).
3. Add authorized redirect URI: `http://127.0.0.1:5000/auth/callback`.
4. Copy the client ID/secret into `.env`.

#### Gemini API key
Create a key at <https://aistudio.google.com/app/apikey> and set `GEMINI_API_KEY`.

> If `GEMINI_API_KEY` is empty, the app automatically uses its built-in offline
> analyzer, so it still runs and produces full results.

### 4. Run
```bash
python app.py
```
Open <http://127.0.0.1:5000>. The SQLite database is created automatically on
first run.

---

## Local testing without Google (optional)

To try the UI without configuring OAuth, set `ALLOW_DEV_LOGIN=1` in `.env` and
use the "local developer account" button on the login page. This creates a real
user record and is **disabled by default** — it is a developer convenience only,
not demo data.

---

## Security notes
- Secrets are read from environment variables and never committed (`.env` is
  git-ignored).
- Uploaded filenames are sanitized; uploads are restricted to PDF/DOCX/ZIP and a
  10 MB limit; file paths are validated against the uploads directory.
- Session cookies are `HttpOnly` with `SameSite=Lax`.

---

## Tech stack
Flask · SQLite · Authlib (Google OAuth) · pdfplumber · PyMuPDF · python-docx ·
google-generativeai (Gemini) · ReportLab · vanilla HTML/CSS/JS.
