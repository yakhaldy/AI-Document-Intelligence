from src.classification.tfidf_baseline import predict, train

TRAIN_TEXTS = [
    "Facture N° FAC/2025/001 ICE TVA Total HT Total TTC montant",
    "Facture N° FAC/2025/002 ICE TVA Total HT Total TTC montant à payer",
    "Contrat de prestation de services entre les soussignés article clause",
    "Contrat de bail commercial entre les soussignés article résiliation",
    "Rapport d'audit interne constats recommandations conclusion",
    "Rapport mensuel d'activité constats recommandations conclusion",
]
TRAIN_LABELS = ["facture", "facture", "contrat", "contrat", "rapport", "rapport"]


def test_train_and_predict_returns_label_and_scores():
    vectorizer, model = train(TRAIN_TEXTS, TRAIN_LABELS)
    results = predict(vectorizer, model, ["Facture N° FAC/2025/999 ICE TVA Total HT Total TTC"])
    assert len(results) == 1
    assert results[0]["label"] in {"facture", "contrat", "rapport"}
    assert set(results[0]["scores"]) == {"facture", "contrat", "rapport"}
    assert abs(sum(results[0]["scores"].values()) - 1.0) < 1e-6


def test_predict_separates_distinct_classes():
    vectorizer, model = train(TRAIN_TEXTS, TRAIN_LABELS)
    results = predict(vectorizer, model, [
        "Facture N° FAC/2025/777 ICE TVA Total HT Total TTC montant",
        "Contrat de sous-traitance entre les soussignés article résiliation",
    ])
    assert results[0]["label"] == "facture"
    assert results[1]["label"] == "contrat"
