"""Tests for scripts/setup_git_hooks.py.

Covers the fresh-clone install path for issue #175: the tracked
``githooks/pre-push`` template must be copied byte-for-byte into
``.git/hooks/pre-push``, made executable, and actually verified to execute
(not just checked for existence/executable bit).
"""

import os
import shutil
import stat
from pathlib import Path

import pytest

from scripts.setup_git_hooks import setup_pre_push_hook, verify_hook_setup

REAL_HOOK_SOURCE = Path(__file__).parent.parent / "githooks" / "pre-push"


@pytest.fixture
def fake_project_root(tmp_path: Path) -> Path:
    """Build a fake project root with .git/hooks/ and a copy of the real hook template."""
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    githooks_dir = tmp_path / "githooks"
    githooks_dir.mkdir()
    shutil.copy2(REAL_HOOK_SOURCE, githooks_dir / "pre-push")
    return tmp_path


class TestSetupPrePushHook:
    """Test installation of the tracked hook template."""

    def test_copies_hook_content_byte_for_byte(self, fake_project_root: Path):
        """As a user I want the installed hook to match the tracked template exactly.

        Guards against the pre-#175 bug where the Unix branch copied
        .git/hooks/pre-push onto itself instead of installing a real template.
        """
        assert setup_pre_push_hook(fake_project_root) is True

        installed = fake_project_root / ".git" / "hooks" / "pre-push"
        assert installed.read_bytes() == REAL_HOOK_SOURCE.read_bytes()

    def test_sets_executable_bit(self, fake_project_root: Path):
        """Installed hook must be marked executable so git can run it directly."""
        setup_pre_push_hook(fake_project_root)

        installed = fake_project_root / ".git" / "hooks" / "pre-push"
        assert os.access(installed, os.X_OK)

    def test_returns_false_when_git_hooks_dir_missing(self, tmp_path: Path):
        """Fails clearly when not run inside a git repository."""
        assert setup_pre_push_hook(tmp_path) is False

    def test_returns_false_when_template_missing(self, tmp_path: Path):
        """Fails clearly when the tracked githooks/pre-push template is absent."""
        (tmp_path / ".git" / "hooks").mkdir(parents=True)
        assert setup_pre_push_hook(tmp_path) is False


class TestVerifyHookSetup:
    """Test that verification actually exercises the installed hook.

    As a user I want setup to fail loudly when the hook can't actually run,
    so I can trust "setup succeeded" instead of discovering a broken hook
    only when a real push silently skips enforcement (the pre-#175 bug).
    """

    def test_returns_false_when_hook_missing(self, tmp_path: Path):
        """No hook installed at all must be reported as not configured."""
        assert verify_hook_setup(tmp_path) is False

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Windows has no meaningful X_OK bit — os.access(X_OK) is a no-op there",
    )
    def test_returns_false_when_hook_not_executable(self, fake_project_root: Path):
        """A present but non-executable hook file must be reported as broken."""
        installed = fake_project_root / ".git" / "hooks" / "pre-push"
        installed.write_text("#!/bin/sh\nexit 0\n")
        os.chmod(installed, stat.S_IRUSR | stat.S_IWUSR)  # not executable

        assert verify_hook_setup(fake_project_root) is False

    def test_self_test_executes_successfully_when_interpreter_available(self, fake_project_root: Path):
        """Verification actually runs the hook (PRE_PUSH_SELF_TEST=1), not just stat() checks."""
        if shutil.which("sh") is None:
            pytest.skip("no sh interpreter available on PATH")

        setup_pre_push_hook(fake_project_root)

        assert verify_hook_setup(fake_project_root) is True

    def test_degrades_gracefully_with_no_interpreter_on_path(self, fake_project_root: Path, monkeypatch: pytest.MonkeyPatch):
        """Missing 'sh' on PATH must warn, not hard-fail — git runs hooks via its own bundled sh."""
        setup_pre_push_hook(fake_project_root)
        monkeypatch.setattr(shutil, "which", lambda _name: None)

        assert verify_hook_setup(fake_project_root) is True

    def test_reports_failure_when_hook_script_itself_fails(self, fake_project_root: Path):
        """A hook that installs cleanly but errors at runtime must fail verification."""
        if shutil.which("sh") is None:
            pytest.skip("no sh interpreter available on PATH")

        installed = fake_project_root / ".git" / "hooks" / "pre-push"
        installed.write_text('#!/bin/sh\necho "boom" >&2\nexit 1\n')
        os.chmod(installed, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

        assert verify_hook_setup(fake_project_root) is False
