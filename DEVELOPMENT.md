# Developer Guide: macOS FaceUnlock

This guide details compilation procedures, testing standards, code signing steps, and development workflows.

---

## 1. Local Environment Setup

To initialize the project dependencies and compile the PAM binary on your local machine:
```bash
./scripts/bootstrap.sh
```

### Dependency Validation
Verify that all system requirements, compiler options, and directory paths are valid using the diagnostics script:
```bash
./scripts/check_env.sh
```

---

## 2. Compiling the C++ PAM Module

The PAM dynamic library compilation is automated using a local `Makefile` inside the `pam/` directory.

To manually re-build:
```bash
cd pam
make clean
make
```

---

## 3. macOS Code Signing (Critical for Library Validation)

Modern versions of macOS (such as Sonoma and Sequoia) enforce library validation. Unsigned dynamic libraries loaded by system boundaries (like `/etc/pam.d/sudo` executing in a root context) can be blocked by gatekeeper.

If you compile locally, you must sign the binary using ad-hoc codesigning:
```bash
codesign --force --sign - pam/pam_faceunlock.so
```

To verify the signature state:
```bash
codesign -dvv pam/pam_faceunlock.so
```

---

## 4. Running the Test Suite

The automated tests are designed to execute with zero dependencies or hardware camera triggers using mock interfaces. Ensure tests run successfully after modifying any logic:
```bash
./venv/bin/python -m unittest discover -s tests -p "test_*.py"
```

---

## 5. Development Code Style

### Python Formatting
- Conform to Python type annotation standards.
- Write docstrings using the **Google style** format guidelines.

### C++ Constraints
- Use standard C++17 compilers (`std=c++17` target standard).
- Keep modules header dependency bindings minimal and clean.
