# Design: Package-Level Roundtrip and Targeted Edit

Status: draft for review. No experiments run against this design yet; nothing here has been spent on.
Scope: extends the current pipeline to multiple files and package scale. The canvas stays the same:
describe -> regenerate -> score against the original tests, with env-safe oracles and by-construction
fixture checks.

## 1. What the data allows (measured on SWE-bench Verified)

Scan of Verified across eight repos (script: `benchmarks/filter_verified_multi.py`,
data: `benchmarks/verified_candidates_multi.json`):

| repo         | 1 file | 2-5 files, same dir | 2-5 files, cross dir |
|--------------|-------:|--------------------:|---------------------:|
| sympy        |     67 |                   3 |                    3 |
| django       |    198 |                   9 |                   23 |
| sphinx       |     36 |                   2 |                    6 |
| matplotlib   |     30 |                   1 |                    3 |
| scikit-learn |     30 |                   0 |                    2 |
| pytest       |     17 |                   1 |                    1 |
| astropy      |     19 |                   3 |                    0 |
| xarray       |     17 |                   5 |                    0 |
| total        |    414 |                  24 |                   38 |

Two consequences:

1. Single-file cross-project expansion is rich. 414 candidates support the 30-40-fixture target
   easily, across four or more projects.
2. Multi-file instances are scarce. Only 24 same-directory candidates exist in all of Verified.
   A package-level benchmark cannot be built from multi-file instances alone.

## 2. Design decision: two fixture kinds, two purposes

The roundtrip task needs only code and tests; it does not need an issue or a gold patch. The
issue-resolution task needs an instance. The scarcity above therefore suggests separating them:

Kind A - package roundtrip fixtures (no instance needed).
A fixture is a self-contained subpackage of a pinned repo commit: all its source files plus the
subpackage's own test directory as the oracle. Selection filter: subpackage with its own tests,
bounded size (3-15 source files proposed), tests pass at the pinned commit (by-construction check),
imports resolvable within the environment. This yields as many package fixtures as the repos
contain qualifying subpackages - not limited to 24.
Decontamination note: these lack the Verified argument. Mitigations: use the same Verified-era
repos and commits; keep the recitation monitor; report this as a stated limitation.

Kind B - multi-file instance fixtures (the 24 same-dir, optionally the 38 cross-dir).
Used for the issue-resolution study at multi-file scale, exactly as single-file instances are used
today: pre-fix state, issue text, instance tests as acceptance.

## 3. Regeneration design (the import-hallucination problem)

Prior multi-file runs regenerated whole file-sets in one shot: mean fidelity ~0.44, unstable,
dominant failure = hallucinated imports (a regenerated file imports names that do not exist in a
sibling it also regenerated). Two candidate designs:

- D1: whole-package regeneration (one prompt, all files). Simple; known-unstable.
- D2: per-file regeneration with a shared contract. The describe stage produces one description
  per file plus a package contract (every public symbol each file must expose, extracted by AST as
  in the current CONTRACT.md). Regeneration is per file against the description plus contract, so a
  file's imports of siblings are grounded in the contract, not guessed.
- Repair loop (either design): on import error at oracle time, feed the error back for one
  bounded repair round.

Proposal: implement D2 as the primary design, D1 as the ablation; repair loop as a measured add-on
(report fidelity with and without it).

## 4. Targeted edit at package scale

The paper's boundary result says description-guided editing pays when code is much larger than its
description; a package is the setting where that holds by construction. Protocol (extends
`resolution_v4.py`):

1. Agent receives the issue and the package description set (one per file plus contract), never the source.
2. Step 1: agent names the files and symbols it needs.
3. Step 2: agent receives only those symbols' source, returns replacements; AST splice; instance
   tests score the result.
4. Conditions: guided (with descriptions) vs unguided (issue only, agent must guess from the file
   listing); ceiling = full package in context where it fits, else noted as infeasible - which is
   itself the point.
5. Metrics: resolved rate, pass fraction, prompt tokens consumed vs the ceiling.

Runs on Kind B fixtures (multi-file instances), where an issue exists.

## 5. Metrics and reporting

- Fidelity: fraction of the oracle tests passed; mean and SD over 3+ runs (API non-determinism).
- Density at package scale: tokens of the description set over tokens of the package source;
  per-file and aggregate. Expectation to test: density improves with size.
- Failure classification per run: import crash / collection error / tests ran.
- Token accounting for the targeted-edit study, as in resolution_v4.

## 6. Phasing and cost

- Phase 0 (free): subpackage selection filter for Kind A over the pinned repos; candidate list with
  the same logged-exclusions discipline as the verified build logs.
- Phase 1: 3-5 pilot Kind-A fixtures from one repo; D2 vs D1 on the pilot; repair-loop ablation.
  Rough cost: tens of runs at current per-run cost; exact estimate after the pilot filter.
- Phase 2: scale Kind A across repos; build the 24 Kind-B fixtures; run the package targeted-edit study.
- Models: current default plus Qwen 3.6 (hosted) when available, so package-scale numbers exist on
  two model families from the start.

## 7. Open questions for review

1. Kind A without the Verified decontamination argument: acceptable with the stated mitigations,
   or restrict Kind A to subpackages untouched by any Verified instance?
2. Subpackage size bounds (proposed 3-15 files): right range?
3. Cross-dir instances (38): include in Kind B from the start, or defer?
4. Repair loop: one bounded round, or excluded from headline numbers entirely?
