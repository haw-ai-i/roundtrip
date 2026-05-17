# Coundetrip

Roundtrip benchmark prototype: treat a natural-language description as the **source** artifact, regenerate a codebase, then score **description metrics** and **test pass rate** against the original fixture’s tests.

See [VISION.md](VISION.md) for the research framing.

## Quick start

Use [uv](https://github.com/astral-sh/uv) (recommended) or any Python 3.10+ environment with `pip`.

```bash
cd coundetrip
uv sync --extra dev
```

Run a full roundtrip on the `calc` fixture using the built-in stub agent (copies `stub/description.md` and `stub/generated_snapshot/`):

```bash
uv run python -m coundetrip run \
  --fixture benchmarks/fixtures/calc \
  --runs-dir runs \
  --run-id demo \
  --agent 'python -m coundetrip.stub_agent'
```

Or use the console script:

```bash
uv run coundetrip run \
  --fixture benchmarks/fixtures/calc \
  --runs-dir runs \
  --run-id demo \
  --agent 'python -m coundetrip.stub_agent'
```

`--agent` is parsed with `shlex.split` (quote the whole command). Use the same interpreter that has `coundetrip` installed (e.g. `uv run` so `python` resolves to the project venv).

## Artifacts

Each run writes under `{runs-dir}/{run-id}/{manifest-name}/`:

| Path | Purpose |
|------|---------|
| `description.md` | NL description produced by the describe stage |
| `generated/` | Regenerated tree evaluated by tests |
| `logs/describe.stdout.txt` (and `.stderr`) | Agent stdout/stderr for describe |
| `logs/regenerate.*` | Agent stdout/stderr for regenerate |
| `logs/test.*` | Pytest output |
| `report.json` | Full JSON report including scores |

## Fixture layout

Add a directory under `benchmarks/fixtures/<name>/` with:

1. **`coundetrip.yaml`** — required keys:
   - `name`: logical case name (defaults to directory name).
   - `test_command`: argv list to run tests from **`generated/`** root (e.g. `python -m pytest -q tests`).
   - `source_paths`: relative paths (files or dirs) that define what the “original” project is for documentation / future ingestion.

2. **Project files** — e.g. `pyproject.toml`, `src/`, `tests/` as needed for pytest.

3. **Stub agent seeds** (for local smoke tests, not for real scoring):
   - `stub/description.md` — copied to `description.md` by `coundetrip.stub_agent describe`.
   - `stub/generated_snapshot/` — copied to `generated/` by `coundetrip.stub_agent regenerate`.

Example fixtures: `benchmarks/fixtures/calc`, `benchmarks/fixtures/reverse`.

## Wiring a real agent

The runner invokes your command twice (describe and regenerate). It sets:

| Variable | Describe | Regenerate |
|----------|----------|------------|
| `COUNDETRIP_STAGE` | `describe` | `regenerate` |
| `COUNDETRIP_FIXTURE` | absolute path to fixture root | same |
| `COUNDETRIP_RUN_DIR` | absolute path to this run directory | same |
| `COUNDETRIP_DESCRIPTION` | path where the agent should write `description.md` | path to existing `description.md` |
| `COUNDETRIP_GENERATED` | unset | directory to populate with the regenerated tree |

If `--agent` contains `stub_agent`, the runner appends the subcommand `describe` or `regenerate` after your argv (for `python -m coundetrip.stub_agent`). Otherwise the same argv is used for both stages; your entrypoint should branch on `COUNDETRIP_STAGE`.

## Scoring (prototype)

- **Description**: `word_count`, `byte_size_utf8`; `readability_rubric` is reserved (currently `null`).
- **Tests**: counts parsed from pytest’s summary line and `pass_fraction` = `passed / (passed + failed + errors)`.

## Development

```bash
uv sync --extra dev
uv run pytest
```
