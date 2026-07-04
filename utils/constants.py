"""Shared constants: job roles, criteria, and role -> keyword maps."""

JOB_ROLES = [
    "Software Engineer",
    "Python Developer",
    "Data Analyst",
    "Data Scientist",
    "AI Engineer",
    "Machine Learning Engineer",
    "Full Stack Developer",
    "Backend Developer",
    "Frontend Developer",
    "Cloud Engineer",
    "Cybersecurity Analyst",
    "Business Analyst",
    "Custom Role",
]

# Criteria the user can weight. Default weights sum to 100.
CRITERIA = [
    {"key": "skills", "label": "Skills", "default": 20},
    {"key": "experience", "label": "Experience", "default": 20},
    {"key": "education", "label": "Education", "default": 10},
    {"key": "projects", "label": "Projects", "default": 15},
    {"key": "ats", "label": "ATS Compatibility", "default": 15},
    {"key": "grammar", "label": "Grammar", "default": 5},
    {"key": "formatting", "label": "Formatting", "default": 5},
    {"key": "keywords", "label": "Keywords", "default": 10},
    {"key": "achievements", "label": "Achievements", "default": 0},
    {"key": "certifications", "label": "Certifications", "default": 0},
    {"key": "leadership", "label": "Leadership", "default": 0},
    {"key": "communication", "label": "Communication", "default": 0},
]

# Reference keyword sets per role (used by ATS/keyword/skills-gap fallbacks
# and to guide the AI).
ROLE_KEYWORDS = {
    "Software Engineer": [
        "python", "java", "c++", "data structures", "algorithms", "git",
        "rest api", "sql", "testing", "agile", "oop", "docker", "ci/cd",
        "system design", "microservices",
    ],
    "Python Developer": [
        "python", "django", "flask", "fastapi", "rest api", "sql", "orm",
        "pytest", "pandas", "numpy", "celery", "redis", "docker", "git",
        "asyncio",
    ],
    "Data Analyst": [
        "sql", "excel", "python", "tableau", "power bi", "statistics",
        "data visualization", "pandas", "reporting", "etl", "dashboards",
        "a/b testing",
    ],
    "Data Scientist": [
        "python", "machine learning", "statistics", "pandas", "numpy",
        "scikit-learn", "sql", "deep learning", "tensorflow", "pytorch",
        "data visualization", "feature engineering", "nlp",
    ],
    "AI Engineer": [
        "python", "machine learning", "deep learning", "tensorflow",
        "pytorch", "nlp", "llm", "transformers", "mlops", "docker",
        "model deployment", "hugging face", "vector database",
    ],
    "Machine Learning Engineer": [
        "python", "machine learning", "pytorch", "tensorflow", "mlops",
        "scikit-learn", "docker", "kubernetes", "feature engineering",
        "model deployment", "aws", "spark", "ci/cd",
    ],
    "Full Stack Developer": [
        "javascript", "react", "node", "html", "css", "rest api", "sql",
        "mongodb", "git", "docker", "typescript", "express", "redux",
        "authentication",
    ],
    "Backend Developer": [
        "python", "java", "node", "rest api", "sql", "microservices",
        "docker", "redis", "kafka", "postgresql", "authentication",
        "system design", "caching",
    ],
    "Frontend Developer": [
        "javascript", "react", "html", "css", "typescript", "redux",
        "responsive design", "webpack", "accessibility", "sass",
        "testing", "vue", "figma",
    ],
    "Cloud Engineer": [
        "aws", "azure", "gcp", "terraform", "kubernetes", "docker",
        "ci/cd", "linux", "networking", "ansible", "iac", "monitoring",
        "cloudformation",
    ],
    "Cybersecurity Analyst": [
        "network security", "siem", "penetration testing", "firewall",
        "incident response", "vulnerability assessment", "python", "linux",
        "encryption", "owasp", "risk assessment", "compliance",
    ],
    "Business Analyst": [
        "requirements gathering", "sql", "excel", "stakeholder management",
        "data analysis", "documentation", "agile", "jira", "process mapping",
        "reporting", "communication", "visualization",
    ],
}

DEFAULT_KEYWORDS = [
    "communication", "teamwork", "problem solving", "leadership", "python",
    "sql", "git", "project", "analysis", "management",
]


def keywords_for_role(role: str) -> list[str]:
    return ROLE_KEYWORDS.get(role, DEFAULT_KEYWORDS)
