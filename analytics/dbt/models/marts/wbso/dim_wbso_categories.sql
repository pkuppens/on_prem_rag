-- One row per WBSO category with a deterministic surrogate key: a hash of the natural key, so a category gets the
-- same key on every run and machine. dbt-side equivalent of the _category_cache (code -> id) that
-- src/wbso/migration.py fills in load order; migration.py is not changed.
select distinct
    {{ dbt_utils.generate_surrogate_key(['wbso_category']) }} as category_key,
    wbso_category as category_code
from {{ ref('int_wbso__sessions_deduped') }}
