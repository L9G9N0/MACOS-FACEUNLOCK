#!/bin/bash
# Developer Bootstrap Script for macOS FaceUnlock

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Starting FaceUnlock Developer Bootstrap ==="

# 1. Navigate to Project Root
cd "$PROJECT_ROOT"

# 2. Check for dependencies
echo "Checking system toolchain..."
if ! command -v clang++ &> /dev/null; then
    echo "[ERROR] clang++ is required to build the PAM module. Install Xcode Command Line Tools: xcode-select --install"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is required. Install Python 3.10+."
    exit 1
fi

# 3. Create Python Virtual Environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# 4. Install dependencies
echo "Installing package dependencies..."
./venv/bin/pip install --upgrade pip
if ! ./venv/bin/pip install -r requirements.txt; then
    echo "------------------------------------------------------------------------"
    echo "[WARNING] Python package installation encountered compilation errors."
    echo "This is typically caused by 'dlib' source compilation constraints under"
    echo "experimental/unstable Python versions (like 3.14) on Apple Silicon."
    echo "To resolve this:"
    echo "  1. Install dlib via Homebrew: brew install dlib"
    echo "  2. Or, use a stable Python version (3.11 or 3.12) to build the environment."
    echo "The native C++ PAM module compilation will still proceed."
    echo "------------------------------------------------------------------------"
fi


# 5. Initialize config directories
echo "Creating daemon runtime directories..."
mkdir -p "$HOME/.faceunlock_run"
mkdir -p "assets/profiles"

# 6. Copy default config if not present
if [ ! -f "configs/config.json" ]; then
    echo "Initializing default config..."
    mkdir -p configs
    cat <<EOT > configs/config.json
{
    "distance_threshold": 0.45,
    "challenge_yaw_threshold": 12.0,
    "timeout_seconds": 5,
    "socket_path": "~/.faceunlock_run/faceunlock.sock",
    "headless": true,
    "camera_id": 0,
    "liveness_buffer_size": 5
}
EOT
fi

# 7. Build C++ PAM module
echo "Compiling pluggable authentication module..."
cd pam
make clean
make
cd ..

echo "=== Bootstrap Successful! ==="
echo "You can now enroll your face using:"
echo "  ./venv/bin/python vision_daemon/core/encoder.py --username $USER"
echo "To run the unit test suite:"
echo "  ./venv/bin/python -m unittest discover -s tests -p \"test_*.py\""
