# Enhancement: Add Square Root Function

## Overview

Add a square root function to the calculator CLI that computes the square root of a number.

## Requirements

### Functional Requirements

1. Add a `sqrt` command to the calculator CLI
2. The function should compute the square root of a single number
3. Handle edge cases:
   - Negative numbers should raise an appropriate error
   - Zero should return 0
   - Positive numbers should return their square root

### Technical Requirements

1. Follow the existing code patterns in `demo/calculator.py`
2. Add comprehensive unit tests in `demo/test_calculator.py`
3. Use Python's `math.sqrt` or the `**` operator for the implementation
4. Include proper error handling with descriptive messages

## Example Usage

```bash
python demo/calculator.py sqrt 16    # Returns 4.0
python demo/calculator.py sqrt 2     # Returns 1.4142135623730951
python demo/calculator.py sqrt 0     # Returns 0.0
python demo/calculator.py sqrt -1    # Error: Cannot compute square root of negative number
```

## Acceptance Criteria

- [ ] `sqrt` command is available in the CLI
- [ ] Correct square root values are returned for positive numbers
- [ ] Appropriate error for negative numbers
- [ ] Unit tests pass
- [ ] Code follows existing patterns
