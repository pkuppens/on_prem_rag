# dbt in on_prem_rag — why, what, and what was left out

Created: 2026-10-30
Updated: 2026-10-30

A 3-minute read for someone judging this repo as a work sample. For commands and setup see
[technical/DBT.md](technical/DBT.md). Epic: [#190](https://github.com/pkuppens/on_prem_rag/issues/190).

**Status:** the epic is in progress. This page describes only what is merged; everything else is listed under
[Not yet built](#not-yet-built) with its issue, rather than presented as done.

## The problem

The WBSO (R&D tax credit) hours pipeline in [`src/wbso/`](../src/wbso/) is hand-written Python: it reads CSV/JSON
exports, deduplicates, joins reference data and rolls hours up for reporting. That works, but:

- **Correctness is implicit.** Overlapping system-event exports repeat events, and the only protection is
  code paths that someone has to remember to call. There was no declared "this column is unique / not null".
- **Reference data lives in two places.** `repositories.csv` is read by the Python pipeline; any SQL-side
  analysis needs its own copy, and nothing noticed when they drifted.
- **No lineage.** Answering "which file does this reported number come from?" meant reading code.

The question the epic answers: can a declarative SQL layer (dbt on DuckDB, no server) prove the same results
with checks and lineage built in — *without* deleting the Python first (deliberately out of scope until trust is established).

## What was built

| dbt concept | Real problem it solved | Where |
|---|---|---|
| **Project bootstrap** (dbt-duckdb, seed → staging → test) | Zero-infrastructure transform layer next to the pipeline | [#180](https://github.com/pkuppens/on_prem_rag/issues/180), [PR #224](https://github.com/pkuppens/on_prem_rag/pull/224), [`analytics/dbt/`](../analytics/dbt/) |
| **Sources** with freshness | Pipeline outputs are declared, not guessed: raw commit CSVs can't be parsed reliably (unescaped `\|`, one UTF-16 file), so the source is the processed JSON; stale data warns after 7 days | [#181](https://github.com/pkuppens/on_prem_rag/issues/181), [PR #227](https://github.com/pkuppens/on_prem_rag/pull/227), [`_wbso__sources.yml`](../analytics/dbt/models/staging/wbso/_wbso__sources.yml) |
| **Staging / intermediate layers** | Repo `owner/name` split once, so commits join to repositories in one place | [`stg_wbso__repositories`](../analytics/dbt/models/staging/wbso/stg_wbso__repositories.sql), [`int_wbso__commits_in_period`](../analytics/dbt/models/intermediate/wbso/int_wbso__commits_in_period.sql) |
| **Seeds** | Repository reference list is versioned data, not a loose file | [`wbso_repositories.csv`](../analytics/dbt/seeds/wbso_repositories.csv) |
| **Custom (singular) tests** | Seed vs. Python-pipeline CSV drift is detected automatically | [`assert_wbso_repositories_seed_matches_pipeline.sql`](../analytics/dbt/tests/assert_wbso_repositories_seed_matches_pipeline.sql), [`assert_hours_in_valid_range.sql`](../analytics/dbt/tests/assert_hours_in_valid_range.sql) |
| **Packages** (`dbt_utils`, version-pinned lockfile) | Same package code on every machine and in CI | [`packages.yml`](../analytics/dbt/packages.yml) |
| **Vars** | Reporting period changes per run (`--vars`), no SQL edit for 2026 | [`dbt_project.yml`](../analytics/dbt/dbt_project.yml) |
| **Environments** (`dev` file DB, `ci` in-memory) | Dev can sample rows for speed; CI always builds the full set | [`profiles.yml`](../analytics/dbt/profiles.yml), [#192](https://github.com/pkuppens/on_prem_rag/issues/192), [PR #231](https://github.com/pkuppens/on_prem_rag/pull/231) |

## Before / after: reference data drift

**Before.** `repositories.csv` fed the Python pipeline (`src/wbso/activity_repo_mapping.py`). A SQL copy
would silently go stale the first time someone edited one file.

**After.** The CSV is a dbt seed, and a singular test compares it with the pipeline's file in both directions:

```sql
(select 'only_in_seed'     as side, * from (select * from seed     except select * from pipeline))
union all
(select 'only_in_pipeline' as side, * from (select * from pipeline except select * from seed))
```

A dbt test fails if it returns any row, so any edit to one copy fails the build and prints which side has the extra row.
Trade-off worth discussing: the seed is a *copy* (dbt seeds must live in the project), so the test is the
safety net; the alternative of reading the CSV as a source was rejected because a seed can be `ref()`-ed and
typed in `dbt_project.yml`.

## Not yet built

Open issues in the epic; this page will be extended when they merge:
staging models [#182](https://github.com/pkuppens/on_prem_rag/issues/182), session dedup as a window-function model [#183](https://github.com/pkuppens/on_prem_rag/issues/183), rollup marts [#184](https://github.com/pkuppens/on_prem_rag/issues/184), CI wiring [#185](https://github.com/pkuppens/on_prem_rag/issues/185), docs/lineage [#186](https://github.com/pkuppens/on_prem_rag/issues/186), evaluation-run mart [#188](https://github.com/pkuppens/on_prem_rag/issues/188), ingestion lineage snapshot [#189](https://github.com/pkuppens/on_prem_rag/issues/189), custom generic test [#196](https://github.com/pkuppens/on_prem_rag/issues/196),
shared macro [#193](https://github.com/pkuppens/on_prem_rag/issues/193), surrogate keys [#194](https://github.com/pkuppens/on_prem_rag/issues/194),
`date_spine` [#195](https://github.com/pkuppens/on_prem_rag/issues/195), exposures [#197](https://github.com/pkuppens/on_prem_rag/issues/197).

## Deliberately out of scope

Scoping judgment, from [#190](https://github.com/pkuppens/on_prem_rag/issues/190):

- **Semantic Layer / MetricFlow**, **model contracts and versions**, **dbt Mesh**: solve cross-team and
  public-interface problems that a single-repo project does not have.
- **Python models**: limited DuckDB support; SQL-first is the priority.
- **dbt Cloud scheduling**: this runs dbt-core locally and in GitHub Actions.
- **Deleting the existing Python ETL**: each dbt equivalent must prove itself first; retirement is a separate decision.
