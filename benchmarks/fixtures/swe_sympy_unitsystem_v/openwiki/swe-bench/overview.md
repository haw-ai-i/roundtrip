# SWE-Bench Fixture Overview

This document describes the components of the SWE-Bench test fixture for the SymPy `UnitSystem` bug.

## Test Configuration (`coundetrip.yaml`)

The test environment is defined in `coundetrip.yaml`. This file specifies:

- **`name`**: `swe_sympy_unitsystem_v`, the unique identifier for this benchmark.
- **`test_command`**: The command to run the test, which executes `run_oracle.py`.
- **`source_paths`**: The path to the source file that the agent needs to modify (`sympy/physics/units/unitsystem.py`).
- **`scaffold_paths`**: The directory containing scaffold files, such as the implementation contract.
- **`test_paths`**: The files that constitute the test itself.

## Test Runner (`run_oracle.py`)

The `run_oracle.py` script is the entry point for executing the test. It performs the following steps:

1.  **Reads `oracle_env.json`**: This file contains paths to the Conda environment, the target source file, and the oracle test file.
2.  **Restores Original File**: Before each run, it restores the original, unmodified version of `sympy/physics/units/unitsystem.py` to ensure a clean test environment.
3.  **Copies Agent's Patch**: It copies the agent-generated version of the file into the test environment.
4.  **Runs Pytest**: It executes the oracle tests using `pytest` within the specified Conda environment.
5.  **Exits with Test Result**: The script exits with the return code from `pytest`, indicating whether the tests passed or failed.

## Implementation Contract (`scaffold/CONTRACT.md`)

The `scaffold/CONTRACT.md` file provides instructions to the agent. It specifies that the agent must implement the module at `sympy/physics/units/unitsystem.py` and ensure that the public class `UnitSystem` is present and correctly implemented.
