"""SQLAlchemy models matching README section 3 (schéma PostgreSQL).

Every table (except document_chunks, whose rows aren't per-invoice) carries
tenant_id for multi-tenant isolation (README §2.3).
"""
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(Text, nullable=False)
    ice = Column(Text)
    if_number = Column(Text)
    rc = Column(Text)
    city = Column(Text)

    invoices = relationship("Invoice", back_populates="supplier")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    file_path = Column(Text, nullable=False)
    doc_type = Column(Text, CheckConstraint("doc_type IN ('invoice','contract','report')"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    ocr_confidence = Column(Numeric)

    invoice = relationship("Invoice", back_populates="document", uselist=False)
    chunks = relationship("DocumentChunk", back_populates="document")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    invoice_number = Column(Text)
    invoice_date = Column(Date)
    due_date = Column(Date)
    total_ht = Column(Numeric)
    tva_rate = Column(Numeric)
    total_tva = Column(Numeric)
    total_ttc = Column(Numeric)
    currency = Column(Text, server_default="MAD")
    payment_status = Column(Text, CheckConstraint("payment_status IN ('paid','unpaid')"))

    document = relationship("Document", back_populates="invoice")
    supplier = relationship("Supplier", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    description = Column(Text)
    quantity = Column(Numeric)
    unit_price_ht = Column(Numeric)
    total_ht = Column(Numeric)

    invoice = relationship("Invoice", back_populates="lines")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_number = Column(Integer)
    content = Column(Text)
    embedding = Column(Vector(1024))  # gemini-embedding-001, outputDimensionality=1024 (voir src/rag)

    document = relationship("Document", back_populates="chunks")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    role = Column(Text, CheckConstraint("role IN ('admin','user')"), server_default="user", nullable=False)
    status = Column(
        Text,
        CheckConstraint("status IN ('pending','approved','rejected')"),
        server_default="pending",
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def default_tenant_id() -> uuid.UUID:
    """Fixed tenant for this single-tenant portfolio dataset."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")
