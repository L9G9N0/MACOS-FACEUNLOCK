#!/bin/bash
# Installation script for macOS FaceUnlock

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== macOS FaceUnlock Installation Tool ==="

# 1. Ensure we have sudo permissions
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] This installer requires root privileges. Please run as: sudo ./scripts/install.sh"
    exit 1
fi

# Detect authenticating non-root user
SUDO_USER_NAME="${SUDO_USER:-$USER}"
SUDO_USER_HOME=$(eval echo "~$SUDO_USER_NAME")

echo "Installing FaceUnlock for system user: $SUDO_USER_NAME"
echo "Project Root: $PROJECT_ROOT"

# 2. Compile PAM module if needed
if [ ! -f "$PROJECT_ROOT/pam/pam_faceunlock.so" ]; then
    echo "Compiled PAM binary missing. Building..."
    cd "$PROJECT_ROOT/pam"
    make
    cd "$PROJECT_ROOT"
fi

# 3. Create PAM directory and install library
echo "Installing C++ PAM library..."
mkdir -p /usr/local/lib/pam
cp "$PROJECT_ROOT/pam/pam_faceunlock.so" /usr/local/lib/pam/
chown root:wheel /usr/local/lib/pam/pam_faceunlock.so
chmod 444 /usr/local/lib/pam/pam_faceunlock.so
echo "[OK] Installed pam_faceunlock.so to /usr/local/lib/pam/"

# 4. Generate macOS LaunchAgent plist dynamically
LAUNCH_AGENT_DIR="$SUDO_USER_HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENT_DIR/com.faceunlock.daemon.plist"
PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"
DAEMON_SCRIPT="$PROJECT_ROOT/vision_daemon/daemon.py"
LOG_DIR="$SUDO_USER_HOME/.faceunlock_run"

echo "Generating LaunchAgent configuration..."
mkdir -p "$LAUNCH_AGENT_DIR"
mkdir -p "$LOG_DIR"

cat <<EOT > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.faceunlock.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>$DAEMON_SCRIPT</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/faceunlock_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/faceunlock_stderr.log</string>
</dict>
</plist>
EOT

# Set correct LaunchAgent file ownership to the GUI user
chown "$SUDO_USER_NAME" "$PLIST_FILE"
chmod 644 "$PLIST_FILE"
echo "[OK] Registered LaunchAgent at $PLIST_FILE"

# 5. Output installation completion instructions
echo ""
echo "=== INSTALLATION COMPLETED SUCCESSFULLY ==="
echo ""
echo "Follow these steps to complete integration:"
echo "1. Start the background vision daemon agent (Run as GUI user, NOT root):"
echo "   launchctl load -w $PLIST_FILE"
echo ""
echo "2. Integrate PAM module with sudo settings:"
echo "   Add the following line to the TOP of /etc/pam.d/sudo:"
echo "   auth       sufficient     /usr/local/lib/pam/pam_faceunlock.so"
echo ""
echo "3. Lock screen integration (Optional):"
echo "   Add the same line to the TOP of /etc/pam.d/screensaver"
echo ""
echo "Remember to enroll your face vector first before using FaceUnlock!"
