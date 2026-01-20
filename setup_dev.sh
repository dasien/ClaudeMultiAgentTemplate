#!/bin/bash
# CMAT Development Environment Setup Script
# This script ensures all dependencies are installed for CMAT to run

set -e

echo "=== CMAT Development Setup ==="
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo "Detected OS: $OS"
echo ""

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "Found Python $PYTHON_VERSION"

    # Check if version is 3.10+
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [[ $MAJOR -lt 3 ]] || [[ $MAJOR -eq 3 && $MINOR -lt 10 ]]; then
        echo "ERROR: Python 3.10 or higher is required. Found $PYTHON_VERSION"
        exit 1
    fi
else
    echo "ERROR: Python 3 not found. Please install Python 3.10 or higher."
    exit 1
fi
echo ""

# Check/Install tkinter
echo "Checking tkinter installation..."
if python3 -c "import tkinter" 2>/dev/null; then
    echo "tkinter is already installed."
else
    echo "tkinter is NOT installed."
    echo ""

    case $OS in
        macos)
            echo "On macOS, tkinter should come with Python. Options to fix:"
            echo ""
            echo "Option 1 - Using Homebrew (recommended):"
            echo "  brew install python-tk@3.12  # or your Python version"
            echo ""
            echo "Option 2 - Reinstall Python with tcl-tk:"
            echo "  brew install tcl-tk"
            echo "  brew reinstall python"
            echo ""
            echo "Option 3 - Using pyenv:"
            echo "  brew install tcl-tk"
            echo "  env PYTHON_CONFIGURE_OPTS=\"--with-tcltk-includes='-I/opt/homebrew/opt/tcl-tk/include' --with-tcltk-libs='-L/opt/homebrew/opt/tcl-tk/lib -ltcl8.6 -ltk8.6'\" pyenv install 3.12"
            echo ""
            read -p "Would you like to try 'brew install python-tk'? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                brew install python-tk || echo "Failed. Please try one of the manual options above."
            fi
            ;;
        linux)
            echo "On Linux, install tkinter via your package manager:"
            echo ""
            echo "Debian/Ubuntu:"
            echo "  sudo apt-get install python3-tk"
            echo ""
            echo "Fedora:"
            echo "  sudo dnf install python3-tkinter"
            echo ""
            echo "Arch:"
            echo "  sudo pacman -S tk"
            echo ""
            read -p "Would you like to try 'sudo apt-get install python3-tk'? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo apt-get install python3-tk || echo "Failed. Please try the appropriate command for your distribution."
            fi
            ;;
        windows)
            echo "On Windows, tkinter should come with the standard Python installer."
            echo "If missing, reinstall Python from python.org and ensure 'tcl/tk' is selected."
            ;;
        *)
            echo "Please install tkinter for your platform manually."
            ;;
    esac
    echo ""
fi

# Verify tkinter after potential install
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "WARNING: tkinter is still not available. CMAT GUI will not work."
    echo "Please install tkinter manually and re-run this script."
    echo ""
fi

# Check if venv module is available
echo "Checking for venv module..."
if ! python3 -c "import venv" 2>/dev/null; then
    echo "ERROR: Python venv module is not installed."
    echo ""
    case $OS in
        linux)
            echo "On Debian/Ubuntu, install it with:"
            echo "  sudo apt-get install python3-venv"
            echo ""
            echo "On Fedora:"
            echo "  sudo dnf install python3-libs"
            echo ""
            read -p "Would you like to try 'sudo apt-get install python3-venv'? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo apt-get install python3-venv
                if ! python3 -c "import venv" 2>/dev/null; then
                    echo "ERROR: venv still not available. Please install manually and re-run."
                    exit 1
                fi
            else
                exit 1
            fi
            ;;
        *)
            echo "Please install the Python venv module for your platform."
            exit 1
            ;;
    esac
else
    echo "venv module is available."
fi
echo ""

# Create virtual environment if it doesn't exist
echo "Setting up virtual environment..."
if [[ ! -d ".venv" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv

    # Verify it was actually created
    if [[ ! -f ".venv/bin/activate" ]]; then
        echo "ERROR: Failed to create virtual environment."
        echo "The venv directory may be incomplete. Try removing it and running again:"
        echo "  rm -rf .venv"
        echo "  ./setup_dev.sh"
        exit 1
    fi
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
    # Verify existing venv is valid
    if [[ ! -f ".venv/bin/activate" ]]; then
        echo "ERROR: Existing .venv directory is invalid (missing bin/activate)."
        echo "Remove it and run again:"
        echo "  rm -rf .venv"
        echo "  ./setup_dev.sh"
        exit 1
    fi
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo ""

# Install package in development mode
echo "Installing CMAT in development mode..."
pip install -e ".[dev]"
echo ""

# Verify installation
echo "=== Verifying Installation ==="
echo ""

echo "Checking required packages..."
python3 -c "import yaml; print('  pyyaml: OK')"
python3 -c "from PIL import Image; print('  pillow: OK')"
python3 -c "import chromadb; print('  chromadb: OK')"
python3 -c "from sentence_transformers import SentenceTransformer; print('  sentence-transformers: OK')"

if python3 -c "import tkinter" 2>/dev/null; then
    echo "  tkinter: OK"
else
    echo "  tkinter: MISSING (GUI will not work)"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To launch CMAT, run:"
echo "  cmat"
echo "  # or: python -m ui.main"
echo ""