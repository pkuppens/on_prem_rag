-- Repositories tracked for WBSO, from the wbso_repositories seed.
-- Splits 'owner/name' so repo_name joins to the commits source, which only stores the name.
select
    split_part(repo_name, '/', 1) as repo_owner,
    split_part(repo_name, '/', 2) as repo_name,
    repo_name as repo_full_name,
    repo_description,
    wbso_relevance,
    wbso_relevance like 'Core WBSO%' as is_core_wbso
from {{ ref('wbso_repositories') }}
