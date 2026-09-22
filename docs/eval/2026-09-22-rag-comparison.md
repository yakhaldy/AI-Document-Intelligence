# RAG — vecteur seul vs hybride vs hybride+rerank

Date : 2026-09-22
N = 50 questions (docs/eval/rag_qa_dataset.json, k=5).
Métriques faithfulness/answer_relevancy : implémentation maison inspirée de RAGAS (LLM-juge OpenRouter), pas le package `ragas` — voir src/rag/metrics.py pour pourquoi.

| Méthode | recall@5 | faithfulness | answer_relevancy | latence retrieval (s) | latence totale (s) |
|---|---|---|---|---|---|
| vector | 0.18 | 1.00 | 1.00 | 0.718 | 4.182 |
| hybrid | 0.26 | 1.00 | 1.00 | 0.660 | 3.745 |
| hybrid_rerank | 0.44 | 0.92 | 1.00 | 2.828 | 6.453 |

## Analyse

- **recall@5 progresse clairement avec la sophistication de la méthode**
  (0.18 → 0.26 → 0.44). Le hybride+rerank gagne sur le vecteur seul et
  l'hybride simple — cohérent avec la littérature, et pas un "100% partout"
  suspect (contrairement à l'Étape 3) : cette évaluation-ci discrimine
  réellement les méthodes.
- **faithfulness légèrement plus bas pour hybride+rerank (0.92 vs 1.00)** :
  contre-intuitif au premier abord, mais explicable — avec un meilleur
  contexte récupéré, le modèle tente de répondre plus souvent au lieu de
  dire "je ne sais pas" (qui est trivialement "fidèle" puisqu'il n'avance
  aucune affirmation) ; plus de tentatives de réponse = plus d'occasions
  d'imperfection.
- **recall@5 reste faible en absolu (0.44 au mieux)** : le jeu de questions
  porte sur des faits ponctuels d'une facture précise parmi 200 documents
  au vocabulaire très répétitif ("Facture", "ICE", "TVA", "Total HT"...).
  Retrouver LE bon chunk parmi ~2500 chunks structurellement très similaires
  est un cas difficile pour une recherche sémantique/lexicale. C'est un
  argument de plus en faveur du principe déjà posé par le README (§1) :
  une recherche par clé exacte ("la facture FAC/2025/00291") est mieux
  servie par une requête SQL exacte que par du RAG — exactement le rôle
  prévu pour l'agent (Étape 6).
- **Coût de latence de hybride+rerank** : ~2.8s de retrieval (vs ~0.7s) à
  cause de l'appel LLM de reranking — un compromis réel précision/latence,
  pas gratuit.
