# Technical Architecture Spec: macOS FaceUnlock

This document explains the technical architecture, execution boundaries, IPC mechanics, and security controls that define the macOS FaceUnlock platform.

---

## 1. System Topology & Context Boundaries

macOS FaceUnlock operates across two distinct process domains:

```text
+------------------------------+       +-------------------------------+
|      PAM Module Domain       |       |     User-Space Daemon         |
|  (Executes as ROOT or Owner) |       |  (Executes as GUI Login User) |
+------------------------------+       +-------------------------------+
               |                                       |
  [sudo auth trigger]                                  |
               |                                 [Reads Camera]
    1. Bind UNIX Socket                                |
    2. chown to GUI User                               |
    3. Listen (select timeout 5s)                      |
               |                                       v
               |                        [Yaw & Face Embedding Match]
               |                                       |
               |<======= Socket Connection ============| (Client connect)
               |
  4. getsockopt(LOCAL_PEERCRED)
     - Validate connecting PID/UID
  5. Read auth signal
               |
               v
    [Authentication Success]
```

### 1.1 Root/PAM Execution Domain
The Pluggable Authentication Module (`pam_faceunlock.so`) executes within the context of the calling process (such as `sudo` running as root, or `screensaver` running under a system authorization daemon). It acts as the socket server.

### 1.2 User GUI Daemon Domain
The vision daemon (`daemon.py`) runs inside the logged-in user's GUI session as a standard `LaunchAgent`. This is a critical macOS sandboxing constraint: processes running in root system contexts lack FaceTime camera entitlements, whereas standard user GUI sessions can access webcam feeds.

---

## 2. Hardened IPC Socket Protocol

Communication is established using a local UNIX stream socket bound to `~/.faceunlock_run/faceunlock.sock`.

### 2.1 Access Control Constraints
1. **Dynamic Ownership Mapping**: When root loads the PAM module, it unlinks stale sockets and binds a new socket file. It calls `chown()` to transfer the socket owner to the authenticating user's UID and GID.
2. **File Permissions**: The socket is locked down to `0600` permissions (read/write access restricted to the user only).
3. **Peer Credential Auditing**: The C++ PAM module calls `getsockopt` with `LOCAL_PEERCRED`. This yields a `struct xucred` containing the UID of the client process. The PAM module compares `xucred.cr_uid` against the target authentication user's UID. If they do not match, the connection is instantly rejected with `PAM_AUTH_ERR` to block cross-user session tampering.

---

## 3. Active Liveness Estimation State Machine

To prevent spoofing via 2D static media (photos, tablet displays), the daemon runs a 3D head-pose validation state machine:

```text
  +--------------------------+
  | STATE_AWAITING_CHALLENGE | <------+ Timeout / Cooldown Lockout
  +--------------------------+        |
               |                      |
      [Yaw crossed threshold]         |
               v                      |
     +--------------------+           |
     | STATE_CHALLENGE_HELD|          |
     +--------------------+           |
               |                      |
       [Frame step transition]        |
               v                      |
     +--------------------+           |
     |  STATE_RETURNING   | ----------+
     +--------------------+
               |
       [Yaw returned < 6deg]
               v
     +--------------------+
     |  STATE_CONFIRMED   |
     +--------------------+
```

1. **Yaw Calculation**: The MediaPipe Landmarker extracts the 4x4 facial transformation matrix. Applying decomposition yields the head yaw Euler rotation angle.
2. **Direction Randomization**: On session startup, the state machine randomly sets the target direction (LEFT or RIGHT).
3. **Transition Latch**: The user must rotate their head past the threshold angle, hold briefly, and then return to center (yaw angle absolute deviation < 6.0 degrees) to unlock the state.
