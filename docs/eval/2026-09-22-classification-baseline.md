# Classification de documents — facture / contrat / rapport

Date : 2026-09-22
TF-IDF+LogReg évalué sur le split test complet (gratuit, instantané). LLM/Jev évalués sur un sous-échantillon stratifié déterministe du split test ({'facture': 15, 'contrat': 13, 'rapport': 16}) pour limiter le coût — jamais choisi à la main, jamais le split dev, jamais utilisé pour ajuster les prompts.
Few-shot : 1 exemple par classe, tiré du split dev (jamais du test).

## ⚠️ Limite méthodologique importante

Les 5 méthodes obtiennent 100% d'accuracy. C'est une mesure réelle (aucun
chiffre inventé), mais **ce résultat doit être lu avec prudence** : les
documents `contrat` et `rapport` sont synthétiques, générés spécifiquement
pour cette évaluation (`generate_docs.py`), avec un vocabulaire volontairement
très différent de celui des factures (Articles/Soussignés/Clauses pour les
contrats, Recommandations/Constats/Conclusion pour les rapports, vs
ICE/TVA/Total HT pour les factures). Une classification par mots-clés
suffirait déjà à séparer parfaitement ces 3 classes.

Ce 100% ne prouve donc **pas** qu'une méthode est meilleure qu'une autre sur
un cas réel — il prouve seulement que toutes fonctionnent sur un cas facile.
Pour un vrai signal de difficulté (et donc de discrimination entre méthodes),
il faudrait de vrais contrats/rapports marocains (cf. Étape 0 : FATURA,
ReceiptSense, documents réels anonymisés — non encore intégrés), où le
vocabulaire administratif/financier se recoupe davantage entre les classes.

À accuracy égale, TF-IDF+LogReg gagne sur le **coût et la latence bruts**
(gratuit et quasi instantané, contre ~$0.00008–0.0002/doc et 0.3–1.8s pour
LLM/Jev) — c'était l'hypothèse de départ du README.

## Décision : Jev retenu

Choix produit fait malgré ce coût légèrement supérieur : TF-IDF+LogReg est
un modèle bag-of-words entraîné sur un vocabulaire synthétique trivialement
disjoint — rien ne garantit qu'il généralise aussi bien à de vrais documents
où facture/contrat/rapport partagent davantage de vocabulaire administratif
et financier. Jev reste peu coûteux et rapide (0.3s de latence, moins cher
qu'un LLM généraliste équivalent) tout en étant un modèle de décision
entraîné, présumé plus robuste hors distribution. À reconfirmer une fois de
vraies données disponibles (Étape 0).

| Méthode | N | Accuracy | Macro F1 | Latence moy. (s) | Latence médiane (s) | Coût total ($) | Coût moy./doc ($) |
|---|---|---|---|---|---|---|---|
| tfidf_logreg | 97 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000000 | 0.000000 |
| llm_zero_shot | 44 | 1.000 | 1.000 | 1.803 | 1.484 | 0.003355 | 0.000076 |
| llm_few_shot | 44 | 1.000 | 1.000 | 1.820 | 1.534 | 0.008061 | 0.000183 |
| jev_zero_shot | 44 | 1.000 | 1.000 | 0.307 | 0.287 | n/d | n/d |
| jev_few_shot | 44 | 1.000 | 1.000 | 0.297 | 0.285 | n/d | n/d |

## tfidf_logreg — détail par classe

| Classe | Précision | Rappel | F1 | Support |
|---|---|---|---|---|
| facture | 1.00 | 1.00 | 1.00 | 68 |
| contrat | 1.00 | 1.00 | 1.00 | 13 |
| rapport | 1.00 | 1.00 | 1.00 | 16 |

Matrice de confusion (lignes = vrai, colonnes = prédit) :

| vrai\prédit | facture | contrat | rapport |
|---|---|---|---|
| facture | 68 | 0 | 0 |
| contrat | 0 | 13 | 0 |
| rapport | 0 | 0 | 16 |

## llm_zero_shot — détail par classe

| Classe | Précision | Rappel | F1 | Support |
|---|---|---|---|---|
| facture | 1.00 | 1.00 | 1.00 | 15 |
| contrat | 1.00 | 1.00 | 1.00 | 13 |
| rapport | 1.00 | 1.00 | 1.00 | 16 |

Matrice de confusion (lignes = vrai, colonnes = prédit) :

| vrai\prédit | facture | contrat | rapport |
|---|---|---|---|
| facture | 15 | 0 | 0 |
| contrat | 0 | 13 | 0 |
| rapport | 0 | 0 | 16 |

## llm_few_shot — détail par classe

| Classe | Précision | Rappel | F1 | Support |
|---|---|---|---|---|
| facture | 1.00 | 1.00 | 1.00 | 15 |
| contrat | 1.00 | 1.00 | 1.00 | 13 |
| rapport | 1.00 | 1.00 | 1.00 | 16 |

Matrice de confusion (lignes = vrai, colonnes = prédit) :

| vrai\prédit | facture | contrat | rapport |
|---|---|---|---|
| facture | 15 | 0 | 0 |
| contrat | 0 | 13 | 0 |
| rapport | 0 | 0 | 16 |

## jev_zero_shot — détail par classe

| Classe | Précision | Rappel | F1 | Support |
|---|---|---|---|---|
| facture | 1.00 | 1.00 | 1.00 | 15 |
| contrat | 1.00 | 1.00 | 1.00 | 13 |
| rapport | 1.00 | 1.00 | 1.00 | 16 |

Matrice de confusion (lignes = vrai, colonnes = prédit) :

| vrai\prédit | facture | contrat | rapport |
|---|---|---|---|
| facture | 15 | 0 | 0 |
| contrat | 0 | 13 | 0 |
| rapport | 0 | 0 | 16 |

## jev_few_shot — détail par classe

| Classe | Précision | Rappel | F1 | Support |
|---|---|---|---|---|
| facture | 1.00 | 1.00 | 1.00 | 15 |
| contrat | 1.00 | 1.00 | 1.00 | 13 |
| rapport | 1.00 | 1.00 | 1.00 | 16 |

Matrice de confusion (lignes = vrai, colonnes = prédit) :

| vrai\prédit | facture | contrat | rapport |
|---|---|---|---|
| facture | 15 | 0 | 0 |
| contrat | 0 | 13 | 0 |
| rapport | 0 | 0 | 16 |
