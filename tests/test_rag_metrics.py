from types import SimpleNamespace

from src.rag.metrics import recall_at_k


def _result(document_id):
    return {"chunk": SimpleNamespace(document_id=document_id), "score": 1.0}


def test_recall_at_k_true_when_expected_document_present():
    retrieved = [_result(5), _result(2), _result(7)]
    assert recall_at_k(retrieved, expected_document_id=2) is True


def test_recall_at_k_false_when_expected_document_absent():
    retrieved = [_result(5), _result(9)]
    assert recall_at_k(retrieved, expected_document_id=2) is False


def test_recall_at_k_false_on_empty_results():
    assert recall_at_k([], expected_document_id=2) is False
