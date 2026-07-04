"""Skills-gap analysis: compare current vs. required skills for a role."""
from __future__ import annotations

from utils.constants import keywords_for_role

# Lightweight learning-roadmap hints for common missing skills.
ROADMAP_HINTS = {
    "docker": "Containerize a small app and push an image to a registry.",
    "kubernetes": "Deploy a multi-service app to a local k8s (minikube/kind).",
    "sql": "Practice JOINs, aggregations and window functions on real data.",
    "machine learning": "Build an end-to-end model with scikit-learn.",
    "deep learning": "Train a CNN/RNN with PyTorch or TensorFlow.",
    "aws": "Earn hands-on time with EC2, S3, Lambda and IAM.",
    "react": "Build a component-driven SPA with hooks and routing.",
    "rest api": "Design and document a CRUD API with proper status codes.",
    "testing": "Add unit + integration tests to an existing project.",
    "ci/cd": "Set up a GitHub Actions pipeline for build, test and deploy.",
}


def analyze(parsed: dict, role: str) -> dict:
    required = keywords_for_role(role)
    current_lower = {s.lower() for s in
                     parsed.get("skills", []) + parsed.get("technical_skills", [])}
    raw_current = sorted(
        set(parsed.get("technical_skills", []) + parsed.get("skills", [])),
        key=str.lower,
    )

    missing = [r for r in required if r not in current_lower and
               not any(r in c for c in current_lower)]

    roadmap = []
    for skill in missing[:6]:
        roadmap.append({
            "skill": skill,
            "action": ROADMAP_HINTS.get(
                skill, f"Complete a focused course/project on '{skill}'."),
        })

    return {
        "current_skills": raw_current,
        "required_skills": required,
        "missing_skills": missing,
        "roadmap": roadmap,
    }
