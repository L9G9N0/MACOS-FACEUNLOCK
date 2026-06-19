# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-06-19

### Added
- Created a robust Active Liveness Challenge state machine resolving 2D visual presentation attacks using facial yaw Euler rotation values.
- Implemented C++ PAM module logic checking connecting client processes with `LOCAL_PEERCRED` getsockopt UID validation.
- Added user-only discretionary permissions controls (`0600`) and dynamic root `chown` owner settings to runtime sockets.
- Integrated structured configs directory structure managing threshold parameters.
- Designed 12 zero-dependency unit and integration tests.
- Designed setup, validation checks, uninstallation, and installer agents plist scripts.

### Changed
- Flattened the codebase directory layout into modular groups (`vision_daemon/`, `pam/`, `ipc/`, `shared/`, `configs/`).

### Removed
- Deleted old nested build folders and obsolete test logs.
