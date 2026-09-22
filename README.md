# AI Document Intelligence & RAG Agent — Moroccan Invoices

Système qui lit des factures marocaines (PDF ou scan), en extrait les champs
structurés (ICE, IF, RC, montants, TVA...), permet de poser des questions en
langage naturel sur les documents (RAG), et répond à des questions chiffrées
via un agent qui interroge une vraie base de données au lieu de deviner.

Objectif du projet : constituer une pièce de portfolio pour candidater à des
postes AI Engineer au Maroc, en démontrant OCR, extraction structurée, RAG,
agents avec tool calling, évaluation rigoureuse, et mise en production
(Docker, CI/CD, monitoring).

---

## 1. Pourquoi ce projet

Les entreprises marocaines reçoivent des factures papier ou scannées en
grand nombre. La saisie manuelle dans un ERP est lente, sujette à erreurs
(montants, TVA, dates), et retrouver une information dans l'archive prend du
temps. Ce projet transforme des documents non structurés en données
interrogeables :

- upload d'une facture → champs extraits automatiquement dans PostgreSQL
- question libre ("quelle est la date d'échéance de la facture X ?") → RAG
  avec citation de la source
- question chiffrée ("total des factures impayées en janvier ?") → agent qui
  choisit l'outil SQL, pas le LLM qui invente un nombre

Le principe directeur du projet : **un LLM ne doit jamais calculer un
montant lui-même**. Il route la question vers l'outil déterministe
approprié (SQL, calculatrice) et se contente de formuler la réponse.

---

## 2. Architecture

### 2.1 Vue d'ensemble

```
                     ┌─────────────────────────────────────────┐
                     │                UPLOAD                    │
                     │        PDF ou image de facture            │
                     └───────────────────┬───────────────────────┘
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │                  OCR                      │
                     │   Tesseract / PaddleOCR (fr + ar)          │
                     └───────────────────┬───────────────────────┘
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │             CLASSIFICATION                │
                     │   facture / contrat / rapport              │
                     └───────────────────┬───────────────────────┘
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │               EXTRACTION                  │
                     │   champs → JSON structuré                 │
                     └──────────┬─────────────────┬───────────────┘
                                ▼                 ▼
                     ┌───────────────────┐ ┌───────────────────┐
                     │    PostgreSQL      │ │    Vector DB       │
                     │  champs structurés │ │  chunks + pages     │
                     └───────────────────┘ └───────────────────┘

                     ┌─────────────────────────────────────────┐
                     │            QUESTION UTILISATEUR            │
                     └───────────────────┬───────────────────────┘
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │              AGENT (LLM)                   │
                     │        choisit l'outil approprié            │
                     └──────┬────────────┬────────────┬────────────┘
                            ▼            ▼            ▼
                    ┌──────────────┐┌──────────┐┌──────────────┐
                    │ Recherche doc ││   SQL    ││ Calculatrice  │
                    │ RAG + page    ││ lecture  ││   arithmétique │
                    │   source      ││  seule   ││    exacte      │
                    └──────┬───────┘└────┬─────┘└──────┬───────┘
                           └─────────────┼─────────────┘
                                         ▼
                     ┌─────────────────────────────────────────┐
                     │        RÉPONSE + sources + chiffres        │
                     └─────────────────────────────────────────┘
```

### 2.2 Stack technique

| Couche | Choix | Remarque |
|---|---|---|
| API | FastAPI | REST, auth JWT simple |
| OCR | Tesseract (baseline) puis PaddleOCR | comparer les deux, mesurer le CER |
| Extraction | LLM (prompt structuré → JSON) + regex de secours pour ICE/IF/RC/TVA | ne pas tout confier au LLM |
| Classification | TF-IDF + LogisticRegression **et** LLM zero-shot **et** Jev (TypeSafe System One) | comparer, garder le meilleur rapport coût/précision |
| RAG | embeddings multilingues (type BGE-M3 / multilingual-e5) + BM25 hybride + reranker | chunking par section, pas par nombre de caractères fixe |
| Vector DB | ChromaDB (dev) → Qdrant (prod) | |
| Base relationnelle | PostgreSQL | champs extraits + statut de paiement |
| Agent | function calling (outils : search_documents, query_sql, calculate) | SQL toujours en lecture seule |
| Observabilité | Langfuse ou équivalent open source | coût, latence, traces |
| Évaluation | jeu de test annoté à la main + RAGAS | seule mesure fiable de qualité |
| Conteneurisation | Docker + docker-compose | |
| CI/CD | GitHub Actions | tests automatiques + build image |
| Frontend | React (minimal : upload, chat, tableau de bord) | pas la priorité |

### 2.2bis Environnements Python

Deux environnements virtuels coexistent, pour une raison purement technique :

- **`.venv`** (Python 3.14) — environnement principal du projet (Tesseract,
  extraction, RAG, agent, API...).
- **`.venv-paddle`** (Python 3.12) — dédié à PaddleOCR. `paddlepaddle` n'a pas
  de wheel pour Python 3.14, et sur ce Mac (macOS x86_64), `paddlepaddle==3.0`
  (backend d'inférence PIR) plante à l'exécution. La combinaison qui fonctionne
  est figée dans l'extra `paddleocr` de `pyproject.toml` :
  `paddlepaddle==2.6.2` + `paddleocr==2.7.3` + `numpy<2` +
  `opencv-python-headless==4.9.0.80` + `scipy==1.11.4` + `scikit-image==0.22.0`
  (les versions récentes de scipy/scikit-image exigent numpy≥2, incompatible
  avec paddlepaddle 2.6.2).

```bash
python3.12 -m venv .venv-paddle
.venv-paddle/bin/pip install -e ".[paddleocr]"
.venv-paddle/bin/python -m src.ocr.evaluate --engine paddleocr --lang fr --out docs/eval
```

### 2.3 Principes de sécurité (à ne pas sauter)

- Le contenu d'un document uploadé est une **entrée non fiable** : un texte
  caché dans un PDF pourrait dire "ignore les instructions précédentes".
  Le contenu du document ne doit jamais être interprété comme une
  instruction système.
- L'outil SQL de l'agent n'a que des droits `SELECT` sur des vues limitées,
  jamais d'accès en écriture ni au schéma complet.
- Isolation des données par utilisateur/entreprise (`tenant_id` sur chaque
  table).
- Aucune clé API ni mot de passe par défaut dans le dépôt ; fichier
  `.env.example` uniquement.

---

## 3. Modèle de données (PostgreSQL)

```sql
CREATE TABLE suppliers (
    id            SERIAL PRIMARY KEY,
    tenant_id     UUID NOT NULL,
    name          TEXT NOT NULL,
    ice           TEXT,
    if_number     TEXT,
    rc            TEXT,
    city          TEXT
);

CREATE TABLE documents (
    id              SERIAL PRIMARY KEY,
    tenant_id       UUID NOT NULL,
    file_path       TEXT NOT NULL,
    doc_type        TEXT CHECK (doc_type IN ('invoice','contract','report')),
    uploaded_at     TIMESTAMPTZ DEFAULT now(),
    ocr_confidence  NUMERIC
);

CREATE TABLE invoices (
    id               SERIAL PRIMARY KEY,
    document_id      INTEGER REFERENCES documents(id),
    supplier_id      INTEGER REFERENCES suppliers(id),
    invoice_number   TEXT,
    invoice_date     DATE,
    due_date         DATE,
    total_ht         NUMERIC,
    tva_rate         NUMERIC,
    total_tva        NUMERIC,
    total_ttc        NUMERIC,
    currency         TEXT DEFAULT 'MAD',
    payment_status   TEXT CHECK (payment_status IN ('paid','unpaid'))
);

CREATE TABLE invoice_lines (
    id               SERIAL PRIMARY KEY,
    invoice_id       INTEGER REFERENCES invoices(id),
    description      TEXT,
    quantity         NUMERIC,
    unit_price_ht    NUMERIC,
    total_ht         NUMERIC
);

CREATE TABLE document_chunks (
    id               SERIAL PRIMARY KEY,
    document_id      INTEGER REFERENCES documents(id),
    page_number      INTEGER,
    content          TEXT,
    embedding        VECTOR(1024)  -- si pgvector ; sinon stocké dans Qdrant/Chroma
);
```

Ce schéma correspond aux labels JSON déjà produits par le générateur de
factures synthétiques (`generate_invoices.py`), ce qui permet de calculer
directement les métriques d'extraction (comparaison valeur prédite vs valeur
du label).

---

## 4. Plan de construction, étape par étape

Chaque étape produit quelque chose de démontrable. Ne pas passer à l'étape
suivante avant que l'étape courante ait ses métriques écrites dans
`docs/eval/`.

### Étape 0 — Données (déjà fait)
- [x] Générateur de factures synthétiques marocaines (`generate_invoices.py`)
- [x] 200 factures : PDF propre + image scannée + JSON de vérité terrain
- [x] Split dev/test par fournisseur (pas de fuite de mise en page)
- [ ] Ajouter 50-100 documents publics (FATURA, ReceiptSense) pour tester la
      robustesse hors distribution — vérifier chaque licence avant usage
- [ ] Ajouter quelques documents réels anonymisés si disponibles

### Étape 1 — OCR baseline
- [x] Tesseract sur les 200 images (`--lang fra`) — arabe hors scope pour le
      moment
- [x] Calculer le CER (character error rate) contre le texte de référence
- [x] Tester PaddleOCR sur le même jeu, comparer
- [x] Livrable : tableau CER par profil de scan (clean/scan/bad) et par outil
      → `docs/eval/2026-09-22-ocr-comparison.md`

### Étape 2 — Extraction de champs
- [x] Prompt LLM structuré : texte OCR → JSON (schéma fixe : numéro, date,
      fournisseur, ICE, montants...)
- [x] Extraction de secours par regex pour les champs à format fixe (ICE 15
      chiffres, dates, montants)
- [x] Comparer champ par champ avec le label (exact match + F1)
- [x] Livrable : precision/recall par champ, dans un tableau README
      → `docs/eval/2026-09-22-extraction-baseline.md`

| Champ | Regex F1 | LLM F1 | Combiné F1 |
|---|---|---|---|
| invoice_number | 0.29 | 0.95 | 0.94 |
| invoice_date | 0.81 | 0.97 | 0.98 |
| due_date | 0.99 | 1.00 | 1.00 |
| supplier_name | 0.00 | 0.91 | 0.91 |
| supplier_ice | 0.84 | 0.88 | 0.87 |
| supplier_if | 0.77 | 0.88 | 0.88 |
| supplier_rc | 0.89 | 0.94 | 0.95 |
| total_ht | 0.59 | 0.95 | 0.95 |
| tva_rate | 0.95 | 0.95 | 0.95 |
| total_tva | 0.63 | 0.95 | 0.95 |
| total_ttc | 0.51 | 0.95 | 0.94 |

Mesuré sur les 68 factures du split `test` (jamais utilisées pour ajuster le
code), à partir de la sortie OCR Tesseract (bruitée, pas du texte propre).
Le LLM (Gemini) domine largement le regex seul (`supplier_name` : le regex ne
l'essaie même pas). Le combiné (LLM + regex en filet de secours, uniquement
quand le LLM ne trouve rien) n'apporte qu'un gain marginal — attendu, vu que
le LLM est déjà très bon sur ce jeu de données propre en structure.

### Étape 3 — Classification de documents
- [x] Baseline TF-IDF + LogisticRegression
- [x] LLM zero-shot puis few-shot (+ Jev/TypeSafe System One zero-shot et few-shot)
- [x] Comparer précision, latence, coût par document
- [x] Garder la méthode la plus adaptée
      → `docs/eval/2026-09-22-classification-baseline.md` — **Jev retenu**
      (choix produit, voir justification ci-dessous)

⚠️ Aucun contrat/rapport réel n'existait dans le projet (`data/public/` et
`data/real_anonymized/` vides, Étape 0 non complétée). Débloqué avec
`generate_docs.py` : 60 contrats + 60 rapports synthétiques en texte brut
(pas de rendu PDF/scan). **Les 5 méthodes obtiennent 100% d'accuracy** sur ce
jeu — le vocabulaire des 3 classes synthétiques est trop disjoint pour être
un test discriminant réel ; voir la limite méthodologique détaillée dans le
rapport. Un vrai test attend les documents publics/réels de l'Étape 0.

**Pourquoi Jev plutôt que TF-IDF malgré un score identique ici** : sur ce
jeu synthétique (vocabulaire trivialement disjoint entre classes), TF-IDF
gagne sur le coût/la latence, mais c'est un modèle bag-of-words qui risque
de moins bien généraliser à de vrais documents (vocabulaire administratif
qui se recoupe davantage entre facture/contrat/rapport dans la réalité).
Jev reste peu coûteux et rapide (~$0.0001/doc de cet ordre de grandeur côté
LLM comparable, latence 0.3s) tout en étant un modèle de décision entraîné
plus robuste hors distribution. À reconfirmer avec de vraies données
(Étape 0) avant de trancher définitivement.

### Étape 4 — Stockage
- [ ] Schéma PostgreSQL (section 3) + migrations (Alembic)
- [ ] Script d'ingestion : image → OCR → extraction → insertion DB
- [ ] Chunking des documents par section + indexation vectorielle

### Étape 5 — RAG
- [ ] Recherche hybride (BM25 + vecteurs) + reranker
- [ ] Génération de réponse avec citation de page
- [ ] Jeu de 50 questions/réponses de référence écrites à la main
- [ ] Évaluation RAGAS : faithfulness, answer relevancy, recall@k
- [ ] Livrable : tableau comparant vecteur seul vs hybride vs hybride+rerank

### Étape 6 — Agent et outils
- [ ] Outil `search_documents` (RAG)
- [ ] Outil `query_sql` (lecture seule, requêtes pré-validées ou générées
      puis vérifiées)
- [ ] Outil `calculate` (arithmétique exacte, jamais via le LLM)
- [ ] Tests : le bon outil est-il choisi ? le résultat est-il correct ?
- [ ] Tests d'attaque : injection de prompt dans un document, tentative
      d'accès hors tenant — documenter les résultats

### Étape 7 — API et frontend
- [ ] FastAPI : endpoints upload, liste documents, chat
- [ ] Authentification simple (JWT)
- [ ] Frontend React minimal (upload + chat + tableau des factures)

### Étape 8 — Production
- [ ] Dockerfile + docker-compose (API, DB, vector store, frontend)
- [ ] GitHub Actions : tests + lint + build image à chaque push
- [ ] Intégration Langfuse (ou équivalent) : coût, latence, traces
- [ ] Déploiement (VPS, ou Azure/GCP) + lien de démo public
- [ ] `.env.example`, jamais de secret commité

### Étape 9 — Documentation finale
- [ ] Ce README mis à jour avec tous les chiffres réels obtenus
- [ ] Section "limites connues" honnête
- [ ] GIF ou courte vidéo de démonstration

---

## 5. Ce qui rend ce projet différent d'un "chat with PDF" générique

- Champs marocains spécifiques (ICE, IF, RC, TVA, MAD) avec formats variés
  entre fournisseurs, donc extraction non triviale
- Comparaison chiffrée systématique à chaque étape (pas d'affirmation sans
  métrique)
- Séparation stricte entre ce qui doit être fait par un LLM (compréhension,
  formulation) et ce qui doit être fait par du code déterministe (calculs,
  agrégations)
- Tests de sécurité documentés (isolation multi-tenant, injection de prompt)
- Chaque étape est démontrable indépendamment : le projet reste présentable
  même arrêté en cours de route

---

## 6. Repère pour l'évaluation (à remplir au fur et à mesure)

| Étape | Métrique | Résultat |
|---|---|---|
| OCR | CER (clean / scan / bad) | Tesseract 0.22/0.24/0.52 — PaddleOCR 0.23/0.30/0.46 (voir limite méthodologique dans le rapport) |
| Extraction | F1 par champ | LLM 0.88–1.00 selon champ, regex 0.00–0.99 (voir Étape 2) |
| Classification | accuracy, coût/doc | 100% (5 méthodes) — voir limite méthodologique, Étape 3 |
| RAG | recall@5, faithfulness | à mesurer |
| Agent | taux de bon choix d'outil | à mesurer |
| Coût | $/requête moyen | à mesurer |
| Latence | p50 / p95 | à mesurer |

Ne jamais écrire une valeur ici sans l'avoir réellement calculée.

---

## 7. Structure du dépôt proposée

```
.
├── data/
│   ├── synthetic/          # sorties de generate_invoices.py
│   ├── public/              # FATURA, ReceiptSense (licences vérifiées)
│   └── real_anonymized/
├── src/
│   ├── ocr/
│   ├── extraction/
│   ├── classification/
│   ├── rag/
│   ├── agent/
│   └── api/
├── db/
│   └── migrations/
├── docs/
│   └── eval/                # résultats d'évaluation par étape
├── tests/
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

## 8. Instructions pour la suite du travail (Claude Code)

- Avancer étape par étape dans l'ordre de la section 4 ; ne pas construire
  l'agent avant que l'extraction ait des métriques correctes.
- Chaque étape doit avoir un test automatisé avant de passer à la suivante.
- Ne jamais laisser le LLM calculer un total ou une somme : toujours passer
  par SQL ou une fonction Python pure.
- Utiliser `data/synthetic/` (déjà généré) comme jeu de développement
  principal ; réserver le split `test` du `manifest.csv` pour l'évaluation
  finale de chaque étape, jamais pour ajuster le code.
- Consigner tout résultat de mesure dans `docs/eval/` au format Markdown,
  avec la date et la méthode utilisée.