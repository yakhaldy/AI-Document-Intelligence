"""Parse the date renderings used by generate_invoices.py into ISO strings."""
import re
from datetime import date

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre",
]

NUMERIC_DATE_RE = re.compile(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})")
LONG_DATE_RE = re.compile(r"(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})")


def parse_date_token(token: str) -> str | None:
    token = token.strip()
    m = NUMERIC_DATE_RE.match(token)
    if m:
        day, month, year = (int(x) for x in m.groups())
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None
    m = LONG_DATE_RE.match(token)
    if m:
        day, month_name, year = m.groups()
        month_name = month_name.lower()
        if month_name not in MONTHS_FR:
            return None
        month = MONTHS_FR.index(month_name) + 1
        try:
            return date(int(year), month, int(day)).isoformat()
        except ValueError:
            return None
    return None
