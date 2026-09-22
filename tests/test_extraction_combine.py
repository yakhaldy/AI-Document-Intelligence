from src.extraction.evaluate import combine


def test_regex_fills_a_field_the_llm_missed():
    llm_pred = {"invoice_number": "FAC/1", "total_ht": None}
    regex_pred = {"invoice_number": None, "total_ht": 100.0}
    assert combine(llm_pred, regex_pred)["total_ht"] == 100.0


def test_regex_never_overrides_a_present_llm_value():
    # Regression: regex is a fallback ("secours"), not an override — an
    # earlier version let a wrong regex value replace a correct LLM value.
    llm_pred = {"invoice_number": "FAC/2025/001"}
    regex_pred = {"invoice_number": "WRONG"}
    assert combine(llm_pred, regex_pred)["invoice_number"] == "FAC/2025/001"


def test_both_null_stays_null():
    llm_pred = {"due_date": None}
    regex_pred = {"due_date": None}
    assert combine(llm_pred, regex_pred)["due_date"] is None
