#!/bin/bash
# cleanup-github-actions.sh
# Cleans up obsolete GitHub Actions workflow runs
#
# Targets:
# 1. Runs that required approval but are now obsolete (queued/waiting, old)
# 2. Runs on PR refs (refs/pull/*) - ephemeral, no value after merge/close
# 3. Runs for branches that no longer exist
# 4. Superseded runs per workflow+branch: keep latest passed (success) only;
#    keep all failed runs after that pass (debug); delete everything older
#    on pass: remove all older runs (passes and failures) for the workflow+branch
#    on failure: do not remove anything - everything can be useful for debugging
# 5a. Repository Cleanup self-cleanup (special case: keeps only most recent)
# 5. Orphaned workflow runs (workflow file deleted, runs still exist)
#
# Usage:
# ./cleanup-github-actions.sh # Dry-run (show what would be cleaned)
# ./cleanup-github-actions.sh --execute # Execute cleanup
# ./cleanup-github-actions.sh --help # Show help
#
# Based on: pkuppens/my_chat_gpt
# Requires: gh CLI with workflow scope (gh auth refresh -s workflow)
#
# Safety / scope:
# - Step 4 and 5a never delete runs with status != completed (in-flight stays until done).
# - This script only removes completed runs; it does not gh run cancel duplicates.
# - Repository Cleanup (cleanup.yml) skips until all Python CI runs for the same commit
#   have finished, so automated cleanup does not run while that commit is still building.

set -e

DRY_RUN=true
STALE_DAYS=7 # Runs queued/waiting older than this are considered obsolete

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
  cat << EOF
GitHub Actions Workflow Run Cleanup

Cleans up:
1. Obsolete approval runs - queued/waiting runs older than ${STALE_DAYS} days
2. PR ref runs - all runs on refs/pull/* (ephemeral, no value after merge/close)
3. Runs for branches that no longer exist
4. Superseded runs - latest passed run per workflow+branch; keep failures after it; delete older passes and older failures
5a. Repository Cleanup self-cleanup - keeps only most recent run
5. Orphaned workflow runs - runs for workflow files that have been deleted

Usage:
  $0 # Dry-run
  $0 --execute # Execute cleanup
  $0 --help # This help

Requirements:
- gh CLI installed and authenticated (in PATH)
- Workflow scope: gh auth refresh -s workflow
- On Windows: run from Git Bash or a terminal where 'gh' works
EOF
  exit 0
}

for arg in "$@"; do
  case $arg in
    --execute) DRY_RUN=false ;;
    --help|-h) show_help ;;
    *) print_error "Unknown argument: $arg"; exit 1 ;;
  esac
done

if [ "$DRY_RUN" = true ]; then
  print_warning "DRY-RUN MODE - No changes will be made"
  print_info "Run with --execute to perform cleanup"
  echo ""
fi

command -v gh >/dev/null 2>&1 || { print_error "gh CLI required (ensure it is in PATH). Install: https://cli.github.com/"; exit 1; }
git rev-parse --git-dir >/dev/null 2>&1 || { print_error "Not in a git repository"; exit 1; }
PYTHON="${PYTHON:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null)}"
if [ -z "$PYTHON" ] || ! $PYTHON -c "import json" 2>/dev/null; then
  print_error "python3 or python required (set PYTHON=path/to/python to override)"
  exit 1
fi

REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
print_info "Repository: $REPO"
echo ""

# Fetch latest refs for accurate branch check
print_info "Fetching latest refs..."
git fetch origin --prune 2>/dev/null || true

TEMP_RUNS="$($PYTHON -c "import tempfile, os; fd, p = tempfile.mkstemp(suffix='.json', prefix='cleanup_actions_runs_'); os.close(fd); print(p.replace(os.sep, '/'))")"
gh run list --limit 1000 --json databaseId,status,conclusion,workflowName,headBranch,createdAt > "$TEMP_RUNS"

# Existing branches (local + remote, normalized)
EXISTING_BRANCHES=$(git branch -a | sed 's/remotes\/origin\///' | sed 's/^[* ]*//' | grep -v "HEAD" | sort -u)

# ============================================================================
# STEP 1: Obsolete approval runs (queued/waiting, old)
# ============================================================================
echo "::group::Step 1: Obsolete queued/waiting runs"
print_info "STEP 1: Checking for obsolete queued/waiting runs (older than ${STALE_DAYS} days)..."

STALE_CUTOFF=$($PYTHON -c "from datetime import datetime, timedelta; print((datetime.utcnow() - timedelta(days=${STALE_DAYS})).strftime('%Y-%m-%dT%H:%M:%SZ'))")

OBSOLETE_APPROVAL_IDS=$($PYTHON << PYEOF
import json
from datetime import datetime

with open("$TEMP_RUNS") as f:
  data = json.load(f)

cutoff = "$STALE_CUTOFF"
stale = []
for r in data:
  if r['status'] in ('queued', 'pending', 'waiting'):
    if r.get('createdAt', '') < cutoff:
      stale.append(str(r['databaseId']))
print('\n'.join(stale))
PYEOF
)

OBSOLETE_COUNT=0
OBSOLETE_DELETED=0

for run_id in $OBSOLETE_APPROVAL_IDS; do
  [ -z "$run_id" ] && continue
  OBSOLETE_COUNT=$((OBSOLETE_COUNT + 1))
  if [ "$DRY_RUN" = false ]; then
    print_info "Deleting obsolete run $run_id"
    if echo "y" | gh run delete "$run_id" 2>/dev/null; then
      OBSOLETE_DELETED=$((OBSOLETE_DELETED + 1))
    else
      print_warning "Failed to delete run $run_id (need: gh auth refresh -s workflow)"
    fi
  else
    print_warning "Would delete obsolete run $run_id"
  fi
done

[ $OBSOLETE_COUNT -eq 0 ] && print_success "No obsolete approval runs" || print_warning "Found $OBSOLETE_COUNT obsolete run(s)"
echo "::endgroup::"
echo ""

# ============================================================================
# STEP 2: Runs on PR refs (refs/pull/*)
# ============================================================================
echo "::group::Step 2: PR ref runs"
print_info "STEP 2: Checking for runs on PR refs (refs/pull/*)..."

PR_REF_BRANCHES=$($PYTHON -c "
import json
with open('$TEMP_RUNS') as f:
  data = json.load(f)
seen = set()
for r in data:
  b = r.get('headBranch', '')
  if b.startswith('refs/pull/') and b not in seen:
    seen.add(b)
    print(b)
")

PR_REF_RUNS=0
PR_REF_DELETED=0

while IFS= read -r branch; do
  branch="${branch%$'\r'}"
  [ -z "$branch" ] && continue
  RUN_IDS=$(gh run list --branch "$branch" --limit 1000 --json databaseId --jq '.[].databaseId')
  if [ -n "$RUN_IDS" ]; then
    for run_id in $RUN_IDS; do
      PR_REF_RUNS=$((PR_REF_RUNS + 1))
      if [ "$DRY_RUN" = false ]; then
        print_info "Deleting run $run_id (PR ref '$branch')"
        if echo "y" | gh run delete "$run_id" 2>/dev/null; then
          PR_REF_DELETED=$((PR_REF_DELETED + 1))
        fi
      else
        print_warning "Would delete run $run_id (PR ref '$branch')"
      fi
    done
  fi
done <<< "$PR_REF_BRANCHES"

[ $PR_REF_RUNS -eq 0 ] && print_success "No PR ref runs" || print_warning "Found $PR_REF_RUNS run(s) on PR refs"
echo "::endgroup::"
echo ""

# ============================================================================
# STEP 3: Runs for deleted branches
# ============================================================================
echo "::group::Step 3: Deleted branch runs"
print_info "STEP 3: Checking runs for deleted branches..."

WORKFLOW_BRANCHES=$($PYTHON -c "
import json
with open('$TEMP_RUNS') as f:
  data = json.load(f)
seen = set()
for r in data:
  b = r.get('headBranch', '')
  if b and b not in seen:
    seen.add(b)
    print(b)
")

DELETED_BRANCH_RUNS=0
DELETED_BRANCH_SUCCESS=0

while IFS= read -r branch; do
  branch="${branch%$'\r'}"  # Strip Windows CR
  [ -z "$branch" ] && continue
  # PR refs already handled in Step 2
  case "$branch" in refs/pull/*) continue ;; esac
  # Check if branch exists
  if ! echo "$EXISTING_BRANCHES" | grep -qxF "$branch"; then
    RUN_IDS=$(gh run list --branch "$branch" --limit 1000 --json databaseId --jq '.[].databaseId')
    if [ -n "$RUN_IDS" ]; then
      for run_id in $RUN_IDS; do
        DELETED_BRANCH_RUNS=$((DELETED_BRANCH_RUNS + 1))
        if [ "$DRY_RUN" = false ]; then
          print_info "Deleting run $run_id (branch '$branch' deleted)"
          if echo "y" | gh run delete "$run_id" 2>/dev/null; then
            DELETED_BRANCH_SUCCESS=$((DELETED_BRANCH_SUCCESS + 1))
          fi
        else
          print_warning "Would delete run $run_id (branch '$branch' deleted)"
        fi
      done
    fi
  fi
done <<< "$WORKFLOW_BRANCHES"

[ $DELETED_BRANCH_RUNS -eq 0 ] && print_success "No runs for deleted branches" || print_warning "Found $DELETED_BRANCH_RUNS run(s) for deleted branches"
echo "::endgroup::"
echo ""

# Get active workflow names (needed for Step 4 and Step 5)
ACTIVE_WORKFLOWS=""
for yml_file in .github/workflows/*.yml; do
  [ -f "$yml_file" ] || continue
  WF_NAME=$($PYTHON -c "
import re, sys
with open('$yml_file', encoding='utf-8') as f:
  for line in f:
    m = re.match(r'^name:\s*(.+)', line)
    if m:
      print(m.group(1).strip().strip('\"').strip(\"'\"))
      break
")
  [ -n "$WF_NAME" ] && ACTIVE_WORKFLOWS="$ACTIVE_WORKFLOWS
$WF_NAME"
done

# ============================================================================
# STEP 4: Superseded runs (latest pass + completed runs after it, per workflow+branch)
# ============================================================================
echo "::group::Step 4: Superseded runs (active workflow+branch)"
# Only for runs where workflow exists and branch exists. Steps 3 and 5 handle deleted branches and orphaned workflows.
print_info "STEP 4: Checking superseded runs (keep latest passed run + completed runs after it per active workflow+branch)..."

EXISTING_BRANCHES_FILE="$($PYTHON -c 'import tempfile; fd, p = tempfile.mkstemp(suffix=".txt", prefix="cleanup_branches_"); __import__("os").close(fd); print(p)')"
ACTIVE_WORKFLOWS_FILE="$($PYTHON -c 'import tempfile; fd, p = tempfile.mkstemp(suffix=".txt", prefix="cleanup_wf_"); __import__("os").close(fd); print(p)')"
echo "$EXISTING_BRANCHES" | grep -v '^$' > "$EXISTING_BRANCHES_FILE"
echo "$ACTIVE_WORKFLOWS" | grep -v '^$' > "$ACTIVE_WORKFLOWS_FILE"

KEEP_RUNS=$($PYTHON << PYEOF
import json
from collections import defaultdict

with open("$TEMP_RUNS") as f:
  data = json.load(f)
with open("$EXISTING_BRANCHES_FILE") as f:
  existing_branches = set(l.strip() for l in f if l.strip())
with open("$ACTIVE_WORKFLOWS_FILE") as f:
  active_workflows = set(l.strip() for l in f if l.strip())

def is_active(r):
  branch = r.get("headBranch", "")
  if not branch or branch.startswith("refs/pull/"):
    return False
  if branch not in existing_branches:
    return False
  if r.get("workflowName", "") not in active_workflows:
    return False
  return True

keep = set()

# Never delete in-progress runs from Step 4 (queued / in_progress / etc.)
for r in data:
  if r.get("status") != "completed":
    keep.add(str(r["databaseId"]))

groups = defaultdict(list)
for r in data:
  if not is_active(r):
    continue
  key = r["workflowName"] + "|" + r["headBranch"]
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
    # No passed run: keep only the most recent completed run for this workflow+branch
    keep.add(str(completed[0]["databaseId"]))

print("\n".join(sorted(keep)))
PYEOF
)
rm -f "$EXISTING_BRANCHES_FILE" "$ACTIVE_WORKFLOWS_FILE"

ALL_IDS=$($PYTHON -c "import json; f=open('$TEMP_RUNS'); d=json.load(f); print('\n'.join(str(r['databaseId']) for r in d))")
SUPERSEDED_COUNT=0
SUPERSEDED_DELETED=0

for run_id in $ALL_IDS; do
  run_id="${run_id%$'\r'}"
  [ -z "$run_id" ] && continue
  echo "$KEEP_RUNS" | grep -qxF "$run_id" && continue
  SUPERSEDED_COUNT=$((SUPERSEDED_COUNT + 1))
  if [ "$DRY_RUN" = false ]; then
    RUN_INFO=$($PYTHON -c "
import json
f=open('$TEMP_RUNS')
for r in json.load(f):
  if r['databaseId']==$run_id:
    print(r['workflowName']+' ['+(r.get('conclusion') or r['status'])+'] on '+r['headBranch'])
    break
" 2>/dev/null) || RUN_INFO="(unknown)"
    print_info "Deleting superseded $run_id: $RUN_INFO"
    echo "y" | gh run delete "$run_id" 2>/dev/null && SUPERSEDED_DELETED=$((SUPERSEDED_DELETED + 1)) || true
  fi
done

[ $SUPERSEDED_COUNT -eq 0 ] && print_success "No superseded runs" || print_warning "Found $SUPERSEDED_COUNT superseded run(s)"
echo "::endgroup::"
echo ""

# ============================================================================
# STEP 5a: Repository Cleanup self-cleanup (same keep rules as Step 4)
# ============================================================================
echo "::group::Step 5a: Repository Cleanup self-cleanup"
# Dedicated fetch: this workflow may be sparse in the global Step 4 list (1000-run cap).
# Same semantics as Step 4: latest passed + completed runs after it per branch; drop older passes/failures.
print_info "STEP 5a: Cleaning Repository Cleanup workflow runs (latest pass + runs after it per branch)..."

CLEANUP_WORKFLOW="Repository Cleanup"
CLEANUP_TEMP="$($PYTHON -c "import tempfile, os; fd, p = tempfile.mkstemp(suffix='.json', prefix='cleanup_self_'); os.close(fd); print(p.replace(os.sep, '/'))")"
gh run list --workflow "$CLEANUP_WORKFLOW" --limit 200 --json databaseId,status,conclusion,headBranch,createdAt > "$CLEANUP_TEMP"

CLEANUP_DELETE_IDS=$($PYTHON << PYEOF
import json
from collections import defaultdict

with open("$CLEANUP_TEMP") as f:
  data = json.load(f)

keep = set()
for r in data:
  if r.get("status") != "completed":
    keep.add(str(r["databaseId"]))

groups = defaultdict(list)
for r in data:
  groups[r.get("headBranch") or ""].append(r)

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

for r in data:
  rid = str(r["databaseId"])
  if rid not in keep:
    print(rid)
PYEOF
)

CLEANUP_COUNT=0
CLEANUP_DELETED=0
for run_id in $CLEANUP_DELETE_IDS; do
  run_id="${run_id%$'\r'}"
  [ -z "$run_id" ] && continue
  CLEANUP_COUNT=$((CLEANUP_COUNT + 1))
  if [ "$DRY_RUN" = false ]; then
    print_info "Deleting superseded Repository Cleanup run $run_id"
    if echo "y" | gh run delete "$run_id" 2>/dev/null; then
      CLEANUP_DELETED=$((CLEANUP_DELETED + 1))
    fi
  else
    print_warning "Would delete Repository Cleanup run $run_id (superseded)"
  fi
done

[ $CLEANUP_COUNT -eq 0 ] && print_success "No extra Repository Cleanup runs to remove" || print_warning "Removed $CLEANUP_DELETED of $CLEANUP_COUNT old Repository Cleanup run(s)"
rm -f "$CLEANUP_TEMP"
echo "::endgroup::"
echo ""

# ============================================================================
# STEP 5: Orphaned workflow runs (workflow file deleted, runs still exist)
# ============================================================================
echo "::group::Step 5: Orphaned workflow runs"
print_info "STEP 5: Checking for runs from deleted/orphaned workflows..."

# Get unique workflow names from the runs we fetched
WORKFLOW_NAMES=$($PYTHON -c "
import json
with open('$TEMP_RUNS') as f:
  data = json.load(f)
seen = set()
for r in data:
  name = r.get('workflowName', '')
  if name and name not in seen:
    seen.add(name)
    print(name)
")

# ACTIVE_WORKFLOWS already computed before Step 4

ORPHANED_COUNT=0
ORPHANED_DELETED=0

while IFS= read -r wf_name; do
  wf_name="${wf_name%$'\r'}"
  [ -z "$wf_name" ] && continue
  # Check if this workflow name exists in active workflow files
  if ! echo "$ACTIVE_WORKFLOWS" | grep -qxF "$wf_name"; then
    # This workflow has runs but no corresponding .yml file — orphaned
    ORPHAN_IDS=$($PYTHON -c "
import json
with open('$TEMP_RUNS') as f:
  data = json.load(f)
for r in data:
  if r.get('workflowName') == '$wf_name':
    print(r['databaseId'])
")
    for run_id in $ORPHAN_IDS; do
      run_id="${run_id%$'\r'}"
      [ -z "$run_id" ] && continue
      ORPHANED_COUNT=$((ORPHANED_COUNT + 1))
      if [ "$DRY_RUN" = false ]; then
        print_info "Deleting orphaned run $run_id (workflow '$wf_name' no longer exists)"
        echo "y" | gh run delete "$run_id" 2>/dev/null && ORPHANED_DELETED=$((ORPHANED_DELETED + 1)) || true
      else
        print_warning "Would delete orphaned run $run_id (workflow '$wf_name' no longer exists)"
      fi
    done
  fi
done <<< "$WORKFLOW_NAMES"

[ $ORPHANED_COUNT -eq 0 ] && print_success "No orphaned workflow runs" || print_warning "Found $ORPHANED_COUNT orphaned run(s)"
echo "::endgroup::"
echo ""

rm -f "$TEMP_RUNS"

# ============================================================================
# SUMMARY
# ============================================================================
echo "========================================"
print_success "CLEANUP SUMMARY"
echo "========================================"
TOTAL=$((OBSOLETE_COUNT + PR_REF_RUNS + DELETED_BRANCH_RUNS + SUPERSEDED_COUNT + CLEANUP_COUNT + ORPHANED_COUNT))
if [ "$DRY_RUN" = true ]; then
  echo "Would clean: $TOTAL runs (obsolete: $OBSOLETE_COUNT, pr-refs: $PR_REF_RUNS, deleted-branch: $DELETED_BRANCH_RUNS, superseded: $SUPERSEDED_COUNT, cleanup-self: $CLEANUP_COUNT, orphaned: $ORPHANED_COUNT)"
  echo ""
  print_info "Run with --execute to perform: $0 --execute"
else
  DELETED=$((OBSOLETE_DELETED + PR_REF_DELETED + DELETED_BRANCH_SUCCESS + SUPERSEDED_DELETED + CLEANUP_DELETED + ORPHANED_DELETED))
  echo "Deleted: $DELETED of $TOTAL runs"
fi
echo ""
