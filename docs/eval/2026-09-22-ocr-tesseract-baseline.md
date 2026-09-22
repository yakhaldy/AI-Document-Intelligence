# OCR baseline — Tesseract (`--lang fra`)

Date : 2026-09-22
Méthode : `tesseract --lang fra` sur `data/synthetic/images/*.jpg`, comparé au texte extrait des PDF vectoriels (`data/synthetic/pdf/*.pdf`) via CER (`jiwer.cer`).
N = 200 factures.

## CER global : 0.2850

## CER par profil de scan

| Profil | CER moyen | N |
|---|---|---|
| bad | 0.5215 | 33 |
| clean | 0.2172 | 32 |
| scan | 0.2432 | 135 |
