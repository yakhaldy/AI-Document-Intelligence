# Extraction de champs — regex vs LLM vs combiné

Date : 2026-09-22
N = 68 factures (split `test` uniquement, texte = sortie OCR Tesseract).
Combiné = sortie LLM, champs remplacés par le regex quand celui-ci trouve une valeur (regex "de secours" sur les champs à format fixe).

⚠️ 1 appel(s) LLM en échec (voir _raw/extraction-llm.json, valeurs null).

## regex

| Champ | Précision | Rappel | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| invoice_number | 0.43 | 0.22 | 0.29 | 15 | 20 | 53 |
| invoice_date | 1.00 | 0.68 | 0.81 | 46 | 0 | 22 |
| due_date | 1.00 | 0.97 | 0.99 | 33 | 0 | 1 |
| supplier_name | 1.00 | 0.00 | 0.00 | 0 | 0 | 68 |
| supplier_ice | 0.86 | 0.82 | 0.84 | 56 | 9 | 12 |
| supplier_if | 0.98 | 0.63 | 0.77 | 43 | 1 | 25 |
| supplier_rc | 0.98 | 0.81 | 0.89 | 55 | 1 | 13 |
| total_ht | 0.94 | 0.43 | 0.59 | 29 | 2 | 39 |
| tva_rate | 1.00 | 0.91 | 0.95 | 62 | 0 | 6 |
| total_tva | 0.97 | 0.47 | 0.63 | 32 | 1 | 36 |
| total_ttc | 0.57 | 0.46 | 0.51 | 31 | 23 | 37 |

## llm

| Champ | Précision | Rappel | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| invoice_number | 0.97 | 0.93 | 0.95 | 63 | 2 | 5 |
| invoice_date | 1.00 | 0.94 | 0.97 | 64 | 0 | 4 |
| due_date | 1.00 | 1.00 | 1.00 | 34 | 0 | 0 |
| supplier_name | 0.95 | 0.87 | 0.91 | 59 | 3 | 9 |
| supplier_ice | 0.93 | 0.84 | 0.88 | 57 | 4 | 11 |
| supplier_if | 0.98 | 0.79 | 0.88 | 54 | 1 | 14 |
| supplier_rc | 1.00 | 0.88 | 0.94 | 60 | 0 | 8 |
| total_ht | 1.00 | 0.91 | 0.95 | 62 | 0 | 6 |
| tva_rate | 1.00 | 0.90 | 0.95 | 61 | 0 | 7 |
| total_tva | 1.00 | 0.90 | 0.95 | 61 | 0 | 7 |
| total_ttc | 1.00 | 0.90 | 0.95 | 61 | 0 | 7 |

## combined

| Champ | Précision | Rappel | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| invoice_number | 0.95 | 0.93 | 0.94 | 63 | 3 | 5 |
| invoice_date | 1.00 | 0.96 | 0.98 | 65 | 0 | 3 |
| due_date | 1.00 | 1.00 | 1.00 | 34 | 0 | 0 |
| supplier_name | 0.95 | 0.87 | 0.91 | 59 | 3 | 9 |
| supplier_ice | 0.89 | 0.85 | 0.87 | 58 | 7 | 10 |
| supplier_if | 0.98 | 0.79 | 0.88 | 54 | 1 | 14 |
| supplier_rc | 1.00 | 0.90 | 0.95 | 61 | 0 | 7 |
| total_ht | 1.00 | 0.91 | 0.95 | 62 | 0 | 6 |
| tva_rate | 1.00 | 0.91 | 0.95 | 62 | 0 | 6 |
| total_tva | 1.00 | 0.90 | 0.95 | 61 | 0 | 7 |
| total_ttc | 0.98 | 0.90 | 0.94 | 61 | 1 | 7 |
