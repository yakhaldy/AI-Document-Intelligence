"""POST /upload — the full pipeline live: OCR -> classification -> extraction
-> DB insertion -> chunking -> embedding (architecture diagram, README §2.1).
"""
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from db.ingest import ingest_invoice
from db.index_chunks import index_document
from db.models import Document, User
from src.api.auth import get_current_user
from src.api.deps import get_db, get_tenant_id
from src.api.routers.invoices import _to_out
from src.api.schemas import UploadResponse
from src.classification.jev_classifier import classify_with_jev
from src.ocr.reference_text import extract_reference_text
from src.ocr.tesseract_ocr import run_tesseract

UPLOAD_DIR = Path("data/uploads")
DOC_TYPE_FR_TO_EN = {"facture": "invoice", "contrat": "contract", "rapport": "report"}


def _extract_text(path: Path, content_type: str | None) -> str:
    if path.suffix.lower() == ".pdf":
        text = extract_reference_text(path)
        if len(text.strip()) > 20:
            return text
    return run_tesseract(path, lang="fra")


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_document(
    file: UploadFile,
    session: Session = Depends(get_db),
    tenant_id=Depends(get_tenant_id),
    _user: User = Depends(get_current_user),
):
    suffix = Path(file.filename or "upload").suffix or ".bin"
    if suffix.lower() not in (".pdf", ".jpg", ".jpeg", ".png"):
        raise HTTPException(status_code=422, detail="Formats acceptés : PDF, JPG, PNG")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f"{tenant_id}_{file.filename}"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)

    text = _extract_text(dest, file.content_type)
    classification = classify_with_jev(text)
    doc_type_fr = classification["label"]
    doc_type_en = DOC_TYPE_FR_TO_EN[doc_type_fr]

    used_regex_fallback = False
    if doc_type_fr == "facture":
        invoice, used_regex_fallback = ingest_invoice(session, tenant_id, dest.stem, text, dest)
        if invoice is None:  # already ingested (same file_path)
            existing_doc = session.query(Document).filter_by(
                tenant_id=tenant_id, file_path=str(dest)
            ).first()
            document_id = existing_doc.id
            invoice_out = None
        else:
            document_id = invoice.document_id
            session.commit()
            invoice_out = _to_out(invoice, invoice.supplier.name if invoice.supplier else None)
    else:
        document = Document(tenant_id=tenant_id, file_path=str(dest), doc_type=doc_type_en)
        session.add(document)
        session.commit()
        document_id = document.id
        invoice_out = None

    document = session.get(Document, document_id)
    index_document(session, document, text)
    session.commit()

    return UploadResponse(
        document_id=document_id,
        doc_type=doc_type_en,
        invoice=invoice_out,
        used_regex_fallback=used_regex_fallback,
    )
