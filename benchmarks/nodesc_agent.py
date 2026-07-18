"""Drop-in agent for the 'no description' condition.
describe stage: writes a minimal placeholder description (no real content), so the regenerate
                agent works essentially from the scaffold alone.
regenerate stage: delegates to the real llm_agent."""
import os, sys, subprocess
from pathlib import Path

stage = os.environ.get("COUNDETRIP_STAGE")
if stage == "describe":
    out = Path(os.environ["COUNDETRIP_DESCRIPTION"])
    out.write_text("(no description provided)\n", encoding="utf-8")
    print("wrote blank description")
    sys.exit(0)
elif stage == "regenerate":
    sys.exit(subprocess.run([sys.executable, "-m", "coundetrip.llm_agent"], env=os.environ).returncode)
else:
    sys.exit(1)
