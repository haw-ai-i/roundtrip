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
            config = {
                "temperature": self._temperature,
                "max_output_tokens": 8192,
            }
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
_COMPOSE_SYSTEM = (
    "You are given per-file natural-language specifications of the modules in a "
    "Python package. Combine them into one coherent package-level specification "
    "that preserves every function and class described (including underscore-prefixed "
    "ones), their inputs, outputs, and edge cases, and makes cross-file relationships "
    "explicit, so an engineer could reimplement the whole package from your text alone. "
    "Do not drop detail; do not include or infer test code."
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


class OpenAIClient:
    """Client for any OpenAI-compatible endpoint (local vLLM or llama.cpp).
    Used for open-weight models such as Qwen. Qwen3 may wrap output in
    <think>...</think>; the wrapper is stripped so describe/regenerate see clean
    text. temperature=0 for determinism. A client may be injected for testing.
    """

    def __init__(self, *, model="qwen3-8b", base_url=None, api_key=None,
                 temperature=0.0, max_retries=5, client=None):
        if client is None:
            from openai import OpenAI
            base_url = base_url or os.environ.get(
                "COUNDETRIP_OPENAI_BASE", "http://localhost:8113/v1")
            client = OpenAI(base_url=base_url, api_key=api_key or "local")
        self._client = client
        self._model = model
        self._temperature = temperature
        self._max_retries = max_retries
        self.usage = None

    @staticmethod
    def _strip_think(text):
        import re
        return re.sub(r"^\s*<think>.*?</think>\s*", "", text, flags=re.DOTALL)

    def complete(self, *, system: str, user: str) -> str:
        import time
        # Reasoning models (e.g. Qwen3.5 via ollama) place their chain-of-thought in
        # a separate field and need generous max_tokens to finish thinking AND emit
        # the answer; too small a budget returns empty content (finish_reason=length).
        max_tokens = int(os.environ.get("COUNDETRIP_MAX_TOKENS", "8192"))
        last = None
        for attempt in range(self._max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self._model,
                    temperature=self._temperature,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                u = getattr(resp, "usage", None)
                if u is not None:
                    self.usage = {
                        "prompt_tokens": getattr(u, "prompt_tokens", None),
                        "completion_tokens": getattr(u, "completion_tokens", None),
                    }
                return self._strip_think(resp.choices[0].message.content or "")
            except Exception as exc:
                last = exc
                if not _is_retryable(exc) or attempt == self._max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        raise last


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences a model may wrap around a file body.
    A leading ```lang line and a trailing ``` line are dropped; content is unchanged
    when no fences are present."""
    lines = text.split("\n")
    if lines and lines[0].lstrip().startswith("```"):
        lines = lines[1:]
        # drop matching closing fence if present
        for j in range(len(lines) - 1, -1, -1):
            if lines[j].strip() == "```":
                lines = lines[:j] + lines[j+1:]
                break
    return "\n".join(lines)


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
        content = _strip_code_fences(content)
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


def ast_describe(sources: dict[str, str]) -> str:
    """Deterministic, zero-cost description baseline: emit each public
    function and class as its signature plus docstring, no model call.

    Tests how much roundtrip fidelity comes from the interface alone versus
    from a model-written behavioural description.
    """
    import ast

    def fmt_args(a: ast.arguments) -> str:
        parts = []
        posonly = getattr(a, "posonlyargs", [])
        for arg in posonly + a.args:
            t = f": {ast.unparse(arg.annotation)}" if arg.annotation else ""
            parts.append(arg.arg + t)
        if posonly:
            parts.insert(len(posonly), "/")
        if a.vararg:
            parts.append("*" + a.vararg.arg)
        elif a.kwonlyargs:
            parts.append("*")
        for arg in a.kwonlyargs:
            t = f": {ast.unparse(arg.annotation)}" if arg.annotation else ""
            parts.append(arg.arg + t)
        if a.kwarg:
            parts.append("**" + a.kwarg.arg)
        return ", ".join(parts)

    def describe_func(node, indent="") -> list[str]:
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        lines = [f"{indent}{prefix} {node.name}({fmt_args(node.args)}){ret}:"]
        doc = ast.get_docstring(node)
        if doc:
            lines.append(f'{indent}    """{doc.strip()}"""')
        return lines

    out = []
    for rel, code in sources.items():
        out.append(f"# File: {rel}")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            out.append("# (unparseable)")
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                out += describe_func(node)
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("_"):
                    continue
                bases = ", ".join(ast.unparse(b) for b in node.bases)
                out.append(f"class {node.name}({bases}):" if bases else f"class {node.name}:")
                cdoc = ast.get_docstring(node)
                if cdoc:
                    out.append(f'    """{cdoc.strip()}"""')
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and not (
                        sub.name.startswith("_") and sub.name != "__init__"
                    ):
                        out += describe_func(sub, indent="    ")
        out.append("")
    return "\n".join(out)


def _chunk_source(code: str, budget: int) -> list[str]:
    """Split a large file into chunks of whole top-level definitions, each under
    ``budget`` chars (rough proxy for context). Line-slices if unparseable."""
    import ast
    try:
        tree = ast.parse(code)
    except SyntaxError:
        lines = code.splitlines(keepends=True)
        step = max(1, len(lines) * budget // max(1, len(code)))
        return ["".join(lines[i:i+step]) for i in range(0, len(lines), step)] or [code]
    lines = code.splitlines(keepends=True)
    tops = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if not tops:
        return [code]
    header = "".join(lines[:tops[0].lineno - 1])
    segs = []
    for i, node in enumerate(tops):
        start = node.lineno - 1
        end = tops[i+1].lineno - 1 if i+1 < len(tops) else len(lines)
        seg = "".join(lines[start:end])
        if len(seg) > budget and isinstance(node, ast.ClassDef):
            # A single class exceeds budget: split it into its methods so no
            # chunk is larger than one method. Each sub-chunk carries the class
            # signature line for context.
            body = [m for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            class_sig = lines[node.lineno - 1]
            if body:
                for j, m in enumerate(body):
                    mstart = m.lineno - 1
                    mend = body[j+1].lineno - 1 if j+1 < len(body) else end
                    segs.append(class_sig + "".join(lines[mstart:mend]))
            else:
                segs.append(seg)
        else:
            segs.append(seg)
    chunks, cur = [], header
    for seg in segs:
        if len(cur) + len(seg) > budget and cur.strip():
            chunks.append(cur); cur = header + seg
        else:
            cur += seg
    if cur.strip():
        chunks.append(cur)
    return chunks


def _compose(client, blocks, budget):
    """Combine per-file spec blocks into one package spec. If the blocks together
    exceed ``budget``, compose in batches then recurse on the batch results, so the
    compose call itself never exceeds context."""
    joined = "\n\n".join(blocks)
    if len(joined) <= budget:
        return client.complete(system=_COMPOSE_SYSTEM, user="Per-file specifications:\n\n" + joined)
    batches, cur, cur_len = [], [], 0
    for b in blocks:
        if cur and cur_len + len(b) > budget:
            batches.append(cur); cur, cur_len = [], 0
        cur.append(b); cur_len += len(b) + 2
    if cur:
        batches.append(cur)
    partials = [client.complete(system=_COMPOSE_SYSTEM, user="Per-file specifications:\n\n" + "\n\n".join(bt)) for bt in batches]
    return _compose(client, partials, budget)


def describe(client: LLMClient) -> int:
    fixture = Path(os.environ["COUNDETRIP_FIXTURE"])
    out = Path(os.environ["COUNDETRIP_DESCRIPTION"])
    manifest = load_manifest(fixture)
    sources = {
        str(p.relative_to(fixture)): p.read_text(encoding="utf-8")
        for p in list_source_files(manifest)
    }
    if os.environ.get("COUNDETRIP_DESCRIBER", "").lower() == "ast":
        description = ast_describe(sources)
    else:
        _describe_sys = os.environ.get("COUNDETRIP_DESCRIBE_PROMPT", _DESCRIBE_SYSTEM)
        budget = int(os.environ.get("COUNDETRIP_DESCRIBE_BUDGET_CHARS", "60000"))
        combined = _render_files(sources)
        if len(combined) <= budget:
            # Fits: single-call describe (original behavior).
            description = client.complete(system=_describe_sys, user="Source files:\n\n" + combined)
        else:
            # Too large for one context: describe each file, then compose. This is the
            # minimal agentic path so packages that exceed the context window still
            # produce a description instead of erroring out.
            per_file = {}
            for rel, code in sources.items():
                rendered = _render_files({rel: code})
                if len(rendered) <= budget:
                    per_file[rel] = client.complete(system=_describe_sys, user="Source file:\n\n" + rendered)
                else:
                    # single file exceeds budget: chunk by top-level defs, describe each
                    chunks = _chunk_source(code, budget)
                    parts = []
                    for j, ch in enumerate(chunks):
                        one = _render_files({f"{rel} (part {j+1}/{len(chunks)})": ch})
                        parts.append(client.complete(system=_describe_sys, user="Source file part:\n\n" + one))
                    per_file[rel] = "\n\n".join(parts)
            blocks = [f"=== {rel} ===\n{d}" for rel, d in per_file.items()]
            description = _compose(client, blocks, budget)
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
    if os.environ.get("COUNDETRIP_LLM", "").lower() == "openai":
        model = os.environ.get("COUNDETRIP_MODEL", "qwen3-8b")
        temperature = float(os.environ.get("COUNDETRIP_TEMPERATURE", "0.0"))
        return OpenAIClient(model=model, temperature=temperature)
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