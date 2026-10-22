"""Document generation, versioning, and export tests."""

from __future__ import annotations

import base64

from app.services.documents.renderers import (
    render_docx,
    render_pdf,
    render_text,
    validate_docx,
    validate_pdf,
)
from app.services.documents.templates import get_template, list_templates


SAMPLE_DOC = {
    "title": "Ada Okafor - CV",
    "subtitle": "Backend Engineer",
    "contact_line": "ada@example.com",
    "template_id": "ats_friendly",
    "sections": [
        {
            "id": "summary",
            "heading": "Professional Summary",
            "blocks": [
                {"type": "paragraph", "text": "Experienced backend engineer."}
            ],
        },
        {
            "id": "experience",
            "heading": "Experience",
            "blocks": [
                {
                    "type": "entry",
                    "title": "Engineer",
                    "organization": "Acme",
                    "date_range": "2021 - Present",
                    "items": ["Built APIs", "Wrote tests"],
                }
            ],
        },
    ],
}


def test_template_registry_has_eight_templates():
    templates = list_templates()
    assert len(templates) >= 8
    ids = {t["id"] for t in templates}
    assert "ats_friendly" in ids
    assert "modern_developer" in ids
    assert "academic" in ids


def test_ats_template_is_conservative():
    template = get_template("ats_friendly")
    assert template["ats_safe"] is True
    assert template["layout"] == "classic"


def test_render_text_contains_sections():
    text = render_text(SAMPLE_DOC)
    assert "PROFESSIONAL SUMMARY" in text
    assert "Acme" in text


def test_render_docx_valid():
    data = render_docx(SAMPLE_DOC)
    assert data[:2] == b"PK"  # zip signature
    validation = validate_docx(data)
    assert validation["valid"] is True


def test_render_pdf_valid():
    data = render_pdf(SAMPLE_DOC)
    assert data.startswith(b"%PDF")
    validation = validate_pdf(data)
    assert validation["valid"] is True


def test_pdf_validation_rejects_garbage():
    assert validate_pdf(b"not a pdf")["valid"] is False


def test_docx_validation_rejects_garbage():
    assert validate_docx(b"not a docx")["valid"] is False


def test_export_endpoint_pdf(client, auth_headers):
    # Create a document directly through the studio flow is heavy;
    # instead create one via the document endpoint after generating.
    # Here we test the export validation path with a seeded document.
    from app.models.documents import Document, DocumentStatus
    from app.core.database import get_session_factory

    session = get_session_factory()()
    document = Document(
        profile_id=1,
        kind="cv",
        title="Export Test CV",
        template_id="ats_friendly",
        status=DocumentStatus.DRAFT.value,
        content=SAMPLE_DOC,
    )
    session.add(document)
    session.commit()
    document_id = document.id
    session.close()

    response = client.post(
        f"/api/v1/documents/{document_id}/export",
        headers=auth_headers,
        json={"format": "pdf"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mime_type"] == "application/pdf"
    raw = base64.b64decode(body["content_b64"])
    assert raw.startswith(b"%PDF")


def test_export_endpoint_docx(client, auth_headers):
    from app.models.documents import Document, DocumentStatus
    from app.core.database import get_session_factory

    session = get_session_factory()()
    document = Document(
        profile_id=1,
        kind="cv",
        title="Export Test DOCX",
        template_id="modern_developer",
        status=DocumentStatus.DRAFT.value,
        content=SAMPLE_DOC,
    )
    session.add(document)
    session.commit()
    document_id = document.id
    session.close()

    response = client.post(
        f"/api/v1/documents/{document_id}/export",
        headers=auth_headers,
        json={"format": "docx"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mime_type"].startswith("application/vnd.openxmlformats")
    raw = base64.b64decode(body["content_b64"])
    assert raw[:2] == b"PK"


def test_export_endpoint_txt(client, auth_headers):
    from app.models.documents import Document, DocumentStatus
    from app.core.database import get_session_factory

    session = get_session_factory()()
    document = Document(
        profile_id=1,
        kind="cover_letter",
        title="Export Test Letter",
        template_id="cover_letter_standard",
        status=DocumentStatus.DRAFT.value,
        content=SAMPLE_DOC,
    )
    session.add(document)
    session.commit()
    document_id = document.id
    session.close()

    response = client.post(
        f"/api/v1/documents/{document_id}/export",
        headers=auth_headers,
        json={"format": "txt"},
    )
    assert response.status_code == 200
    raw = base64.b64decode(response.json()["content_b64"])
    assert b"PROFESSIONAL SUMMARY" in raw


def test_document_versioning_on_manual_edit(client, auth_headers):
    from app.models.documents import Document, DocumentStatus
    from app.core.database import get_session_factory

    session = get_session_factory()()
    document = Document(
        profile_id=1,
        kind="cv",
        title="Versioned CV",
        content=SAMPLE_DOC,
    )
    session.add(document)
    session.commit()
    document_id = document.id
    session.close()

    updated = dict(SAMPLE_DOC)
    updated["title"] = "Versioned CV v2"
    response = client.patch(
        f"/api/v1/documents/{document_id}",
        headers=auth_headers,
        json={"content": updated},
    )
    assert response.status_code == 200
    assert response.json()["current_version"] == 2

    versions = client.get(
        f"/api/v1/documents/{document_id}/versions", headers=auth_headers
    ).json()
    assert len(versions) >= 1
