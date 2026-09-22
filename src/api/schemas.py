"""Pydantic request/response models."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class RegisterResponse(BaseModel):
    message: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    status: str


class InvoiceOut(BaseModel):
    invoice_id: int
    invoice_number: str | None
    invoice_date: date | None
    due_date: date | None
    total_ht: Decimal | None
    tva_rate: Decimal | None
    total_tva: Decimal | None
    total_ttc: Decimal | None
    currency: str | None
    payment_status: str | None
    supplier_name: str | None


class InvoiceListResponse(BaseModel):
    items: list[InvoiceOut]
    total: int


class UploadResponse(BaseModel):
    document_id: int
    doc_type: str
    invoice: InvoiceOut | None
    used_regex_fallback: bool


class DocumentOut(BaseModel):
    id: int
    doc_type: str
    filename: str
    uploaded_at: datetime | None
    ocr_confidence: Decimal | None


class DocumentListResponse(BaseModel):
    items: list[DocumentOut]
    total: int


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    tools_used: list[str]
