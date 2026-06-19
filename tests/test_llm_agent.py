"""Tests for the LLM-backed roundtrip agent.

The describe/regenerate machinery is exercised with deterministic clients so it
needs no API key. The full pipeline roundtrip uses replay mode, where the
"model" returns the calc source and the original tests pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from coundetrip import llm_agent
from coundetrip.llm_agent import describe, parse_file_blocks, regenerate
from coundetrip.pipeline import run_roundtrip

FIXTURES = Path(__file__).resolve().parent.parent / "benchmarks" / "fixtures"


class _FixedClient:
    def __init__(self, reply: str) -> None:
        self._reply = reply

    def complete(self, *, system: str, user: str) -> str:
        return self._reply


def test_parse_file_blocks() -> None:
    text = "preamble to ignore\n=== a.py ===\nprint(1)\n=== b/c.py ===\nx = 2\n"
    assert parse_file_blocks(text) == {"a.py": "print(1)", "b/c.py": "x = 2"}


def test_describe_writes_description(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "description.md"
    monkeypatch.setenv("COUNDETRIP_FIXTURE", str(FIXTURES / "calc"))
    monkeypatch.setenv("COUNDETRIP_DESCRIPTION", str(out))
    rc = describe(_FixedClient("a precise behavioral spec"))
    assert rc == 0
    assert out.read_text(encoding="utf-8") == "a precise behavioral spec"


def test_regenerate_keeps_scaffold_and_writes_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    desc = tmp_path / "description.md"
    desc.write_text("spec", encoding="utf-8")
    gen = tmp_path / "generated"
    monkeypatch.setenv("COUNDETRIP_DESCRIPTION", str(desc))
    monkeypatch.setenv("COUNDETRIP_WORKSPACE", str(workspace))
    monkeypatch.setenv("COUNDETRIP_GENERATED", str(gen))

    reply = "=== src/calc/__init__.py ===\ndef add(a, b):\n    return a + b\n"
    rc = regenerate(_FixedClient(reply))
    assert rc == 0
    assert (gen / "pyproject.toml").is_file()  # scaffold preserved
    assert "def add" in (gen / "src" / "calc" / "__init__.py").read_text(encoding="utf-8")


def test_roundtrip_with_replay_passes_oracle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end through the pipeline: replayed source must pass the original tests."""
    # Build a replay dir: describe -> any spec; regenerate -> the real calc source.
    replay = tmp_path / "replay"
    replay.mkdir()
    (replay / "describe.txt").write_text("a spec", encoding="utf-8")
    src_file = FIXTURES / "calc" / "src" / "calc" / "__init__.py"
    rendered = f"=== src/calc/__init__.py ===\n{src_file.read_text(encoding='utf-8')}"
    (replay / "regenerate.txt").write_text(rendered, encoding="utf-8")
    monkeypatch.setenv("COUNDETRIP_REPLAY_DIR", str(replay))

    report = run_roundtrip(
        fixture_path=FIXTURES / "calc",
        agent_cmd=[sys.executable, "-m", "coundetrip.llm_agent"],
        runs_dir=tmp_path / "runs",
        run_id="replay_calc",
    )
    assert report["success"] is True
    assert report["score"]["tests"]["passed"] >= 2


# --- GeminiClient: verified with a fake SDK client (no real API call) ---


class _FakeUsage:
    def __init__(self, prompt_tokens: int, output_tokens: int) -> None:
        self.prompt_token_count = prompt_tokens
        self.candidates_token_count = output_tokens


class _FakeResponse:
    def __init__(self, text: str, usage: _FakeUsage) -> None:
        self.text = text
        self.usage_metadata = usage


class _FakeModels:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.calls: list[dict] = []

    def generate_content(self, *, model: str, contents: str, config: dict) -> _FakeResponse:
        self.calls.append({"model": model, "contents": contents, "config": config})
        return self._response


class _FakeGenAIClient:
    def __init__(self, response: _FakeResponse) -> None:
        self.models = _FakeModels(response)


def test_gemini_client_returns_text_and_tallies_usage() -> None:
    fake = _FakeGenAIClient(_FakeResponse("=== a.py ===\nx = 1\n", _FakeUsage(120, 40)))
    client = llm_agent.GeminiClient(model="gemini-3.5-flash", client=fake)

    out = client.complete(system="SYS", user="USR")

    assert out == "=== a.py ===\nx = 1\n"
    assert client.usage == {"calls": 1, "prompt_tokens": 120, "output_tokens": 40}
    # model and system instruction are threaded through to the SDK
    sent = fake.models.calls[0]
    assert sent["model"] == "gemini-3.5-flash"
    assert sent["contents"] == "USR"
    assert sent["config"]["system_instruction"] == "SYS"
    assert sent["config"]["temperature"] == 0.0


def test_gemini_client_usage_accumulates_across_calls() -> None:
    fake = _FakeGenAIClient(_FakeResponse("ok", _FakeUsage(10, 5)))
    client = llm_agent.GeminiClient(client=fake)

    client.complete(system="s", user="u")
    client.complete(system="s", user="u")

    assert client.usage == {"calls": 2, "prompt_tokens": 20, "output_tokens": 10}