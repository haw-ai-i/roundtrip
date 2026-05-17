"""Tests for pytest summary parsing and description metrics."""

from __future__ import annotations

from pathlib import Path

from coundetrip.scoring import describe_text_metrics, parse_pytest_summary


def test_parse_pytest_all_passed() -> None:
    out = "....                                                                   [100%]\n2 passed in 0.01s\n"
    s = parse_pytest_summary("", out)
    assert s.passed == 2
    assert s.failed == 0
    assert s.pass_fraction == 1.0


def test_parse_pytest_mixed() -> None:
    err = "\n=========================== short test summary info ============================\nFAILED tests/test_x.py::test_a\n========================= 1 failed, 2 passed in 0.50s ==========================\n"
    s = parse_pytest_summary(err, "")
    assert s.passed == 2
    assert s.failed == 1
    assert abs(s.pass_fraction - 2 / 3) < 1e-9


def test_describe_text_metrics(tmp_path: Path) -> None:
    p = tmp_path / "d.md"
    p.write_text("hello world three", encoding="utf-8")
    m = describe_text_metrics(p)
    assert m["word_count"] == 3
    assert m["byte_size_utf8"] == len("hello world three".encode("utf-8"))
