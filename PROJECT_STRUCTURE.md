# Project Directory Layout: macOS FaceUnlock

This document describes the directory hierarchy, file purposes, and architectural division of components.

---

## 1. Project Directory Layout

```text
.
├── SECURITY_REVIEW.md       # Comprehensive threat assessment and hardening spec
├── requirements.txt        # Core dependencies list (mediapipe, face-recognition, numpy, cv2)
├── configs/
│   └── config.json          # System config options (thresholds, timeouts, paths)
├── shared/
│   └── utils.py             # Common utilities (JSON config parser, logger initialization)
├── ipc/
│   └── protocol.py          # Socket signal transmitter client
├── pam/
│   ├── Makefile             # Compilation rules for the native PAM module
│   ├── pam_faceunlock.cpp   # Pluggable Authentication Module in C++
│   └── pam_faceunlock.so    # [Local compiled artifact - Git ignored]
├── vision_daemon/
│   ├── daemon.py            # Headless execution loop coordinating components
│   └── core/
│       ├── detector.py      # Face detection and padded bounding box crop generator
│       ├── antispoof.py     # Liveness Euler yaw rotation active FSM challenge
│       ├── recognizer.py    # Multi-identity dlib vector matching controller
│       ├── encoder.py       # Enrollment CLI helper
│       └── face_landmarker.task # Local model asset binary
├── tests/
│   ├── __init__.py          # Test suite package definition
│   ├── test_antispoof.py    # Verification cases for liveness challenges FSM
│   ├── test_daemon.py       # Frame reading iteration loops test cases
│   ├── test_ipc.py          # UNIX domain socket transmission tests
│   └── test_recognizer.py   # Identity registration database test cases
└── scripts/
    ├── bootstrap.sh         # Dependencies setup and PAM module compilation script
    ├── check_env.sh         # JSON schema config validation and environment diagnostic checker
    ├── install.sh           # Copies PAM library and registers LaunchAgent plist service
    └── uninstall.sh         # Service cleaner and binary paths uninstaller
```

---

## 2. Directory Separation of Concerns

- **`pam/` (Native Kernel Bridge)**: Contains native C++ codes that compile into dynamic library binaries. It interfaces with the macOS PAM library hooks.
- **`vision_daemon/` (Core Computer Vision)**: Contains the Python models interfaces, frame processing buffers, landmarker trackers, and facial recognition logic.
- **`tests/` (Verification Boundary)**: Contains zero-dependency mocked tests to run validation suites in sandbox environments or CI runners.
- **`scripts/` (DevOps & Orchestration)**: Shell scripts managing environment lifecycles, configs validation, and launchd process registration.
