# Agent — sélection d'outil et exactitude des réponses

Date : 2026-09-22
N = 7 questions.

**Bon outil choisi : 86%**  |  **Réponse correcte : 100%**

| Question | Outil attendu | Outils appelés | Outil OK | Réponse OK |
|---|---|---|---|---|
| Quel est le montant total des factures impayées ? | total_by_payment_status | total_by_payment_status | ✓ | ✓ |
| Quel est le montant total des factures payées ? | total_by_payment_status | total_by_payment_status | ✓ | ✓ |
| Combien de factures sont impayées ? | count_by_payment_status | count_by_payment_status | ✓ | ✓ |
| Quels sont les 2 fournisseurs auxquels on doit le plus au total ? | top_suppliers_by_total | top_suppliers_by_total | ✓ | ✓ |
| Quel est le montant TTC de la facture FA-000089 ? | invoice_lookup | invoice_lookup | ✓ | ✓ |
| Combien font 43302.70 plus 1026.00 plus 8138.87 ? | calculate | calculate | ✓ | ✓ |
| Quelle est l'adresse du fournisseur sur la facture FAC/2025/00291 ? | search_documents | invoice_lookup | ✗ | ✓ |

**Quel est le montant total des factures impayées ?**
> Le montant total des factures impayées est de 1 542 744,82 MAD.

**Quel est le montant total des factures payées ?**
> Le montant total des factures payées est de 4 634 305,27 MAD.

**Combien de factures sont impayées ?**
> Il y a 40 factures impayées.

**Quels sont les 2 fournisseurs auxquels on doit le plus au total ?**
> Les deux fournisseurs auxquels on doit le plus au total sont :

1. **Doukkala Hygiène SNC** : 545 901,09 MAD
2. **Tafilalet Conseil SNC** : 481 365,11 MAD

**Quel est le montant TTC de la facture FA-000089 ?**
> Le montant TTC de la facture FA-000089 est de 1026 MAD.

**Combien font 43302.70 plus 1026.00 plus 8138.87 ?**
> La somme de 43302.70, 1026.00 et 8138.87 est de 52467.57.

**Quelle est l'adresse du fournisseur sur la facture FAC/2025/00291 ?**
> L'adresse du fournisseur "Tafilalet Conseil SNC" sur la facture FAC/2025/00291 n'est pas spécifiée dans les informations disponibles.
