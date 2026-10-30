{{ config(
    materialized='incremental',
    unique_key='month_start',
    incremental_strategy='delete+insert'
) }}
-- Hours per calendar month. Incremental: a run recomputes only months from the latest loaded month onward
-- (delete+insert on month_start). Earlier months are closed once registered; the latest month can still receive late
-- corrections, which is why it is replaced rather than appended. Use --full-refresh after a rule change.
-- Months without sessions have no row here; mart_hours_by_month_gapless fills them with zero.
select
    cast(date_trunc('month', session_date) as date) as month_start,
    count(*) as session_count,
    round(sum(hours), 2) as total_hours
from {{ ref('int_wbso__sessions_deduped') }}
{% if is_incremental() %}
where session_date >= (select max(month_start) from {{ this }})
{% endif %}
group by 1
