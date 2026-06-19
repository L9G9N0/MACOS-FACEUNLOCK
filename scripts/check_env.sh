#!/bin/bash
# Environment Checker & Config Validator for macOS FaceUnlock

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== System Environment Checker ==="

# 1. OS Verification
OS_NAME=$(uname)
if [ "$OS_NAME" != "Darwin" ]; then
    echo "[WARNING] This platform is designed specifically for macOS (Darwin). Running on $OS_NAME is not supported."
else
    echo "[OK] Platform: macOS"
fi

# 2. Xcode command line tools
if xcode-select -p &>/dev/null; then
    echo "[OK] Xcode Command Line Tools installed."
else
    echo "[WARNING] Xcode Command Line Tools are missing. You may need to run: xcode-select --install"
fi

# 3. Python venv check
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "[OK] Local venv virtual environment folder found."
    
    # Check packages
    echo "Verifying package imports inside venv..."
    if ! "$PROJECT_ROOT/venv/bin/python" -c "import numpy; import cv2; import mediapipe;" &>/dev/null; then
        echo "[ERROR] Key python packages (numpy, cv2, mediapipe) could not be loaded in venv. Run bootstrap.sh first."
        exit 1
    else
        echo "[OK] Key packages imported successfully."
    fi
else
    echo "[ERROR] Python venv directory not found at $PROJECT_ROOT/venv. Run bootstrap.sh first."
    exit 1
fi

# 4. Config validation
CONFIG_FILE="$PROJECT_ROOT/configs/config.json"
if [ -f "$CONFIG_FILE" ]; then
    echo "[OK] config.json exists."
    # Validate JSON syntax
    if ! python3 -m json.tool "$CONFIG_FILE" &>/dev/null; then
        echo "[ERROR] config.json is not a valid JSON file."
        exit 1
    else
        echo "[OK] config.json has valid JSON syntax."
    fi
else
    echo "[ERROR] config.json is missing from $CONFIG_FILE."
    exit 1
fi

# 5. Runtime Socket permissions verification
RUN_DIR="$HOME/.faceunlock_run"
if [ -d "$RUN_DIR" ]; then
    PERMS=$(stat -f "%Lp" "$RUN_DIR")
    if [ "$PERMS" -ne "700" ] && [ "$PERMS" -ne "755" ]; then
        echo "[WARNING] Runtime folder $RUN_DIR has permissions $PERMS. Recommending chmod 700 to secure lock socket."
    else
        echo "[OK] Runtime socket folder has correct permissions ($PERMS)."
    fi
else
    echo "[WARNING] Runtime directory $RUN_DIR does not exist. It will be created by bootstrap/daemon."
fi

# 6. Check landmark task file
TASK_FILE="$PROJECT_ROOT/vision_daemon/core/face_landmarker.task"
if [ -f "$TASK_FILE" ]; then
    echo "[OK] MediaPipe face_landmarker.task model file found."
else
    echo "[WARNING] face_landmarker.task is missing at $TASK_FILE. Downloading now..."
    curl -L -o "$TASK_FILE" "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    echo "[OK] face_landmarker.task downloaded successfully."
fi

echo "=== System Environment Verification Passed! ==="
exit 0
