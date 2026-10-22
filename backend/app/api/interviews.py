"""Interview coach API."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.models.applications import InterviewAnswer, InterviewQuestion, InterviewSession
from app.models.jobs import JobListing
from app.models.profile import UserProfile
from app.schemas.applications import (
    InterviewAnswerIn,
    InterviewAnswerOut,
    InterviewEvaluation,
    InterviewQuestionOut,
    InterviewSessionCreate,
    InterviewSessionOut,
)
from app.services.tasks.manager import task_manager

router = APIRouter(prefix="/api/v1/interviews", dependencies=[TokenDep])


@router.get("/sessions", response_model=list[InterviewSessionOut])
def list_sessions(session: SessionDep):
    return session.query(InterviewSession).order_by(InterviewSession.id.desc()).limit(100).all()


@router.post("/sessions", response_model=InterviewSessionOut)
def create_session(payload: InterviewSessionCreate, session: SessionDep):
    title = payload.title
    if not title:
        listing = session.get(JobListing, payload.job_listing_id) if payload.job_listing_id else None
        title = f"Interview prep: {listing.job_title if listing else 'General'}"
    profile = session.query(UserProfile).first()
    from app.services.profile_service import get_or_create_profile

    profile = get_or_create_profile(session)
    session_record = InterviewSession(
        profile_id=profile.id,
        application_id=payload.application_id,
        job_listing_id=payload.job_listing_id,
        title=title,
        started_at=_utcnow(),
    )
    session.add(session_record)
    session.flush()

    listing = session.get(JobListing, payload.job_listing_id) if payload.job_listing_id else None
    questions = generate_questions(listing, profile)
    for index, (category, question, follow_ups) in enumerate(questions):
        session.add(
            InterviewQuestion(
                session_id=session_record.id,
                category=category,
                question=question,
                order_index=index,
                follow_ups=follow_ups,
            )
        )
    session.commit()
    session.refresh(session_record)
    return session_record


@router.get("/sessions/{session_id}", response_model=InterviewSessionOut)
def get_session(session_id: int, session: SessionDep):
    record = session.get(InterviewSession, session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return record


@router.post("/sessions/{session_id}/answer/{question_id}")
def answer_question(
    session_id: int,
    question_id: int,
    payload: InterviewAnswerIn,
    session: SessionDep,
):
    question = session.get(InterviewQuestion, question_id)
    if question is None or question.session_id != session_id:
        raise HTTPException(status_code=404, detail="Question not found")

    evaluation = evaluate_answer(question.question, payload.answer_text)
    answer = InterviewAnswer(
        question_id=question_id,
        answer_text=payload.answer_text,
        duration_seconds=payload.duration_seconds,
        scores=evaluation.scores,
        feedback=evaluation.feedback,
        suggested_improvements=evaluation.suggested_improvements,
        evidence_used=evaluation.evidence_used,
    )
    session.add(answer)
    session.commit()

    record = session.get(InterviewSession, session_id)
    answered = (
        session.query(InterviewAnswer)
        .join(InterviewQuestion)
        .filter(InterviewQuestion.session_id == session_id)
        .count()
    )
    total = (
        session.query(InterviewQuestion)
        .filter(InterviewQuestion.session_id == session_id)
        .count()
    )
    if total and answered >= total and record.completed_at is None:
        record.completed_at = _utcnow()
        # Overall score: average of dimension scores.
        all_answers = (
            session.query(InterviewAnswer)
            .join(InterviewQuestion)
            .filter(InterviewQuestion.session_id == session_id)
            .all()
        )
        scores = [
            a.scores.get("overall", 0) for a in all_answers if isinstance(a.scores, dict)
        ]
        record.overall_score = round(sum(scores) / len(scores), 1) if scores else None
        record.summary = _session_summary(record, all_answers)
    session.commit()
    return answer


@router.post("/sessions/{session_id}/notes")
def save_session_notes(session_id: int, notes: str, session: SessionDep):
    record = session.get(InterviewSession, session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found")
    record.feedback = {"notes": notes}
    session.commit()
    return {"ok": True}


def _utcnow():
    from datetime import datetime

    return datetime.utcnow()


# --------------------------------------------------------------------------- generation
QUESTION_BANK = {
    "technical": [
        "Walk me through how you would approach designing a {system}.",
        "How do you ensure code quality in a {tech} codebase?",
        "What trade-offs did you consider when choosing {tech} for a project?",
        "How would you debug a performance issue in a {system}?",
    ],
    "behavioral": [
        "Tell me about a time you disagreed with a teammate. How did you resolve it?",
        "Describe a situation where you had to deliver under a tight deadline.",
        "Tell me about a mistake you made at work and how you handled it.",
        "Describe a time you took ownership of a difficult problem.",
    ],
    "experience": [
        "Tell me about your experience with {tech}.",
        "What was your role in the {project} project?",
        "What did you learn from your time at {organization}?",
    ],
    "project": [
        "Walk me through the {project} project: the problem, your approach, and the outcome.",
        "What was the hardest technical decision in {project}?",
    ],
    "problem_solving": [
        "How do you approach a problem you have never seen before?",
        "Describe a time you had to make a decision with incomplete information.",
    ],
    "system_design": [
        "How would you design a {system} that needs to scale?",
        "What are the key trade-offs in designing a {system}?",
    ],
    "scenario": [
        "How would you handle a production incident affecting users right now?",
        "A stakeholder wants a feature that conflicts with technical constraints. What do you do?",
    ],
    "questions_for_employer": [
        "What does success look like for this role in the first 90 days?",
        "How does the team approach code review and knowledge sharing?",
        "What are the biggest technical challenges the team faces right now?",
    ],
}


def generate_questions(listing: JobListing | None, profile: UserProfile | None) -> list[tuple[str, str, list[str]]]:
    """Generate job-specific questions from the listing and profile."""
    title = (listing.title if listing else "") or ""
    company = (listing.company if listing else "") or ""
    requirements = listing.requirements if listing else []
    description = (listing.description if listing else "") or ""

    techs = [str(r) for r in (requirements or [])[:3]]
    projects = [p.name for p in (profile.projects if profile else [])][:2]
    organizations = [e.organization for e in (profile.experience if profile else [])][:2]

    questions: list[tuple[str, str, list[str]]] = []

    def render(template: str) -> str:
        result = template
        result = result.replace("{system}", techs[0] if techs else "distributed system")
        result = result.replace("{tech}", techs[0] if techs else "your primary technology")
        result = result.replace("{project}", projects[0] if projects else "a significant project")
        result = result.replace("{organization}", organizations[0] if organizations else "a previous employer")
        result = result.replace("{title}", title or "this role")
        result = result.replace("{company}", company or "the company")
        return result

    plan = [
        ("technical", 0),
        ("experience", 0),
        ("behavioral", 0),
        ("project", 0),
        ("technical", 1),
        ("problem_solving", 0),
        ("experience", 1),
        ("system_design", 0),
        ("scenario", 0),
        ("questions_for_employer", 0),
    ]
    if not any(techs):
        plan = [p for p in plan if p[0] != "technical"] or plan

    used: set[tuple[str, int]] = set()
    for category, index in plan:
        bank = QUESTION_BANK[category]
        idx = index % len(bank)
        if (category, idx) in used:
            continue
        used.add((category, idx))
        question = render(bank[idx])
        follow_ups = [render(t) for t in bank[:2] if render(t) != question][:2]
        questions.append((category, question, follow_ups))

    return questions[:10]


def evaluate_answer(question: str, answer: str) -> InterviewEvaluation:
    """Heuristic, transparent answer evaluation.

    Scores relevance, structure (STAR markers), evidence, and
    conciseness.  Never invents autobiographical content.
    """
    words = answer.split()
    word_count = len(words)
    lowered = answer.lower()

    # Relevance: overlap with question keywords.
    question_keywords = {w for w in re.findall(r"[a-z]{4,}", question.lower())}
    answer_keywords = {w for w in re.findall(r"[a-z]{4,}", lowered)}
    overlap = len(question_keywords & answer_keywords)
    relevance = min(100, round(overlap / max(len(question_keywords), 1) * 220))

    # Structure: STAR markers.
    star_markers = sum(
        1 for marker in ("situation", "task", "action", "result") if marker in lowered
    )
    structure = min(100, star_markers * 25 + (20 if word_count > 40 else 0))

    # Evidence: numbers, concrete technologies, named outcomes.
    evidence_score = 0
    if re.search(r"\d+", answer):
        evidence_score += 25
    if any(word in lowered for word in ("because", "so that", "which led")):
        evidence_score += 20
    if word_count >= 60:
        evidence_score += 15
    evidence = min(100, evidence_score)

    # Conciseness: ideal 60-220 words for spoken answers.
    if word_count == 0:
        conciseness = 0
    elif word_count < 25:
        conciseness = 45
    elif word_count <= 220:
        conciseness = 100
    else:
        conciseness = max(40, 100 - (word_count - 220) // 10)

    clarity = min(100, 60 + (20 if word_count >= 40 else 0) - (10 if answer.count(",") > 8 else 0))

    overall = round(
        relevance * 0.3 + structure * 0.2 + evidence * 0.25 + conciseness * 0.15 + clarity * 0.1,
        1,
    )

    improvements = []
    if relevance < 50:
        improvements.append("Reference the specific skills or context from the question.")
    if structure < 50:
        improvements.append("Structure your answer with the situation, action, and result.")
    if evidence < 50:
        improvements.append("Add a concrete outcome, number, or named technology from your experience.")
    if conciseness < 60:
        improvements.append("Keep answers to roughly 30-180 spoken words.")
    if not improvements:
        improvements.append("Strong answer - practice delivering it aloud with natural pacing.")

    feedback = (
        f"Overall {overall}/100. "
        f"Relevance {relevance}, structure {structure}, evidence {evidence}, "
        f"conciseness {conciseness}, clarity {clarity}."
    )

    return InterviewEvaluation(
        scores={
            "relevance": relevance,
            "structure": structure,
            "evidence": evidence,
            "conciseness": conciseness,
            "clarity": clarity,
            "overall": overall,
        },
        feedback=feedback,
        suggested_improvements=improvements,
        evidence_used=["Question keyword overlap", "STAR marker detection", "Length analysis"],
    )


def _session_summary(record: InterviewSession, answers: list) -> str:
    if not answers:
        return "No answers recorded yet."
    scores = [a.scores.get("overall", 0) for a in answers if isinstance(a.scores, dict)]
    average = sum(scores) / len(scores) if scores else 0
    if average >= 75:
        verdict = "Strong performance overall."
    elif average >= 55:
        verdict = "Solid foundations with room to sharpen structure and evidence."
    else:
        verdict = "Focus on structuring answers with concrete evidence."
    return f"{verdict} Average dimension score: {average:.0f}/100 across {len(answers)} answers."
