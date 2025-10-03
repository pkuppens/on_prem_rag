#!/usr/bin/env python3
"""Setup git hooks for the project.

This script sets up the pre-push hook to enforce unit test passing.
It detects the operating system and sets up the appropriate hook.
"""

import os
import platform
import shutil
import stat
import sys
from pathlib import Path


def setup_pre_push_hook():
    """Set up the pre-push hook for enforcing unit tests."""
    project_root = Path(__file__).parent.parent
    hooks_dir = project_root / ".git" / "hooks"

    if not hooks_dir.exists():
        print("Error: .git/hooks directory not found. Are you in a git repository?")
        return False

    # Determine the appropriate hook script based on OS
    system = platform.system().lower()

    if system == "windows":
        # Use PowerShell script for Windows
        hook_source = project_root / ".git" / "hooks" / "pre-push.ps1"
        hook_target = hooks_dir / "pre-push"

        # Create a batch file wrapper for Windows
        batch_content = """@echo off
powershell.exe -ExecutionPolicy Bypass -File "%~dp0pre-push.ps1" %*
"""
        with open(hook_target, "w") as f:
            f.write(batch_content)

        # Make the batch file executable (Windows doesn't use chmod, but we set it anyway)
        os.chmod(hook_target, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

    else:
        # Use shell script for Unix-like systems
        hook_source = project_root / ".git" / "hooks" / "pre-push"
        hook_target = hooks_dir / "pre-push"

        # Copy the shell script
        shutil.copy2(hook_source, hook_target)

        # Make it executable
        os.chmod(hook_target, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

    print(f"[OK] Pre-push hook installed successfully!")
    print(f"   Hook location: {hook_target}")
    print(f"   System: {system}")

    return True


def verify_hook_setup():
    """Verify that the hook is properly set up."""
    project_root = Path(__file__).parent.parent
    hook_path = project_root / ".git" / "hooks" / "pre-push"

    if not hook_path.exists():
        print("[ERROR] Pre-push hook not found")
        return False

    # Check if it's executable
    if not os.access(hook_path, os.X_OK):
        print("[ERROR] Pre-push hook is not executable")
        return False

    print("[OK] Pre-push hook is properly configured")
    return True


def main():
    """Main function to set up git hooks."""
    print("Setting up git hooks for unit test enforcement...")

    if setup_pre_push_hook():
        print("\n" + "=" * 60)
        print("GIT HOOK SETUP COMPLETE")
        print("=" * 60)
        print("The pre-push hook will now enforce unit test passing.")
        print("\nHow it works:")
        print("• Before every git push, unit tests will run automatically")
        print("• If tests fail, the push will be blocked")
        print("• Only fast unit tests run (excludes slow and internet tests)")
        print("\nEmergency bypass option:")
        print("• Git flag: git push --no-verify")
        print("\nThis bypass should only be used in emergency situations!")
        print("=" * 60)

        if verify_hook_setup():
            print("\n[OK] Setup verification passed!")
        else:
            print("\n[ERROR] Setup verification failed!")
            return 1
    else:
        print("[ERROR] Failed to set up git hooks")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
