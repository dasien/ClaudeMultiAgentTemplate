# Add Power Function to Calculator

## Overview

Add a `power` command to the demo calculator that raises a number to an exponent.

## User Story

As a calculator user, I want to compute powers (exponentiation) so that I can perform calculations like 2^3 = 8.

## Acceptance Criteria

- [ ] `python demo/calculator.py power 2 3` returns `8.0` (2 raised to the power of 3)
- [ ] `python demo/calculator.py power 10 0` returns `1.0` (any number to the power of 0)
- [ ] `python demo/calculator.py power 2 -1` returns `0.5` (negative exponents work)
- [ ] `python demo/calculator.py power 0 0` returns `1.0` (mathematical convention)
- [ ] Tests are added to `demo/test_calculator.py` for the new function
- [ ] Help text updated to show the new command

## Technical Notes

- Follow existing code patterns in `demo/calculator.py`
- Add a `power(base: float, exponent: float) -> float` function
- Add corresponding CLI subparser for the `power` command
- Use Python's built-in `**` operator for exponentiation
- Add a `TestPower` class in `demo/test_calculator.py` following the existing test pattern

## Files to Modify

- `demo/calculator.py` - Add power function and CLI command
- `demo/test_calculator.py` - Add tests for power function

## Example Usage

```bash
# Basic power operations
python demo/calculator.py power 2 3      # 8.0
python demo/calculator.py power 5 2      # 25.0
python demo/calculator.py power 10 -1    # 0.1

# Edge cases
python demo/calculator.py power 0 5      # 0.0
python demo/calculator.py power 10 0     # 1.0
```
