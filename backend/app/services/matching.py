"""Structured job-matching engine.

The engine is deterministic and explainable: it compares a job's
requirements against the verified career profile and produces
per-dimension evidence.  It does *not* ask an LLM "is this person
suitable" — every score is computed from structured data with
explicit weights, and missing data is reported as "unknown"
rather than treated as a deficiency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.schemas.jobs import DimensionResult, MatchCategory, MatchWeights

# ---------------------------------------------------------------------------
# skill normalization
# ---------------------------------------------------------------------------

SKILL_ALIASES: dict[str, str] = {
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "node.js": "node.js",
    "expressjs": "express",
    "nextjs": "next.js",
    "next": "next.js",
    "gcp": "google cloud",
    "aws": "amazon web services",
    "azure": "microsoft azure",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "llm": "large language models",
    "llms": "large language models",
    "ci/cd": "ci cd",
    "cicd": "ci cd",
    "c++": "c++",
    "c#": "c#",
    ".net": ".net",
    "dotnet": ".net",
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "spring": "spring",
    "spring boot": "spring boot",
    "k8s": "kubernetes",
    "sql": "sql",
    "nosql": "nosql",
    "react native": "react native",
    "rn": "react native",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "py": "python",
    "rs": "rust",
    "golang": "go",
    "ui": "ui design",
    "ux": "ux design",
    "selenium": "selenium",
    "jest": "jest",
    "cypress": "cypress",
    "docker": "docker",
    "kubernets": "kubernetes",
    "terraform": "terraform",
    "git": "git",
    "github": "github",
    "gitlab": "gitlab",
    "figma": "figma",
    "agile": "agile",
    "scrumm": "scrum",
    "scrum": "scrum",
    "rest": "rest apis",
    "rest api": "rest apis",
    "restful": "rest apis",
    "graphql": "graphql",
    "grpc": "grpc",
    "microservices": "microservices",
}

# Common technology tokens used for heuristic requirement extraction.
TECH_LEXICON: set[str] = {
    "python", "java", "javascript", "typescript", "c++", "c#", ".net", "go",
    "golang", "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "sql",
    "nosql", "react", "react native", "vue", "vue.js", "angular", "svelte",
    "next.js", "nuxt", "node.js", "express", "django", "flask", "fastapi",
    "spring", "spring boot", "rails", "laravel", "asp.net",
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle",
    "aws", "amazon web services", "gcp", "google cloud", "azure",
    "microsoft azure", "kubernetes", "docker", "terraform", "pulumi",
    "ci cd", "github actions", "jenkins", "gitlab ci", "circleci",
    "kafka", "rabbitmq", "grpc", "graphql", "rest apis", "websockets",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "pyspark", "hadoop", "spark", "airflow", "dbt",
    "machine learning", "deep learning", "artificial intelligence",
    "large language models", "llm", "nlp", "computer vision",
    "react native", "flutter", "ios", "android",
    "html", "css", "sass", "tailwind", "webpack", "vite",
    "git", "github", "gitlab", "figma", "jira", "confluence",
    "linux", "bash", "prometheus", "grafana", "nginx",
    "security", "oauth", "jwt", "encryption",
    "agile", "scrum", "kanban", "saas", "paas", "iaas",
    "microservices", "event-driven", "serverless",
}

SENIORITY_LEVELS = ["intern", "junior", "mid", "senior", "lead", "staff", "principal", "manager", "director", "vp", "c-level"]

SENIORITY_KEYWORDS = {
    "intern": 0, "internship": 0,
    "junior": 1, "entry": 1, "entry-level": 1, "graduate": 1, "early career": 1,
    "mid": 2, "intermediate": 2,
    "senior": 3, "sr": 3,
    "lead": 4, "staff": 5, "principal": 6,
    "manager": 5, "head of": 6, "director": 7, "vp": 8, "chief": 8,
}

DEGREE_LEVELS = {
    "high school": 1, "associate": 2, "bachelor": 3, "b.sc": 3, "b.tech": 3,
    "bs": 3, "ba": 3, "master": 4, "m.sc": 4, "ms": 4, "mba": 4,
    "phd": 5, "doctorate": 5,
}


def normalize_skill(skill: str) -> str:
    cleaned = re.sub(r"[^\w\s.+#-]", " ", skill.lower()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace(" .", ".")
    if cleaned in SKILL_ALIASES:
        return SKILL_ALIASES[cleaned]
    return cleaned


def skill_similarity(a: str, b: str) -> float:
    """0.0 - 1.0 similarity between two skill strings."""
    na, nb = normalize_skill(a), normalize_skill(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in SKILL_ALIASES and SKILL_ALIASES[na] == nb:
        return 1.0
    if nb in SKILL_ALIASES and SKILL_ALIASES[nb] == na:
        return 1.0
    # token containment: "react js" ~ "react"
    ta, tb = set(na.split()), set(nb.split())
    if ta and tb:
        overlap = len(ta & tb) / max(len(ta | tb), 1)
        if overlap >= 0.75:
            return 0.9
    # substring containment
    if na in nb or nb in na:
        shorter = min(len(na), len(nb))
        longer = max(len(na), len(nb))
        return shorter / longer
    return 0.0


def match_skill_against_profile(skill: str, profile_skills: list[dict]) -> tuple[str, float, str | None]:
    """Return (status, score, matched_skill_name)."""
    best_score = 0.0
    best_name: str | None = None
    for ps in profile_skills:
        score = skill_similarity(skill, ps.get("name", ""))
        if score > best_score:
            best_score = score
            best_name = ps.get("name")
    if best_score >= 0.9:
        return "match", best_score, best_name
    if best_score >= 0.55:
        return "partial", best_score, best_name
    return "missing", best_score, None


def extract_required_skills(listing: dict) -> list[str]:
    """Extract required technical skills from a job listing."""
    found: dict[str, int] = {}

    def scan(text: str | None, weight: int = 1) -> None:
        if not text:
            return
        lowered = text.lower()
        for tech in TECH_LEXICON:
            if re.search(
                r"(?<![a-z0-9])" + re.escape(tech) + r"(?![a-z0-9])",
                lowered,
            ):
                found[tech] = found.get(tech, 0) + weight

    for req in listing.get("requirements") or []:
        scan(str(req), weight=2)
    scan(listing.get("description"), weight=1)
    scan(listing.get("title"), weight=1)

    return sorted(found, key=lambda k: -found[k])


def extract_preferred_skills(listing: dict) -> list[str]:
    found: set[str] = set()

    def scan(text: str | None) -> None:
        if not text:
            return
        lowered = text.lower()
        for tech in TECH_LEXICON:
            if tech in lowered:
                found.add(tech)

    for req in listing.get("preferred_qualifications") or []:
        scan(str(req))
    return sorted(found)


def extract_required_years(listing: dict) -> int | None:
    text = " ".join(str(r) for r in (listing.get("requirements") or []))
    text += " " + str(listing.get("description") or "")
    match = re.search(r"(\d+)\+\s*years?(?:\s+of)?\s+(?:experience|working)", text, re.I)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*years?(?:\s+of)?\s+(?:experience|working)", text, re.I)
    if match:
        return int(match.group(1))
    return None


def extract_education_requirement(listing: dict) -> str | None:
    text = " ".join(str(r) for r in (listing.get("requirements") or []))
    text += " " + str(listing.get("description") or "")
    lowered = text.lower()
    for level in ("phd", "doctorate", "master", "mba", "bachelor", "b.sc", "b.tech", "degree"):
        if level in lowered:
            if level in ("phd", "doctorate"):
                return "phd"
            if level in ("master", "mba"):
                return "master"
            if level in ("bachelor", "b.sc", "b.tech", "degree"):
                return "bachelor"
    return None


def extract_seniority_from_title(title: str) -> int | None:
    lowered = title.lower()
    best: int | None = None
    best_len = 0
    for keyword, level in SENIORITY_KEYWORDS.items():
        if keyword in lowered and len(keyword) > best_len:
            best = level
            best_len = len(keyword)
    return best


def profile_total_years(experience: list[dict]) -> float:
    """Estimate total professional experience in years."""
    total = 0.0
    for exp in experience:
        start = exp.get("start_date")
        end = exp.get("end_date")
        if not start:
            continue
        from datetime import date as _date

        try:
            if isinstance(start, str):
                start_d = _date.fromisoformat(start[:10])
            else:
                start_d = start
            if end:
                if isinstance(end, str):
                    end_d = _date.fromisoformat(end[:10])
                else:
                    end_d = end
            else:
                end_d = _date.today()
            years = (end_d - start_d).days / 365.25
            total += max(0.0, years)
        except (ValueError, TypeError):
            continue
    return total


def profile_highest_degree(education: list[dict]) -> int | None:
    best: int | None = None
    for edu in education:
        qual = str(edu.get("qualification") or "").lower()
        for key, level in DEGREE_LEVELS.items():
            if key in qual:
                if best is None or level > best:
                    best = level
                break
    return best


def profile_seniority(experience: list[dict]) -> int | None:
    """Infer seniority from job titles and total years."""
    best: int | None = None
    for exp in experience:
        level = extract_seniority_from_title(str(exp.get("job_title") or ""))
        if level is not None and (best is None or level > best):
            best = level
    years = profile_total_years(experience)
    if best is None:
        if years >= 8:
            best = 3
        elif years >= 3:
            best = 2
        elif years >= 1:
            best = 1
    return best


# ---------------------------------------------------------------------------
# dimension evaluators
# ---------------------------------------------------------------------------

@dataclass
class DimensionOutcome:
    name: str
    label: str
    score: float  # 0-100
    status: str  # match|partial|missing|unknown
    evidence: list[str] = field(default_factory=list)
    details: str | None = None


def _score_required_skills(requirements: list[str], profile_skills: list[dict]) -> DimensionOutcome:
    if not requirements:
        return DimensionOutcome(
            name="required_skills", label="Required technical skills",
            score=50.0, status="unknown",
            evidence=["The job listing did not specify explicit technical requirements."],
            details="Requirements could not be extracted; this dimension is unknown.",
        )
    matched, partial, missing = [], [], []
    scores = []
    for req in requirements[:12]:
        status, score, matched_name = match_skill_against_profile(req, profile_skills)
        if status == "match":
            matched.append(req)
            scores.append(1.0)
        elif status == "partial":
            partial.append(f"{req} (closest: {matched_name})")
            scores.append(0.5)
        else:
            missing.append(req)
            scores.append(0.0)
    avg = sum(scores) / len(scores) if scores else 0.0
    status = "match" if avg >= 0.7 else ("partial" if avg >= 0.35 else "missing")
    evidence = []
    if matched:
        evidence.append(f"Confirmed skills: {', '.join(matched)}.")
    if partial:
        evidence.append(f"Partial matches: {', '.join(partial)}.")
    if missing:
        evidence.append(f"Missing requirements: {', '.join(missing)}.")
    return DimensionOutcome(
        name="required_skills", label="Required technical skills",
        score=round(avg * 100, 1), status=status, evidence=evidence,
        details=f"{len(matched)} confirmed, {len(partial)} partial, {len(missing)} missing of {len(requireds := requirements[:12])}.",
    )


def _score_preferred_skills(preferred: list[str], profile_skills: list[dict]) -> DimensionOutcome:
    if not preferred:
        return DimensionOutcome(
            name="preferred_skills", label="Preferred skills",
            score=50.0, status="unknown",
            evidence=["No preferred qualifications were listed."],
        )
    hits = 0
    matched_names = []
    for pref in preferred[:8]:
        status, _, matched_name = match_skill_against_profile(pref, profile_skills)
        if status == "match":
            hits += 1
            matched_names.append(pref)
    score = round(hits / len(preferred[:8]) * 100, 1)
    status = "match" if score >= 60 else ("partial" if score > 0 else "missing")
    return DimensionOutcome(
        name="preferred_skills", label="Preferred skills",
        score=score, status=status,
        evidence=[f"Matched preferred skills: {', '.join(matched_names)}." if matched_names else "None of the preferred skills were found in the profile."],
    )


def _score_experience(required_years: int | None, total_years: float) -> DimensionOutcome:
    if required_years is None:
        return DimensionOutcome(
            name="experience", label="Professional experience",
            score=50.0, status="unknown",
            evidence=["The listing did not state an experience requirement."],
        )
    if total_years >= required_years:
        return DimensionOutcome(
            name="experience", label="Professional experience",
            score=100.0, status="match",
            evidence=[f"{total_years:.1f} years of verified experience meets the {required_years}-year requirement."],
        )
    ratio = total_years / required_years
    score = min(100.0, round(ratio * 100, 1))
    return DimensionOutcome(
        name="experience", label="Professional experience",
        score=score, status="partial" if ratio >= 0.5 else "missing",
        evidence=[f"{total_years:.1f} years of experience vs. {required_years} required."],
        details="Missing experience is a gap, not a disqualifier; equivalent experience may count.",
    )


def _score_education(required: str | None, education: list[dict]) -> DimensionOutcome:
    if required is None:
        return DimensionOutcome(
            name="education", label="Education",
            score=50.0, status="unknown",
            evidence=["No formal education requirement was stated."],
        )
    required_level = DEGREE_LEVELS.get(required, 3)
    highest = profile_highest_degree(education)
    if highest is None:
        return DimensionOutcome(
            name="education", label="Education",
            score=50.0, status="unknown",
            evidence=[f"The role lists '{required}' but the profile has no education records. Missing data is not evidence of absence."],
        )
    if highest >= required_level:
        return DimensionOutcome(
            name="education", label="Education",
            score=100.0, status="match",
            evidence=[f"Highest qualification meets or exceeds the '{required}' requirement."],
        )
    return DimensionOutcome(
        name="education", label="Education",
        score=40.0, status="partial",
        evidence=[f"Highest qualification is below the stated '{required}' requirement; equivalent experience may compensate."],
    )


def _score_certifications(requirements: list[str], certifications: list[dict]) -> DimensionOutcome:
    if not certifications:
        return DimensionOutcome(
            name="certifications", label="Certifications",
            score=50.0, status="unknown",
            evidence=["No certifications recorded in the profile."],
        )
    cert_text = " ".join(
        f"{c.get('name', '')} {c.get('issuing_organization', '')}" for c in certifications
    ).lower()
    hits = [r for r in requirements if r.lower() in cert_text]
    if hits:
        return DimensionOutcome(
            name="certifications", label="Certifications",
            score=100.0, status="match",
            evidence=[f"Relevant certifications: {', '.join(hits)}."],
        )
    return DimensionOutcome(
        name="certifications", label="Certifications",
        score=50.0, status="unknown",
        evidence=["Certifications are on file but none directly match stated requirements."],
    )


def _score_projects(requirements: list[str], projects: list[dict]) -> DimensionOutcome:
    if not projects:
        return DimensionOutcome(
            name="projects", label="Relevant projects",
            score=50.0, status="unknown",
            evidence=["No projects recorded in the profile."],
        )
    req_set = {normalize_skill(r) for r in requirements}
    best_score = 0.0
    best_name = None
    for project in projects:
        techs = [normalize_skill(t) for t in (project.get("technologies") or [])]
        text = f"{project.get('name', '')} {project.get('description', '')} {project.get('problem_solved', '')}".lower()
        score = 0.0
        for tech in techs:
            for req in req_set:
                if skill_similarity(tech, req) >= 0.8:
                    score += 1
        if score > best_score:
            best_score = score
            best_name = project.get("name")
    if best_score == 0:
        return DimensionOutcome(
            name="projects", label="Relevant projects",
            score=40.0, status="missing",
            evidence=["No projects directly overlap with the required technologies."],
        )
    ratio = min(1.0, best_score / max(len(req_set), 1))
    return DimensionOutcome(
        name="projects", label="Relevant projects",
        score=round(40 + ratio * 60, 1), status="match" if ratio >= 0.5 else "partial",
        evidence=[f"Project '{best_name}' overlaps with {int(best_score)} required technology area(s)."],
    )


def _score_seniority(listing: dict, experience: list[dict]) -> DimensionOutcome:
    required = extract_seniority_from_title(listing.get("title", ""))
    profile_level = profile_seniority(experience)
    if required is None:
        return DimensionOutcome(
            name="seniority", label="Seniority level",
            score=50.0, status="unknown",
            evidence=["Seniority could not be determined from the job title."],
        )
    if profile_level is None:
        return DimensionOutcome(
            name="seniority", label="Seniority level",
            score=50.0, status="unknown",
            evidence=[f"The role targets a '{_level_name(required)}' level; the profile has no experience records yet."],
        )
    if profile_level >= required:
        return DimensionOutcome(
            name="seniority", label="Seniority level",
            score=100.0, status="match",
            evidence=[f"Profile level ('{_level_name(profile_level)}') meets the '{_level_name(required)}' target."],
        )
    gap = required - profile_level
    score = max(0.0, 100 - gap * 25)
    return DimensionOutcome(
        name="seniority", label="Seniority level",
        score=score, status="partial" if gap == 1 else "missing",
        evidence=[f"Profile level '{_level_name(profile_level)}' vs. target '{_level_name(required)}'."],
        details="Seniority is inferred from titles and experience years; it is an estimate.",
    )


def _level_name(level: int) -> str:
    if level <= 1:
        return "junior"
    if level == 2:
        return "mid-level"
    if level == 3:
        return "senior"
    if level == 4:
        return "lead"
    return "staff+"


def _score_location(listing: dict, preferences: dict | None) -> DimensionOutcome:
    location = (listing.get("location") or "").lower()
    workplace = (listing.get("workplace_type") or "").lower()
    if not preferences:
        return DimensionOutcome(
            name="location", label="Location & work authorization",
            score=50.0, status="unknown",
            evidence=["Location preferences have not been set yet."],
        )
    preferred_countries = [str(c).lower() for c in (preferences.get("preferred_countries") or [])]
    preferred_cities = [str(c).lower() for c in (preferences.get("preferred_cities") or [])]
    workplace_types = [str(w).lower() for w in (preferences.get("workplace_types") or [])]

    evidence = []
    score = 100.0
    status = "match"

    if workplace_types:
        if workplace and any(wt in workplace for wt in workplace_types):
            evidence.append(f"Workplace type '{workplace}' matches preference.")
        elif workplace:
            evidence.append(f"Workplace type '{workplace}' is outside stated preferences.")
            score -= 30
            status = "partial"
    if preferred_countries or preferred_cities:
        country_match = any(c in location for c in preferred_countries)
        city_match = any(c in location for c in preferred_cities)
        if country_match or city_match:
            evidence.append("Location matches preferred locations.")
        elif not workplace or "remote" not in workplace:
            evidence.append("Location does not match preferred locations.")
            score -= 25
            status = "partial"
    if not evidence:
        evidence.append("No location constraints configured; no conflict detected.")

    return DimensionOutcome(
        name="location", label="Location & work authorization",
        score=max(0.0, round(score, 1)), status=status, evidence=evidence,
    )


def _score_employment_type(listing: dict, preferences: dict | None) -> DimensionOutcome:
    employment = (listing.get("employment_type") or "").lower()
    if not employment:
        return DimensionOutcome(
            name="employment_type", label="Employment type",
            score=50.0, status="unknown",
            evidence=["Employment type not stated in the listing."],
        )
    if not preferences or not preferences.get("employment_types"):
        return DimensionOutcome(
            name="employment_type", label="Employment type",
            score=75.0, status="match",
            evidence=[f"Listing is '{employment}'; no employment-type preference set."],
        )
    preferred = [str(e).lower() for e in preferences["employment_types"]]
    if any(employment.startswith(p) or p in employment for p in preferred):
        return DimensionOutcome(
            name="employment_type", label="Employment type",
            score=100.0, status="match",
            evidence=[f"'{employment}' matches preferred employment types."],
        )
    return DimensionOutcome(
        name="employment_type", label="Employment type",
        score=20.0, status="missing",
        evidence=[f"'{employment}' does not match preferred types: {', '.join(preferred)}."],
    )


def _score_salary(listing: dict, preferences: dict | None) -> DimensionOutcome:
    salary_min = listing.get("salary_min")
    salary_max = listing.get("salary_max")
    if salary_min is None and salary_max is None:
        return DimensionOutcome(
            name="salary", label="Salary compatibility",
            score=50.0, status="unknown",
            evidence=["The listing does not disclose salary information."],
        )
    if not preferences or not preferences.get("minimum_acceptable_salary"):
        return DimensionOutcome(
            name="salary", label="Salary compatibility",
            score=75.0, status="unknown",
            evidence=["Salary is listed but no minimum acceptable compensation is configured."],
        )
    minimum = preferences["minimum_acceptable_salary"]
    offered = salary_min if salary_min else (salary_max or 0)
    if offered >= minimum:
        return DimensionOutcome(
            name="salary", label="Salary compatibility",
            score=100.0, status="match",
            evidence=[f"Listed salary meets or exceeds the configured minimum."],
        )
    return DimensionOutcome(
        name="salary", label="Salary compatibility",
        score=20.0, status="missing",
        evidence=[f"Listed salary is below the configured minimum acceptable compensation."],
    )


def _score_portfolio(requirements: list[str], projects: list[dict]) -> DimensionOutcome:
    public_projects = [p for p in projects if p.get("is_public", True)]
    if not public_projects:
        return DimensionOutcome(
            name="portfolio", label="Portfolio relevance",
            score=50.0, status="unknown",
            evidence=["No public projects are available to evaluate."],
        )
    req_set = {normalize_skill(r) for r in requirements}
    best = 0.0
    for project in public_projects:
        techs = [normalize_skill(t) for t in (project.get("technologies") or [])]
        overlap = sum(1 for t in techs for r in req_set if skill_similarity(t, r) >= 0.8)
        best = max(best, min(1.0, overlap / max(len(req_set), 1)))
    score = round(40 + best * 60, 1)
    return DimensionOutcome(
        name="portfolio", label="Portfolio relevance",
        score=score, status="match" if best >= 0.4 else "partial",
        evidence=[f"Public portfolio overlaps with {int(best * 100)}% of required technology areas."],
    )


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------

DIMENSION_LABELS = {
    "required_skills": "Required technical skills",
    "preferred_skills": "Preferred technical skills",
    "experience": "Relevant professional experience",
    "education": "Education requirements",
    "certifications": "Certifications",
    "projects": "Relevant projects",
    "seniority": "Seniority & experience level",
    "location": "Location & work authorization",
    "employment_type": "Employment type",
    "salary": "Salary compatibility",
    "portfolio": "Portfolio relevance",
}


def compute_match(
    profile_data: dict,
    listing: dict,
    weights: MatchWeights | None = None,
) -> dict:
    """Compute a structured, explainable match report.

    ``profile_data`` contains: experience, education, skills, projects,
    certifications, preferences.
    """
    weights = weights or MatchWeights()
    experience = profile_data.get("experience") or []
    education = profile_data.get("education") or []
    skills = profile_data.get("skills") or []
    projects = profile_data.get("projects") or []
    certifications = profile_data.get("certifications") or []
    preferences = profile_data.get("preferences")

    requirements = extract_required_skills(listing)
    preferred = extract_preferred_skills(listing)
    required_years = extract_required_years(listing)
    education_req = extract_education_requirement(listing)

    dimensions: list[DimensionOutcome] = [
        _score_required_skills(requirements, skills),
        _score_preferred_skills(preferred, skills),
        _score_experience(required_years, profile_total_years(experience)),
        _score_education(education_req, education),
        _score_certifications(requirements, certifications),
        _score_projects(requirements, projects),
        _score_seniority(listing, experience),
        _score_location(listing, preferences),
        _score_employment_type(listing, preferences),
        _score_salary(listing, preferences),
        _score_portfolio(requirements, projects),
    ]

    weight_map = {
        "required_skills": weights.required_skills,
        "preferred_skills": weights.preferred_skills,
        "experience": weights.experience,
        "education": weights.education,
        "certifications": weights.certifications,
        "projects": weights.projects,
        "seniority": weights.seniority,
        "location": weights.location,
        "employment_type": weights.employment_type,
        "salary": weights.salary,
        "portfolio": weights.portfolio,
    }

    total_weight = 0.0
    weighted_sum = 0.0
    for dim in dimensions:
        w = weight_map.get(dim.name, 0.0)
        if dim.status == "unknown":
            # Unknown dimensions are excluded from the weighted average
            # so missing data never penalizes the candidate.
            continue
        weighted_sum += dim.score * w
        total_weight += w

    overall = round(weighted_sum / total_weight, 1) if total_weight > 0 else 50.0

    strong = []
    partial = []
    missing = []
    unknown = []
    for dim in dimensions:
        if dim.status == "match":
            strong.append(f"{dim.label}: {dim.score:.0f}/100")
        elif dim.status == "partial":
            partial.append(f"{dim.label}: {dim.score:.0f}/100")
        elif dim.status == "missing":
            missing.append(f"{dim.label}: {dim.score:.0f}/100")
        else:
            unknown.append(dim.label)

    # Report the actual missing requirement items (not just dimensions).
    profile_skill_names = [normalize_skill(s.get("name", "")) for s in skills]
    missing_skill_items = [
        req
        for req in requirements[:12]
        if not any(
            skill_similarity(req, ps) >= 0.55 for ps in profile_skill_names if ps
        )
    ]
    for item in missing_skill_items:
        entry = f"Missing requirement: {item}"
        if entry not in missing:
            missing.append(entry)

    # Also surface the specific confirmed skills, not just dimensions.
    matched_skill_items = [
        req
        for req in requirements[:12]
        if any(skill_similarity(req, ps) >= 0.9 for ps in profile_skill_names if ps)
    ]
    for item in matched_skill_items:
        entry = f"Confirmed skill: {item}"
        if entry not in strong:
            strong.append(entry)

    # Potential disqualifiers: hard requirements with zero profile evidence.
    disqualifiers = []
    for dim in dimensions:
        if dim.name in ("required_skills", "experience", "education") and dim.status == "missing":
            disqualifiers.append(dim.label)

    category = categorize_match(overall)

    factors = []
    for dim in sorted(dimensions, key=lambda d: -d.score):
        if dim.status != "unknown":
            factors.append(f"{dim.label} ({dim.score:.0f}/100, {dim.status})")

    narrative = _build_narrative(overall, category, strong, missing, unknown)

    return {
        "overall_score": overall,
        "category": category.value,
        "dimensions": [
            DimensionResult(
                name=d.name, label=d.label, score=d.score,
                weight=round(weight_map.get(d.name, 0.0), 3),
                status=d.status, evidence=d.evidence, details=d.details,
            ).model_dump()
            for d in dimensions
        ],
        "strong_matches": strong,
        "partial_matches": partial,
        "missing_requirements": missing,
        "potential_disqualifiers": disqualifiers,
        "unknown_items": unknown,
        "factors": factors,
        "narrative": narrative,
        "weights_snapshot": weights.model_dump(),
    }


def categorize_match(score: float) -> MatchCategory:
    if score >= 75:
        return MatchCategory.STRONG
    if score >= 55:
        return MatchCategory.CONSIDER
    if score >= 35:
        return MatchCategory.STRETCH
    return MatchCategory.LOW


def _build_narrative(score: float, category: MatchCategory, strong: list, missing: list, unknown: list) -> str:
    parts = [f"Overall suitability: {score:.0f}/100 ({category.value.replace('_', ' ')})."]
    if strong:
        parts.append("Strong alignment in: " + "; ".join(strong[:3]) + ".")
    if missing:
        parts.append("Gaps to address truthfully: " + "; ".join(missing[:3]) + ".")
    if unknown:
        parts.append("Could not be assessed (missing data): " + ", ".join(unknown[:3]) + ".")
    return " ".join(parts)
