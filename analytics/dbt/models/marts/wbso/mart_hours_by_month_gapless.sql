-- Every month from the first to the last session month, zero-filled.
-- Before: a month with no logged hours had no row, so a chart silently skipped it.
-- After: dbt_utils.date_spine generates the calendar and the monthly mart is left-joined onto it.
with calendar as (
    {{ dbt_utils.date_spine(
        datepart='month',
        start_date="(select min(month_start) from " ~ ref('mart_hours_by_month') ~ ")",
        end_date="(select max(month_start) + interval 1 month from " ~ ref('mart_hours_by_month') ~ ")"
    ) }}
)

select
    cast(c.date_month as date) as month_start,
    coalesce(m.session_count, 0) as session_count,
    coalesce(m.total_hours, 0) as total_hours
from calendar as c
left join {{ ref('mart_hours_by_month') }} as m on cast(c.date_month as date) = m.month_start
