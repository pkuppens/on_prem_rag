#!/usr/bin/env python3
"""Setup git hooks for the project.

This script installs the tracked ``githooks/pre-push`` template into
``.git/hooks/pre-push`` to enforce unit test passing before every push.
The hook itself is a single POSIX script that runs unmodified on both
Windows (via Git for Windows' bundled ``sh``) and Unix.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

EXECUTABLE_MODE = stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH


def setup_pre_push_hook(project_root: Path | None = None) -> bool:
    """Install the tracked pre-push hook template into .git/hooks/pre-push."""
    project_root = project_root or Path(__file__).parent.parent
    hooks_dir = project_root / ".git" / "hooks"
    hook_source = project_root / "githooks" / "pre-push"
    hook_target = hooks_dir / "pre-push"

    if not hooks_dir.exists():
        print("Error: .git/hooks directory not found. Are you in a git repository?")
        return False

    if not hook_source.exists():
        print(f"Error: hook template not found at {hook_source}")
        return False

    shutil.copy2(hook_source, hook_target)
    os.chmod(hook_target, EXECUTABLE_MODE)

    print("[OK] Pre-push hook installed successfully!")
    print(f"   Hook location: {hook_target}")

    return True


def verify_hook_setup(project_root: Path | None = None) -> bool:
    """Verify that the hook is installed and can actually execute."""
    project_root = project_root or Path(__file__).parent.parent
    hook_path = project_root / ".git" / "hooks" / "pre-push"

    if not hook_path.exists():
        print("[ERROR] Pre-push hook not found")
        return False

    if not os.access(hook_path, os.X_OK):
        print("[ERROR] Pre-push hook is not executable")
        return False

    # Only try "sh": it's what Git for Windows itself uses to run hooks, and is
    # bundled alongside git regardless of the invoking shell. Falling back to a
    # generic "bash" lookup risks resolving to an unrelated launcher (e.g. the
    # Windows/WSL bash stub in System32), which fails on Windows-style paths and
    # would misreport a working hook as broken.
    interpreter = shutil.which("sh")
    if interpreter is None:
        print("[WARN] Could not find 'sh' on PATH — skipping execution check.")
        print("       Git itself invokes hooks through its own bundled sh, so this")
        print("       does not necessarily mean the hook is broken.")
        print("[OK] Pre-push hook is installed (execution not independently verified)")
        return True

    result = subprocess.run(
        [interpreter, str(hook_path)],
        env={**os.environ, "PRE_PUSH_SELF_TEST": "1"},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("[ERROR] Pre-push hook failed to execute (self-test):")
        print(result.stdout)
        print(result.stderr)
        return False

    print("[OK] Pre-push hook is properly configured and executes successfully")
    return True


def main() -> int:
    """Main function to set up git hooks."""
    print("Setting up git hooks for unit test enforcement...")

    if not setup_pre_push_hook():
        print("[ERROR] Failed to set up git hooks")
        return 1

    print("\n" + "=" * 60)
    print("GIT HOOK SETUP COMPLETE")
    print("=" * 60)
    print("The pre-push hook will now enforce code quality and unit tests.")
    print("\nHow it works:")
    print("• Before every git push, automatic linting and formatting runs")
    print("  - Runs 'ruff check --fix' to auto-fix linting issues")
    print("  - Runs 'ruff format' to auto-format code")
    print("  - Auto-stages any fixed files (no confirmation needed)")
    print("• Then runs unit tests automatically")
    print("• If linting or tests fail, the push will be blocked")
    print("• Only fast unit tests run (excludes slow and internet tests)")
    print("\nAuto-fixed files:")
    print("• Files modified by ruff are automatically staged")
    print("• Review staged changes before pushing if needed")
    print("\nEmergency bypass option:")
    print("• Git flag: git push --no-verify")
    print("\nThis bypass should only be used in emergency situations!")
    print("=" * 60)

    if not verify_hook_setup():
        print("\n[ERROR] Setup verification failed!")
        return 1

    print("\n[OK] Setup verification passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
