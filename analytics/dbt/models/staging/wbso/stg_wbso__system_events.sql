-- Windows system events from every export file, typed and renamed. Overlapping exports repeat events, so rows are
-- NOT unique here; deduplication is a later (intermediate) concern.
-- DateTime arrives in two text formats; try_strptime returns NULL for the format that does not match.
select
    coalesce(
        try_strptime("DateTime", '%Y/%m/%d %H:%M:%S'),
        try_strptime("DateTime", '%m/%d/%Y %I:%M:%S %p')
    ) as event_at,
    cast("EventId" as varchar) as event_id,
    "EventType" as event_type,
    "Username" as username,
    "RecordId" as record_id,
    filename as source_file
from {{ source('wbso', 'system_events') }}
