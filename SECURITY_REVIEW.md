# Security Review: macOS FaceUnlock Platform

This document details the security posture, vulnerability vectors, threat models, and architectural hardening applied to the macOS FaceUnlock module.

---

## 1. Threat Modeling & Vulnerability Vector Assessment

### 1.1 Local Socket Spoofing & Privilege Escalation (Resolved)
- **Vulnerability**: UNIX domain sockets created by root but writable by everyone (`0777` permissions) allow unprivileged local processes to write mock success payloads (such as `"AUTH_SUCCESS_HARIOM"`) and bypass lock screens.
- **Hardening**:
  1. **User Ownership Constraint**: The PAM module creates the socket and changes its owner to the logging-in user (`chown` dynamically to the authenticating user UID/GID).
  2. **Restrictive DAC Permissions**: File permissions are set strictly to `0600` (readable/writable only by the owner user).
  3. **macOS Peer Credentials Verification**: The C++ PAM module calls `getsockopt` with the `LOCAL_PEERCRED` option to check that the connecting process UID matches the target logging user's UID. Connections from other processes are dropped immediately.

### 1.2 Facial Presentation Spoofing Attacks (Resolved)
- **Vulnerability**: 2D facial recognition through webcam feeds can be bypassed using high-resolution print photos or video playbacks on mobile screens.
- **Hardening**:
  - **Randomized Challenge-Response**: Uses a 3D Pose Transformation Matrix (from the landmarker task) to calculate head yaw angles. The state machine remains locked until the user rotates their head left or right (randomly selected on session start) and returns center. This cannot be spoofed by flat screens or static prints.

### 1.3 System Lockout Prevention (Resolved)
- **Vulnerability**: If the camera is unavailable, lighting is poor, or the python daemon crashes, the system could hang at authentication prompts.
- **Hardening**:
  - **Select Timeouts**: The PAM library uses `select()` to wait for socket connections for a maximum of 5 seconds. If the timer expires, the module unlinks the socket and returns `PAM_IGNORE`, cleanly falling back to password/Touch ID login prompts.
