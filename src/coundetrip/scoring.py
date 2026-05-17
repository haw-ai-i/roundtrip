"""Parse test output and compute description metrics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestSummary:
    passed: int
    failed: int
    errors: int
    skipped: int
    total_reported: int

    @property
    def pass_fraction(self) -> float:
        t = self.passed + self.failed + self.errors
        if t == 0:
            return 0.0
        return self.passed / t


def parse_pytest_summary(stderr: str, stdout: str) -> TestSummary:
    """Best-effort parse of pytest last-line summary."""
    text = (stderr + "\n" + stdout).strip()
    # Typical: "===== 2 passed, 1 failed in 0.50s =====" or "2 passed in 0.01s"
    passed = failed = errors = skipped = 0
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        m_passed = re.findall(r"(\d+)\s+passed", line)
        m_failed = re.findall(r"(\d+)\s+failed", line)
        m_error = re.findall(r"(\d+)\s+error", line)
        m_errors = re.findall(r"(\d+)\s+errors", line)
        m_skipped = re.findall(r"(\d+)\s+skipped", line)
        if m_passed:
            passed = int(m_passed[-1])
        if m_failed:
            failed = int(m_failed[-1])
        if m_error:
            errors = int(m_error[-1])
        elif m_errors:
            errors = int(m_errors[-1])
        if m_skipped:
            skipped = int(m_skipped[-1])
        if "passed" in line or "failed" in line or "error" in line.lower():
            break

    total = passed + failed + errors + skipped
    return TestSummary(
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        total_reported=total,
    )


def describe_text_metrics(description_path: Path) -> dict[str, int]:
    """Word count and UTF-8 byte size for a description file."""
    text = description_path.read_text(encoding="utf-8")
    words = len(text.split())
    byte_len = len(text.encode("utf-8"))
    return {
        "word_count": words,
        "byte_size_utf8": byte_len,
    }
