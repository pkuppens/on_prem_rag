-- Registered WBSO work sessions, renamed and typed one-to-one from the calendar_events source (no business logic).
-- dbt-side counterpart of the session load in src/wbso/ (CalendarEvent); the Python code stays in place for now.
select
    session_id,
    summary as activity_name,
    cast(start_datetime as timestamp) as started_at,
    cast(end_datetime as timestamp) as ended_at,
    cast(date as date) as session_date,
    cast(hours as double) as hours,
    location,
    description
from {{ source('wbso', 'calendar_events') }}
