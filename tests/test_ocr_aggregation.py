from src.ocr.evaluate import aggregate_by_profile


def test_aggregate_by_profile_averages_per_bucket():
    results = [
        {"scan_profile": "clean", "cer": 0.1},
        {"scan_profile": "clean", "cer": 0.3},
        {"scan_profile": "bad", "cer": 0.5},
    ]
    by_profile = aggregate_by_profile(results)
    assert by_profile == {"clean": 0.2, "bad": 0.5}


def test_aggregate_by_profile_empty_input_returns_empty_dict():
    assert aggregate_by_profile([]) == {}
