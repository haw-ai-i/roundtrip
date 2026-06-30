set -e
FX=benchmarks/fixtures/swe_saferepr
COMMIT=4787fd64a4ca0dba5528b5651bddd254102fe9f3
RAW="https://raw.githubusercontent.com/pytest-dev/pytest/$COMMIT"

mkdir -p "$FX/src" "$FX/tests"

curl -fsSL "$RAW/src/_pytest/_io/saferepr.py" \
  | sed 's/obj\.__class__\.__name__/type(obj).__name__/' > "$FX/src/saferepr.py"

curl -fsSL "$RAW/testing/io/test_saferepr.py" \
  | sed 's/from _pytest\._io\.saferepr import/from saferepr import/g' > "$FX/tests/test_saferepr.py"
cat >> "$FX/tests/test_saferepr.py" << 'PYEOF'


def test_broken_getattribute():
    """saferepr() can create proper representations of classes with
    broken __getattribute__ (#7145)
    """

    class SomeClass:
        def __getattribute__(self, attr):
            raise RuntimeError

        def __repr__(self):
            raise RuntimeError

    assert saferepr(SomeClass()).startswith(
        "<[RuntimeError() raised in repr()] SomeClass object at 0x"
    )
PYEOF

cat > "$FX/pyproject.toml" << 'EOF'
[project]
name = "swe-saferepr-fixture"
version = "0"
requires-python = ">=3.10"
dependencies = []

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
EOF
cat > "$FX/coundetrip.yaml" << 'EOF'
name: swe_saferepr
test_command:
  - python
  - -m
  - pytest
  - -q
  - tests
source_paths:
  - src
  - pyproject.toml
scaffold_paths:
  - pyproject.toml
test_paths:
  - tests
EOF
echo "--- built ---"; find "$FX" -type f | sort
