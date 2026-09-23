"""read-only agent role and limited views

Revision ID: 762bde9e7953
Revises: c20e9c80396c
Create Date: 2026-09-22 18:02:16.125438

"""
import os
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '762bde9e7953'
down_revision: Union[str, Sequence[str], None] = 'c20e9c80396c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


VIEW_SQL = """
CREATE VIEW v_invoices AS
SELECT
    inv.id AS invoice_id,
    doc.tenant_id,
    inv.invoice_number,
    inv.invoice_date,
    inv.due_date,
    inv.total_ht,
    inv.tva_rate,
    inv.total_tva,
    inv.total_ttc,
    inv.currency,
    inv.payment_status,
    sup.name AS supplier_name,
    sup.ice AS supplier_ice,
    sup.city AS supplier_city
FROM invoices inv
JOIN documents doc ON doc.id = inv.document_id
LEFT JOIN suppliers sup ON sup.id = inv.supplier_id;
"""


def upgrade() -> None:
    op.execute(VIEW_SQL)

    password = os.environ.get("AGENT_DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "AGENT_DB_PASSWORD manquant (voir .env) — requis pour créer le rôle "
            "PostgreSQL en lecture seule de l'agent (README §2.3)"
        )
    # Idempotent: skip role creation if it already exists (e.g. migration re-run).
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rag_agent') THEN
                CREATE ROLE rag_agent LOGIN PASSWORD '{password}';
            END IF;
        END
        $$;
    """)
    # SELECT only on the one view — no grants at all on base tables, so even
    # a raw-SQL bug in the agent's query builder can't reach them, and
    # certainly can't INSERT/UPDATE/DELETE/DROP anything.
    op.execute("GRANT SELECT ON v_invoices TO rag_agent;")


def downgrade() -> None:
    op.execute("DROP OWNED BY rag_agent;")
    op.execute("DROP ROLE IF EXISTS rag_agent;")
    op.execute("DROP VIEW IF EXISTS v_invoices;")
