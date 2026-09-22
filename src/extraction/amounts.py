"""Parse Moroccan-invoice amount strings into floats.

Three renderings appear in the synthetic data: "36,085.58" (dot decimal),
"36 085,58" (space thousands, comma decimal), "36085,58" (comma decimal,
no thousands separator). All three are disambiguated by taking whichever
of the last "," or "." is the decimal separator.
"""
import re

AMOUNT_TOKEN_RE = re.compile(r"\d{1,3}(?:[ ,]\d{3})+[.,]\d{2}|\d+[.,]\d{2}")


def parse_amount(token: str) -> float:
    token = token.strip()
    last_comma = token.rfind(",")
    last_dot = token.rfind(".")
    if last_comma > last_dot:
        decimal_sep, thousand_seps = ",", (".", " ")
    else:
        decimal_sep, thousand_seps = ".", (",", " ")
    for sep in thousand_seps:
        token = token.replace(sep, "")
    token = token.replace(decimal_sep, ".")
    return float(token)
