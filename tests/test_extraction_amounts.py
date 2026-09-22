from src.extraction.amounts import AMOUNT_TOKEN_RE, parse_amount


def test_parse_amount_default_style_dot_decimal():
    assert parse_amount("36,085.58") == 36085.58


def test_parse_amount_fr_style_space_thousands_comma_decimal():
    assert parse_amount("36 085,58") == 36085.58


def test_parse_amount_plain_style_comma_decimal_no_thousands():
    assert parse_amount("36085,58") == 36085.58


def test_parse_amount_small_value_no_thousands_separator():
    assert parse_amount("1 365,00") == 1365.00


def test_amount_token_does_not_run_on_across_two_adjacent_amounts():
    # Regression: an earlier greedy pattern let two OCR-merged amounts
    # (no separator between them) collapse into a single bogus token.
    merged = "48993.3035973.20"
    match = AMOUNT_TOKEN_RE.search(merged)
    assert match.group(0) == "48993.30"


def test_amount_token_stops_before_unrelated_trailing_text():
    match = AMOUNT_TOKEN_RE.search("36 085,58 Dhs")
    assert match.group(0) == "36 085,58"
