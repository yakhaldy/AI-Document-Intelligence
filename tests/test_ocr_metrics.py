from src.ocr.metrics import compute_cer


def test_cer_identical_strings_is_zero():
    assert compute_cer("bonjour le monde", "bonjour le monde") == 0.0


def test_cer_one_character_deletion():
    reference = "bonjour le monde"
    hypothesis = "bonjour le mond"
    cer = compute_cer(reference, hypothesis)
    assert cer == 1 / len(reference)


def test_cer_completely_wrong_hypothesis_is_high():
    assert compute_cer("bonjour", "xxxxxxx") > 0.5
