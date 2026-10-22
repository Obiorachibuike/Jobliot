"""CV import and extraction tests."""

from __future__ import annotations

import io

from app.services.profile_service import (
    extract_cv_structured,
    extract_text_from_docx,
    extract_cv_text,
)


def _make_docx(lines):
    from docx import Document

    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def test_extract_text_from_docx():
    content = _make_docx([
        "Ada Okafor",
        "ada@example.com",
        "Professional Summary",
        "Backend engineer with 5 years of experience.",
        "Skills",
        "Python, FastAPI, Docker",
    ])
    text = extract_text_from_docx(content)
    assert "Ada Okafor" in text
    assert "Python, FastAPI, Docker" in text


def test_extract_cv_text_unsupported_format():
    import pytest

    with pytest.raises(ValueError):
        extract_cv_text("resume.exe", b"binary")


def test_extract_cv_structured_detects_name_and_contact():
    text = (
        "Ada Okafor\n"
        "ada.okafor@example.com\n"
        "+234 801 234 5678\n\n"
        "Professional Summary\n"
        "Backend engineer with 5 years building APIs.\n\n"
        "Skills\n"
        "Python, FastAPI, Docker, Kubernetes\n"
    )
    extracted, uncertain = extract_cv_structured(text)
    assert extracted["full_name"] == "Ada Okafor"
    assert extracted["email"] == "ada.okafor@example.com"
    assert "Python" in extracted["skills"]
    # Name and skills are uncertain until confirmed.
    assert "full_name" in uncertain
    assert any("skills" in u for u in uncertain)


def test_extract_cv_structured_marks_sections_uncertain():
    text = (
        "Jane Doe\n\n"
        "Experience\n"
        "Senior Engineer at Acme\n\n"
        "Education\n"
        "BSc Computer Science\n"
    )
    extracted, uncertain = extract_cv_structured(text)
    assert "experience_raw" in extracted
    assert any("experience" in u for u in uncertain)


def test_cv_import_endpoint_rejects_unsupported(client, auth_headers):
    response = client.post(
        "/api/v1/cv-import",
        headers=auth_headers,
        files={"file": ("resume.exe", b"data", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_cv_import_endpoint_processes_docx(client, auth_headers):
    content = _make_docx([
        "Ada Okafor",
        "ada@example.com",
        "Skills",
        "Python, FastAPI",
    ])
    response = client.post(
        "/api/v1/cv-import",
        headers=auth_headers,
        files={"file": ("cv.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["extracted"]["full_name"] == "Ada Okafor"
    assert "Python" in body["extracted"]["skills"]
    assert body["uncertain_fields"], "imported fields must be flagged uncertain"
