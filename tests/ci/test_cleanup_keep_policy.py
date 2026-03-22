"""Tests for GitHub Actions cleanup keep policy (Step 4 semantics).

As a maintainer I want retention rules to match the bash cleanup script, so automated
cleanup deletes superseded passes and old failures while keeping the latest green and
post-green regressions.
Technical: compute_keep_database_ids must match scripts/cleanup-github-actions.sh Step 4.
"""

from __future__ import annotations

from tests.ci.cleanup_keep_policy import compute_keep_database_ids


def test_latest_pass_and_failures_after_main() -> None:
    """Latest success on main is kept; older passes and failures before it are dropped; failures after stay."""

    wf = "Python CI"
    br = "main"
    existing = {br}
    active = {wf}
    data = [
        {
            "databaseId": 409,
            "status": "completed",
            "conclusion": "failure",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-22T09:10:26Z",
        },
        {
            "databaseId": 411,
            "status": "completed",
            "conclusion": "failure",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-22T09:10:53Z",
        },
        {
            "databaseId": 415,
            "status": "completed",
            "conclusion": "success",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-22T09:42:00Z",
        },
    ]
    keep = compute_keep_database_ids(data, existing, active)
    assert keep == {"415"}


def test_failure_after_latest_pass_kept() -> None:
    """A failed run after the latest pass is kept for debugging."""

    wf = "Python CI"
    br = "main"
    existing = {br}
    active = {wf}
    data = [
        {
            "databaseId": 1,
            "status": "completed",
            "conclusion": "success",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-22T10:00:00Z",
        },
        {
            "databaseId": 2,
            "status": "completed",
            "conclusion": "failure",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-22T11:00:00Z",
        },
    ]
    keep = compute_keep_database_ids(data, existing, active)
    assert keep == {"1", "2"}


def test_two_passes_only_newest_kept() -> None:
    """Older successful runs are removed when a newer pass exists."""

    wf = "Lint"
    br = "feature/x"
    existing = {br}
    active = {wf}
    data = [
        {
            "databaseId": 10,
            "status": "completed",
            "conclusion": "success",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-20T10:00:00Z",
        },
        {
            "databaseId": 11,
            "status": "completed",
            "conclusion": "success",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-21T10:00:00Z",
        },
    ]
    keep = compute_keep_database_ids(data, existing, active)
    assert keep == {"11"}


def test_no_success_keeps_newest_completed_only() -> None:
    """When there is no passed run, only the most recent completed run is kept."""

    wf = "Python CI"
    br = "main"
    existing = {br}
    active = {wf}
    data = [
        {
            "databaseId": 1,
            "status": "completed",
            "conclusion": "failure",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-22T09:00:00Z",
        },
        {
            "databaseId": 2,
            "status": "completed",
            "conclusion": "cancelled",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-22T10:00:00Z",
        },
    ]
    keep = compute_keep_database_ids(data, existing, active)
    assert keep == {"2"}


def test_in_progress_run_always_kept() -> None:
    """Non-completed runs are never dropped in Step 4."""

    wf = "Python CI"
    br = "main"
    existing = {br}
    active = {wf}
    data = [
        {
            "databaseId": 99,
            "status": "in_progress",
            "conclusion": "",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-22T12:00:00Z",
        },
        {
            "databaseId": 100,
            "status": "completed",
            "conclusion": "success",
            "workflowName": wf,
            "headBranch": br,
            "createdAt": "2026-03-22T09:00:00Z",
        },
    ]
    keep = compute_keep_database_ids(data, existing, active)
    assert "99" in keep and "100" in keep
