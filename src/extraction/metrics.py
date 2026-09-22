"""Field-by-field precision/recall/F1 for structured extraction.

A field counts as a true positive only when both the gold label and the
prediction are non-null AND equal (numeric fields compared with a small
tolerance, everything else by exact string match after stripping).
"""


def _values_match(pred, gold) -> bool:
    if gold is None or pred is None:
        return pred is None and gold is None
    if isinstance(gold, (int, float)) and isinstance(pred, (int, float)):
        return abs(float(pred) - float(gold)) < 0.01
    return str(pred).strip() == str(gold).strip()


def evaluate_field(preds: list, golds: list) -> dict:
    tp = fp = fn = tn = 0
    for pred, gold in zip(preds, golds):
        gold_present = gold is not None
        pred_present = pred is not None
        match = _values_match(pred, gold)
        if gold_present and match:
            tp += 1
        elif gold_present and not match:
            fn += 1
            if pred_present:
                fp += 1
        elif not gold_present and pred_present:
            fp += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": precision, "recall": recall, "f1": f1,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn, "n": len(preds),
    }


def evaluate_all_fields(predictions: list[dict], golds: list[dict], fields: list[str]) -> dict:
    return {
        field: evaluate_field(
            [p.get(field) for p in predictions],
            [g.get(field) for g in golds],
        )
        for field in fields
    }


def gold_from_label(label: dict) -> dict:
    supplier = label["supplier"]
    return {
        "invoice_number": label["invoice_number"],
        "invoice_date": label["invoice_date"],
        "due_date": label["due_date"],
        "supplier_name": supplier["name"],
        "supplier_ice": supplier["ice"],
        "supplier_if": supplier["if"],
        "supplier_rc": supplier["rc"],
        "total_ht": label["total_ht"],
        "tva_rate": label["tva_rate"],
        "total_tva": label["total_tva"],
        "total_ttc": label["total_ttc"],
    }
