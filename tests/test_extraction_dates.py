from src.extraction.dates import parse_date_token


def test_parse_date_slash_format():
    assert parse_date_token("08/01/2025") == "2025-01-08"


def test_parse_date_dash_format():
    assert parse_date_token("08-01-2025") == "2025-01-08"


def test_parse_date_long_french_format():
    assert parse_date_token("8 janvier 2025") == "2025-01-08"


def test_parse_date_long_french_format_accented_month():
    assert parse_date_token("23 février 2025") == "2025-02-23"


def test_parse_date_unrecognized_returns_none():
    assert parse_date_token("not a date") is None


def test_parse_date_invalid_month_from_ocr_noise_returns_none():
    # Regression: OCR garbling can produce an out-of-range month (e.g. 18);
    # this must not raise, just fail to extract.
    assert parse_date_token("05/18/2025") is None
