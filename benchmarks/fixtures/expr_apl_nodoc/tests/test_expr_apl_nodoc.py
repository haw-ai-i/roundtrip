from expr_apl_nodoc import evaluate

import pytest


def test_single_operations():
    assert evaluate("2 + 3") == 5
    assert evaluate("10 - 4") == 6
    assert evaluate("6 * 7") == 42


def test_no_operator_precedence():
    # All operators have equal precedence and evaluate right-to-left.
    assert evaluate("2 * 3 + 4") == 14   # 2 * (3 + 4), not (2 * 3) + 4 == 10
    assert evaluate("2 - 3 + 4") == -5   # 2 - (3 + 4), not (2 - 3) + 4 == 3


def test_right_associativity():
    assert evaluate("100 - 10 - 5") == 95   # 100 - (10 - 5), not 85
    assert evaluate("16 / 4 / 2") == 8.0    # 16 / (4 / 2), not 2.0


def test_parentheses_override_evaluation_order():
    assert evaluate("(2 - 3) + 4") == 3     # parens force left grouping; without them it's -5
    assert evaluate("2 * (3 + 4)") == 14


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
    assert evaluate("6/3") == 2.0


def test_division_by_zero_raises_zero_division_error():
    with pytest.raises(ZeroDivisionError):
        evaluate("1 / 0")


def test_malformed_input_raises_value_error():
    for bad in ["", "2 +", "(2 + 3", "2 3", "2 @ 3", "* 5"]:
        with pytest.raises(ValueError):
            evaluate(bad)
