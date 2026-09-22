from src.rag.chunking import chunk_by_section

INVOICE_TEXT = """Tafilalet Conseil SNC
72 Rue des Orangers
24000 El Jadida
FACTURE
N° : FAC/2025/00291
Date : 08/01/2025
Facturé à
Ifrane Electro SNC
91 Avenue Mohammed V
Libellé Qte Prix unitaire HT Total HT
Ordinateur portable 15,6 pouces 3 8 575,00 25 725,00
Montant HT 36 085,58 Dhs
TVA 20% 7 217,12 Dhs
Net à payer TTC 43 302,70 Dhs"""

CONTRACT_TEXT = """CONTRAT DE SOUS-TRAITANCE

ENTRE LES SOUSSIGNÉS :
Maghreb Distribution SARL, ci-après désigné « la Première Partie »,

Article 1 – Objet
Le Donneur d'ordre confie au Sous-traitant l'exécution des travaux décrits en annexe.

Article 2 – Délais d'exécution
Le Sous-traitant s'engage à exécuter les travaux dans un délai de 6 mois."""


def test_chunk_by_section_splits_on_all_caps_title():
    chunks = chunk_by_section(INVOICE_TEXT)
    assert any(c.startswith("FACTURE") for c in chunks)


def test_chunk_by_section_splits_on_facture_a_anchor():
    chunks = chunk_by_section(INVOICE_TEXT)
    assert any(c.startswith("Facturé à") for c in chunks)


def test_chunk_by_section_splits_numbered_contract_articles():
    chunks = chunk_by_section(CONTRACT_TEXT)
    article_chunks = [c for c in chunks if c.startswith("Article")]
    assert len(article_chunks) == 2
    assert article_chunks[0].startswith("Article 1")
    assert article_chunks[1].startswith("Article 2")


def test_chunk_by_section_respects_max_length_safety_valve():
    long_line = "mot " * 500  # no structure at all, single huge line
    chunks = chunk_by_section(long_line, max_chunk_chars=100)
    assert len(chunks) > 1
    assert all(len(c) <= 150 for c in chunks)  # some slack for the flush-after-exceed logic


def test_chunk_by_section_ignores_blank_lines_in_output():
    chunks = chunk_by_section(INVOICE_TEXT)
    assert all(c.strip() for c in chunks)
