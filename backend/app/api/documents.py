"""Documents API: master CV, tailored documents, versions, exports."""

from __future__ import annotations

import base64
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.core.config import get_settings
from app.models.documents import Document, DocumentStatus, DocumentVersion, MasterCV, CVVersion
from app.models.jobs import JobListing
from app.schemas.documents import (
    CVVersionOut,
    DocumentCreate,
    DocumentOut,
    DocumentTemplateOut,
    DocumentUpdate,
    DocumentVersionOut,
    ExportRequest,
    ExportResult,
    MasterCVOut,
    ReviewRoundsConfig,
)
from app.services.documents.renderers import render_docx, render_pdf, render_text, render_latex, validate_docx, validate_pdf
from app.services.documents.templates import list_templates
from app.services.profile_service import get_or_create_profile

router = APIRouter(prefix="/api/v1/documents", dependencies=[TokenDep])


def _document_out(document: Document) -> dict:
    return {
        "id": document.id,
        "profile_id": document.profile_id,
        "job_listing_id": document.job_listing_id,
        "application_id": document.application_id,
        "kind": document.kind.value if hasattr(document.kind, "value") else document.kind,
        "title": document.title,
        "template_id": document.template_id,
        "status": document.status.value if hasattr(document.status, "value") else document.status,
        "content": document.content,
        "strategy": document.strategy,
        "match_data": document.match_data,
        "metadata": document.meta,
        "approved_by_user": document.approved_by_user,
        "current_version": document.current_version,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }


# --------------------------------------------------------------------------- templates
@router.get("/templates", response_model=list[DocumentTemplateOut])
def get_templates():
    return list_templates()


# --------------------------------------------------------------------------- master CV
@router.get("/master-cv", response_model=MasterCVOut)
def get_master_cv(session: SessionDep):
    profile = get_or_create_profile(session)
    master = session.query(MasterCV).filter(MasterCV.profile_id == profile.id).first()
    if master is None:
        master = MasterCV(profile_id=profile.id, content={"sections": []})
        session.add(master)
        session.commit()
        session.refresh(master)
    return master


@router.put("/master-cv", response_model=MasterCVOut)
def update_master_cv(content: dict, session: SessionDep):
    profile = get_or_create_profile(session)
    master = session.query(MasterCV).filter(MasterCV.profile_id == profile.id).first()
    if master is None:
        master = MasterCV(profile_id=profile.id, content=content)
        session.add(master)
    else:
        version = CVVersion(
            master_cv_id=master.id,
            version_number=master.version,
            content=master.content or {},
            note="Auto-saved before edit",
        )
        session.add(version)
        master.content = content
        master.version += 1
    session.commit()
    session.refresh(master)
    return master


@router.post("/master-cv/versions/{version_id}/restore", response_model=MasterCVOut)
def restore_master_cv_version(version_id: int, session: SessionDep):
    profile = get_or_create_profile(session)
    master = session.query(MasterCV).filter(MasterCV.profile_id == profile.id).first()
    version = session.get(CVVersion, version_id)
    if version is None or master is None or version.master_cv_id != master.id:
        raise HTTPException(status_code=404, detail="Version not found")
    snapshot = CVVersion(
        master_cv_id=master.id,
        version_number=master.version,
        content=master.content or {},
        note="Snapshot before restore",
    )
    session.add(snapshot)
    master.content = version.content
    master.version += 1
    session.commit()
    session.refresh(master)
    return master


@router.get("/master-cv/versions", response_model=list[CVVersionOut])
def list_master_cv_versions(session: SessionDep):
    profile = get_or_create_profile(session)
    master = session.query(MasterCV).filter(MasterCV.profile_id == profile.id).first()
    if master is None:
        return []
    return (
        session.query(CVVersion)
        .filter(CVVersion.master_cv_id == master.id)
        .order_by(CVVersion.version_number.desc())
        .all()
    )


# --------------------------------------------------------------------------- documents
@router.get("", response_model=list[DocumentOut])
def list_documents(session: SessionDep, kind: str | None = None):
    query = session.query(Document).order_by(Document.id.desc())
    if kind:
        query = query.filter(Document.kind == kind)
    return query.all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, session: SessionDep):
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.patch("/{document_id}", response_model=DocumentOut)
def update_document(document_id: int, payload: DocumentUpdate, session: SessionDep):
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    data = payload.model_dump(exclude_unset=True)
    if "content" in data:
        version = DocumentVersion(
            document_id=document.id,
            version_number=document.current_version,
            content=document.content or {},
            status=document.status.value if hasattr(document.status, "value") else document.status,
            change_summary="Snapshot before manual edit",
            agent_stage="user",
        )
        session.add(version)
        document.content = data["content"]
        document.current_version += 1
        data.pop("content")
    for key, value in data.items():
        setattr(document, key, value)
    session.commit()
    session.refresh(document)
    return document


@router.delete("/{document_id}")
def delete_document(document_id: int, session: SessionDep):
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    session.delete(document)
    session.commit()
    return {"ok": True}


@router.get("/{document_id}/versions", response_model=list[DocumentVersionOut])
def list_document_versions(document_id: int, session: SessionDep):
    return (
        session.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
        .all()
    )


@router.post("/{document_id}/approve")
def approve_document(document_id: int, session: SessionDep):
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    # Quality gate: unresolved critical findings block approval.
    metadata = document.meta or {}
    final_review = metadata.get("final_review") or {}
    if final_review.get("critical_count", 0) > 0:
        raise HTTPException(
            status_code=409,
            detail="Approval blocked: unresolved critical findings remain.",
        )
    document.status = DocumentStatus.APPROVED.value
    document.approved_by_user = True
    session.commit()
    session.refresh(document)
    return document


@router.post("/{document_id}/status")
def set_document_status(document_id: int, status: str, session: SessionDep):
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    valid = {s.value for s in DocumentStatus}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {sorted(valid)}")
    document.status = status
    session.commit()
    session.refresh(document)
    return document


# --------------------------------------------------------------------------- export
@router.post("/{document_id}/export", response_model=ExportResult)
def export_document(document_id: int, payload: ExportRequest, session: SessionDep):
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    content = document.content or {}
    if payload.format == "pdf":
        data = render_pdf(content)
        validator = validate_pdf(data)
        mime = "application/pdf"
        extension = "pdf"
    elif payload.format == "docx":
        data = render_docx(content)
        validator = validate_docx(data)
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        extension = "docx"
    elif payload.format == "txt":
        data = render_text(content).encode("utf-8")
        validator = {"valid": True}
        mime = "text/plain"
        extension = "txt"
    elif payload.format == "tex":
        data = render_latex(content).encode("utf-8")
        validator = {"valid": bool(data)}
        mime = "application/x-tex"
        extension = "tex"
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")

    if not validator.get("valid"):
        raise HTTPException(
            status_code=500,
            detail=f"Export validation failed: {validator.get('error')}",
        )

    settings = get_settings()
    settings.documents_dir.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in document.title)[:60]
    filename = f"{safe_title}-{datetime.utcnow().strftime('%Y%m%d-%H%M')}.{extension}"
    path = settings.documents_dir / filename
    path.write_bytes(data)

    document.status = DocumentStatus.EXPORTED.value
    session.commit()

    return ExportResult(
        filename=filename,
        mime_type=mime,
        size_bytes=len(data),
        content_b64=base64.b64encode(data).decode(),
        validator=validator,
    )
