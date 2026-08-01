# Quickstart: `saferepr`

This repository contains the `saferepr` module, a Python utility designed for robust and safe object representation. It is particularly useful in environments where `repr()` must not fail, such as in logging, debugging, or during test reporting.

## Overview

The `saferepr` module provides functions that generate string representations of Python objects while handling exceptions that might occur in custom `__repr__` implementations. It also enforces size limits on the output to prevent overly long representations from causing issues.

This ensures that even with misbehaving objects, your program can continue to run without crashing, and you still get meaningful, albeit truncated, output.

## Core Features

- **Exception Safety**: Catches and reports exceptions raised during object representation.
- **Size Limiting**: Truncates long representations to a configurable maximum size.
- **Pretty Printing**: Offers a safe version of `pprint.pformat`.

## Key Files

- `src/saferepr.py`: The main module containing all the logic.
- `tests/test_saferepr.py`: A comprehensive suite of tests demonstrating usage and edge cases.

## Next Steps

For a deeper dive into the module's functions and classes, refer to the detailed documentation:

- **[saferepr Module](saferepr-module.md)**
