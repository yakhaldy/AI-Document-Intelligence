from src.classification.metrics import accuracy, confusion_matrix, evaluate_classification, per_class_metrics

LABELS = ["facture", "contrat", "rapport"]


def test_perfect_predictions():
    preds = ["facture", "contrat", "rapport"]
    golds = ["facture", "contrat", "rapport"]
    assert accuracy(preds, golds) == 1.0


def test_confusion_matrix_counts():
    preds = ["facture", "contrat", "facture"]
    golds = ["facture", "contrat", "contrat"]
    matrix = confusion_matrix(preds, golds, LABELS)
    assert matrix["facture"]["facture"] == 1
    assert matrix["contrat"]["contrat"] == 1
    assert matrix["contrat"]["facture"] == 1  # one contrat misclassified as facture


def test_per_class_metrics_with_one_confusion():
    # facture: 2 correct; contrat: 1 correct, 1 predicted as facture (FN for
    # contrat, and NOT an FP for facture since it's a wrong-class swap)
    preds = ["facture", "facture", "contrat", "rapport"]
    golds = ["facture", "contrat", "contrat", "rapport"]
    metrics = per_class_metrics(preds, golds, LABELS)
    assert metrics["facture"]["precision"] == 0.5  # 1 tp / (1 tp + 1 fp)
    assert metrics["facture"]["recall"] == 1.0
    assert metrics["contrat"]["precision"] == 1.0
    assert metrics["contrat"]["recall"] == 0.5
    assert metrics["rapport"]["precision"] == 1.0
    assert metrics["rapport"]["recall"] == 1.0


def test_evaluate_classification_shape():
    preds = ["facture", "contrat", "rapport"]
    golds = ["facture", "contrat", "rapport"]
    result = evaluate_classification(preds, golds, LABELS)
    assert result["accuracy"] == 1.0
    assert result["macro_f1"] == 1.0
    assert result["n"] == 3
    assert set(result["per_class"]) == set(LABELS)
