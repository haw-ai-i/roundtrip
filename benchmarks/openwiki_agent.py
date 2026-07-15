"""A drop-in 'agent' for the coundetrip pipeline that supplies OpenWiki's documentation
as the description instead of calling a model. For regenerate, it delegates to the real
llm_agent. This lets OpenWiki's docs flow through the real pipeline + oracle.

describe stage: write concatenated OpenWiki docs (from the fixture's openwiki/ folder) to
                COUNDETRIP_DESCRIPTION.
regenerate stage: delegate to coundetrip.llm_agent (normal Gemini regenerate).
"""
import os, sys, subprocess
from pathlib import Path

stage = os.environ.get("COUNDETRIP_STAGE")

if stage == "describe":
    fixture = Path(os.environ["COUNDETRIP_FIXTURE"])
    out = Path(os.environ["COUNDETRIP_DESCRIPTION"])
    ow = fixture / "openwiki"
    docs = sorted(ow.rglob("*.md"))
    text = "\n\n".join(d.read_text(encoding="utf-8") for d in docs if d.is_file())
    if not text.strip():
        print("no openwiki docs for", fixture, file=sys.stderr); sys.exit(1)
    out.write_text(text, encoding="utf-8")
    print(f"wrote OpenWiki description: {len(text.split())} words from {len(docs)} docs")
    sys.exit(0)
elif stage == "regenerate":
    # delegate to the real agent
    sys.exit(subprocess.run([sys.executable, "-m", "coundetrip.llm_agent"], env=os.environ).returncode)
else:
    print("unknown stage", stage, file=sys.stderr); sys.exit(1)
