# macOS FaceUnlock Platform

[![Release Version](https://img.shields.io/github/v/release/L9G9N0/MACOS-FACEUNLOCK?style=flat-square)](https://github.com/L9G9N0/MACOS-FACEUNLOCK/releases)
[![License](https://img.shields.io/github/license/L9G9N0/MACOS-FACEUNLOCK?style=flat-square)](LICENSE)
[![Python Compatibility](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square)](https://www.python.org)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)](#)
[![GitHub Stars](https://img.shields.io/github/stars/L9G9N0/MACOS-FACEUNLOCK?style=flat-square)](https://github.com/L9G9N0/MACOS-FACEUNLOCK/stargazers)
[![GitHub Open Issues](https://img.shields.io/github/issues/L9G9N0/MACOS-FACEUNLOCK?style=flat-square)](https://github.com/L9G9N0/MACOS-FACEUNLOCK/issues)
[![GitHub Forks](https://img.shields.io/github/forks/L9G9N0/MACOS-FACEUNLOCK?style=flat-square)](https://github.com/L9G9N0/MACOS-FACEUNLOCK/network/members)
[![Latest Release](https://img.shields.io/github/v/release/L9G9N0/MACOS-FACEUNLOCK?include_prereleases&label=release&style=flat-square)](https://github.com/L9G9N0/MACOS-FACEUNLOCK/releases)

An enterprise-grade, offline face authentication platform designed for macOS. This platform implements a secure, local biometric authentication flow using standard FaceTime RGB webcams, integrating directly into the macOS PAM boundary.

---

## Table of Contents
- [Overview](#overview)
- [Why This Project Exists](#why-this-project-exists)
- [Features](#features)
- [Architecture & System Design](#architecture--system-design)
- [Folder Structure](#folder-structure)
- [Technology Stack](#technology-stack)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Configuration](#configuration)
- [Running Locally](#running-locally)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Security Model](#security-model)
- [Performance Optimizations](#performance-optimizations)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Deployment](#deployment)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Code Style](#code-style)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Maintainers](#maintainers)
- [Support](#support)
- [Future Work](#future-work)

---

## Overview

macOS FaceUnlock provides software-based biometric unlock mechanisms on macOS systems by combining computer vision pipelines in user-space with a hardened kernel-level authentication module written in C++. It eliminates the threat of static photo spoofing using a randomized 3D challenge-response state machine.

---

## Why This Project Exists

### Problem Statement
Standard MacBook hardware lacks infrared (IR) dot projectors or structured-light depth sensors. Traditional 2D face matching engines using flat webcam images are highly vulnerable to presentation attacks (e.g., holding up a high-resolution printed photo or video loop on an iPad). Additionally, running biometric loops directly under root-level contexts exposes systems to local privilege escalation vectors via UNIX domain socket spoofing.

### Solution
macOS FaceUnlock solves these vulnerabilities by:
1. Moving face landmarks processing into a user-space daemon executing under the target user's session context.
2. Implementing an active liveness FSM checking real-time 3D head yaw rotation values derived from facial projection matrices.
3. Securing kernel-to-daemon communication using a UNIX stream socket bound to user home paths with dynamic owner chown configurations and macOS Peer Credentials UID validation.

---

## Screenshots Placeholder

*Visual documentation and runtime console outputs are available in the [Architecture Guide](ARCHITECTURE.md).*

---

## Features

- **Active 3D Liveness Detection**: Measures facial transformation matrixes to compute head rotation, prompting randomized left/right turn challenges.
- **Padded Bounding Crops**: Auto-expanding face cropping checks to ensure hair, neck, and head boundaries are evaluated.
- **Hardened UNIX Domain Socket**: Peer credentials verification enforces that only the authenticating user's local python daemon can dispatch verification signals.
- **Multi-Identity Enrollment**: Enrolls, removes, loads, and manages multiple identity profile files.
- **Fail-Safe Sudo Integration**: Structured `select()` timeouts fall back cleanly to passcode entry, preventing lockout loops.
- **LaunchAgent Automation**: Startup scripts configure, run, and reload background daemons cleanly on macOS login triggers.

---

## Architecture & System Design

```text
+----------------------------------------------------------------------+
|                           macOS Auth Boundary                        |
+----------------------------------------------------------------------+
  | (e.g. sudo / screensaver prompt)
  v
+--------------------------+
|  pam_faceunlock.so (C++) | <------------------+
+--------------------------+                    |
  | (Creates socket, sets 0600)                 | (LOCAL_PEERCRED check
  | (Changes owner to target UID)               |  on client UID)
  v                                             |
+---------------------------------------------+ |
| Path: ~/.faceunlock_run/faceunlock.sock      | |
+---------------------------------------------+ |
  ^                                             |
  | (Dispatches: AUTH_SUCCESS_<username>)       |
  |                                             |
+--------------------------+                    |
|   ipc/protocol.py (Py)   | -------------------+
+--------------------------+
  ^
  | (Liveness verified & profile match)
+--------------------------+
|   vision_daemon (Py)     |
|   - BlazeFace Detection  |
|   - Liveness 3D FSM      |
|   - Face Encodings Match |
+--------------------------+
```

---

## Folder Structure

For a comprehensive explanation of file mappings, review the [Project Structure Guide](PROJECT_STRUCTURE.md).

```text
.
├── SECURITY_REVIEW.md       # Security review documentation
├── requirements.txt        # Core dependencies list
├── configs/
│   └── config.json          # Configuration parameters
├── shared/
│   └── utils.py             # Common config & logger modules
├── ipc/
│   └── protocol.py          # Socket transmitter client
├── pam/
│   ├── Makefile             # C++ compiler parameters
│   └── pam_faceunlock.cpp   # Native macOS PAM module
├── vision_daemon/
│   ├── daemon.py            # Headless loop coordinator
│   └── core/
│       ├── detector.py      # Face detector landmarker
│       ├── antispoof.py     # Liveness 3D Euler state machine
│       ├── recognizer.py    # Identity embeddings controller
│       └── encoder.py       # User face enrollment tool
├── tests/
│   └── test_*.py            # Automated mock test suite
└── scripts/
    ├── bootstrap.sh         # Development dependencies compiler
    ├── check_env.sh         # Diagnostics environment validator
    ├── install.sh           # Library and LaunchAgent installer
    └── uninstall.sh         # Cleanup scripts and service cleaner
```

---

## Technology Stack

- **Core Engine**: C++17, Python 3.10+
- **Machine Learning**: MediaPipe Tasks Vision, dlib
- **Computer Vision**: OpenCV (Python wrapper)
- **Authentication Services**: macOS PAM API (`<security/pam_appl.h>`)
- **System Services**: macOS Launchd (`LaunchAgents`)

---

## Core Components

- **PAM Wrapper (`pam/`)**: Compiles into `pam_faceunlock.so`. Hooks into PAM callbacks to handle `pam_sm_authenticate` challenges.
- **Vision Daemon (`vision_daemon/`)**: Orchestrates the frame capture threads, processes face crops, checks angles, matches profiles, and outputs socket events.
- **Socket Transmitter (`ipc/`)**: Establishes connections, serializes username parameters, and transmits authorization signals.

---

## Data Flow

1. **Authentication Trigger**: User runs `sudo`. PAM loads `pam_faceunlock.so`.
2. **Socket Initialization**: The PAM library creates a UNIX socket at `~/.faceunlock_run/faceunlock.sock`, sets permissions to `0600`, and `chown`s ownership to the target user.
3. **Challenge Validation**: The background Vision Daemon reads camera frames, checks for a matching user, and processes the head-turn challenge.
4. **Identity Verification**: Once liveness is confirmed, the daemon extracts a 128-D vector and checks it against cached profiles.
5. **Authorization Signal**: If verified, the daemon connects to the socket. The PAM module verifies the connecting process UID using `LOCAL_PEERCRED`.
6. **Session Access**: On success, the PAM module unlinks the socket and returns `PAM_SUCCESS`.

---

## Installation

Run the bootstrap tool to initialize paths and compile binaries:
```bash
./scripts/bootstrap.sh
```
Follow the detailed setup guides in [Installation Manual](DEVELOPMENT.md).

---

## Environment Variables

This platform relies on system configurations rather than external environment variables. Model directories and runtime folders are resolved dynamically using user home directory definitions (`$HOME`).

---

## Configuration

System-wide properties are loaded from [configs/config.json](configs/config.json). Detailed definitions are listed in the [Configuration Guide](#configuration-guide).

---

## Running Locally

Run the diagnostic verification script first:
```bash
./scripts/check_env.sh
```
To test the daemon user loop locally in headless mode:
```bash
./venv/bin/python vision_daemon/daemon.py
```

---

## Usage

To register your identity in the database:
```bash
./venv/bin/python vision_daemon/core/encoder.py --username $USER
```
For dynamic GUI monitor displays, set `"headless": false` in `configs/config.json`.

---

## API Reference

The UNIX socket interface acts as an internal IPC channel. The transaction details are documented in the [API Contract Specification](API.md).

---

## Configuration Guide

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `distance_threshold` | float | `0.45` | Distance score for identity matching. |
| `challenge_yaw_threshold` | float | `12.0` | Target angle deviation in degrees. |
| `timeout_seconds` | int | `5` | Maximum socket listening wait time. |
| `socket_path` | string | `~/.faceunlock_run/...` | Path to socket file. |
| `headless` | bool | `true` | Runs daemon without creating UI windows. |
| `camera_id` | int | `0` | Camera device system index. |
| `liveness_buffer_size` | int | `5` | Buffer queue size for liveness frames. |

---

## Security Model

The security configurations of this platform are described in the [Security Policy](SECURITY.md) and [SECURITY_REVIEW.md](SECURITY_REVIEW.md).

---

## Performance Optimizations

- **RAM Caching**: Enrolment JSON profiles are parsed once during daemon startup and stored in memory to prevent disk read latencies during authentication triggers.
- **Headless CPU Optimizations**: Frame processing loops utilize brief sleep intervals (`time.sleep(0.02)`) in headless mode to limit CPU cycles.
- **Hardware-Level Decoupling**: Landmark math models compile dynamically on CPU/GPU without thread-locking boundaries.

---

## Error Handling

- **Camera Failures**: The daemon logs warnings and retries frame retrieval.
- **Socket Unlink Safety**: The PAM module cleans and unlinks the socket path under all return vectors (success, timeout, failure).
- **Graceful Password Fallback**: Returns `PAM_IGNORE` on timeout, falling back cleanly to traditional macOS authentication.

---

## Testing

Run the zero-dependency automated unit and integration tests:
```bash
./venv/bin/python -m unittest discover -s tests -p "test_*.py"
```

---

## Deployment

Install the compiled module and LaunchAgent configurations:
```bash
sudo ./scripts/install.sh
```

---

## Roadmap

Upcoming enhancements, including transitioning the daemon to Rust, are listed in [Engineering Roadmap](ROADMAP.md).

---

## Contributing

Review structural development standards and pull request workflows in [Contributing Guidelines](CONTRIBUTING.md).

---

## Code Style

- **Python**: Conforms to Python type hint standards and uses Google docstring formats.
- **C++**: Follows native systems formatting standards (`std=c++17` target constraints).

---

## License

This repository is distributed under the terms of the MIT License. Details are available in [LICENSE](LICENSE).

---

## Acknowledgements

- Google MediaPipe team for on-device landmarkers.
- Davis King for the dlib library.
- Apple security documentation for local authentication boundaries.

---

## Maintainers

- **Hariom** (hariom24229@iiitd.ac.in)

---

## Support

For usage issues or platform bugs, review the [Support Policy](SUPPORT.md).

---

## Future Work

- Implement multi-camera selector checks.
- Add hardware validation checks for raw camera input source verification.
