"""query_sql tool: pre-validated, parameterized read-only queries.

No freeform SQL from the LLM at all — the agent can only pick one of these
named templates and fill in typed parameters. This is the stronger of the
two designs README §4 allows ("requêtes pré-validées ou générées puis
vérifiées") — no SQL-injection surface, no need to parse/validate arbitrary
generated SQL. All queries run through the `rag_agent` DB role (SELECT only
on v_invoices — see db/migrations, verified empirically: permission denied
on base tables and on writes) and are always filtered by tenant_id, which
the caller supplies — never trusted from LLM-controlled input.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from db.ingest import UNKNOWN_SUPPLIER_PLACEHOLDER

load_dotenv()

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        url = os.environ.get("AGENT_DATABASE_URL")
        if not url:
            raise RuntimeError("AGENT_DATABASE_URL manquant (voir .env)")
        _engine = create_engine(url)
    return _engine


def total_by_payment_status(tenant_id, status: str, year: int | None = None, month: int | None = None) -> float:
    if status not in ("paid", "unpaid"):
        raise ValueError("status doit être 'paid' ou 'unpaid'")
    stmt = text("""
        SELECT COALESCE(SUM(total_ttc), 0) FROM v_invoices
        WHERE tenant_id = :tenant_id AND payment_status = :status
          AND (CAST(:year AS INTEGER) IS NULL OR EXTRACT(YEAR FROM invoice_date) = CAST(:year AS INTEGER))
          AND (CAST(:month AS INTEGER) IS NULL OR EXTRACT(MONTH FROM invoice_date) = CAST(:month AS INTEGER))
    """)
    with _get_engine().connect() as conn:
        result = conn.execute(stmt, {"tenant_id": tenant_id, "status": status, "year": year, "month": month})
        return float(result.scalar())


def count_by_payment_status(tenant_id, status: str) -> int:
    if status not in ("paid", "unpaid"):
        raise ValueError("status doit être 'paid' ou 'unpaid'")
    stmt = text("SELECT count(*) FROM v_invoices WHERE tenant_id = :tenant_id AND payment_status = :status")
    with _get_engine().connect() as conn:
        return int(conn.execute(stmt, {"tenant_id": tenant_id, "status": status}).scalar())


def invoice_lookup(tenant_id, invoice_number: str) -> dict | None:
    stmt = text("SELECT * FROM v_invoices WHERE tenant_id = :tenant_id AND invoice_number = :invoice_number")
    with _get_engine().connect() as conn:
        row = conn.execute(stmt, {"tenant_id": tenant_id, "invoice_number": invoice_number}).mappings().first()
        return dict(row) if row else None


def top_suppliers_by_total(tenant_id, limit: int = 5, payment_status: str | None = None) -> list[dict]:
    if payment_status is not None and payment_status not in ("paid", "unpaid"):
        raise ValueError("payment_status doit être 'paid', 'unpaid' ou None")
    stmt = text("""
        SELECT supplier_name, SUM(total_ttc) AS total
        FROM v_invoices
        WHERE tenant_id = :tenant_id
          AND (CAST(:payment_status AS TEXT) IS NULL OR payment_status = CAST(:payment_status AS TEXT))
          AND supplier_name IS NOT NULL
          AND supplier_name != :unknown_placeholder
        GROUP BY supplier_name
        ORDER BY total DESC
        LIMIT :limit
    """)
    with _get_engine().connect() as conn:
        rows = conn.execute(
            stmt,
            {
                "tenant_id": tenant_id,
                "payment_status": payment_status,
                "limit": limit,
                "unknown_placeholder": UNKNOWN_SUPPLIER_PLACEHOLDER,
            },
        ).mappings().all()
        return [dict(r) for r in rows]


TEMPLATES = {
    "total_by_payment_status": total_by_payment_status,
    "count_by_payment_status": count_by_payment_status,
    "invoice_lookup": invoice_lookup,
    "top_suppliers_by_total": top_suppliers_by_total,
}


def query_sql(tenant_id, template: str, **params):
    if template not in TEMPLATES:
        raise ValueError(f"template inconnu : {template} (attendu : {list(TEMPLATES)})")
    return TEMPLATES[template](tenant_id, **params)
