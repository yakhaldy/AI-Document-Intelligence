# OCR baseline — paddleocr (`--lang fr`)

Date : 2026-09-22
Méthode : `paddleocr` (lang=fr) sur `data/synthetic/images/*.jpg`, comparé au texte extrait des PDF vectoriels (`data/synthetic/pdf/*.pdf`) via CER (`jiwer.cer`).
N = 200 factures.

## CER global : 0.3158

## CER par profil de scan

| Profil | CER moyen | N |
|---|---|---|
| bad | 0.4559 | 33 |
| clean | 0.2258 | 32 |
| scan | 0.3028 | 135 |
