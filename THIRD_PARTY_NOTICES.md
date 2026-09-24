# Third-Party Notices

The original code, scripts, generated descriptions, and experimental results in
this repository are released under the MIT License (see [`LICENSE`](LICENSE)).

This repository also redistributes material created by others. That material is
**not** relicensed under the MIT License; it remains under its original terms,
reproduced in [`third_party_licenses/`](third_party_licenses/).

## Source code in benchmark fixtures

The directories under `benchmarks/fixtures/` whose names begin with `swe_`
contain unmodified or task-specific excerpts of source code and tests from the
open-source projects below, selected from SWE-bench task instances. Each
excerpt is used only as test material for the benchmark.

| Upstream project | Fixture directories | License | License text |
|---|---|---|---|
| [Django](https://github.com/django/django) | `swe_django_*` | BSD-3-Clause | [`django.txt`](third_party_licenses/django.txt) |
| [SymPy](https://github.com/sympy/sympy) | `swe_sympy_*`, `swe_v_*` | BSD-3-Clause | [`sympy.txt`](third_party_licenses/sympy.txt) |
| [Sphinx](https://github.com/sphinx-doc/sphinx) | `swe_sphinx_doc_*` | BSD-2-Clause | [`sphinx.txt`](third_party_licenses/sphinx.txt) |
| [xarray](https://github.com/pydata/xarray) | `swe_pydata_*` | Apache-2.0 | [`xarray.txt`](third_party_licenses/xarray.txt) |
| [pytest](https://github.com/pytest-dev/pytest) | `swe_pytest_dev_*`, `swe_saferepr` | MIT | [`pytest.txt`](third_party_licenses/pytest.txt) |
| [pylint](https://github.com/pylint-dev/pylint) | `swe_pylint_dev_*` | GPL-2.0 | [`pylint.txt`](third_party_licenses/pylint.txt) |
| [Flask](https://github.com/pallets/flask) | `swe_flask_*` | BSD-3-Clause | [`flask.txt`](third_party_licenses/flask.txt) |
| [seaborn](https://github.com/mwaskom/seaborn) | `swe_mwaskom_*` | BSD-3-Clause | [`seaborn.txt`](third_party_licenses/seaborn.txt) |

The `swe_saferepr` fixture is adapted from pytest's `src/_pytest/_io/saferepr.py`.

The pylint excerpts are distributed under the GNU General Public License,
version 2. They are kept in their own fixture directories and are not linked
into or distributed as part of the MIT-licensed `coundetrip` package.

The remaining fixtures (`calc`, `expr`, `expr_apl`, `expr_apl_nodoc`,
`reverse`) and the hand-built codebases in `benchmarks/cb2/` and
`benchmarks/cb3/` are original to this project.

## Benchmark datasets

- **SWE-bench** (Jimenez et al., ICLR 2024,
  [github.com/SWE-bench/SWE-bench](https://github.com/SWE-bench/SWE-bench)).
  Task metadata, issue texts, and test specifications used to build the `swe_`
  fixtures are derived from SWE-bench, released under the MIT License
  ([`swe-bench.txt`](third_party_licenses/swe-bench.txt)).

- **SWE-ContextBench** (Zhu et al., 2026, arXiv:2602.08316,
  [github.com/jiayuanz3/SWEContextBench](https://github.com/jiayuanz3/SWEContextBench)).
  `benchmarks/scb_lite_dataset.json` and the issue and context files in
  `benchmarks/fixtures_scb/` are derived from the SWE-ContextBench Lite split.
  At the time of release the upstream repository does not publish a license;
  this material is included with attribution solely to allow the experiments in
  our paper to be reproduced. Please cite the original work when using it. We
  will remove it on request from the upstream authors.

## Contact

Questions about licensing may be directed to the maintainers through the
repository's issue tracker.
