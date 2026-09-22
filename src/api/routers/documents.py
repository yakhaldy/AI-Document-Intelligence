from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import Document, User
from src.api.auth import get_current_user
from src.api.deps import get_db, get_tenant_id
from src.api.schemas import DocumentListResponse, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_out(document: Document) -> DocumentOut:
    return DocumentOut(
        id=document.id,
        doc_type=document.doc_type,
        filename=Path(document.file_path).name,
        uploaded_at=document.uploaded_at,
        ocr_confidence=document.ocr_confidence,
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = 1,
    page_size: int = 20,
    doc_type: str | None = None,
    session: Session = Depends(get_db),
    tenant_id=Depends(get_tenant_id),
    _user: User = Depends(get_current_user),
):
    page_size = min(page_size, 100)
    stmt = select(Document).where(Document.tenant_id == tenant_id)
    if doc_type:
        stmt = stmt.where(Document.doc_type == doc_type)

    total = session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    stmt = stmt.order_by(Document.uploaded_at.desc().nulls_last()).offset((page - 1) * page_size).limit(page_size)
    documents = session.execute(stmt).scalars().all()
    return DocumentListResponse(items=[_to_out(d) for d in documents], total=total)
