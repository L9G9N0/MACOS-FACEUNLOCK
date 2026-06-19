# Engineering Roadmap

This document outlines the planned technical milestones and features for the macOS FaceUnlock platform.

---

## 1. Short-Term Objectives (Q3 2026)

### Rust Transition for Vision Daemon
- **Goal**: Port the daemon stream processing and local UNIX socket server from Python to Rust.
- **Why**: Enforces compile-time memory safety guarantees, reduces daemon CPU overhead below 1% in active monitoring loops, and produces a single binary distribution package without Python virtualenv dependencies.

### Supply Chain Security Hardening
- **Goal**: Implement dynamic SHA-256 validation checks for the MediaPipe TFLite landmarker tasks model files before starting the vision loop.
- **Why**: Detects on-disk model tampers or unauthorized binary model swap attempts.

---

## 2. Mid-Term Objectives (Q4 2026)

### macOS Local Library Validation & Code Signing
- **Goal**: Integrate unified compile targets inside the Makefile to handle ad-hoc and Apple Developer code signing boundaries for the `pam_faceunlock.so` dynamic library.
- **Why**: Eliminates gatekeeper validation conflicts on macOS Sequoia/Sonoma.

### Camera Hardware Integrity Verification
- **Goal**: Read system hardware metadata to verify that webcam feed frames originate from the FaceTime HD Camera, preventing fake camera injection attacks (virtual webcams).
- **Why**: Hardens presentation attack detection.

---

## 3. Long-Term Objectives (2027)

### Swift UI System Configuration Panel
- **Goal**: Build a native macOS configuration GUI in Swift to manage profiles (enrollment, export, removals) and slide thresholds visually.
- **Why**: Simplifies setup workflows.
