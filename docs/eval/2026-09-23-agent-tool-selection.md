# Agent — sélection d'outil, exactitude, coût et latence

Date : 2026-09-23
N = 7 questions (mêmes questions que l'évaluation initiale du 2026-09-22, ré-exécutées pour mesurer coût/latence réels).

**Bon outil choisi : 86%**  |  **Réponse correcte : 100%**
**Latence p50 : 2.25s**  |  **Latence p95 : 2.83s**
**Coût total : $0.001133**  |  **Coût moyen/requête : $0.000162**

| Question | Outil attendu | Outils appelés | Outil OK | Réponse OK | Latence (s) | Coût ($) |
|---|---|---|---|---|---|---|
| Quel est le montant total des factures impayées ? | total_by_payment_status | total_by_payment_status | ✓ | ✓ | 2.84 | 0.000151 |
| Quel est le montant total des factures payées ? | total_by_payment_status | total_by_payment_status | ✓ | ✓ | 2.82 | 0.000149 |
| Combien de factures sont impayées ? | count_by_payment_status | count_by_payment_status | ✓ | ✓ | 1.58 | 0.000144 |
| Quels sont les 2 fournisseurs auxquels on doit le plus au total ? | top_suppliers_by_total | top_suppliers_by_total | ✓ | ✓ | 1.89 | 0.000172 |
| Quel est le montant TTC de la facture FA-000089 ? | invoice_lookup | invoice_lookup | ✓ | ✓ | 2.70 | 0.000168 |
| Combien font 43302.70 plus 1026.00 plus 8138.87 ? | calculate | calculate | ✓ | ✓ | 2.25 | 0.000165 |
| Quelle est l'adresse du fournisseur sur la facture FAC/2025/00291 ? | search_documents | invoice_lookup | ✗ | ✓ | 2.15 | 0.000183 |

**Quel est le montant total des factures impayées ?**
> Le montant total des factures impayées est de 1 542 744,82 MAD.

**Quel est le montant total des factures payées ?**
> Le montant total des factures payées est de 4 634 305,27 MAD.

**Combien de factures sont impayées ?**
> Il y a 40 factures impayées.

**Quels sont les 2 fournisseurs auxquels on doit le plus au total ?**
> Les deux fournisseurs auxquels on doit le plus au total sont :

1. **Tafilalet Conseil SNC** : 606228.63 MAD
2. **Doukkala Hygiène SNC** : 545901.09 MAD

**Quel est le montant TTC de la facture FA-000089 ?**
> Le montant TTC de la facture FA-000089 est de 1026 MAD.

**Combien font 43302.70 plus 1026.00 plus 8138.87 ?**
> La somme de 43302.70, 1026.00 et 8138.87 est de 52467.57.

**Quelle est l'adresse du fournisseur sur la facture FAC/2025/00291 ?**
> L'adresse du fournisseur "Tafilalet Conseil SNC" sur la facture FAC/2025/00291 n'est pas spécifiée dans les informations disponibles.
