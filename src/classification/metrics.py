"""Accuracy, per-class precision/recall/F1, and confusion matrix."""

LABELS = ["facture", "contrat", "rapport"]


def confusion_matrix(preds: list[str], golds: list[str], labels: list[str] = LABELS) -> dict:
    matrix = {g: {p: 0 for p in labels} for g in labels}
    for pred, gold in zip(preds, golds):
        matrix[gold][pred] += 1
    return matrix


def per_class_metrics(preds: list[str], golds: list[str], labels: list[str] = LABELS) -> dict:
    matrix = confusion_matrix(preds, golds, labels)
    result = {}
    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[g][label] for g in labels if g != label)
        fn = sum(matrix[label][p] for p in labels if p != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        support = sum(matrix[label].values())
        result[label] = {"precision": precision, "recall": recall, "f1": f1, "support": support}
    return result


def accuracy(preds: list[str], golds: list[str]) -> float:
    if not golds:
        return 0.0
    return sum(p == g for p, g in zip(preds, golds)) / len(golds)


def macro_f1(preds: list[str], golds: list[str], labels: list[str] = LABELS) -> float:
    per_class = per_class_metrics(preds, golds, labels)
    return sum(m["f1"] for m in per_class.values()) / len(labels)


def evaluate_classification(preds: list[str], golds: list[str], labels: list[str] = LABELS) -> dict:
    return {
        "accuracy": accuracy(preds, golds),
        "macro_f1": macro_f1(preds, golds, labels),
        "per_class": per_class_metrics(preds, golds, labels),
        "confusion_matrix": confusion_matrix(preds, golds, labels),
        "n": len(golds),
    }
