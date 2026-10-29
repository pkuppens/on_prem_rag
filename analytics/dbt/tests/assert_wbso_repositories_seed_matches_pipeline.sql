-- The wbso_repositories seed is a copy of docs/project/hours/data/repositories.csv, which the Python pipeline reads.
-- Returns rows present in one but not the other; any row means the copies drifted. Fix: copy the file again.
with seed as (
    select repo_name, repo_description, wbso_relevance from {{ ref('wbso_repositories') }}
),

pipeline as (
    select repo_name, repo_description, wbso_relevance
    from read_csv('../../docs/project/hours/data/repositories.csv', header = true, all_varchar = true)
)

(select 'only_in_seed' as side, * from (select * from seed except select * from pipeline))
union all
(select 'only_in_pipeline' as side, * from (select * from pipeline except select * from seed))
