-- Commits from the Stage 2 output (commits_processed.json), renamed one-to-one. dbt-side counterpart of the
-- normalization in scripts/process_commits.py; the script is not removed.
select
    hash as commit_sha,
    "timestamp" as committed_at,
    cast(date as date) as commit_date,
    repo_name,
    author,
    message,
    is_wbso,
    outside_work_block
from {{ source('wbso', 'commits') }}
