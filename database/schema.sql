-- ------------------------------------------------------------------
-- AI Resume Analyzer - SQLite schema
-- ------------------------------------------------------------------

PRAGMA foreign_keys = ON;

-- Application users (populated from Google Sign-In).
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    google_id     TEXT    UNIQUE NOT NULL,
    email         TEXT    UNIQUE NOT NULL,
    name          TEXT    NOT NULL,
    picture       TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Uploaded resumes and their extracted (parsed) content.
CREATE TABLE IF NOT EXISTS resumes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    filename      TEXT    NOT NULL,      -- sanitized stored filename
    original_name TEXT    NOT NULL,      -- name as uploaded by the user
    file_ext      TEXT    NOT NULL,
    file_size     INTEGER NOT NULL,
    raw_text      TEXT,                  -- full extracted text
    parsed_json   TEXT,                  -- JSON of extracted fields
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- AI analyses performed against a resume.
CREATE TABLE IF NOT EXISTS analyses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    resume_id     INTEGER NOT NULL,
    job_role      TEXT,
    criteria_json TEXT,                  -- selected criteria + weights
    result_json   TEXT,                  -- full AI analysis result
    overall_score INTEGER DEFAULT 0,
    ats_score     INTEGER DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id)   REFERENCES users (id)    ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resumes (id)  ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resumes_user  ON resumes  (user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses (user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_resume ON analyses (resume_id);
