"""TF-IDF + LogisticRegression baseline classifier (facture/contrat/rapport)."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

FRENCH_STOPWORDS = [
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "à", "au", "aux",
    "en", "pour", "par", "sur", "dans", "ce", "cette", "ces", "son", "sa",
    "ses", "est", "sont", "avec", "que", "qui", "ou", "il", "elle", "ne",
    "pas", "plus", "se", "sa", "leur", "leurs",
]


def train(texts: list[str], labels: list[str]):
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2, stop_words=FRENCH_STOPWORDS)
    X = vectorizer.fit_transform(texts)
    model = LogisticRegression(max_iter=1000)
    model.fit(X, labels)
    return vectorizer, model


def predict(vectorizer, model, texts: list[str]):
    X = vectorizer.transform(texts)
    labels = model.predict(X)
    proba = model.predict_proba(X)
    classes = list(model.classes_)
    return [
        {"label": label, "scores": dict(zip(classes, row.tolist()))}
        for label, row in zip(labels, proba)
    ]
