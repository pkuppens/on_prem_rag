-- One row per work session: duplicates and overlaps removed, activity mapped to its WBSO category.
-- SQL equivalent of WBSODataValidator.validate_duplicates() / step_deduplicate in src/wbso/ ("keep first, drop
-- rest"), as window functions instead of a Python loop. The Python code is not replaced.
-- Rules: (1) duplicate session_id -> keep the first by start time; (2) a session that starts before the latest end
-- of the sessions before it is an overlap and is dropped. Ties break on session_id, so reruns are stable.
with ranked as (
    select
        *,
        row_number() over (partition by session_id order by started_at, ended_at) as id_rank
    from {{ ref('stg_wbso__calendar_events') }}
),

unique_ids as (
    select * exclude (id_rank) from ranked where id_rank = 1
),

with_previous_end as (
    select
        *,
        max(ended_at) over (
            order by started_at, session_id
            rows between unbounded preceding and 1 preceding
        ) as previous_max_end
    from unique_ids
)

select
    session_id,
    activity_name,
    {{ normalize_wbso_category('activity_name') }} as wbso_category,
    started_at,
    ended_at,
    session_date,
    hours,
    location
from with_previous_end
where previous_max_end is null or started_at >= previous_max_end
