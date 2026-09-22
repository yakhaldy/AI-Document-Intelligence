import pytest

from src.agent.query_sql import count_by_payment_status, top_suppliers_by_total, total_by_payment_status


def test_total_by_payment_status_rejects_invalid_status():
    with pytest.raises(ValueError):
        total_by_payment_status("tenant", "invalide")


def test_count_by_payment_status_rejects_invalid_status():
    with pytest.raises(ValueError):
        count_by_payment_status("tenant", "invalide")


def test_top_suppliers_by_total_rejects_invalid_payment_status():
    with pytest.raises(ValueError):
        top_suppliers_by_total("tenant", payment_status="invalide")
