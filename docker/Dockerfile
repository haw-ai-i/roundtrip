# Sandbox image for coundetrip: runs agent stages and generated-code tests
# inside a container instead of on the host.
#
# Nothing from the repo is baked in — the run directory and (for describe) the
# fixture are bind-mounted at run time. The image only provides a Python
# interpreter and pytest, which is what fixture test_commands invoke
# (`python -m pytest`).

FROM python:3.12-slim

RUN pip install --no-cache-dir "pytest>=7.0"

# Agent stages set their own absolute paths via COUNDETRIP_* env vars; this is
# just a sane default working directory.
WORKDIR /coundetrip/run