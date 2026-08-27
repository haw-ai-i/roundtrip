"""omp-backed roundtrip agent: describe and regenerate via the oh-my-pi harness.

Same env-var contract as the built-in agent (COUNDETRIP_STAGE / FIXTURE /
DESCRIPTION / WORKSPACE / GENERATED). Each stage shells out to omp, which
navigates files with its own tools, so large sources need no manual chunking.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from coundetrip.manifest import list_source_files, load_manifest

OMP = os.environ.get("COUNDETRIP_OMP_BIN", "omp")
PROVIDER = os.environ.get("COUNDETRIP_OMP_PROVIDER", "local-qwen")
MODEL = os.environ.get("COUNDETRIP_MODEL", "hf.co/unsloth/Qwen3.6-35B-A3B-GGUF:UD-Q4_K_M")

_DESCRIBE_SYSTEM = (
    "You are given the source of a Python program in the working directory. "
    "Write a precise natural-language specification of its behavior: every "
    "module-level function and class, including any whose names begin with an "
    "underscore, since callers and tests may import them directly. Cover each "
    "one's inputs, outputs, and edge cases, detailed enough that another engineer "
    "could reimplement it from your description alone, without seeing the code. "
    "Describe behavior, not a line-by-line transcription. Do not include or infer "
    "test code. Output only the specification as your final message."
)

_REGENERATE_SYSTEM = (
    "You are given a natural-language specification and a project scaffold in the "
    "working directory. Implement the program so it satisfies the specification by "
    "writing the source files into the working directory, preserving the scaffold "
    "layout. You MUST use the write tool to create every required source file on "
    "disk; do not print code as your final message and do not stop until each "
    "target file named in the contract exists."
)


def _run_omp(cwd, system_prompt, user_prompt):
    cmd = [
        OMP, "--provider", PROVIDER, "--model", MODEL,
        "--no-session", "--no-lsp", "--mode", "json",
        "--thinking", "off",
        "--system-prompt", system_prompt,
        "-p", user_prompt,
    ]
    proc = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True,
        timeout=int(os.environ.get("COUNDETRIP_AGENT_TIMEOUT", "1800")),
    )
    dbg = os.environ.get('COUNDETRIP_OMP_DEBUG')
    if dbg:
        Path(dbg).write_text(proc.stdout + chr(10) + '=STDERR=' + chr(10) + proc.stderr, encoding='utf-8')
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-2000:])
        raise SystemExit("omp failed rc=%d" % proc.returncode)
    final = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "agent_end":
            final = obj
    if final is None:
        raise SystemExit("omp produced no terminal frame")
    return final


def _final_text(frame):
    msgs = frame.get('messages') or ([frame['message']] if frame.get('message') else [])
    for msg in reversed(msgs):
        if msg.get('role') != 'assistant':
            continue
        parts = [b.get('text', '') for b in msg.get('content', []) if b.get('type') == 'text']
        text = chr(10).join(parts).strip()
        if text:
            return text
    return ''


def describe():
    fixture = Path(os.environ['COUNDETRIP_FIXTURE'])
    out = Path(os.environ['COUNDETRIP_DESCRIPTION'])
    manifest = load_manifest(fixture)
    sources = list_source_files(manifest)
    with tempfile.TemporaryDirectory(prefix='omp_desc_') as td:
        stage = Path(td)
        rels = []
        for sp in sources:
            rel = sp.relative_to(fixture)
            rels.append(str(rel))
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sp, dest)
        file_list = ', '.join(rels)
        user = (
            'Read the following source file(s) in full using your read tool: '
            + file_list
            + '. Then write the complete natural-language specification as your '
            + 'final message. You must actually read each file before writing, '
            + 'and your final message must contain the full specification text.'
        )
        text = ''
        for _attempt in range(4):
            frame = _run_omp(stage, _DESCRIBE_SYSTEM, user)
            text = _final_text(frame)
            if text.strip():
                break
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding='utf-8')
    return 0


def regenerate():
    description = Path(os.environ['COUNDETRIP_DESCRIPTION']).read_text(encoding='utf-8')
    workspace = Path(os.environ['COUNDETRIP_WORKSPACE'])
    generated = Path(os.environ['COUNDETRIP_GENERATED'])
    generated.mkdir(parents=True, exist_ok=True)
    for sp in sorted(workspace.rglob('*')):
        if sp.is_file():
            dest = generated / sp.relative_to(workspace)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sp, dest)
    (generated / 'SPECIFICATION.md').write_text(description, encoding='utf-8')
    user = (
        'SPECIFICATION.md contains the spec. CONTRACT.md names the exact file(s) '
        'you must create and the names they must export. Implement the code now: '
        'use your write tool to create each target file with the full Python implementation that satisfies the specification. You MUST call the write tool for each required file - do not just describe the code. After writing, delete SPECIFICATION.md.'
    )
    # Retry: the reasoning model sometimes ends a turn without writing files.
    # Consider it done when at least one non-scaffold .py file exists in generated.
    def wrote_code():
        for f in generated.rglob('*.py'):
            rel = f.relative_to(generated)
            if 'scaffold' not in rel.parts and f.stat().st_size > 0:
                return True
        return False
    for _attempt in range(4):
        _run_omp(generated, _REGENERATE_SYSTEM, user)
        if wrote_code():
            break
    spec = generated / 'SPECIFICATION.md'
    if spec.exists():
        spec.unlink()
    return 0


def main(argv=None):
    stage = os.environ.get("COUNDETRIP_STAGE")
    if stage == "describe":
        return describe()
    if stage == "regenerate":
        return regenerate()
    print("Unknown or missing COUNDETRIP_STAGE: %r" % stage, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
