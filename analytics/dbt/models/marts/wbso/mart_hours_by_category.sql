-- Hours per WBSO category, rebuilt from the activity name with the same macro as the intermediate model.
-- Declarative replacement for the Counter / func.sum(case(...)) rollups in src/wbso/database_reporting.py and
-- audit_trail/wbso_report_generator.py (both stay in place).
select
    {{ dbt_utils.generate_surrogate_key(['wbso_category']) }} as category_key,
    wbso_category,
    count(*) as session_count,
    round(sum(hours), 2) as total_hours
from (
    select {{ normalize_wbso_category('activity_name') }} as wbso_category, hours
    from {{ ref('int_wbso__sessions_deduped') }}
)
group by 1, 2
