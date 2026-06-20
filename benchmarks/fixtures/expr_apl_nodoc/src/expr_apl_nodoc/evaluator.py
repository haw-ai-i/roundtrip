"""Implementation of the arithmetic expression evaluator.

Supports ``+``, ``-``, ``*``, ``/``, parentheses, and unary minus over integer
and floating-point literals. The implementation is a hand-written
recursive-descent parser; malformed input is rejected rather than guessed at.
"""

from __future__ import annotations


def evaluate(expression: str) -> int | float:
    """Evaluate ``expression`` and return its numeric value.

    Integer-only ``+``, ``-`` and ``*`` keep integer results; ``/`` performs
    true division and so always yields a float. Raises ``ValueError`` for
    malformed input and propagates ``ZeroDivisionError`` for division by zero.
    """
    tokens = _tokenize(expression)
    if not tokens:
        raise ValueError("empty expression")
    parser = _Parser(tokens)
    value = parser.parse_expr()
    parser.expect_end()
    return value


def _tokenize(expression: str) -> list[tuple[str, object]]:
    tokens: list[tuple[str, object]] = []
    i = 0
    n = len(expression)
    while i < n:
        c = expression[i]
        if c.isspace():
            i += 1
            continue
        if c in "+-*/()":
            tokens.append((c, c))
            i += 1
            continue
        if c.isdigit() or c == ".":
            j = i
            seen_dot = False
            while j < n and (expression[j].isdigit() or expression[j] == "."):
                if expression[j] == ".":
                    if seen_dot:
                        raise ValueError(f"malformed number at position {i}")
                    seen_dot = True
                j += 1
            literal = expression[i:j]
            if literal == ".":
                raise ValueError(f"malformed number at position {i}")
            tokens.append(("num", float(literal) if seen_dot else int(literal)))
            i = j
            continue
        raise ValueError(f"invalid character {c!r} at position {i}")
    return tokens


class _Parser:
    def __init__(self, tokens: list[tuple[str, object]]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> tuple[str | None, object]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return (None, None)

    def _advance(self) -> tuple[str, object]:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok  # type: ignore[return-value]

    def parse_expr(self) -> int | float:
        left = self.parse_factor()
        if self._peek()[0] in ("+", "-", "*", "/"):
            op, _ = self._advance()
            right = self.parse_expr()
            return _apply(op, left, right)
        return left

    def parse_factor(self) -> int | float:
        kind, val = self._peek()
        if kind == "-":
            self._advance()
            return -self.parse_factor()
        if kind == "(":
            self._advance()
            value = self.parse_expr()
            if self._peek()[0] != ")":
                raise ValueError("expected ')'")
            self._advance()
            return value
        if kind == "num":
            self._advance()
            return val  # type: ignore[return-value]
        raise ValueError("expected a number or '('")

    def expect_end(self) -> None:
        if self._pos != len(self._tokens):
            raise ValueError("unexpected trailing input")


def _apply(op: str, a: int | float, b: int | float) -> int | float:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    return a / b
