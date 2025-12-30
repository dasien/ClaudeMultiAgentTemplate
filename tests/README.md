# ClaudeMultiAgentUI Tests

Integration and unit tests for the Claude Multi-Agent UI.

## Setup

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

## Running Tests

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_cmat_integration.py
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=html
```

Run only integration tests:
```bash
pytest -m integration
```

## Test Categories

- **Integration tests**: Test interaction with CMAT v8.2+ services
- **Unit tests**: Test individual components in isolation
- **UI tests**: Test UI components (may require display)

## What Gets Tested

### CMAT Integration (`test_cmat_integration.py`)

Tests that verify the UI correctly interfaces with CMAT v8.2+ Python services:

1. **Method Signatures**: Ensures all CMAT service methods are called with correct parameters
2. **Return Types**: Validates that return values match expected types
3. **Data Transformations**: Tests mapping between CMAT models and UI models
4. **Error Handling**: Verifies graceful handling of edge cases

### Examples of Bugs Caught

These tests catch bugs like:
- ❌ Calling `build_prompt()` instead of `build_skills_prompt()`
- ❌ Passing wrong field names (e.g., `slug` vs `id`)
- ❌ Type mismatches (e.g., string vs int for step_index)
- ❌ Missing parameters in method calls

## Writing New Tests

When adding new CMAT integration code:

1. Add test to `test_cmat_integration.py`
2. Test both success and failure cases
3. Verify data transformations
4. Check error handling

Example test structure:
```python
def test_new_cmat_method(self, cmat_interface):
    """Test description."""
    # Call the method
    result = cmat_interface.new_method(param1, param2)

    # Verify return type
    assert isinstance(result, ExpectedType)

    # Verify data structure
    assert hasattr(result, 'expected_field')
```

## CI/CD Integration

To run tests automatically on commits, add to `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: pytest
```

## Pre-commit Hook

Run tests before committing:

```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/test_cmat_integration.py -v
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```
