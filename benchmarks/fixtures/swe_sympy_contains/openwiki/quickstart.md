# Quickstart: swe_sympy_contains

This repository contains a test fixture for the `Contains` class in the `sympy` library, which is used for symbolic mathematics in Python. The test is part of the SWE-Bench benchmark, designed to evaluate code generation and modification tasks.

The primary goal of this repository is to test the implementation of `sympy.sets.contains.Contains`.

## Repository Structure

The repository is organized as follows:

- `/coundetrip.yaml`: The main configuration file for the test runner. It defines the source, scaffold, and test paths.
- `/run_oracle.py`: A Python script that acts as the test runner. It prepares the environment and executes the tests using `pytest`.
- `/oracle_env.json`: A JSON configuration file for `run_oracle.py`, specifying the environment path and the locations of the target and oracle files.
- `/sympy/sets/contains.py`: The Python source code for the `Contains` class, which is the subject of the test.
- `/scaffold/CONTRACT.md`: A markdown file that specifies the implementation requirements for the `Contains` class.

## Workflow

The testing workflow is orchestrated by the `run_oracle.py` script. When executed, it performs the following steps:

1.  **Reads Configuration**: It loads the environment and file paths from `/oracle_env.json`.
2.  **Restores Environment**: It restores the target file (`sympy/sets/contains.py`) from a backup to ensure a clean state for each test run.
3.  **Copies Candidate Code**: It copies the version of `contains.py` to be tested into the target location.
4.  **Executes Tests**: It runs `pytest` on the test file (`sympy/sets/tests/test_contains.py`), which is specified as the "oracle" in the configuration.

This setup allows for a consistent and repeatable way to test the functionality of the `Contains` class.

## Next Steps

- For a more detailed explanation of the components, see the [Architecture](architecture.md) documentation.
