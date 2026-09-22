from src.extraction.regex_extractor import IF_RE, RC_RE, extract_fields, extract_supplier_ice

SAMPLE_TEXT = """Tafilalet Conseil SNC
72 Rue des Orangers
24000 El Jadida
ICE N° : 889373467065627
Identifiant fiscal : 29806990
N° RC : 162720 El Jadida
FACTURE
N° : FAC/2025/00291
Date : 08/01/2025
À payer avant le : 07/02/2025
Facturé à
Ifrane Electro SNC
91 Avenue Mohammed V
50000 Meknès
Libellé Qte Prix unitaire HT Total HT
Ordinateur portable 15,6 pouces 3 8 575,00 25 725,00
Montant HT 36 085,58 Dhs
TVA 20% 7 217,12 Dhs
Net à payer TTC 43 302,70 Dhs
Paiement par virement ou chèque"""


def test_extract_fields_on_clean_reference_text():
    fields = extract_fields(SAMPLE_TEXT)
    assert fields == {
        "invoice_number": "FAC/2025/00291",
        "invoice_date": "2025-01-08",
        "due_date": "2025-02-07",
        "supplier_ice": "889373467065627",
        "supplier_if": "29806990",
        "supplier_rc": "162720",
        "total_ht": 36085.58,
        "tva_rate": 20,
        "total_tva": 7217.12,
        "total_ttc": 43302.70,
    }


def test_extract_fields_missing_due_date_returns_none():
    text = SAMPLE_TEXT.replace("À payer avant le : 07/02/2025\n", "")
    fields = extract_fields(text)
    assert fields["due_date"] is None
    assert fields["invoice_date"] == "2025-01-08"


def test_extract_fields_does_not_confuse_invoice_number_with_rc():
    fields = extract_fields(SAMPLE_TEXT)
    assert fields["invoice_number"] != fields["supplier_rc"]


# Regression: the customer block can also show an "ICE :" line (see
# generate_invoices.py's customer_lines()). A plain first-match search picks
# the customer's ICE here (it comes first in the text) instead of the
# supplier's, which only appears later, next to "Identifiant fiscal"/"R.C.".
CUSTOMER_AND_SUPPLIER_ICE_TEXT = """FACTURE FAC/2025/00082

Facturé à:
Ifrane Electro SNC
91 Avenue Mohammed V
50000 Meknès
ICE : 736576615654527

Libellé Qte Prix unitaire HT Total HT
Pièces détachées - lot 1 3 140,00 3 140,00
Sous-total HT 6 782,39 MAD

Souss Matériaux SARL
140 Bd Zerktouni, 50000 Meknès

ICE : 841241182449353 | Identifiant fiscal : 48740164
R.C. : 005242 Meknès"""


def test_extract_supplier_ice_ignores_customer_ice_appearing_earlier():
    assert extract_supplier_ice(CUSTOMER_AND_SUPPLIER_ICE_TEXT) == "841241182449353"


# Regression: two-column header ("Émetteur | Facturé à") interleaves OCR text
# so the customer's header ICE can sit textually CLOSER to the supplier's
# header RC than the supplier's own header ICE does. The footer trio (always
# present, see draw_footer) is the tie-breaker — it's far closer to its own
# RC/IF than any header collision is.
TWO_COLUMN_HEADER_WITH_FOOTER_TEXT = """Rif Services SARL FACTURE

Émetteur Facturé à

N° ICE : 241904966319314 Tingis Electro SA
Identifiant fiscal : 91905865 117 Avenue Hassan II
N° RC : 185067 Tétouan 11000 Salé

N° ICE : 731585149368998

Total HT 32954,10 MAD

Rif Services SARL - N° ICE : 241904966319314 - Identifiant fiscal : 91905865 - N° RC : 185067 Tétouan"""


def test_extract_supplier_ice_uses_footer_when_header_is_ambiguous():
    assert extract_supplier_ice(TWO_COLUMN_HEADER_WITH_FOOTER_TEXT) == "241904966319314"


# Regression: a trailing \b right after "I.F." / "R.C." (both end in a period,
# a non-word char) can never match — \b requires a word/non-word transition,
# and here both the period and the following space are non-word. This made
# IF_RE/RC_RE silently find nothing whenever a template used the dotted
# abbreviation, which in turn starved extract_supplier_ice of its anchor.
def test_if_re_matches_dotted_abbreviation():
    m = IF_RE.search("I.F. : 01543039")
    assert m is not None
    assert m.group(1) == "01543039"


def test_rc_re_matches_dotted_abbreviation():
    m = RC_RE.search("R.C. : 117182 Fès")
    assert m is not None
    assert m.group(1) == "117182"
