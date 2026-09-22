from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import Document, Invoice, Supplier, User
from src.api.auth import get_current_user
from src.api.deps import get_db, get_tenant_id
from src.api.schemas import InvoiceListResponse, InvoiceOut

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _to_out(invoice: Invoice, supplier_name: str | None) -> InvoiceOut:
    return InvoiceOut(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        total_ht=invoice.total_ht,
        tva_rate=invoice.tva_rate,
        total_tva=invoice.total_tva,
        total_ttc=invoice.total_ttc,
        currency=invoice.currency,
        payment_status=invoice.payment_status,
        supplier_name=supplier_name,
    )


@router.get("", response_model=InvoiceListResponse)
def list_invoices(
    page: int = 1,
    page_size: int = 20,
    payment_status: str | None = None,
    session: Session = Depends(get_db),
    tenant_id=Depends(get_tenant_id),
    _user: User = Depends(get_current_user),
):
    page_size = min(page_size, 100)
    stmt = (
        select(Invoice, Supplier.name)
        .join(Document, Document.id == Invoice.document_id)
        .outerjoin(Supplier, Supplier.id == Invoice.supplier_id)
        .where(Document.tenant_id == tenant_id)
    )
    if payment_status:
        stmt = stmt.where(Invoice.payment_status == payment_status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.execute(count_stmt).scalar_one()

    stmt = stmt.order_by(Invoice.invoice_date.desc().nulls_last()).offset((page - 1) * page_size).limit(page_size)
    rows = session.execute(stmt).all()
    items = [_to_out(invoice, supplier_name) for invoice, supplier_name in rows]
    return InvoiceListResponse(items=items, total=total)


@router.get("/{invoice_id}", response_model=InvoiceOut, responses={404: {"description": "Facture introuvable"}})
def get_invoice(
    invoice_id: int,
    session: Session = Depends(get_db),
    tenant_id=Depends(get_tenant_id),
    _user: User = Depends(get_current_user),
):
    stmt = (
        select(Invoice, Supplier.name)
        .join(Document, Document.id == Invoice.document_id)
        .outerjoin(Supplier, Supplier.id == Invoice.supplier_id)
        .where(Document.tenant_id == tenant_id, Invoice.id == invoice_id)
    )
    row = session.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    invoice, supplier_name = row
    return _to_out(invoice, supplier_name)
