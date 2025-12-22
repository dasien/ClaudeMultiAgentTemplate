"""
Simple calculator CLI for CMAT demos.

This is a minimal Python application used to demonstrate the CMAT
multi-agent workflow system. Enhancements in the enhancements/ directory
can add new features to this calculator.

Usage:
    python demo/calculator.py add 2 3        # Returns 5.0
    python demo/calculator.py subtract 10 4  # Returns 6.0
    python demo/calculator.py multiply 3 7   # Returns 21.0
    python demo/calculator.py divide 15 3    # Returns 5.0
    python demo/calculator.py power 2 3      # Returns 8.0
"""

import argparse
import sys


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    if base == 0 and exponent < 0:
        raise ValueError("Cannot raise zero to a negative power")
    return base ** exponent


def main():
    parser = argparse.ArgumentParser(
        description="Simple calculator CLI",
        epilog="Example: python demo/calculator.py add 2 3"
    )
    subparsers = parser.add_subparsers(dest="command", help="Operation to perform")

    # add command
    add_parser = subparsers.add_parser("add", help="Add two numbers")
    add_parser.add_argument("a", type=float, help="First number")
    add_parser.add_argument("b", type=float, help="Second number")

    # subtract command
    sub_parser = subparsers.add_parser("subtract", help="Subtract two numbers")
    sub_parser.add_argument("a", type=float, help="First number")
    sub_parser.add_argument("b", type=float, help="Second number")

    # multiply command
    mul_parser = subparsers.add_parser("multiply", help="Multiply two numbers")
    mul_parser.add_argument("a", type=float, help="First number")
    mul_parser.add_argument("b", type=float, help="Second number")

    # divide command
    div_parser = subparsers.add_parser("divide", help="Divide two numbers")
    div_parser.add_argument("a", type=float, help="First number (dividend)")
    div_parser.add_argument("b", type=float, help="Second number (divisor)")

    # power command
    pow_parser = subparsers.add_parser("power", help="Raise a number to a power")
    pow_parser.add_argument("a", type=float, help="Base number")
    pow_parser.add_argument("b", type=float, help="Exponent")

    args = parser.parse_args()

    if args.command == "add":
        print(add(args.a, args.b))
    elif args.command == "subtract":
        print(subtract(args.a, args.b))
    elif args.command == "multiply":
        print(multiply(args.a, args.b))
    elif args.command == "divide":
        try:
            print(divide(args.a, args.b))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "power":
        try:
            print(power(args.a, args.b))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
