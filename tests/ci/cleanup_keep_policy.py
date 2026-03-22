"""Shared logic for workflow run retention (mirrors scripts/cleanup-github-actions.sh Step 4)."""

from __future__ import annotations

from collections import defaultdict


def is_active_run(
    run: dict,
    existing_branches: set[str],
    active_workflows: set[str],
) -> bool:
    """Return True if the run matches active workflow + existing non-PR ref branch."""

    branch = run.get("headBranch", "")
    if not branch or branch.startswith("refs/pull/"):
        return False
    if branch not in existing_branches:
        return False
    if run.get("workflowName", "") not in active_workflows:
        return False
    return True


def compute_keep_database_ids(
    data: list[dict],
    existing_branches: set[str],
    active_workflows: set[str],
) -> set[str]:
    """Return database IDs to keep: in-flight runs, plus Step 4 rules per active workflow+branch."""

    keep: set[str] = set()

    for r in data:
        if r.get("status") != "completed":
            keep.add(str(r["databaseId"]))

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in data:
        if not is_active_run(r, existing_branches, active_workflows):
            continue
        key = f"{r['workflowName']}|{r['headBranch']}"
        groups[key].append(r)

    for runs in groups.values():
        completed = [r for r in runs if r.get("status") == "completed"]
        if not completed:
            continue
        completed.sort(key=lambda x: x["createdAt"], reverse=True)

        successes = [r for r in completed if r.get("conclusion") == "success"]
        if successes:
            latest_pass = max(successes, key=lambda x: x["createdAt"])
            t = latest_pass["createdAt"]
            keep.add(str(latest_pass["databaseId"]))
            for r in completed:
                if r["createdAt"] > t:
                    keep.add(str(r["databaseId"]))
        else:
            keep.add(str(completed[0]["databaseId"]))

    return keep
