from expr import evaluate

import pytest


def test_basic_arithmetic():
    assert evaluate("2 + 3") == 5
    assert evaluate("10 - 4") == 6
    assert evaluate("6 * 7") == 42


def test_precedence():
    assert evaluate("2 + 3 * 4") == 14
    assert evaluate("2 * 3 + 4") == 10


def test_parentheses_override_precedence():
    assert evaluate("(2 + 3) * 4") == 20
    assert evaluate("2 * (3 + 4)") == 14


def test_left_associativity():
    assert evaluate("100 - 10 - 5") == 85
    # (64 / 4) / 2 == 8.0, not 64 / (4 / 2) == 32.0
    assert evaluate("64 / 4 / 2") == 8.0


def test_unary_minus():
    assert evaluate("-5") == -5
    assert evaluate("3 * -2") == -6
    assert evaluate("-(2 + 3)") == -5
    assert evaluate("--3") == 3


def test_division_always_returns_float():
    result = evaluate("8 / 2")
    assert result == 4.0
    assert isinstance(result, float)
    assert evaluate("7 / 2") == 3.5


def test_integer_operations_return_int():
    assert isinstance(evaluate("2 + 3"), int)
    assert isinstance(evaluate("4 * 5"), int)
    assert isinstance(evaluate("9 - 1"), int)


def test_float_literals():
    assert evaluate("1.5 + 2.5") == 4.0
    assert evaluate("3.0 * 2") == 6.0


def test_whitespace_is_ignored():
    assert evaluate("  2+2  ") == 4
    assert evaluate("2*3+4") == 10


def test_division_by_zero_raises_zero_division_error():
    with pytest.raises(ZeroDivisionError):
        evaluate("1 / 0")


def test_malformed_input_raises_value_error():
    for bad in ["", "2 +", "(2 + 3", "2 3", "2 @ 3", "* 5"]:
        with pytest.raises(ValueError):
            evaluate(bad)
