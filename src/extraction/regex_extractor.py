"""Regex-based "secours" extractor for the fixed-format fields.

Targets only the fields with a rigid, non-freeform shape (identifiers, dates,
amounts) — everything else (supplier name, line items) is left to the LLM
extractor. See docs/eval for the field-by-field precision/recall this gets.
"""
import re

from src.extraction.amounts import AMOUNT_TOKEN_RE, parse_amount
from src.extraction.dates import LONG_DATE_RE, NUMERIC_DATE_RE, parse_date_token

DATE_TOKEN = rf"(?:{NUMERIC_DATE_RE.pattern}|{LONG_DATE_RE.pattern})"

ICE_RE = re.compile(r"ICE\b[^\d]{0,15}(\d{15})", re.IGNORECASE)
IF_RE = re.compile(r"\b(?:Identifiant fiscal|I\.F\.|IF)\s*:?\s*(\d{5,10})", re.IGNORECASE)
RC_RE = re.compile(r"\b(?:N°\s*RC|R\.C\.|RC)\s*:?\s*(\d{4,8})", re.IGNORECASE)

INVOICE_DATE_RE = re.compile(rf"\bDate\s*:\s*({DATE_TOKEN})", re.IGNORECASE)
DUE_DATE_RE = re.compile(
    rf"(?:Échéance|Date d'échéance|À payer avant le)\s*:?\s*({DATE_TOKEN})",
    re.IGNORECASE,
)

HT_RE = re.compile(
    rf"(?:Total HT|Montant HT|Sous-total HT)\s*:?\s*({AMOUNT_TOKEN_RE.pattern})",
    re.IGNORECASE,
)
TVA_RATE_RE = re.compile(r"TVA\s*\(?\s*(\d{1,2})\s*%", re.IGNORECASE)
TVA_AMOUNT_RE = re.compile(
    rf"TVA\s*\(?\s*\d{{1,2}}\s*%\)?\s*:?\s*({AMOUNT_TOKEN_RE.pattern})",
    re.IGNORECASE,
)
TTC_RE = re.compile(
    rf"(?:Total TTC|Net à payer TTC|Montant TTC)\s*:?\s*({AMOUNT_TOKEN_RE.pattern})",
    re.IGNORECASE,
)

INVOICE_NUMBER_RE = re.compile(
    r"(?:N°|Réf)\s*:?\s*([A-Za-z0-9][A-Za-z0-9/\-]{2,20})", re.IGNORECASE
)


def _first_match(pattern, text):
    m = pattern.search(text)
    return m.group(1) if m else None


def extract_supplier_ice(text: str) -> str | None:
    # The customer block can also show an "ICE :" line (see
    # generate_invoices.py's customer_lines()), so a plain first-match search
    # sometimes grabs the customer's ICE instead of the supplier's. IF/RC
    # never appear on the customer block, and the footer always reprints the
    # supplier's ICE tightly clustered with its IF/RC (draw_footer). So: take
    # every IF/RC occurrence as an anchor (header AND footer), and pick
    # whichever ICE match sits closest to ANY of them — a two-column layout
    # can put a header customer-ICE deceptively close to a header RC, but the
    # footer trio is always far closer to its own RC/IF than that is.
    ice_matches = list(ICE_RE.finditer(text))
    if not ice_matches:
        return None
    anchors = list(RC_RE.finditer(text)) + list(IF_RE.finditer(text))
    if not anchors:
        return ice_matches[0].group(1)
    closest = min(
        ice_matches,
        key=lambda ice: min(abs(ice.start() - a.start()) for a in anchors),
    )
    return closest.group(1)


def extract_invoice_number(text: str) -> str | None:
    for line in text.splitlines():
        if "RC" in line or "ICE" in line:
            continue
        m = INVOICE_NUMBER_RE.search(line)
        if m:
            return m.group(1)
    return None


def extract_fields(text: str) -> dict:
    invoice_date_token = _first_match(INVOICE_DATE_RE, text)
    due_date_token = _first_match(DUE_DATE_RE, text)
    ht_token = _first_match(HT_RE, text)
    tva_amount_token = _first_match(TVA_AMOUNT_RE, text)
    ttc_token = _first_match(TTC_RE, text)
    tva_rate_token = _first_match(TVA_RATE_RE, text)

    return {
        "invoice_number": extract_invoice_number(text),
        "invoice_date": parse_date_token(invoice_date_token) if invoice_date_token else None,
        "due_date": parse_date_token(due_date_token) if due_date_token else None,
        "supplier_ice": extract_supplier_ice(text),
        "supplier_if": _first_match(IF_RE, text),
        "supplier_rc": _first_match(RC_RE, text),
        "total_ht": parse_amount(ht_token) if ht_token else None,
        "tva_rate": int(tva_rate_token) if tva_rate_token else None,
        "total_tva": parse_amount(tva_amount_token) if tva_amount_token else None,
        "total_ttc": parse_amount(ttc_token) if ttc_token else None,
    }
