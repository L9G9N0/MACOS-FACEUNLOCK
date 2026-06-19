# Support Guide

Thank you for using macOS FaceUnlock. Here are the channels and processes for obtaining support.

---

## 1. Troubleshooting Checklist

Before opening an issue or asking for support, please perform the following checks:
1. Verify system components and dependencies using the diagnostic tool:
   ```bash
   ./scripts/check_env.sh
   ```
2. Verify that your camera has permissions enabled. If you see camera errors, check if you have allowed terminal/python to access the camera under:
   `System Settings -> Privacy & Security -> Camera`
3. Inspect active runtime log traces:
   ```bash
   tail -n 50 ~/.faceunlock_run/faceunlock.log
   ```

---

## 2. Support Channels

### GitHub Issues (Recommended)
- **Bug Reports**: For software errors or daemon crashes, use the **Bug Report Template** on the GitHub Issue Tracker.
- **Feature Requests**: To suggest enhancements or support for custom cameras, use the **Feature Request Template**.
- **Questions**: For assistance with installation or configuration setups, submit a question.

### Email Support
For direct inquiries or architectural alignment discussions, contact the maintainer at **hariom24229@iiitd.ac.in**.
