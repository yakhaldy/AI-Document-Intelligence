from src.extraction.metrics import evaluate_field, gold_from_label


def test_exact_match_string_field_is_true_positive():
    result = evaluate_field(["FAC/2025/001"], ["FAC/2025/001"])
    assert result == {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 1, "fp": 0, "fn": 0, "tn": 0, "n": 1}


def test_numeric_field_within_tolerance_is_true_positive():
    result = evaluate_field([36085.579], [36085.58])
    assert result["tp"] == 1
    assert result["fp"] == 0


def test_both_null_is_true_negative_not_counted_in_precision_recall():
    result = evaluate_field([None], [None])
    assert result["tn"] == 1
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0


def test_wrong_non_null_prediction_is_both_fp_and_fn():
    result = evaluate_field(["162720 El Jadida"], ["162720"])
    assert result["fp"] == 1
    assert result["fn"] == 1
    assert result["tp"] == 0


def test_hallucinated_value_when_gold_is_null_is_false_positive():
    result = evaluate_field(["some value"], [None])
    assert result["fp"] == 1
    assert result["tp"] == 0
    assert result["fn"] == 0


def test_missed_value_when_gold_present_is_false_negative():
    result = evaluate_field([None], ["162720"])
    assert result["fn"] == 1
    assert result["fp"] == 0


def test_precision_recall_f1_over_mixed_batch():
    preds = ["A", "B", None, "wrong"]
    golds = ["A", None, "C", "D"]
    result = evaluate_field(preds, golds)
    # tp=1 (A), fp=2 (B hallucinated, wrong≠D), fn=2 (C missed, D wrong)
    assert result["tp"] == 1
    assert result["fp"] == 2
    assert result["fn"] == 2
    assert result["precision"] == 1 / 3
    assert result["recall"] == 1 / 3


def test_gold_from_label_flattens_supplier_subfields():
    label = {
        "invoice_number": "FAC/2025/001",
        "invoice_date": "2025-01-08",
        "due_date": None,
        "supplier": {"name": "Acme SARL", "ice": "123", "if": "456", "rc": "789"},
        "total_ht": 100.0,
        "tva_rate": 20,
        "total_tva": 20.0,
        "total_ttc": 120.0,
    }
    assert gold_from_label(label) == {
        "invoice_number": "FAC/2025/001",
        "invoice_date": "2025-01-08",
        "due_date": None,
        "supplier_name": "Acme SARL",
        "supplier_ice": "123",
        "supplier_if": "456",
        "supplier_rc": "789",
        "total_ht": 100.0,
        "tva_rate": 20,
        "total_tva": 20.0,
        "total_ttc": 120.0,
    }
