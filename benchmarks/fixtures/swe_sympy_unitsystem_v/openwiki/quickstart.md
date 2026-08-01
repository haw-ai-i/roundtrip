# Quickstart: SWE-Bench SymPy UnitSystem Fixture

This repository contains a test fixture for the [SWE-Bench benchmark](https://www.swebench.com/), specifically targeting a bug in the `UnitSystem` class of the SymPy library. The fixture is designed to test the ability of a code-generation agent to fix the bug described in the problem statement.

## Repository Structure

The repository is organized into two main parts: the SWE-Bench testing infrastructure and the SymPy source code under test.

- **SWE-Bench infrastructure**: Configures the testing environment and runs the oracle to verify the bug fix.
- **SymPy source code**: Contains the specific version of the `sympy.physics.units.unitsystem` module with the bug to be fixed.

## Documentation Sections

- **[SWE-Bench Fixture](swe-bench/overview.md)**: Explains the testing setup, including the configuration files and the test execution script.
- **[SymPy Codebase](sympy-codebase/unit-system.md)**: Provides an overview of the `UnitSystem` class and the relevant parts of the SymPy library.
