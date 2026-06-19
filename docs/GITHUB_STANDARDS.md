# GitHub Repository Standards & Recommendations

This document defines the configurations and organization guidelines for issues, pull requests, project boards, and discussions.

---

## 1. GitHub Labels Recommendations

We recommend configuring the following label classification schema on the GitHub repository:

| Label | Color Code | Description |
| :--- | :--- | :--- |
| `bug` | `#d73a4a` | Validation defects, daemon crashes, or PAM lockouts. |
| `enhancement` | `#a2eeef` | New features, FSM extensions, or hardware support. |
| `security` | `#e11d21` | Vulnerability reports, socket hardening, or permissions updates. |
| `performance` | `#8f28db` | Latency reduction, thread optimizations, or caching changes. |
| `documentation` | `#0075ca` | README updates, architectural specs, or comments polishing. |
| `tests` | `#c5def5` | Automated test suite additions or mock adjustments. |
| `question` | `#d876e3` | Support inquiries, compilation assistance, or installations help. |
| `invalid` | `#e6e6e6` | Issues that are out of scope, duplicated, or not reproducible. |

---

## 2. GitHub Project Board Kanban Structure

To coordinate development cycles, we recommend establishing a GitHub Project board with the following columns:

1. **Backlog**: Open tickets, potential improvements, and roadmap items awaiting prioritization.
2. **Triage**: Newly submitted issues requiring validation, reproducibility checks, or log audits.
3. **To Do**: Prioritized items selected for the current development sprint.
4. **In Progress**: Active coding, compilation, and testing.
5. **Review / QA**: Staged pull requests awaiting code signing checks and test validations.
6. **Done**: Merged pull requests and closed issues.

---

## 3. GitHub Discussions Setup

For questions and showcase features, configure GitHub Discussions with the following categories:

- **Announcements**: Official stable release announcements (Maintainers only).
- **Q&A**: Community support questions regarding camera permissions, Python venvs, or PAM loading.
- **Ideas**: Feature requests and architecture proposals.
- **Show and Tell**: Sharing custom integrations, codesigning scripts, or installations configurations.
