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
| Classification | TF-IDF + LogisticRegression **et** LLM zero-shot | comparer, garder le meilleur rapport coût/précision |
| RAG | embeddings multilingues (type BGE-M3 / multilingual-e5) + BM25 hybride + reranker | chunking par section, pas par nombre de caractères fixe |
| Vector DB | ChromaDB (dev) → Qdrant (prod) | |
| Base relationnelle | PostgreSQL | champs extraits + statut de paiement |
| Agent | function calling (outils : search_documents, query_sql, calculate) | SQL toujours en lecture seule |
| Observabilité | Langfuse ou équivalent open source | coût, latence, traces |
| Évaluation | jeu de test annoté à la main + RAGAS | seule mesure fiable de qualité |
| Conteneurisation | Docker + docker-compose | |
| CI/CD | GitHub Actions | tests automatiques + build image |
| Frontend | React (minimal : upload, chat, tableau de bord) | pas la priorité |

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
- [] 200 factures : PDF propre + image scannée + JSON de vérité terrain
- [] Split dev/test par fournisseur (pas de fuite de mise en page)
- [ ] Ajouter 50-100 documents publics (FATURA, ReceiptSense) pour tester la
      robustesse hors distribution — vérifier chaque licence avant usage
- [ ] Ajouter quelques documents réels anonymisés si disponibles

### Étape 1 — OCR baseline
- [ ] Tesseract sur les 200 images (`--lang fra` puis `--lang fra+ara` sur un
      sous-ensemble bilingue)
- [ ] Calculer le CER (character error rate) contre le texte de référence
- [ ] Tester PaddleOCR sur le même jeu, comparer
- [ ] Livrable : tableau CER par profil de scan (clean/scan/bad) et par outil

### Étape 2 — Extraction de champs
- [ ] Prompt LLM structuré : texte OCR → JSON (schéma fixe : numéro, date,
      fournisseur, ICE, montants...)
- [ ] Extraction de secours par regex pour les champs à format fixe (ICE 15
      chiffres, dates, montants)
- [ ] Comparer champ par champ avec le label (exact match + F1)
- [ ] Livrable : precision/recall par champ, dans un tableau README

### Étape 3 — Classification de documents
- [ ] Baseline TF-IDF + LogisticRegression
- [ ] LLM zero-shot puis few-shot
- [ ] Comparer précision, latence, coût par document
- [ ] Garder la méthode la plus adaptée (probablement TF-IDF pour ce cas,
      documenter pourquoi)

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
| OCR | CER (clean / scan / bad) | à mesurer |
| Extraction | F1 par champ | à mesurer |
| Classification | accuracy, coût/doc | à mesurer |
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