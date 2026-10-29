-- Commits inside the WBSO grant period, with the repository's WBSO relevance attached.
{#
  Jinja comment: unlike a SQL -- comment, dbt does not render it, so it can mention template syntax.
  var('...') reads project variables from dbt_project.yml (or --vars on the command line), so the period
  changes per run without editing SQL. target.name is the active profile output (dev or ci).
#}
select
    c.hash,
    c."timestamp" as committed_at,
    c.date as commit_date,
    c.repo_name,
    c.author,
    c.message,
    c.is_wbso,
    r.repo_name is not null as is_tracked_repo,
    coalesce(r.is_core_wbso, false) as is_core_wbso_repo
from {{ source('wbso', 'commits') }} as c
left join {{ ref('stg_wbso__repositories') }} as r
    on c.repo_name = r.repo_name
where c.date between cast('{{ var("wbso_period_start") }}' as date) and cast('{{ var("wbso_period_end") }}' as date)
{% if target.name == 'dev' and var('dev_sample_rows') | int > 0 %}
-- Dev-only sample for quick iteration; CI always builds the full set.
order by c."timestamp" desc
limit {{ var('dev_sample_rows') }}
{% endif %}
