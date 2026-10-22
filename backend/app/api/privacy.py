"""Privacy & data management API: export, backup, restore, deletion."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, TokenDep
from app.core.config import get_settings
from app.schemas.applications import DataExportOut, DeleteScopeRequest
from app.services import privacy_service

router = APIRouter(prefix="/api/v1/privacy", dependencies=[TokenDep])


@router.get("/export", response_model=DataExportOut)
def export_data(session: SessionDep):
    data = privacy_service.export_all_data(session)
    payload = json.dumps(data, indent=2, default=str).encode("utf-8")
    filename = f"careerpilot-export-{_stamp()}.json"
    return DataExportOut(
        filename=filename,
        content_b64=base64.b64encode(payload).decode(),
        size_bytes=len(payload),
    )


@router.post("/backup")
def create_backup():
    path = privacy_service.backup_database()
    return {
        "ok": True,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "created_at": _stamp(),
    }


@router.get("/backups")
def list_backups():
    settings = get_settings()
    if not settings.backup_dir.exists():
        return []
    backups = []
    for path in sorted(settings.backup_dir.glob("*.db"), reverse=True):
        backups.append(
            {
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "created_at": path.stat().st_mtime,
            }
        )
    return backups


@router.post("/restore")
async def restore_backup(file: UploadFile = File(...)):
    settings = get_settings()
    settings.backup_dir.mkdir(parents=True, exist_ok=True)
    target = settings.backup_dir / f"restore-{_stamp()}.db"
    content = await file.read()
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Backup file is too large.")
    target.write_bytes(content)
    try:
        privacy_service.restore_database(target)
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Restore failed: {exc}")
    return {"ok": True, "detail": "Database restored. Restart the backend to use it."}


@router.post("/delete")
def delete_data(payload: DeleteScopeRequest, session: SessionDep):
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required.")

    if payload.scope == "everything":
        privacy_service.delete_everything(session)
        return {"ok": True, "detail": "All local profile data deleted."}
    if payload.scope == "documents":
        count = privacy_service.delete_documents(session, payload.document_ids)
        return {"ok": True, "deleted": count}
    if payload.scope == "jobs":
        count = privacy_service.delete_jobs(session, payload.job_ids)
        return {"ok": True, "deleted": count}
    if payload.scope == "applications":
        count = privacy_service.delete_applications(session, payload.application_ids)
        return {"ok": True, "deleted": count}
    raise HTTPException(status_code=400, detail="Unknown deletion scope.")


@router.get("/integrity")
def database_integrity():
    return privacy_service.database_integrity_check()


def _stamp() -> str:
    from datetime import datetime

    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")
