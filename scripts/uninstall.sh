#!/bin/bash
# Uninstallation script for macOS FaceUnlock

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== macOS FaceUnlock Uninstallation Tool ==="

# 1. Ensure we run as root
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] This uninstaller requires root privileges. Please run as: sudo ./scripts/uninstall.sh"
    exit 1
fi

SUDO_USER_NAME="${SUDO_USER:-$USER}"
SUDO_USER_HOME=$(eval echo "~$SUDO_USER_NAME")

# 2. Stop and remove the LaunchAgent
PLIST_FILE="$SUDO_USER_HOME/Library/LaunchAgents/com.faceunlock.daemon.plist"
if [ -f "$PLIST_FILE" ]; then
    echo "Stopping and removing GUI daemon LaunchAgent..."
    # Unload as the GUI user, not root
    sudo -u "$SUDO_USER_NAME" launchctl unload "$PLIST_FILE" || true
    rm -f "$PLIST_FILE"
    echo "[OK] Removed LaunchAgent plist."
fi

# 3. Kill any remaining daemon processes
echo "Checking for running daemon processes..."
pids=$(pgrep -f "vision_daemon/daemon.py" || true)
if [ -n "$pids" ]; then
    echo "Terminating daemon processes: $pids"
    kill -9 $pids || true
fi

# 4. Remove C++ PAM module binary
PAM_SO="/usr/local/lib/pam/pam_faceunlock.so"
if [ -f "$PAM_SO" ]; then
    echo "Removing PAM binary..."
    rm -f "$PAM_SO"
    echo "[OK] Removed $PAM_SO"
fi

# 5. Instructions to clean up PAM config
echo ""
echo "=== UNINSTALLATION COMPLETED ==="
echo "All system binaries and configurations have been removed."
echo "Please verify that you have removed the following line from /etc/pam.d/sudo:"
echo "  auth       sufficient     /usr/local/lib/pam/pam_faceunlock.so"
echo "And from /etc/pam.d/screensaver (if added)."
echo ""
echo "Failing to remove this configuration may cause minor validation warnings in your system console."
