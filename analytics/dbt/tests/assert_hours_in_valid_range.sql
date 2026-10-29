-- Singular test: returns the rows that break the rule. dbt test passes when this returns zero rows.
-- A single entry must be more than 0 and at most 24 hours.
select *
from {{ ref('stg_example_hours') }}
where hours <= 0 or hours > 24
