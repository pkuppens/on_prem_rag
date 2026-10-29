-- Demo staging model: cleans the raw CSV seed `example_hours_raw` into a tidy view.
--
-- How a model works:
--   * This file is a plain `select`. dbt wraps it in `create view stg_example_hours as ...`
--     (view because dbt_project.yml sets staging/ to +materialized: view).
--   * {{ ref('example_hours_raw') }} points at another model or seed by name. dbt replaces it with
--     the real table name AND records the dependency, so it always builds the seed first. Those
--     dependencies are what the lineage graph in `dbt docs` is drawn from.
--   * Descriptions and tests for this model live in _staging.yml, not here.
--
-- Staging convention: one stg_ model per raw input; only rename, cast and clean. No joins, no aggregation.
select
    work_date,
    lower(trim(category)) as category, -- ' research ' and 'DEVELOPMENT' become 'research' and 'development'
    hours,
    note
from {{ ref('example_hours_raw') }}
