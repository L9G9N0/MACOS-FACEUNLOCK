# Release Lifecycle & Workflows

This document defines the semantic versioning standards, branching models, and validation checklists for creating official releases.

---

## 1. Versioning Standards

This project adheres strictly to [Semantic Versioning (SemVer) 2.0.0](https://semver.org):

```text
MAJOR . MINOR . PATCH
```

- **MAJOR**: Incompatible API socket payload contract changes or breaking architecture refactorings.
- **MINOR**: Backward-compatible new features (e.g. adding new challenge state options to the FSM).
- **PATCH**: Backward-compatible bug fixes (e.g. fixing socket descriptor leak paths).

---

## 2. Release Branching Strategy

- **Development Branching**: All feature additions and bug fixes must trigger pull requests targeting the `main` branch.
- **Release Tagging**: Once changes are merged, developers compile final validation checks on `main` and tag the release version:
  ```bash
  git tag -a v1.0.0 -m "Release version 1.0.0"
  git push origin v1.0.0
  ```

---

## 3. Pre-Release Validation Checklist

Before tagging any release version, developers must execute this validation loop:

- [ ] Run diagnostic checks (`./scripts/check_env.sh`) and verify all requirements match.
- [ ] Execute the full unit and integration test suite (`./venv/bin/python -m unittest discover -s tests -p "test_*.py"`) and verify 100% of cases pass.
- [ ] Verify the compiled library (`pam/pam_faceunlock.so`) is signed successfully and contains no dynamic memory leak risks.
- [ ] Update `CHANGELOG.md` with description logs of the release contents.
