# Comparatif OCR — CER par profil de scan et par outil

Date : 2026-09-22

| Outil | N | clean | scan | bad | Global |
|---|---|---|---|---|---|
| tesseract (`fra`) | 200 | 0.2172 | 0.2432 | 0.5215 | 0.2850 |
| paddleocr (`fr`) | 200 | 0.2258 | 0.3028 | 0.4559 | 0.3158 |

## Lecture des résultats

- Tesseract est légèrement meilleur en moyenne globale (0.2850 vs 0.3158), mais
  PaddleOCR est meilleur sur les scans dégradés (`bad` : 0.4559 vs 0.5215) —
  cohérent avec sa réputation de plus grande robustesse au bruit/flou.
- Aucun des deux n'est retenu comme définitif à ce stade : ce sont des
  baselines brutes, sans prétraitement d'image (débruitage, redressement,
  binarisation).

## Limite méthodologique connue

Le CER est calculé caractère par caractère entre le texte OCR et le texte de
référence extrait du PDF. Le texte de référence suit l'ordre de rendu du PDF
(colonnes), tandis que la sortie OCR suit l'ordre de détection des boîtes de
texte — ces deux ordres ne coïncident pas toujours sur les factures à deux
colonnes (ex. bloc fournisseur à gauche / bloc facture à droite). Une partie
du CER mesuré vient donc de ces décalages d'ordre plutôt que d'erreurs de
reconnaissance pures. Ce biais affecte les deux outils de la même façon (même
méthode de comparaison), donc **la comparaison relative reste valide**, mais
le CER absolu est probablement surestimé pour les deux. À corriger avant
l'étape d'extraction (Étape 2) si on veut un chiffre de CER absolu fiable —
par exemple en normalisant l'ordre des lignes ou en comparant par bloc plutôt
que sur le texte concaténé.
