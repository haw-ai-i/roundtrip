"""LLM-backed roundtrip agent: describe (source -> NL) and regenerate (NL -> code).

Uses the same environment-variable contract as the stub agent (COUNDETRIP_STAGE,
COUNDETRIP_FIXTURE, COUNDETRIP_DESCRIPTION, COUNDETRIP_WORKSPACE,
COUNDETRIP_GENERATED). The model is reached through a small ``LLMClient``
interface so the describe/regenerate logic can be exercised deterministically;
the concrete provider client is added once an API key is available.

``ReplayClient`` returns canned responses from a directory (``<stage>.txt``),
which gives deterministic, offline runs -- useful for reproducibility and tests
without calling a live model. Set COUNDETRIP_REPLAY_DIR to enable it.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Protocol

from coundetrip.manifest import list_source_files, load_manifest


class LLMClient(Protocol):
    """Minimal text-in/text-out model interface."""

    def complete(self, *, system: str, user: str) -> str:
        ...


class ReplayClient:
    """Return a canned response read from ``<replay_dir>/<stage>.txt``.

    Enables deterministic, offline roundtrips (no live model call). The stage is
    taken from COUNDETRIP_STAGE so one client serves both describe and regenerate.
    """

    def __init__(self, replay_dir: Path) -> None:
        self._dir = replay_dir

    def complete(self, *, system: str, user: str) -> str:
        stage = os.environ.get("COUNDETRIP_STAGE", "")
        return (self._dir / f"{stage}.txt").read_text(encoding="utf-8")


def _is_retryable(exc: Exception) -> bool:
    """True for transient server-side errors worth retrying with backoff.

    Covers HTTP 429 (rate limit) and 5xx (e.g. 503 UNAVAILABLE "high demand"),
    detected via a status attribute when present and otherwise by message text.
    """
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code in (429, 500, 502, 503, 504):
        return True
    msg = str(exc).lower()
    return any(
        s in msg
        for s in (
            "unavailable",
            "overloaded",
            "high demand",
            "try again later",
            "internal error",
            "deadline exceeded",
        )
    )


class GeminiClient:
    """Live client for the Google Gemini API via the ``google-genai`` SDK.

    The API key is read from the ``GEMINI_API_KEY`` environment variable by the
    SDK (so it works the same on the host and inside a container where the key is
    forwarded). ``temperature=0`` keeps generations as deterministic as the model
    allows, which matters for a reproducible benchmark. Token usage is tallied on
    ``self.usage`` so the caller can account for cost.

    A pre-built ``client`` may be injected for testing.
    """

    def __init__(
        self,
        model: str = "gemini-3.5-flash",
        *,
        api_key: str | None = None,
        temperature: float = 0.0,
        max_retries: int = 6,
        retry_backoff: float = 2.0,
        client: object | None = None,
    ) -> None:
        if client is None:
            from google import genai  # imported lazily so the SDK is optional

            client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self._client = client
        self._model = model
        self._temperature = temperature
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
        self.usage = {"calls": 0, "prompt_tokens": 0, "output_tokens": 0}
        self.last_finish_reason = None

    def complete(self, *, system: str, user: str) -> str:
        if "gemma" in self._model.lower():
            # Gemma models have no system role; fold the system prompt into the
            # user turn instead of passing it as a system instruction.
            contents = f"{system}\n\n{user}"
            config = {"temperature": self._temperature}
        else:
            contents = user
            config = {"system_instruction": system, "temperature": self._temperature}
        resp = None
        for attempt in range(self._max_retries):
            try:
                resp = self._client.models.generate_content(
                    model=self._model,
                    contents=contents,
                    config=config,
                )
                break
            except Exception as exc:  # noqa: BLE001 - retry transient server errors
                if attempt < self._max_retries - 1 and _is_retryable(exc):
                    time.sleep(min(self._retry_backoff * (2 ** attempt), 30.0))
                    continue
                raise
        um = getattr(resp, "usage_metadata", None)
        if um is not None:
            self.usage["prompt_tokens"] += getattr(um, "prompt_token_count", 0) or 0
            self.usage["output_tokens"] += getattr(um, "candidates_token_count", 0) or 0
        self.usage["calls"] += 1
        text = resp.text or ""
        reason = None
        try:
            cand = (resp.candidates or [None])[0]
            reason = getattr(cand, "finish_reason", None)
        except Exception:  # noqa: BLE001 - diagnostics only
            reason = None
        self.last_finish_reason = reason
        if not text:
            feedback = getattr(resp, "prompt_feedback", None)
            sys.stderr.write(
                f"[GeminiClient] empty response: finish_reason={reason} "
                f"prompt_feedback={feedback}\n"
            )
        return text


_DESCRIBE_SYSTEM = (
    "You are given the complete source of a small Python program. Write a precise "
    "natural-language specification of its behavior: every module-level function and "
    "class, including any whose names begin with an underscore, since callers and "
    "tests may import them directly. Cover each one's inputs, outputs, and edge "
    "cases, detailed enough that another engineer could reimplement it from your "
    "description alone, without seeing the code. Describe behavior, not a "
    "line-by-line transcription. Do not include or infer test code."
)

_REGENERATE_SYSTEM = (
    "You are given a natural-language specification and a project scaffold. Implement "
    "the program so it satisfies the specification. Output every source file you create "
    "as a block in exactly this format:\n"
    "=== <relative/path> ===\n"
    "<full file contents>\n"
    "Start each file with its own '=== path ===' header line. Follow the scaffold's "
    "layout (e.g. packages under src/). Do not write tests."
)

_BLOCK_RE = re.compile(r"^=== (.+?) ===$", re.MULTILINE)


def parse_file_blocks(text: str) -> dict[str, str]:
    """Parse '=== path ===' delimited blocks into ``{path: content}``.

    Text before the first header is ignored (model preamble). One trailing
    newline before the next header / end of text is dropped.
    """
    files: dict[str, str] = {}
    matches = list(_BLOCK_RE.finditer(text))
    for i, m in enumerate(matches):
        path = m.group(1).strip()
        nl = text.find("\n", m.end())
        if nl == -1:
            files[path] = ""
            continue
        body_start = nl + 1
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[body_start:body_end]
        if content.endswith("\n"):
            content = content[:-1]
        files[path] = content
    return files


def _read_tree(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = p.read_text(encoding="utf-8")
    return out


def _render_files(files: dict[str, str]) -> str:
    return "\n".join(f"=== {path} ===\n{content}" for path, content in files.items())


def describe(client: LLMClient) -> int:
    fixture = Path(os.environ["COUNDETRIP_FIXTURE"])
    out = Path(os.environ["COUNDETRIP_DESCRIPTION"])
    manifest = load_manifest(fixture)
    sources = {
        str(p.relative_to(fixture)): p.read_text(encoding="utf-8")
        for p in list_source_files(manifest)
    }
    user = "Source files:\n\n" + _render_files(sources)
    _describe_sys = os.environ.get("COUNDETRIP_DESCRIBE_PROMPT", _DESCRIBE_SYSTEM)
    description = client.complete(system=_describe_sys, user=user)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(description, encoding="utf-8")
    return 0


def regenerate(client: LLMClient) -> int:
    description = Path(os.environ["COUNDETRIP_DESCRIPTION"]).read_text(encoding="utf-8")
    workspace = Path(os.environ["COUNDETRIP_WORKSPACE"])
    generated = Path(os.environ["COUNDETRIP_GENERATED"])
    scaffold = _read_tree(workspace)
    user = (
        "Specification:\n\n"
        + description
        + "\n\nProject scaffold (keep these files):\n\n"
        + _render_files(scaffold)
    )
    reply = client.complete(system=_REGENERATE_SYSTEM, user=user)
    try:  # keep the raw reply for debugging format/parse issues
        (generated.parent / "regenerate_reply.txt").write_text(reply, encoding="utf-8")
    except OSError:
        pass
    produced = parse_file_blocks(reply)
    generated.mkdir(parents=True, exist_ok=True)
    # Keep the scaffold, then write the model's source files over it.
    for rel, content in {**scaffold, **produced}.items():
        dest = generated / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    return 0


def _build_client() -> LLMClient:
    replay = os.environ.get("COUNDETRIP_REPLAY_DIR")
    if replay:
        return ReplayClient(Path(replay))
    if os.environ.get("GEMINI_API_KEY"):
        model = os.environ.get("COUNDETRIP_MODEL", "gemini-3.5-flash")
        temperature = float(os.environ.get("COUNDETRIP_TEMPERATURE", "0.0"))
        return GeminiClient(model=model, temperature=temperature)
    raise NotImplementedError(
        "No client configured. Set GEMINI_API_KEY for a live run, or "
        "COUNDETRIP_REPLAY_DIR for a deterministic offline replay."
    )


def main(argv: list[str] | None = None) -> int:
    stage = os.environ.get("COUNDETRIP_STAGE")
    client = _build_client()
    if stage == "describe":
        rc = describe(client)
    elif stage == "regenerate":
        rc = regenerate(client)
    else:
        print(f"Unknown or missing COUNDETRIP_STAGE: {stage!r}", file=sys.stderr)
        return 1
    _log_usage(client, stage)
    return rc


def _log_usage(client: LLMClient, stage: str) -> None:
    """Write this stage's token usage to the run dir, if the client tracks it."""
    usage = getattr(client, "usage", None)
    run_dir = os.environ.get("COUNDETRIP_RUN_DIR")
    if usage and run_dir:
        Path(run_dir, f"usage_{stage}.json").write_text(
            json.dumps(usage), encoding="utf-8"
        )


if __name__ == "__main__":
    raise SystemExit(main())