import pytest

from src.agent.calculate import calculate


def test_calculate_basic_arithmetic():
    assert calculate("2 + 3") == 5
    assert calculate("10 - 4") == 6
    assert calculate("6 * 7") == 42
    assert calculate("10 / 4") == 2.5


def test_calculate_respects_operator_precedence():
    assert calculate("2 + 3 * 4") == 14
    assert calculate("(2 + 3) * 4") == 20


def test_calculate_unary_minus():
    assert calculate("-5 + 10") == 5


def test_calculate_realistic_invoice_sum():
    assert calculate("43302.70 + 1026.00 + 8138.87") == pytest.approx(52467.57)


def test_calculate_rejects_arbitrary_code_execution():
    with pytest.raises(ValueError):
        calculate("__import__('os').system('echo pwned')")


def test_calculate_rejects_function_calls():
    with pytest.raises(ValueError):
        calculate("print(1)")


def test_calculate_division_by_zero_raises_value_error():
    with pytest.raises(ValueError):
        calculate("1 / 0")


def test_calculate_rejects_invalid_syntax():
    with pytest.raises(ValueError):
        calculate("2 +")
