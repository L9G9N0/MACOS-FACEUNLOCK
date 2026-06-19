# Contributing to macOS FaceUnlock

Thank you for your interest in contributing to the macOS FaceUnlock platform. To ensure high standards for system safety, security engineering, and codebase maintainability, please review the following guidelines.

---

## 1. Code of Conduct

By participating in this project, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 2. Development Process

### 2.1 Issue Reporting
- Search active issues to avoid duplicates.
- Submit a detailed bug report using the template if you discover validation defects.
- Include OS version, logs from `~/.faceunlock_run/faceunlock.log`, and steps to reproduce.

### 2.2 Pull Request Guidelines
- Always branch from `main`. Use naming structures: `feature/description` or `bugfix/description`.
- Run the environment validations checker (`./scripts/check_env.sh`) and confirm all 12 tests pass successfully:
  ```bash
  ./venv/bin/python -m unittest discover -s tests -p "test_*.py"
  ```
- Keep commits atomic and adhere to [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):
  - `feat: add camera index selector check`
  - `fix: correct socket unlinking on connection error`
- Ensure all public functions are annotated with type hints and documented with Google style docstrings.

---

## 3. Style Guidelines

### Python
- Format Python scripts to conform to pep8 formatting limits (maximum 120-character line width).
- Ensure all public API signatures are explicitly typed.

### C++
- Write C++ code compatible with `std=c++17` standard parameters.
- Do not utilize dynamic heap allocations (`new`/`malloc`) inside core pam loops; keep execution bounds static to prevent memory leaks and segmentation issues.
- Format C++ files with `clang-format` if available.
