"""Tests for the calculator module."""

import pytest
from calculator import add, subtract, multiply, divide


class TestAdd:
    """Tests for the add function."""

    def test_add_positive_numbers(self):
        assert add(2, 3) == 5.0

    def test_add_negative_numbers(self):
        assert add(-2, -3) == -5.0

    def test_add_mixed_numbers(self):
        assert add(-2, 5) == 3.0

    def test_add_with_zero(self):
        assert add(5, 0) == 5.0


class TestSubtract:
    """Tests for the subtract function."""

    def test_subtract_positive_numbers(self):
        assert subtract(10, 4) == 6.0

    def test_subtract_negative_result(self):
        assert subtract(4, 10) == -6.0

    def test_subtract_with_zero(self):
        assert subtract(5, 0) == 5.0


class TestMultiply:
    """Tests for the multiply function."""

    def test_multiply_positive_numbers(self):
        assert multiply(3, 7) == 21.0

    def test_multiply_with_zero(self):
        assert multiply(5, 0) == 0.0

    def test_multiply_negative_numbers(self):
        assert multiply(-3, -4) == 12.0


class TestDivide:
    """Tests for the divide function."""

    def test_divide_positive_numbers(self):
        assert divide(15, 3) == 5.0

    def test_divide_with_remainder(self):
        assert divide(10, 4) == 2.5

    def test_divide_by_zero_raises_error(self):
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, 0)

    def test_divide_negative_numbers(self):
        assert divide(-12, 4) == -3.0
