"""Deterministic local agent implementations.

These engines produce structured, evidence-grounded results
without any AI provider.  They are the fallback *and* the
default when no provider is configured, which keeps the
application fully usable offline.  When a provider is
configured, the same agents additionally attempt an LLM
pass - but never trust it with facts the profile does not
contain.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.matching import (
    extract_required_skills,
    normalize_skill,
    profile_total_years,
    skill_similarity,
)

FILLER_PHRASES = [
    "hardworking", "team player", "synergy", "go-getter", "detail-oriented",
    "thought leader", "rockstar", "ninja", "guru", "passionate about",
    "dynamic", "results-driven", "self-starter", "people person",
    "responsible for", "duties include", "assisted with",
]

DISCOURAGED_OPENERS = [
    "i am writing to apply", "i am excited to apply", "i am writing to express",
]


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

def corpus_text(profile: dict) -> str:
    """All known facts about the user, used for grounding checks."""
    chunks: list[str] = []
    for exp in profile.get("experience") or []:
        chunks.extend(
            [
                str(exp.get("organization", "")),
                str(exp.get("job_title", "")),
                " ".join(exp.get("responsibilities") or []),
                " ".join(exp.get("achievements") or []),
                " ".join(exp.get("technologies") or []),
            ]
        )
    for project in profile.get("projects") or []:
        chunks.extend(
            [
                str(project.get("name", "")),
                str(project.get("description", "")),
                " ".join(project.get("technologies") or []),
            ]
        )
    for skill in profile.get("skills") or []:
        chunks.append(str(skill.get("name", "")))
        # Category labels legitimately appear in the skills section.
        chunks.append(str(skill.get("category") or ""))
    for edu in profile.get("education") or []:
        chunks.extend(
            [str(edu.get("institution", "")), str(edu.get("qualification", ""))]
        )
    for cert in profile.get("certifications") or []:
        chunks.extend(
            [str(cert.get("name", "")), str(cert.get("issuing_organization", ""))]
        )
    return " ".join(chunks).lower()


def doc_text(document: dict) -> str:
    parts: list[str] = []
    for section in document.get("sections") or []:
        parts.append(section.get("heading", ""))
        for block in section.get("blocks") or []:
            parts.append(block.get("text") or "")
            parts.append(block.get("title") or "")
            parts.append(block.get("organization") or "")
            parts.extend(block.get("items") or [])
    return "\n".join(parts)


def doc_body_text(document: dict) -> str:
    """Body text only - section headings are excluded from the
    fabrication scan so structural labels are never flagged."""
    parts: list[str] = []
    for section in document.get("sections") or []:
        for block in section.get("blocks") or []:
            parts.append(block.get("text") or "")
            parts.append(block.get("title") or "")
            parts.append(block.get("organization") or "")
            parts.extend(block.get("items") or [])
    return "\n".join(parts)


# Words that legitimately appear in documents but are not
# profile facts.  Anything here is never treated as a
# fabricated claim.
CV_STOPWORDS = {
    "professional", "summary", "experience", "skills", "education",
    "certifications", "projects", "selected", "career", "cv",
    "resume", "cover", "letter", "application", "page", "present",
    "years", "year", "responsibilities", "achievements", "technologies",
    "key", "core", "about", "contact", "details", "overview",
    "profile", "history", "background", "qualifications", "license",
    "licenses", "membership", "publications", "awards", "volunteer",
    "volunteering", "research", "interests", "references", "languages",
    "framework", "frameworks", "library", "libraries", "platform",
    "tools", "tool", "methodologies", "methodology", "stack",
}


def _looks_like_claim(token: str) -> bool:
    """Heuristic: does a capitalized token look like a named
    entity or technology worth verifying?"""
    if not token or len(token) < 3:
        return False
    # Acronyms (AWS, SQL, CI)
    if re.fullmatch(r"[A-Z][A-Za-z0-9.+#-]*", token) and any(
        c.isupper() for c in token[1:]
    ):
        return True
    # camelCase technology names (FastAPI, ReactNative)
    if re.search(r"[a-z][A-Z]", token):
        return True
    # Contains a digit (C++, .NET, Vue3)
    if re.search(r"\d", token):
        return True
    # In the known technology lexicon
    if normalize_skill(token) in TECH_CLAIM_LEXICON:
        return True
    return False


# A broad lexicon of technology/product names used only to
# recognize claim-like tokens; membership is checked against
# the profile corpus before anything is flagged.
TECH_CLAIM_LEXICON = {
    "python", "java", "javascript", "typescript", "react", "vue",
    "angular", "svelte", "node", "django", "flask", "fastapi",
    "spring", "rails", "laravel", "kubernetes", "docker", "terraform",
    "aws", "azure", "gcp", "kafka", "redis", "postgresql", "postgres",
    "mysql", "mongodb", "elasticsearch", "tensorflow", "pytorch",
    "kubernetes", "graphql", "grpc", "rust", "golang", "swift",
    "kotlin", "scala", "php", "ruby", "linux", "git", "jenkins",
    "figma", "jira", "sql", "nosql", "hadoop", "spark", "airflow",
}


# ---------------------------------------------------------------------------
# Agent 1: Career Strategist
# ---------------------------------------------------------------------------

def local_strategy(profile: dict, listing: dict, match_report: dict) -> dict:
    requirements = extract_required_skills(listing)
    skills = profile.get("skills") or []
    experience = profile.get("experience") or []
    projects = profile.get("projects") or []

    def relevance(text: str) -> int:
        lowered = text.lower()
        return sum(1 for req in requirements if req.lower() in lowered)

    scored_exp = []
    for exp in experience:
        text = " ".join(
            [
                str(exp.get("organization", "")),
                str(exp.get("job_title", "")),
                " ".join(exp.get("responsibilities") or []),
                " ".join(exp.get("achievements") or []),
                " ".join(exp.get("technologies") or []),
            ]
        )
        scored_exp.append((relevance(text), exp))
    scored_exp.sort(key=lambda pair: -pair[0])
    selected_experience = [exp for _, exp in scored_exp[:3]]

    scored_projects = []
    for project in projects:
        text = " ".join(
            [
                str(project.get("name", "")),
                str(project.get("description", "")),
                str(project.get("problem_solved", "")),
                " ".join(project.get("technologies") or []),
            ]
        )
        scored_projects.append((relevance(text), project))
    scored_projects.sort(key=lambda pair: -pair[0])
    selected_projects = [proj for _, proj in scored_projects[:3]]

    matched_skills = [
        s.get("name")
        for s in skills
        if any(skill_similarity(s.get("name", ""), req) >= 0.8 for req in requirements)
    ]

    strong_matches = match_report.get("strong_matches") or []
    gaps = match_report.get("missing_requirements") or []
    partial = match_report.get("partial_matches") or []

    positioning = _positioning_line(profile, listing, matched_skills, strong_matches)
    key_messages = [
        positioning,
        _evidence_line(profile, selected_experience, matched_skills),
        _gap_line(gaps, partial),
    ]

    return {
        "positioning": positioning,
        "selected_experience": [
            {"id": e.get("id"), "organization": e.get("organization"), "job_title": e.get("job_title")}
            for e in selected_experience
        ],
        "selected_projects": [
            {"id": p.get("id"), "name": p.get("name")} for p in selected_projects
        ],
        "selected_skills": matched_skills[:10],
        "key_messages": [m for m in key_messages if m],
        "gaps": gaps,
        "gap_mitigations": [
            f"Present verified experience with {gap.split(':')[0].strip() or gap} where it genuinely exists; otherwise omit it."
            for gap in gaps[:3]
        ],
        "keyword_targets": [r for r in requirements[:8]],
        "evidence_refs": [],
    }


def _positioning_line(profile: dict, listing: dict, matched_skills: list, strong: list) -> str:
    title = listing.get("title", "this role")
    company = listing.get("company", "this company")
    skills_part = ", ".join(matched_skills[:4]) if matched_skills else "the core requirements"
    headline = profile.get("headline") or ""
    if headline:
        return f"Position {profile.get('preferred_name') or profile.get('full_name') or 'the candidate'} as {headline} for {title} at {company}, leading with {skills_part}."
    return f"Position the candidate for {title} at {company}, leading with verified strengths in {skills_part}."


def _evidence_line(profile: dict, selected_experience: list, matched_skills: list) -> str:
    if not selected_experience:
        return "No prior experience records were available to draw evidence from."
    orgs = ", ".join(
        str(e.get("organization", "")) for e in selected_experience[:2] if e.get("organization")
    )
    return f"Lead with evidence from: {orgs}."


def _gap_line(gaps: list, partial: list) -> str:
    if not gaps and not partial:
        return "No significant gaps were detected."
    if gaps:
        return f"Address honestly: the profile does not yet evidence {', '.join(gaps[:3])}."
    return f"Partial matches to strengthen: {', '.join(partial[:3])}."


# ---------------------------------------------------------------------------
# Agent 2: Document Drafter
# ---------------------------------------------------------------------------

def _format_date_range(start, end, is_current: bool) -> str:
    def fmt(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value[:7]
        return value.isoformat()[:7]

    start_s = fmt(start)
    if is_current or end is None:
        return f"{start_s} - Present" if start_s else "Present"
    return f"{start_s} - {fmt(end)}" if start_s else fmt(end)


def _summary_paragraph(profile: dict, strategy: dict, listing: dict) -> str:
    name = profile.get("preferred_name") or profile.get("full_name") or "The candidate"
    headline = profile.get("headline")
    years = profile_total_years(profile.get("experience") or [])
    skills = strategy.get("selected_skills") or []
    title = listing.get("title", "this role")

    parts = []
    if headline:
        parts.append(f"{name} is a {headline}.")
    elif years:
        parts.append(f"{name} is a professional with {years:.0f} years of experience.")
    else:
        parts.append(f"{name} is applying for the {title} role.")

    if years:
        parts.append(f"They bring {years:.0f} years of professional experience.")
    if skills:
        parts.append(f"Verified strengths include {', '.join(skills[:6])}.")
    parts.append(f"They are seeking the {title} position at {listing.get('company', 'the organization')}.")

    style = profile.get("writing_style") or {}
    if style.get("detail_level") == "concise":
        return parts[0] + (" " + parts[-1] if len(parts) > 1 else "")
    return " ".join(parts)


def local_draft_cv(profile: dict, strategy: dict, listing: dict, template_id: str) -> dict:
    """Draft a tailored CV as a structured document."""
    sections = []

    contact_blocks = []
    if profile.get("email"):
        contact_blocks.append({"type": "text", "text": profile["email"]})
    if profile.get("phone"):
        contact_blocks.append({"type": "text", "text": profile["phone"]})
    if profile.get("location_city"):
        loc = profile["location_city"]
        if profile.get("location_country"):
            loc += f", {profile['location_country']}"
        contact_blocks.append({"type": "text", "text": loc})
    if profile.get("linkedin_url"):
        contact_blocks.append({"type": "text", "text": profile["linkedin_url"]})
    if profile.get("github_url"):
        contact_blocks.append({"type": "text", "text": profile["github_url"]})
    if profile.get("website") or profile.get("portfolio_url"):
        contact_blocks.append(
            {"type": "text", "text": profile.get("website") or profile.get("portfolio_url")}
        )

    summary_text = _summary_paragraph(profile, strategy, listing)
    sections.append({
        "id": "summary",
        "heading": "Professional Summary",
        "blocks": [{"type": "paragraph", "text": summary_text}],
    })

    selected_ids = {e.get("id") for e in (strategy.get("selected_experience") or [])}
    experience_entries = []
    for exp in profile.get("experience") or []:
        bullets = []
        achievements = exp.get("achievements") or []
        responsibilities = exp.get("responsibilities") or []
        # Strategy-selected experience leads; achievements before duties.
        for achievement in achievements:
            bullets.append(achievement)
        for resp in responsibilities:
            if resp not in bullets:
                bullets.append(resp)
        techs = exp.get("technologies") or []
        entry = {
            "type": "entry",
            "title": exp.get("job_title"),
            "organization": exp.get("organization"),
            "date_range": _format_date_range(
                exp.get("start_date"), exp.get("end_date"), exp.get("is_current")
            ),
            "items": bullets[:8],
            "meta": ", ".join(techs) if techs else None,
            "highlighted": exp.get("id") in selected_ids,
        }
        experience_entries.append(entry)
    if experience_entries:
        sections.append({
            "id": "experience",
            "heading": "Professional Experience",
            "blocks": experience_entries,
        })

    selected_project_ids = {p.get("id") for p in (strategy.get("selected_projects") or [])}
    project_blocks = []
    for project in profile.get("projects") or []:
        items = list(project.get("responsibilities") or [])
        if project.get("outcomes"):
            items.append(str(project["outcomes"]))
        meta = ", ".join(project.get("technologies") or [])
        project_blocks.append({
            "type": "entry",
            "title": project.get("name"),
            "organization": meta or None,
            "date_range": None,
            "items": items[:5],
            "meta": (project.get("repository_url") or project.get("live_demo_url")),
            "highlighted": project.get("id") in selected_project_ids,
        })
    if project_blocks:
        sections.append({
            "id": "projects",
            "heading": "Selected Projects",
            "blocks": project_blocks,
        })

    skills = profile.get("skills") or []
    if skills:
        by_category: dict[str, list[str]] = {}
        for skill in skills:
            category = skill.get("category") or "General"
            by_category.setdefault(category, []).append(skill.get("name", ""))
        blocks = [
            {"type": "bullets", "items": [f"{cat}: {', '.join(names)}" for cat, names in by_category.items()]}
        ]
        sections.append({"id": "skills", "heading": "Skills", "blocks": blocks})

    education_blocks = []
    for edu in profile.get("education") or []:
        education_blocks.append({
            "type": "entry",
            "title": f"{edu.get('qualification') or 'Degree'} in {edu.get('field_of_study') or 'General'}".strip(" in "),
            "organization": edu.get("institution"),
            "date_range": _format_date_range(edu.get("start_date"), edu.get("end_date"), edu.get("is_current")),
            "items": [],
            "meta": None,
        })
    if education_blocks:
        sections.append({"id": "education", "heading": "Education", "blocks": education_blocks})

    cert_blocks = []
    for cert in profile.get("certifications") or []:
        issuer = cert.get("issuing_organization")
        name = cert.get("name", "")
        cert_blocks.append({
            "type": "bullets",
            "items": [f"{name}" + (f" - {issuer}" if issuer else "")],
        })
    if cert_blocks:
        sections.append({"id": "certifications", "heading": "Certifications", "blocks": cert_blocks})

    return {
        "title": f"{profile.get('full_name') or 'Candidate'} - CV",
        "subtitle": profile.get("headline"),
        "contact_line": "; ".join(
            filter(
                None,
                [
                    profile.get("email"),
                    profile.get("phone"),
                    profile.get("location_city"),
                    profile.get("linkedin_url"),
                    profile.get("github_url"),
                    profile.get("website") or profile.get("portfolio_url"),
                ],
            )
        ),
        "template_id": template_id,
        "sections": sections,
    }


def local_draft_cover_letter(profile: dict, strategy: dict, listing: dict, length: str) -> dict:
    name = profile.get("preferred_name") or profile.get("full_name") or "The applicant"
    title = listing.get("title", "the position")
    company = listing.get("company", "your organization")
    style = profile.get("writing_style") or {}
    first_person = style.get("uses_first_person", True)

    subject = "I am" if first_person else "The applicant is"
    opening = f"{subject} writing to express interest in the {title} position at {company}."
    if first_person and opening.startswith("I am writing"):
        opening = f"I am writing to express my interest in the {title} position at {company}."

    matched = strategy.get("selected_skills") or []
    experiences = strategy.get("selected_experience") or []
    projects = strategy.get("selected_projects") or []
    gaps = strategy.get("gaps") or []

    evidence_bits = []
    if experiences:
        orgs = " and ".join(
            str(e.get("organization")) for e in experiences[:2] if e.get("organization")
        )
        evidence_bits.append(f"My experience at {orgs} directly supports the requirements of this role.")
    if matched:
        evidence_bits.append(
            f"I have demonstrated proficiency in {', '.join(matched[:5])}, "
            "which align with the core requirements of the position."
        )
    if projects:
        names = " and ".join(
            str(p.get("name")) for p in projects[:2] if p.get("name")
        )
        evidence_bits.append(f"Selected projects such as {names} evidence the applied skills described above.")

    gap_sentence = ""
    if gaps:
        gap_sentence = (
            "I am transparent about areas still developing: "
            + ", ".join(gaps[:2])
            + ". I would welcome the opportunity to discuss how my verified background can nevertheless contribute."
        )

    closing = "I would welcome the opportunity to discuss how my background can contribute to your team. Thank you for your consideration."

    paragraphs = [opening]
    paragraphs.extend(evidence_bits[:2] if length == "concise" else evidence_bits)
    if length in ("standard", "detailed") and gap_sentence:
        paragraphs.append(gap_sentence)
    if length == "detailed":
        paragraphs.append(
            "I have structured this letter around verified accomplishments from my career profile; "
            "every claim can be traced to confirmed experience, projects, or skills."
        )
    paragraphs.append(closing)

    body = "\n\n".join(paragraphs)
    # Apply disliked-phrase preferences.
    for phrase in style.get("disliked_phrases") or []:
        body = re.sub(re.escape(phrase), "", body, flags=re.I)

    return {
        "title": f"Cover Letter - {title}",
        "subtitle": f"Application for {title} at {company}",
        "contact_line": profile.get("email") or None,
        "template_id": "cover_letter_standard",
        "sections": [
            {
                "id": "greeting",
                "heading": "",
                "blocks": [
                    {"type": "paragraph", "text": f"Dear Hiring Manager,"},
                ],
            },
            {
                "id": "body",
                "heading": "",
                "blocks": [
                    {"type": "paragraph", "text": body},
                ],
            },
            {
                "id": "signoff",
                "heading": "",
                "blocks": [
                    {"type": "paragraph", "text": "Sincerely,"},
                    {"type": "paragraph", "text": profile.get("full_name") or ""},
                ],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Agent 3: Independent Reviewer
# ---------------------------------------------------------------------------

def local_review(document: dict, listing: dict, profile: dict, match_report: dict) -> dict:
    findings = []
    text = doc_text(document)
    body_text = doc_body_text(document)
    lowered = text.lower()
    # The document may legitimately reference the target
    # employer and job title, so those are allowed.
    listing_context = f"{listing.get('company', '')} {listing.get('title', '')}".lower()
    known = corpus_text(profile) + " " + listing_context
    requirements = extract_required_skills(listing)
    word_count = len(re.findall(r"\w+", text))

    # 1. Fabrication guard: named/technical claims not present
    #    in the verified profile (and not from the job itself).
    #    Only body text is scanned; headings are structural.
    claimed_techs = []
    for tech in _TECH_CLAIM_RE.findall(body_text):
        normalized = normalize_skill(tech)
        if len(normalized) < 3:
            continue
        if normalized in CV_STOPWORDS:
            continue
        # Skip category labels like "Languages:" or "DevOps:".
        if re.search(re.escape(tech) + r"\s*:", body_text):
            continue
        if not _looks_like_claim(tech):
            continue
        if normalized not in known and not any(
            skill_similarity(normalized, k) >= 0.8 for k in known.split()
        ):
            claimed_techs.append(tech)
    for tech in sorted(set(claimed_techs))[:6]:
        findings.append({
            "id": f"fab-{tech}",
            "severity": "critical",
            "category": "factual_accuracy",
            "location": "document body",
            "message": f"'{tech}' appears in the document but is not in the verified career profile.",
            "evidence": "No matching skill, technology, or experience record exists.",
            "recommendation": "Remove the claim or add the skill to your verified profile first.",
            "requires_user_confirmation": True,
            "resolved": False,
        })

    # 2. Missing must-have keywords.
    present_keywords = {normalize_skill(k) for k in requirements if k.lower() in lowered}
    missing_keywords = [k for k in requirements[:8] if normalize_skill(k) not in present_keywords]
    if missing_keywords:
        findings.append({
            "id": "missing-keywords",
            "severity": "major",
            "category": "keyword_relevance",
            "location": "summary / skills",
            "message": f"Required keywords not present: {', '.join(missing_keywords[:5])}.",
            "evidence": "Keyword comparison against the job description.",
            "recommendation": "Add these terms only where the underlying skill is genuinely verified.",
            "requires_user_confirmation": False,
            "resolved": False,
        })

    # 3. Length checks.
    kind = document.get("kind", "cv")
    if kind == "cv" and word_count > 800:
        findings.append({
            "id": "cv-too-long",
            "severity": "minor",
            "category": "conciseness",
            "location": "whole document",
            "message": f"CV is approximately {word_count} words; consider trimming to ~600.",
            "evidence": f"Word count: {word_count}.",
            "recommendation": "Remove duties that duplicate other roles or are unrelated.",
            "requires_user_confirmation": False,
            "resolved": False,
        })
    if kind == "cover_letter":
        if word_count > 450:
            findings.append({
                "id": "cl-too-long",
                "severity": "minor",
                "category": "conciseness",
                "location": "whole document",
                "message": f"Cover letter is approximately {word_count} words; concise letters perform better.",
                "evidence": f"Word count: {word_count}.",
                "recommendation": "Cut the least relevant paragraph.",
                "requires_user_confirmation": False,
                "resolved": False,
            })
        elif word_count < 80:
            findings.append({
                "id": "cl-too-short",
                "severity": "minor",
                "category": "completeness",
                "location": "whole document",
                "message": f"Cover letter is only {word_count} words.",
                "evidence": f"Word count: {word_count}.",
                "recommendation": "Add one concrete, verified example of relevant work.",
                "requires_user_confirmation": False,
                "resolved": False,
            })

    # 4. Repetition.
    bullets: list[str] = []
    for section in document.get("sections") or []:
        for block in section.get("blocks") or []:
            bullets.extend(block.get("items") or [])
    seen: dict[str, int] = {}
    for bullet in bullets:
        key = re.sub(r"\W+", "", bullet.lower())
        seen[key] = seen.get(key, 0) + 1
    duplicates = [b for b in bullets if seen[re.sub(r"\W+", "", b.lower())] > 1]
    if duplicates:
        findings.append({
            "id": "repetition",
            "severity": "minor",
            "category": "repetition",
            "location": "bullet lists",
            "message": f"{len(duplicates)} bullet(s) are repeated verbatim.",
            "evidence": f"Example: '{duplicates[0][:80]}'",
            "recommendation": "Remove or rephrase duplicates.",
            "requires_user_confirmation": False,
            "resolved": False,
        })

    # 5. Filler phrases.
    found_filler = [p for p in FILLER_PHRASES if p in lowered]
    if found_filler:
        findings.append({
            "id": "filler",
            "severity": "minor",
            "category": "professional_tone",
            "location": "summary / bullets",
            "message": f"Generic filler detected: {', '.join(found_filler[:4])}.",
            "evidence": "Phrase list comparison.",
            "recommendation": "Replace with concrete, verified accomplishments.",
            "requires_user_confirmation": False,
            "resolved": False,
        })

    # 6. Grammar / typography.
    if "  " in text:
        findings.append({
            "id": "double-space",
            "severity": "minor",
            "category": "grammar",
            "location": "document body",
            "message": "Double spaces detected.",
            "evidence": "Whitespace scan.",
            "recommendation": "Collapse double spaces.",
            "requires_user_confirmation": False,
            "resolved": False,
        })
    repeated_word = re.search(r"\b(\w+)\s+\1\b", lowered)
    if repeated_word:
        findings.append({
            "id": "repeated-word",
            "severity": "minor",
            "category": "grammar",
            "location": "document body",
            "message": f"Repeated word: '{repeated_word.group(0)}'.",
            "evidence": "Token scan.",
            "recommendation": "Remove the duplicated word.",
            "requires_user_confirmation": False,
            "resolved": False,
        })

    # 7. Exclamation marks in a CV are unprofessional.
    if kind == "cv" and "!" in text:
        findings.append({
            "id": "exclamation",
            "severity": "suggestion",
            "category": "professional_tone",
            "location": "document body",
            "message": "Exclamation marks are unusual in a CV.",
            "evidence": "Punctuation scan.",
            "recommendation": "Use a neutral, declarative tone.",
            "requires_user_confirmation": False,
            "resolved": False,
        })

    # 8. Overconfident claims about weak skills.
    for skill in profile.get("skills") or []:
        if (skill.get("proficiency") or "").lower() in ("beginner", "basic"):
            if skill.get("name", "").lower() in lowered:
                for pattern in ("expert in", "mastery of", "deep expertise in"):
                    idx = lowered.find(pattern)
                    if idx != -1 and skill["name"].lower() in lowered[idx : idx + 80]:
                        findings.append({
                            "id": f"overclaim-{skill['id']}",
                            "severity": "major",
                            "category": "misleading_wording",
                            "location": "skills context",
                            "message": f"'{pattern}' is claimed for '{skill['name']}', which the profile marks as {skill.get('proficiency')}.",
                            "evidence": "Profile proficiency record.",
                            "recommendation": "State the accurate proficiency level.",
                            "requires_user_confirmation": True,
                            "resolved": False,
                        })
                        break

    # 9. ATS heuristics.
    template_id = document.get("template_id", "")
    if template_id == "ats_friendly":
        headings = [s.get("heading", "") for s in document.get("sections") or []]
        if headings and any(len(h) > 40 for h in headings):
            findings.append({
                "id": "ats-heading-length",
                "severity": "suggestion",
                "category": "ats_readability",
                "location": "section headings",
                "message": "Some ATS-friendly template headings are long; shorter headings parse more reliably.",
                "evidence": "Heading length scan.",
                "recommendation": "Use conventional headings like 'Experience', 'Education'.",
                "requires_user_confirmation": False,
                "resolved": False,
            })

    # 10. Missing contact information in CV.
    if kind == "cv":
        contact_line = document.get("contact_line") or ""
        if not contact_line and "@" not in text:
            findings.append({
                "id": "missing-contact",
                "severity": "major",
                "category": "completeness",
                "location": "header",
                "message": "No contact information is present.",
                "evidence": "Header scan found no email.",
                "recommendation": "Add an email address (and optionally phone/location).",
                "requires_user_confirmation": False,
                "resolved": False,
            })

    # 11. Disliked phrases from the writing-style profile.
    for phrase in (profile.get("writing_style") or {}).get("disliked_phrases") or []:
        if phrase.lower() in lowered:
            findings.append({
                "id": f"disliked-{phrase[:20]}",
                "severity": "suggestion",
                "category": "writing_style",
                "location": "document body",
                "message": f"The phrase '{phrase}' is on your disliked-phrases list.",
                "evidence": "Writing-style profile.",
                "recommendation": "Rephrase to match your preferred style.",
                "requires_user_confirmation": False,
                "resolved": False,
            })

    critical = sum(1 for f in findings if f["severity"] == "critical")
    major = sum(1 for f in findings if f["severity"] == "major")
    minor = sum(1 for f in findings if f["severity"] == "minor")
    suggestion = sum(1 for f in findings if f["severity"] == "suggestion")

    if critical == 0 and major == 0:
        readiness = "ready"
        assessment = "The draft passed all automated checks. Review it once more before approving."
    elif critical > 0:
        readiness = "not_ready"
        assessment = "Critical factual issues must be resolved before this document can be approved."
    else:
        readiness = "needs_confirmation"
        assessment = "No critical issues, but some findings need your confirmation."

    return {
        "findings": findings,
        "critical_count": critical,
        "major_count": major,
        "minor_count": minor,
        "suggestion_count": suggestion,
        "overall_assessment": assessment,
        "readiness": readiness,
    }


_TECH_CLAIM_RE = re.compile(r"\b([A-Z][A-Za-z0-9.+#-]{1,20}(?:\s(?:[A-Z][A-Za-z0-9.+#-]{1,12})){0,2})\b")


# ---------------------------------------------------------------------------
# Agent 4: Revision
# ---------------------------------------------------------------------------

def local_revise(document: dict, findings: list[dict], profile: dict, listing: dict) -> dict:
    """Apply deterministic, evidence-safe fixes.

    Findings that would require inventing facts are escalated to the
    user instead of being 'fixed' silently.
    """
    import copy

    revised = copy.deepcopy(document)
    changes = []
    addressed = []
    unresolved = []
    requires_confirmation = False

    for finding in findings:
        fid = finding.get("id", "")
        category = finding.get("category", "")

        if fid == "double-space":
            _walk_blocks(revised, lambda s: re.sub(r" {2,}", " ", s))
            changes.append({"finding": fid, "action": "Collapsed double spaces."})
            addressed.append(fid)
        elif fid == "repeated-word":
            def _dedupe(text: str) -> str:
                return re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.I)
            _walk_blocks(revised, _dedupe)
            changes.append({"finding": fid, "action": "Removed duplicated word."})
            addressed.append(fid)
        elif fid == "exclamation":
            _walk_blocks(revised, lambda s: s.replace("!", ""))
            changes.append({"finding": fid, "action": "Removed exclamation marks."})
            addressed.append(fid)
        elif fid == "repetition":
            seen = set()
            for section in revised.get("sections") or []:
                for block in section.get("blocks") or []:
                    items = block.get("items") or []
                    deduped = []
                    for item in items:
                        key = re.sub(r"\W+", "", item.lower())
                        if key in seen:
                            continue
                        seen.add(key)
                        deduped.append(item)
                    if len(deduped) != len(items):
                        block["items"] = deduped
            changes.append({"finding": fid, "action": "Removed duplicate bullets."})
            addressed.append(fid)
        elif fid == "filler":
            for phrase in FILLER_PHRASES:
                filler_phrase = phrase
                _walk_blocks(
                    revised,
                    lambda s, fp=filler_phrase: re.sub(r"\b" + re.escape(fp) + r"\b,?\s*", "", s, flags=re.I),
                )
            changes.append({"finding": fid, "action": "Removed generic filler phrases."})
            addressed.append(fid)
        elif fid == "missing-keywords":
            # Add genuinely verified keywords only.
            strategy_skills = set()
            text_before = doc_text(revised).lower()
            # We only add keywords that exist in the profile corpus.
            known = corpus_text(profile)
            requirements = extract_required_skills(listing)
            addable = [
                k for k in requirements[:8]
                if k.lower() not in text_before
                and k.lower() in known
            ]
            if addable:
                for section in revised.get("sections") or []:
                    if section.get("id") == "skills":
                        for block in section.get("blocks") or []:
                            block.setdefault("items", []).extend(addable[:3])
                        changes.append({
                            "finding": fid,
                            "action": f"Added verified keywords to skills: {', '.join(addable[:3])}.",
                        })
                        addressed.append(fid)
                        break
                else:
                    for section in revised.get("sections") or []:
                        if section.get("id") == "summary":
                            para = section["blocks"][0]
                            para["text"] = para.get("text", "") + f" Verified skills include {', '.join(addable[:3])}."
                            changes.append({
                                "finding": fid,
                                "action": f"Mentioned verified keywords in the summary: {', '.join(addable[:3])}.",
                            })
                            addressed.append(fid)
                            break
            else:
                unresolved.append({**finding, "resolution": "None of the missing keywords are verified in the profile; add them only if true."})
        elif fid.startswith("fab-"):
            requires_confirmation = True
            unresolved.append({**finding, "resolution": "Automated revision cannot verify this claim. Confirm or remove it manually."})
        elif fid.startswith("overclaim-"):
            requires_confirmation = True
            unresolved.append({**finding, "resolution": "Proficiency wording needs your confirmation."})
        else:
            # Length, tone, ATS suggestions: keep for user decision.
            unresolved.append(finding)

    status = "ready_for_approval" if not unresolved else "needs_user_confirmation"
    return {
        "content": revised,
        "changes": changes,
        "findings_addressed": addressed,
        "findings_unresolved": unresolved,
        "status": status,
        "requires_user_confirmation": requires_confirmation,
    }


def _walk_blocks(document: dict, transform) -> None:
    for section in document.get("sections") or []:
        for block in section.get("blocks") or []:
            for key in ("text", "title", "organization", "meta"):
                value = block.get(key)
                if isinstance(value, str):
                    block[key] = transform(value)
            if block.get("items"):
                block["items"] = [transform(item) for item in block["items"]]
